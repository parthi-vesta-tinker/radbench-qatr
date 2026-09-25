"""Controlled JEV classification through the real API, DBOS queue and HTTP adapter."""

import json
import time
import uuid

import httpx
import pytest

from backend import jev, store, classification_store
from backend.classification import ClassificationProblem, snapshot
from backend.contracts import ClassificationInput
from backend.reviewer import SAMPLES


@pytest.fixture
def workspace(client, monkeypatch, tmp_path):
    monkeypatch.setattr(store, "DATA", tmp_path / "data")
    store.init()
    monkeypatch.setenv("QA_JEV_ENABLED", "false")
    monkeypatch.setenv("TYPESAFE_API_KEY", "controlled-test-key")
    monkeypatch.setenv("QA_JEV_MODEL", "jev-1.13.0")
    return client


def responses(monkeypatch, outcome="valid"):
    calls = []

    def respond(request):
        assert request.url == jev.URL
        calls.append(json.loads(request.content))
        if outcome == "timeout":
            raise httpx.ReadTimeout("controlled timeout")
        if outcome == "busy":
            return httpx.Response(429, json={"detail": "private provider response"})
        answers = {}
        for field, question in calls[-1]["questions"].items():
            options = list(question["criteria"])
            chosen = {"finding_group": "thoracic", "polarity": "affirmed", "certainty": "definite",
                      "temporal_status": "not_stated", "urgency": "minutes" if outcome == "urgent" else "cannot_determine"}[field]
            values = {label: 1.0 if label == chosen else 0.0 for label in options}
            if outcome == "bad_distribution" and field == "urgency":
                values[chosen] = .8
            answers[field] = {"type": "choice", "choice": chosen,
                              "probabilities": values, "confidence": .93}
        return httpx.Response(200, json={"model": "jev-1.13.0", "answers": answers,
                                         "usage": {"input_tokens": 40, "output_tokens": 15}})

    monkeypatch.setattr(jev, "make_client", lambda timeout: httpx.Client(
        transport=httpx.MockTransport(respond), timeout=timeout))
    return calls


def review(client, sample="critical"):
    text = next(item["report_text"] for item in SAMPLES if item["id"] == sample)
    accepted = client.post("/api/v1/reviews", json={"report_text": text},
                           headers={"Idempotency-Key": str(uuid.uuid4())})
    assert accepted.status_code == 202, accepted.text
    rid = accepted.json()["id"]
    for _ in range(200):
        item = client.get("/api/v1/reviews/" + rid).json()
        if item["execution_status"] not in ("queued", "running"):
            return item
        time.sleep(.025)
    raise AssertionError("Review did not finish")


def classify(client, review, key=None):
    return client.post("/api/v1/classifications", json={
        "review_id": review["id"], "input_version": review["input_version"],
        "observation_id": review["result"]["critical_comments"][0]["observation_id"],
    }, headers={"Idempotency-Key": key or str(uuid.uuid4())})


def settle(client, rid):
    for _ in range(200):
        item = client.get("/api/v1/classifications/" + rid).json()
        if item["execution_status"] in ("completed", "failed"):
            return item
        time.sleep(.025)
    raise AssertionError("Classification did not finish")


def test_critical_review_uses_one_five_question_jev_request(workspace, monkeypatch):
    calls = responses(monkeypatch)
    source = review(workspace)
    monkeypatch.setenv("QA_JEV_ENABLED", "true")
    accepted = classify(workspace, source)
    assert accepted.status_code == 202, accepted.text
    run = settle(workspace, accepted.json()["id"])
    assert run["execution_status"] == "completed", run
    assert run["source_status"] == "current"
    assert run["result"]["fields"]["finding_group"]["label"] == "thoracic"
    assert run["result"]["human_review_required"] is True
    assert len(calls) == 1 and len(calls[0]["questions"]) == 5
    assert calls[0]["state"]["qa_comment"] == source["result"]["critical_comments"][0]["comment"]
    assert calls[0]["state"]["report_context"] == source["input"]["report_text"]
    assert calls[0]["state"]["target"]["report_excerpts"]
    assert "finding_text" not in calls[0]["state"]
    assert "report_quotes" not in calls[0]["state"]
    assert "Authorization" not in json.dumps(run)
    assert "report_quotes" not in run["input"]
    assert len(workspace.get(f'/api/v1/reviews/{source["id"]}/classifications').json()) == 1


