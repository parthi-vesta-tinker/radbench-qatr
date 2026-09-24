"""Playground isolation, execution and access. No network call is made."""
import json
import re
import time
import uuid

import httpx
import pytest
from openai import AsyncOpenAI

from backend import playground, reviewer, store


@pytest.fixture
def pg(client, monkeypatch, tmp_path):
    monkeypatch.setattr(store, "DATA", tmp_path / "data")
    store.init()
    return client


def provider(monkeypatch, outcome="valid"):
    """The real HTTP adapter against a local transport, as the live provider tests do."""
    calls = []

    def respond(request):
        body = json.loads(request.content)
        calls.append(body)
        checks = json.loads(re.search(
            r"checked_skills must contain each of these exactly once: (\[.*?\])",
            body["instructions"]).group(1))
        output = dict(input_problem=None, checked_skills=checks, observations=[],
                      designation=dict(status="unknown", anchor=None))
        if outcome == "bad_coverage":
            output["checked_skills"] = []
        return httpx.Response(200, json=dict(
            id="resp_controlled", object="response", created_at=1, model="gpt-6-astra",
            status="completed",
            output=[dict(id="msg", type="message", role="assistant", status="completed",
                         content=[{"type": "output_text", "text": json.dumps(output), "annotations": []}])],
            usage=dict(input_tokens=20, output_tokens=10, total_tokens=30)))

    monkeypatch.setattr(reviewer, "AsyncOpenAI", lambda **kwargs: AsyncOpenAI(
        **kwargs, api_key="controlled-never-transmitted",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(respond))))
    monkeypatch.setenv("RUN_MODE", "live")
    monkeypatch.setenv("OPENAI_API_KEY", "controlled-never-transmitted")
    monkeypatch.setenv("OPENAI_MODEL", "configured-live-model")
    return calls


def start(client, **body):
    return client.post("/api/v1/playground/runs",
                       json={"model": "gpt-6-astra", **body},
                       headers={"Idempotency-Key": uuid.uuid4().hex})


def settle(client, run_id, timeout=20):
    for _ in range(timeout * 10):
        run = client.get(f"/api/v1/playground/runs/{run_id}").json()
        if run["status"] in ("completed", "failed", "needs_input"):
            return run
        time.sleep(0.1)
    raise AssertionError("Playground run did not settle")


def test_catalog_offers_two_categories_and_one_model(pg):
    body = pg.get("/api/v1/playground").json()
    assert [c["id"] for c in body["categories"]] == ["critical_finding", "inconsistency"]
    assert body["models"] == ["gpt-6-astra"]
    for category in ("critical_finding", "inconsistency"):
        chosen = [s for s in body["samples"] if s["category"] == category]
        assert len(chosen) >= 2 and any(s["demo_supported"] for s in chosen)
        assert all(s["report_text"].strip() for s in chosen)
    assert "never a review" in body["boundary"] or "not a clinical review" in body["boundary"]
    # The composed prompt is never part of the playground catalog.
    assert "combined_instructions" not in pg.get("/api/v1/playground").text


def test_sample_text_is_read_from_the_verified_package(pg):
    cases = playground.case_reports()
    body = pg.get("/api/v1/playground").json()
    flagged = next(s for s in body["samples"] if s["sample_id"] == "critical-flagged")
    assert flagged["report_text"] == cases["W13"]["input"]["report_text"]
    assert flagged["title"] == cases["W13"]["title"]


def test_run_executes_the_real_path_and_stays_out_of_live_tables(pg, monkeypatch):
    calls = provider(monkeypatch)
    accepted = start(pg, sample_id="critical-flagged")
    assert accepted.status_code == 202, accepted.text
    run = settle(pg, accepted.json()["run_id"])
    assert run["status"] == "completed", run
    assert run["model"] == "gpt-6-astra" and run["pack_ref"] == "published"
    assert [s["step"] for s in run["steps"]] == [
        "input_validation", "combined_review", "output_validation", "comment_assembly"]
    assert all(s["status"] == "completed" for s in run["steps"])
    assert len(calls) == 1 and calls[0]["model"] == "gpt-6-astra"
    with store.db() as conn:
        assert conn.execute("SELECT count(*) FROM playground_runs").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM playground_attempts").fetchone()[0] == 1
        for table in ("review_records", "review_results", "observations", "feedback",
                      "outcomes", "model_attempts"):
            assert conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0
    # No live surface shows the run.
    assert pg.get("/api/v1/reviews").json()["items"] == []
    assert pg.get("/api/v1/analytics").json()["reviews"]["total"] == 0
    assert pg.get("/api/v1/feedback").json()["items"] == []


