import uuid
import pytest
from backend.contracts import parse_sections, section_index, ReviewProblem
from backend import store
from test_api import post, finish
from test_api_design import credentials, create_as, finish_as


@pytest.mark.parametrize(
    "text",
    [
        "CT chest. Findings: Lungs are clear. Impression: No acute abnormality.",
        "CT chest FINDINGS Lungs are clear. IMPRESSION No acute abnormality.",
        "  Findings: Lungs are clear. Impression: No acute abnormality.",
        "History: cough. Findings: Lungs are clear. Conclusion: No acute abnormality.",
    ],
)
def test_compressed_sections_preserve_exact_offsets(text):
    parsed = parse_sections(text)
    assert parsed["findings"] == "Lungs are clear."
    assert parsed["impression"] == "No acute abnormality."
    for section in section_index(text):
        if section["kind"] in parsed:
            assert (
                text[section["start"] : section["end"]].strip()
                == parsed[section["kind"]]
            )


def test_mentions_and_addenda_are_not_new_sections():
    text = "Findings: See the Impression: for interpretation.\nImpression: No acute abnormality.\nAddendum: Correction to the Impression: unchanged."
    assert len([s for s in section_index(text) if s["kind"] == "impression"]) == 1
    assert parse_sections(text)["findings"] == "See the Impression: for interpretation."
    with pytest.raises(ReviewProblem):
        parse_sections("The findings are normal and my impression is unchanged.")
    with pytest.raises(ReviewProblem):
        parse_sections(
            "Findings: Clear. Impression: Normal. Findings: Clear. Impression: Normal."
        )


def test_comments_only_copy_and_historical_storage_unchanged(client):
    review = finish(client, post(client))
    result = review["result"]
    assert "missed flag" not in result["comments_copy_text"]
    assert "missed flag" not in result["critical_comments_copy_text"]
    assert "Critical Findings comments:" in result["critical_comments_copy_text"]
    stored = store.get("vesta", review["id"])
    assert "missed flag" in stored["result"]["copy_text"]
    assert stored["input"] == review["input"]
    from backend import presentation
    stored['result']['general_copy_text'] = 'QA review:\n\nGeneral Comments:\n1. Old formatting'
    projected = presentation.review(stored)['result']
    for field in ('general_copy_text', 'comments_copy_text', 'critical_comments_copy_text'):
        assert 'QA review' not in projected[field]
        assert all(not line.split('. ', 1)[0].isdigit() for line in projected[field].splitlines() if '. ' in line)
    assert projected['general_copy_text'] == 'PACS comments:\n' + '\n\n'.join(x['comment'] for x in stored['result']['general_comments'])
    assert presentation.review(stored)['result']['general_copy_text'].startswith('PACS comments:')


def test_history_filters_pagination_feedback_and_restart_reads(client):
    first = finish(client, post(client, "mixed"))
    second = finish(client, post(client, "clean"))
    endpoint = "/api/v1/reviews"
    feedback = client.post(
        f"{endpoint}/{first['id']}/feedback",
        headers={"Idempotency-Key": uuid.uuid4().hex},
        json={
            "rating": "down",
            "reason": "unclear_wording",
            "explanation": "Be concise.",
        },
    )
    assert feedback.status_code == 201
    page = client.get(
        endpoint,
        params={"q": first["id"], "has_feedback": "true", "critical": "true"},
    ).json()
    assert page["items"][0]["feedback_count"] == 1
    assert "input" not in page["items"][0]
    assert (
        client.get(
            endpoint, params={"q": second["id"], "outcome": "no_observations"}
        ).json()["items"][0]["general_count"]
        == 0
    )
    page = client.get(endpoint, params={"limit": 1}).json()
    assert page["has_more"] and page["items"][0]["id"] == second["id"]
    next_page = client.get(
        endpoint, params={"limit": 1, "starting_after": page["next_cursor"]}
    ).json()
    assert next_page["items"][0]["id"] == first["id"]
    store.init()  # reopen persistent store, never browser-only history
    assert (
        client.get(f"{endpoint}/{first['id']}/feedback").json()["items"][0][
            "explanation"
        ]
        == "Be concise."
    )
    assert client.get(endpoint, params={"status": "invented"}).status_code == 422
    assert client.get(endpoint, params={"starting_after": "absent"}).status_code == 400


def test_history_tenant_and_feedback_scope(client, credentials):
    b = finish_as(
        client, create_as(client, credentials["b"], uuid.uuid4().hex), credentials["b"]
    )
    assert (
        client.get(
            "/api/v1/reviews", params={"q": b["id"]}, headers=credentials["a"]
        ).json()["items"]
        == []
    )
    assert (
        client.get(
            "/api/v1/reviews",
            params={"starting_after": b["id"]},
            headers=credentials["a"],
        ).status_code
        == 400
    )
    read = client.get("/api/v1/reviews", headers=credentials["read"]).json()
    assert all(item["feedback_count"] is None for item in read["items"])
    assert (
        client.get(
            "/api/v1/reviews?has_feedback=true", headers=credentials["read"]
        ).status_code
        == 403
    )