def test_noncritical_review_never_calls_jev(workspace, monkeypatch):
    calls = responses(monkeypatch)
    monkeypatch.setenv("QA_JEV_ENABLED", "true")
    source = review(workspace, "clean")
    payload = {"review_id": source["id"], "input_version": source["input_version"], "observation_id": "obs-1"}
    denied = workspace.post("/api/v1/classifications", json=payload,
                            headers={"Idempotency-Key": str(uuid.uuid4())})
    assert denied.status_code == 422 and denied.json()["error"]["code"] == "NO_CRITICAL_FINDING"
    assert calls == []


def test_urgent_suggestion_requires_visible_review_cue(workspace, monkeypatch):
    responses(monkeypatch, "urgent")
    source = review(workspace)
    monkeypatch.setenv("QA_JEV_ENABLED", "true")
    run = settle(workspace, classify(workspace, source).json()["id"])
    assert run["execution_status"] == "completed"
    urgency = run["result"]["fields"]["urgency"]
    assert urgency["label"] == "minutes"
    assert any("Verify this draft communication priority" in text for text in urgency["review_reasons"])


def test_receipt_replay_and_feedback_are_immutable(workspace, monkeypatch):
    responses(monkeypatch)
    source = review(workspace)
    monkeypatch.setenv("QA_JEV_ENABLED", "true")
    key = str(uuid.uuid4())
    first = classify(workspace, source, key)
    assert first.status_code == 202, first.text
    run = settle(workspace, first.json()["id"])
    monkeypatch.delenv("TYPESAFE_API_KEY")
    replay = classify(workspace, source, key)
    assert replay.status_code == 202 and replay.json() == first.json()
    assert replay.headers["Idempotency-Replayed"] == "true"
    rejected = workspace.post("/api/v1/classifications", json={"review_id": source["id"],
        "input_version": source["input_version"], "observation_id": "obs-other"},
        headers={"Idempotency-Key": key})
    assert rejected.status_code == 409
    fbkey = str(uuid.uuid4())
    accepted = workspace.post(f'/api/v1/classifications/{run["id"]}/feedback',
        json={"action": "accept"}, headers={"Idempotency-Key": fbkey})
    assert accepted.status_code == 201, accepted.text
    assert accepted.json()["predicted_labels"] == accepted.json()["final_labels"]
    assert workspace.post(f'/api/v1/classifications/{run["id"]}/feedback',
        json={"action": "accept"}, headers={"Idempotency-Key": fbkey}).json() == accepted.json()
    assert workspace.get(f'/api/v1/classifications/{run["id"]}/feedback').json()["items"][0]["action"] == "accept"


@pytest.mark.parametrize("outcome,code", [("bad_distribution", "JEV_INVALID_OUTPUT"),
                                          ("timeout", "MODEL_OUTCOME_UNKNOWN"),
                                          ("busy", "JEV_BUSY")])
def test_provider_failures_never_become_empty_success(workspace, monkeypatch, outcome, code):
    calls = responses(monkeypatch, outcome)
    source = review(workspace)
    monkeypatch.setenv("QA_JEV_ENABLED", "true")
    accepted = classify(workspace, source)
    run = settle(workspace, accepted.json()["id"])
    assert run["execution_status"] == "failed", run
    assert run["result"] is None and run["error"]["code"] == code
    assert len(calls) == 1


def test_automatic_classification_only_after_critical_review(workspace, monkeypatch):
    calls = responses(monkeypatch)
    monkeypatch.setenv("QA_JEV_ENABLED", "true")
    source = review(workspace)
    found = []
    for _ in range(200):
        found = workspace.get(f'/api/v1/reviews/{source["id"]}/classifications').json()
        if found and found[0]["execution_status"] in ("completed", "failed"):
            break
        time.sleep(.05)
    assert len(found) == 1, found
    assert found[0]["execution_status"] == "completed", found
    assert len(calls) == 1