def test_logs_are_phases_and_timings_only(pg, monkeypatch):
    provider(monkeypatch)
    run = settle(pg, start(pg, sample_id="laterality-swap").json()["run_id"])
    assert set(run["steps"][0]) == {"step", "status", "elapsed_ms"}
    body = json.dumps(run)
    for secret in ("instructions", "combined_instructions", "input_tokens", "resp_controlled"):
        assert secret not in body


def test_paste_your_own_runs_and_input_is_validated(pg, monkeypatch):
    provider(monkeypatch)
    ok = start(pg, report_text="Findings:\nLeft pleural effusion.\n\nImpression:\nRight pleural effusion.")
    assert ok.status_code == 202
    assert settle(pg, ok.json()["run_id"])["source"] == "pasted"
    both = start(pg, sample_id="critical-flagged", report_text="Findings: x\nImpression: y")
    assert both.status_code == 422 and both.json()["error"]["code"] == "PLAYGROUND_INPUT_INVALID"
    assert start(pg).status_code == 422
    assert start(pg, sample_id="no-such-sample").status_code == 404


def test_only_offered_models_are_accepted(pg, monkeypatch):
    provider(monkeypatch)
    assert start(pg, sample_id="critical-flagged").status_code == 202
    refused = pg.post("/api/v1/playground/runs",
                      json={"sample_id": "critical-flagged", "model": "gpt-4o"},
                      headers={"Idempotency-Key": uuid.uuid4().hex})
    assert refused.status_code == 422


def test_replay_returns_the_original_run(pg, monkeypatch):
    provider(monkeypatch)
    key = uuid.uuid4().hex
    body = {"sample_id": "critical-flagged", "model": "gpt-6-astra"}
    first = pg.post("/api/v1/playground/runs", json=body, headers={"Idempotency-Key": key})
    again = pg.post("/api/v1/playground/runs", json=body, headers={"Idempotency-Key": key})
    assert again.json()["run_id"] == first.json()["run_id"]
    assert again.headers["Idempotency-Replayed"] == "true"
    changed = pg.post("/api/v1/playground/runs",
                      json={"sample_id": "critical-unflagged", "model": "gpt-6-astra"},
                      headers={"Idempotency-Key": key})
    assert changed.status_code == 409


def test_every_demo_supported_sample_actually_runs_in_demo_mode(pg):
    """The flag is computed from the canned path, so it can never advertise support falsely."""
    catalog = pg.get("/api/v1/playground").json()
    supported = [s for s in catalog["samples"] if s["demo_supported"]]
    assert {s["category"] for s in supported} == {"critical_finding", "inconsistency"}
    for sample in supported:
        run = settle(pg, start(pg, sample_id=sample["sample_id"]).json()["run_id"])
        assert run["status"] == "completed", (sample["sample_id"], run)
        assert run["mode"] == "demo"
    unsupported = next(s for s in catalog["samples"] if not s["demo_supported"])
    refused = settle(pg, start(pg, sample_id=unsupported["sample_id"]).json()["run_id"])
    assert refused["status"] == "failed"
    assert refused["error"]["code"] == "DEMO_INPUT_UNSUPPORTED"


def test_provider_failure_is_reported_and_never_retried(pg, monkeypatch):
    calls = provider(monkeypatch, outcome="bad_coverage")
    run = settle(pg, start(pg, sample_id="critical-flagged").json()["run_id"])
    assert run["status"] == "failed" and run["error"]["code"] == "INVALID_SKILL_OUTPUT"
    assert len(calls) == 1
    with store.db() as conn:
        assert conn.execute("SELECT outcome FROM playground_attempts").fetchone()[0] == "response"


def test_runs_are_tenant_scoped(pg, monkeypatch):
    provider(monkeypatch)
    run_id = start(pg, sample_id="critical-flagged").json()["run_id"]
    with store.db() as conn:
        conn.execute("INSERT INTO tenants(id,active_release) VALUES('other','generic')")
        assert conn.execute(
            "SELECT count(*) FROM playground_runs WHERE tenant_id='other' AND id=?", (run_id,)
        ).fetchone()[0] == 0
    assert pg.get("/api/v1/playground/runs/pg_missing").status_code == 404
