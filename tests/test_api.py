import time
import uuid
from concurrent.futures import ThreadPoolExecutor
import pytest
from backend.reviewer import SAMPLES


def post(client, sample="mixed", key=None, text=None):
    return client.post(
        "/api/v1/reviews",
        headers={"Idempotency-Key": key or str(uuid.uuid4())},
        json={
            "report_text": text
            if text is not None
            else next(x["report_text"] for x in SAMPLES if x["id"] == sample)
        },
    )


def finish(client, response):
    assert response.status_code == 202, response.text
    rid = response.json()["id"]
    for _ in range(300):
        d = client.get("/api/v1/reviews/" + rid).json()
        if d["execution_status"] not in ("running", "queued"):
            return d
        time.sleep(0.02)
    raise AssertionError("Review did not terminate")


@pytest.mark.parametrize(
    "sample,missed,critical,status,outcome",
    [
        ("mixed", None, True, "unknown", "observations"),
        ("critical", None, True, "unknown", "observations"),
        ("critical_documented", False, True, "documented_flagged", "observations"),
        ("critical_unflagged", True, True, "documented_not_flagged", "observations"),
        ("clean", False, False, "unknown", "no_observations"),
        ("discrepancy", False, False, "unknown", "observations"),
        ("language", False, False, "unknown", "observations"),
    ],
)
def test_report_only_results(client, sample, missed, critical, status, outcome):
    d = finish(client, post(client, sample))
    assert d["execution_status"] == "completed", d
    r = d["result"]
    assert (
        r["missed_flag"],
        r["critical_finding_detected"],
        r["critical_flag_status"],
        r["outcome"],
    ) == (missed, critical, status, outcome)
    assert all(s["status"] == "completed" for s in d["steps"])
    assert set(d["input"]) == {"report_text"}
    if r["critical_flag_quote"]:
        assert r["critical_flag_quote"] in d["input"]["report_text"]
    if outcome == "no_observations":
        assert not r["copy_text"]
    else:
        assert r["copy_text"].startswith("PACS comments:")
        label = "Cannot determine" if missed is None else "Yes" if missed else "No"
        assert "Critical Findings missed flag: " + label in r["copy_text"]
        assert (
            r["copy_text"].index("PACS comments:")
            < r["copy_text"].index("Critical Findings missed flag:")
            < r["copy_text"].index("Critical Findings comments:")
        )


def test_removed_flag_is_rejected_and_report_required(client):
    payload = {
        "report_text": SAMPLES[0]["report_text"],
        "radiologist_critical_flag": True,
    }
    assert (
        client.post(
            "/api/v1/reviews",
            headers={"Idempotency-Key": str(uuid.uuid4())},
            json=payload,
        ).status_code
        == 422
    )
    assert post(client, text="   ").status_code == 422
    schema = client.get("/openapi.json").json()["components"]["schemas"]["ReviewInput"]
    assert schema["required"] == ["report_text"] and set(schema["properties"]) == {
        "report_text"
    }


def test_missing_section(client):
    d = finish(client, post(client, text="Findings: Lungs are clear."))
    assert d["execution_status"] == "needs_input" and d["result"] is None
    assert all(s["status"] == "skipped" for s in d["steps"][1:])


def test_arbitrary_demo_input_fails_explicitly(client):
    d = finish(
        client,
        post(
            client,
            text="Findings: A different synthetic report. Impression: Unrelated report.",
        ),
    )
    assert d["execution_status"] == "failed" and d["result"] is None
    assert d["error"]["code"] == "DEMO_INPUT_UNSUPPORTED"


def test_concurrent_idempotency_and_report_change(client):
    key = str(uuid.uuid4())
    with ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(pool.map(lambda _: post(client, key=key), range(4)))
    assert len({r.json()["id"] for r in responses}) == 1
    assert post(client, key=key, sample="clean").status_code == 409
    a = finish(client, responses[0])
    b = finish(client, post(client, sample="clean"))
    assert a["input_hash"] != b["input_hash"]


def test_feedback_minimal_and_bindings(client):
    d = finish(client, post(client, "clean"))
    url = "/api/v1/reviews/" + d["id"] + "/feedback"
    payload = dict(rating="down", reason="missed_observation")
    key = str(uuid.uuid4())
    r = client.post(url, headers={"Idempotency-Key": key}, json=payload)
    assert r.status_code == 201, r.text
    assert r.json()["explanation"] is None and "input_hash" not in r.json()
    assert (
        client.post(url, headers={"Idempotency-Key": key}, json=payload).json()[
            "id"
        ]
        == r.json()["id"]
    )
    assert len(client.get(url).json()["items"]) == 1
    assert (
        client.post(
            url,
            headers={"Idempotency-Key": str(uuid.uuid4())},
            json={**payload, "result_version": 2},
        ).status_code
        == 422
    )
    assert (
        client.post(
            url,
            headers={"Idempotency-Key": str(uuid.uuid4())},
            json={**payload, "target": "observation", "observation_id": "obs-invalid"},
        ).status_code
        == 422
    )
    assert (
        client.post(
            url,
            headers={"Idempotency-Key": str(uuid.uuid4())},
            json={"rating": "down"},
        ).status_code
        == 422
    )


def test_no_live_fallback(client, monkeypatch):
    monkeypatch.setenv("QA_MODE", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    r = post(client)
    assert r.status_code == 503 and r.json()["error"]["code"] == "MODEL_NOT_CONFIGURED"
