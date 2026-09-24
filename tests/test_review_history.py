from datetime import datetime, timedelta, timezone

from backend import presentation, store
from backend.contracts import ReviewInput


def config():
    return {"mode": "demo", "workflow_version": "controlled"}


def finish(review_id):
    store.update(
        "vesta",
        review_id,
        execution_status="completed",
        result={
            "result_version": 1,
            "outcome": "observations",
            "critical_finding_detected": True,
            "general_comments": [
                {
                    "observation_id": "obs-1",
                    "finding_type": "suggestion",
                    "report_section": "findings",
                    "comment": "Please reconcile the comparison statement.",
                }
            ],
            "critical_comments": [
                {
                    "observation_id": "obs-2",
                    "finding_type": "discrepancy",
                    "report_section": "impression",
                    "comment": "Potential Critical Finding: Controlled test only. Please review.",
                }
            ],
        },
    )


def test_history_summary_uses_display_id_actor_and_submission_time_filters(monkeypatch, tmp_path):
    monkeypatch.setattr(store, "DATA", tmp_path)
    store.init()
    saved, _ = store.reserve(
        "vesta",
        "history-test",
        ReviewInput(report_text="Findings: controlled. Impression: controlled."),
        config(),
        submitted_by="Samson",
    )
    review_id = saved["body"]["id"]
    finish(review_id)
    record = store.get("vesta", review_id)
    created = datetime.fromisoformat(record["created_at"])

    rows, more = store.list_reviews("vesta", submitted_after=(created - timedelta(seconds=1)).isoformat())
    assert not more and len(rows) == 1
    assert rows[0]["display_id"] == review_id[-5:].upper()
    assert rows[0]["submitted_by"] == "Samson"
    assert rows[0]["general_count"] == 1 and rows[0]["critical_count"] == 1

    future = (created + timedelta(seconds=1)).astimezone(timezone.utc).isoformat()
    assert store.list_reviews("vesta", submitted_after=future)[0] == []


def test_history_comment_type_filters_distinguish_general_and_critical_comments(monkeypatch, tmp_path):
    monkeypatch.setattr(store, "DATA", tmp_path)
    store.init()

    def create(key, general, critical):
        saved, _ = store.reserve(
            "vesta", key, ReviewInput(report_text=f"Findings: {key}. Impression: {key}."), config()
        )
        review_id = saved["body"]["id"]
        store.update(
            "vesta",
            review_id,
            execution_status="completed",
            result={
                "result_version": 1,
                "outcome": "observations" if general or critical else "no_observations",
                "critical_finding_detected": critical,
                "general_comments": ([{"observation_id": f"{key}-g", "finding_type": "suggestion", "report_section": "findings", "comment": "General."}] if general else []),
                "critical_comments": ([{"observation_id": f"{key}-c", "finding_type": "discrepancy", "report_section": "impression", "comment": "Critical."}] if critical else []),
            },
        )
        return review_id

    general = create("general-only", True, False)
    critical = create("critical-only", False, True)
    no_comments = create("no-comments", False, False)

    assert {row["id"] for row in store.list_reviews("vesta", comment_type="any")[0]} == {general, critical, no_comments}
    assert [row["id"] for row in store.list_reviews("vesta", comment_type="general")[0]] == [general]
    assert [row["id"] for row in store.list_reviews("vesta", comment_type="critical")[0]] == [critical]


def test_history_failed_filter_includes_needs_input(monkeypatch, tmp_path):
    monkeypatch.setattr(store, "DATA", tmp_path)
    store.init()

    def create(key, status):
        saved, _ = store.reserve(
            "vesta", key, ReviewInput(report_text=f"Findings: {key}. Impression: {key}."), config()
        )
        review_id = saved["body"]["id"]
        if status != "queued":
            store.update("vesta", review_id, execution_status=status)
        return review_id

    failed = create("failed", "failed")
    needs_input = create("needs-input", "needs_input")
    create("queued", "queued")

    assert {row["id"] for row in store.list_reviews("vesta", status_group="failed_or_needs_input")[0]} == {failed, needs_input}


def test_comments_projection_exposes_observations_without_raw_report(monkeypatch, tmp_path):
    monkeypatch.setattr(store, "DATA", tmp_path)
    store.init()
    saved, _ = store.reserve(
        "vesta",
        "comments-test",
        ReviewInput(report_text="Findings: confidential text. Impression: confidential text."),
        config(),
    )
    review_id = saved["body"]["id"]
    finish(review_id)

    comments = presentation.comments(store.get("vesta", review_id))
    assert comments["review_id"] == review_id
    assert comments["general_comments"][0]["comment"].startswith("Please reconcile")
    assert comments["critical_comments"][0]["comment"].startswith("Potential Critical Finding")
    assert "report_text" not in comments
    assert "confidential" not in str(comments)


def test_history_routes_filter_by_latest_submission_and_hide_raw_text(client):
    saved, _ = store.reserve(
        "vesta",
        "history-route",
        ReviewInput(report_text="Findings: route-private text. Impression: route-private text."),
        config(),
        submitted_by="Demo operator",
    )
    review_id = saved["body"]["id"]
    created = store.get("vesta", review_id)["created_at"]
    response = client.get(
        "/api/v1/reviews",
        params={"q": review_id, "submitted_after": (datetime.fromisoformat(created) - timedelta(seconds=1)).isoformat()},
    )
    assert response.status_code == 200, response.text
    item = response.json()["items"][0]
    assert item["display_id"] == review_id[-5:].upper()
    assert item["submitted_by"] == "Demo operator"

    comments = client.get(f"/api/v1/reviews/{review_id}/comments")
    assert comments.status_code == 200
    assert "report_text" not in comments.json()
    assert "route-private" not in comments.text

    invalid = client.get(
        "/api/v1/reviews",
        params={"submitted_after": created, "submitted_before": created},
    )
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "INVALID_SUBMISSION_RANGE"