def test_claimed_attempt_is_unknown_on_recovery_without_a_second_request(workspace, monkeypatch):
    calls = responses(monkeypatch)
    source = review(workspace)
    monkeypatch.setenv("QA_JEV_ENABLED", "true")
    payload = ClassificationInput(review_id=source["id"], input_version=source["input_version"],
                                  observation_id=source["result"]["critical_comments"][0]["observation_id"])
    accepted, created = classification_store.reserve("vesta", str(uuid.uuid4()), payload, snapshot())
    assert created
    rid = accepted["body"]["id"]
    # The provider might have received the request before this process stopped.
    assert classification_store.claim("vesta", rid)
    input_data, config = classification_store.job("vesta", rid)
    with pytest.raises(ClassificationProblem) as caught:
        jev.dispatch_once("vesta", rid, input_data, config)
    assert caught.value.code == "MODEL_OUTCOME_UNKNOWN"
    assert classification_store.attempt("vesta", rid)["outcome"] == "unknown"
    assert calls == []


def test_replaced_review_does_not_attach_old_classification(workspace, monkeypatch):
    responses(monkeypatch)
    source = review(workspace)
    monkeypatch.setenv("QA_JEV_ENABLED", "true")
    run = settle(workspace, classify(workspace, source).json()["id"])
    clean = next(item["report_text"] for item in SAMPLES if item["id"] == "clean")
    replacement = workspace.put(f'/api/v1/reviews/{source["id"]}',
        json={"report_text": clean, "expected_input_version": source["input_version"]},
        headers={"Idempotency-Key": str(uuid.uuid4())})
    assert replacement.status_code == 202, replacement.text
    old = workspace.get(f'/api/v1/classifications/{run["id"]}').json()
    assert old["source_status"] == "superseded"
    assert old["result"] == run["result"]
    assert workspace.get(f'/api/v1/reviews/{source["id"]}/classifications').json() == []


def test_analysis_uses_saved_request_and_excludes_private_metadata(workspace, monkeypatch):
    calls = responses(monkeypatch)
    source = review(workspace)
    monkeypatch.setenv("QA_JEV_ENABLED", "true")
    run = settle(workspace, classify(workspace, source).json()["id"])
    # Inspection remains possible without current provider readiness or current rubric.
    monkeypatch.delenv("TYPESAFE_API_KEY")
    monkeypatch.setattr("backend.classification.rubric", lambda: (_ for _ in ()).throw(ValueError("changed")))
    response = workspace.get(f'/api/v1/classifications/{run["id"]}/analysis')
    assert response.status_code == 200, response.text
    analysis = response.json()
    assert analysis["state"] == calls[0]["state"]
    assert analysis["questions"] == calls[0]["questions"]
    assert analysis["model"] == calls[0]["model"]
    assert analysis["rubric_version"] == "1.1.0"
    assert analysis["rubric_status"] == "draft_research"
    assert run["input"]["source"] == "report_excerpts"
    assert classification_store.job("different-tenant", run["id"]) is None
    from backend.access import principal, Principal
    from backend.main import app
    monkeypatch.setitem(app.dependency_overrides, principal,
                        lambda: Principal("different-tenant", frozenset({"reviews:read"})))
    assert workspace.get(f'/api/v1/classifications/{run["id"]}/analysis').status_code == 404
    assert workspace.get('/api/v1/classifications/missing/analysis').status_code == 404
    assert len(calls) == 1
    assert not any(key in response.text for key in ("grounded_anchors", "Authorization", "controlled-test-key", "workflow_id"))


def test_classification_projection_identifies_quote_source_without_anchor_metadata():
    from backend import presentation
    item = dict(id="jc", review_id="qr", input_version=1, observation_id="obs", input_hash="hash",
                input=dict(finding_text="Exact quote", qa_comment="QA", report_quotes=["Exact quote"]),
                execution_status="completed", steps=[], result=None, error=None,
                config=dict(model="jev", rubric=dict(id="rubric"), rubric_hash="hash", workflow_version="v1"),
                created_at="now", updated_at="now")
    public = presentation.classification(item, "current")
    assert public["input"] == dict(finding_text="Exact quote", qa_comment="QA", source="report_excerpts")
