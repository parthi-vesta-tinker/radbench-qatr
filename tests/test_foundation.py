"""Foundation contracts and storage safety; no network/provider calls."""
import json
import sqlite3
import uuid
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pytest
from backend import store, presentation
from backend.contracts import ReviewInput, FeedbackInput
from backend.main import app
from backend.settings import APP_VERSION
from scripts.export_contracts import generate, ts


@pytest.fixture
def fresh(monkeypatch, tmp_path):
    monkeypatch.setattr(store, "DATA", tmp_path)
    store.init()
    return tmp_path


def accept(tenant="vesta", key=None):
    return store.reserve(tenant, key or uuid.uuid4().hex,
                         ReviewInput(report_text="Findings: Clear lungs. Impression: No acute disease."),
                         {"mode": "demo", "workflow_version": APP_VERSION, "instructions": "Original bytes."})[0]["body"]["id"]


def result():
    return {"result_version": 1, "outcome": "observations", "critical_finding_detected": False,
            "general_comments": [{"observation_id": "obs-1", "comment": "Controlled test only."}],
            "critical_comments": []}


def test_normalized_storage_snapshot_and_idempotent_completion(fresh):
    rid = accept()
    with store.db() as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == store.SCHEMA_VERSION == 6
        assert conn.execute("SELECT type FROM sqlite_master WHERE name='reviews'").fetchone()[0] == "view"
        assert "document" not in {row[1] for row in conn.execute("PRAGMA table_info(review_records)")}
        assert conn.execute("SELECT count(*) FROM review_snapshots").fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            conn.execute("UPDATE review_snapshots SET config='{}'")
    assert store.job("vesta", rid)[1]["instructions"] == "Original bytes."
    store.update("vesta", rid, execution_status="completed", result=result())
    store.update("vesta", rid, execution_status="completed", result=result())
    with store.db() as conn:
        metadata = json.loads(conn.execute("SELECT metadata FROM review_results").fetchone()[0])
        assert "general_comments" not in metadata
        assert conn.execute("SELECT count(*) FROM observations").fetchone()[0] == 1
    with pytest.raises(ValueError, match="terminal"):
        store.update("vesta", rid, execution_status="running")
    store.init()  # same-schema restart is non-destructive
    assert store.get("vesta", rid)["result"] == result()


def test_tenant_result_and_observation_foreign_keys(fresh):
    rid = accept()
    store.update("vesta", rid, execution_status="completed", result=result())
    with store.db() as conn:
        conn.execute("INSERT INTO tenants(id) VALUES('tenant_b')")
    for tenant, version, observation in (("tenant_b", 1, None), ("vesta", 2, None), ("vesta", 1, "not-present")):
        payload = {"result_version": version, "rating": "up", "observation_id": observation}
        with pytest.raises(sqlite3.IntegrityError):
            with store.db() as conn:
                conn.execute("INSERT INTO feedback(tenant_id,id,review_id,document,schema_version) VALUES(?,?,?,?,4)",
                             (tenant, uuid.uuid4().hex, rid, json.dumps(payload)))
    with store.db() as conn:
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


def test_concurrent_receipts_capture_one_snapshot(fresh):
    with ThreadPoolExecutor(max_workers=6) as pool:
        ids = list(pool.map(lambda _: accept(key="same-operation"), range(6)))
    assert len(set(ids)) == 1
    with store.db() as conn:
        for table in ("review_records", "review_snapshots", "idempotency"):
            assert conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 1
        plan = conn.execute("EXPLAIN QUERY PLAN SELECT id FROM review_records WHERE execution_status='queued'").fetchall()
        assert any("review_dispatch" in str(tuple(row)) for row in plan)


def test_public_schema_and_generated_client_do_not_drift():
    root = Path(__file__).resolve().parents[1]
    assert json.loads((root / "prototype/openapi.json").read_text()) == app.openapi()
    assert (root / "frontend/src/generated-api.ts").read_text() == generate()
    public = app.openapi()["components"]["schemas"]
    assert "review_id" not in public["ReviewResource"]["properties"]
    assert "feedback_id" not in public["FeedbackResource"]["properties"]
    with pytest.raises(ValueError):
        ts({"type": "unsupported"})
