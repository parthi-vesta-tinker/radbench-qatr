"""Behavioral API guarantees: tenant isolation, immutable replay, version adapters."""

import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from backend import store, presentation
from backend.main import app
from backend.reviewer import SAMPLES
from backend.settings import runtime_config
from test_api import post, finish


@pytest.fixture
def credentials(monkeypatch, tmp_path):
    tenants = tmp_path / "tenants.json"
    tenants.write_text(json.dumps({"vesta": {}, "tenant_b": {}}))
    grants = tmp_path / "keys.json"
    token_a = "test-vesta-" + uuid.uuid4().hex
    token_b = "test-other-" + uuid.uuid4().hex
    token_read = "test-read-" + uuid.uuid4().hex
    token_rotate = "test-rotated-" + uuid.uuid4().hex
    rights = ["reviews:read", "reviews:write", "feedback:read", "feedback:write"]
    grants.write_text(
        json.dumps(
            [
                {
                    "key_sha256": hashlib.sha256(token.encode()).hexdigest(),
                    "tenant_id": tenant,
                    "scopes": scopes,
                }
                for token, tenant, scopes in [
                    (token_a, "vesta", rights),
                    (token_b, "tenant_b", rights),
                    (token_read, "vesta", ["reviews:read"]),
                    (token_rotate, "vesta", rights),
                ]
            ]
        )
    )
    monkeypatch.setenv("ACCESS_MODE", "api_key")
    monkeypatch.setenv("QA_TENANTS_FILE", str(tenants))
    monkeypatch.setenv("QA_TENANT_KEYS_FILE", str(grants))
    store.init()
    return {
        name: {"Authorization": "Bearer " + token}
        for name, token in [
            ("a", token_a),
            ("b", token_b),
            ("read", token_read),
            ("rotated", token_rotate),
        ]
    }


def create_as(client, headers, key, sample=0):
    return client.post(
        "/api/v1/reviews",
        headers=headers | {"Idempotency-Key": key},
        json={"report_text": SAMPLES[sample]["report_text"]},
    )


def finish_as(client, response, headers):
    import time

    assert response.status_code == 202, response.text
    for _ in range(300):
        r = client.get(response.headers["Location"], headers=headers)
        assert r.status_code == 200, r.text
        doc = r.json()
        if doc["execution_status"] not in ("queued", "running"):
            return doc
        time.sleep(0.02)
    raise AssertionError("Review did not finish")


def test_replay_is_original_ack_even_after_configuration_changes(client, monkeypatch):
    key = uuid.uuid4().hex
    a = post(client, key=key)
    finished = finish(client, a)
    assert finished["execution_status"] == "completed"
    monkeypatch.setenv("RUN_MODE", "live")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    b = post(client, key=key)
    assert a.status_code == b.status_code == 202 and a.content == b.content
    assert a.headers["Location"] == b.headers["Location"]
    assert (
        a.headers["Idempotency-Replayed"] == "false"
        and b.headers["Idempotency-Replayed"] == "true"
    )
    assert a.headers["Request-Id"] != b.headers["Request-Id"]
    assert b.json()["execution_status"] == "queued" and b.json()["result"] is None
    assert (
        b.headers["QA-Version"] == presentation.API_VERSION
        and b.headers["Cache-Control"] == "no-store"
    )


def test_tenant_reads_writes_replays_and_pagination_are_isolated(client, credentials):
    a, b = credentials["a"], credentials["b"]
    key = uuid.uuid4().hex
    with ThreadPoolExecutor(max_workers=2) as pool:
        ra, rb = list(pool.map(lambda h: create_as(client, h, key), [a, b]))
    da = finish_as(client, ra, a)
    db = finish_as(client, rb, b)
    assert (
        da["tenant_id"] == "vesta"
        and db["tenant_id"] == "tenant_b"
        and da["id"] != db["id"]
    )
    assert da["id"].startswith("qr_") and "review_id" not in da
    ua = f"/api/v1/reviews/{da['id']}"
    ub = f"/api/v1/reviews/{db['id']}"
    for path, headers in [
        (ua, b),
        (ub, a),
        (ua + "/feedback", b),
        (ub + "/feedback", a),
    ]:
        response = client.get(path, headers=headers)
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "REVIEW_NOT_FOUND"
    payload = {"rating": "down", "reason": "other"}
    assert (
        client.post(
            ua + "/feedback", headers=b | {"Idempotency-Key": key}, json=payload
        ).status_code
        == 404
    )
    # The same key is safe across different authorized operations and tenants.
    fa = client.post(
        ua + "/feedback", headers=a | {"Idempotency-Key": key}, json=payload
    )
    fb = client.post(
        ub + "/feedback", headers=b | {"Idempotency-Key": key}, json=payload
    )
    assert (
        fa.status_code == fb.status_code == 201 and fa.json()["id"] != fb.json()["id"]
    )
    assert client.get(ua + "/feedback", headers=a).json()["items"] == [fa.json()]
    assert (
        client.get(
            ua + "/feedback", headers=a, params={"starting_after": fb.json()["id"]}
        ).status_code
        == 400
    )
    assert create_as(client, credentials["rotated"], key).content == ra.content


def test_authentication_scopes_and_tenant_spoofing(client, credentials):
    assert client.get("/api/v1/config").status_code == 401
    invalid = client.get("/api/v1/config", headers={"Authorization": "Bearer invalid"})
    assert (
        invalid.status_code == 401 and invalid.headers["WWW-Authenticate"] == "Bearer"
    )
    assert (
        client.get(
            "/api/v1/config", headers=credentials["a"] | {"X-Tenant-Id": "tenant_b"}
        ).status_code
        == 400
    )
    assert create_as(client, credentials["read"], uuid.uuid4().hex).status_code == 403
    forged = client.post(
        "/api/v1/reviews",
        headers=credentials["a"] | {"Idempotency-Key": uuid.uuid4().hex},
        json={"report_text": SAMPLES[0]["report_text"], "tenant_id": "tenant_b"},
    )
    assert forged.status_code == 422
    assert (
        client.get("/api/v1/config", headers=credentials["a"]).json()["tenant_id"]
        == "vesta"
    )


def test_local_mode_cannot_select_tenant_or_accept_remote_client(client):
    assert (
        client.get("/api/v1/config", headers={"X-Tenant-Id": "tenant_b"}).status_code
        == 400
    )
    remote = TestClient(app, client=("203.0.113.10", 1234))
    try:
        assert remote.get("/api/v1/config").status_code == 403
    finally:
        remote.close()


@pytest.mark.parametrize("mode, status", [(None, 403), ("local", 403), ("public", 200)])
def test_forwarded_remote_client_requires_explicit_public_mode(client, monkeypatch, mode, status):
    from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

    if mode is None:
        monkeypatch.delenv("ACCESS_MODE", raising=False)
    else:
        monkeypatch.setenv("ACCESS_MODE", mode)
    proxy = ProxyHeadersMiddleware(app, trusted_hosts=["127.0.0.1"])
    remote = TestClient(proxy, client=("127.0.0.1", 1234))
    try:
        response = remote.get("/api/v1/config", headers={"X-Forwarded-For": "203.0.113.10"})
        assert response.status_code == status, response.text
        if status == 200:
            assert response.json()["tenant_id"] == "vesta"
        else:
            assert response.json()["error"]["code"] == "LOCAL_ACCESS_ONLY"
    finally:
        remote.close()


def test_public_visitors_share_vesta_reviews_without_credentials(client, monkeypatch):
    from backend.access import validate_access_config

    monkeypatch.setenv("ACCESS_MODE", "public")
    monkeypatch.delenv("QA_TENANT_KEYS_FILE", raising=False)
    validate_access_config()
    visitor = TestClient(app, client=("203.0.113.10", 1234))
    other = TestClient(app, client=("203.0.113.11", 1234))
    try:
        accepted = post(visitor)
        result = finish(visitor, accepted)
        assert result["execution_status"] == "completed"
        assert result["tenant_id"] == "vesta"
        assert other.get(accepted.headers["Location"]).json() == result
        feedback = other.post(
            accepted.headers["Location"] + "/feedback",
            headers={"Idempotency-Key": uuid.uuid4().hex},
            json={"rating": "up"},
        )
        assert feedback.status_code == 201, feedback.text
        assert other.get("/api/v1/knowledge").status_code == 200
        assert other.get("/api/v1/playground").status_code == 200
        spoofed = other.get("/api/v1/config", headers={"X-Tenant-Id": "tenant_b"})
        assert spoofed.status_code == 400
        assert spoofed.json()["error"]["code"] == "TENANT_OVERRIDE_NOT_ALLOWED"
        credential = other.get("/api/v1/config", headers={"Authorization": "Bearer invalid"})
        assert credential.status_code == 401
        assert credential.json()["error"]["code"] == "AUTH_MODE_MISMATCH"
        forged = other.post(
            "/api/v1/reviews",
            headers={"Idempotency-Key": uuid.uuid4().hex},
            json={"report_text": SAMPLES[0]["report_text"], "tenant_id": "tenant_b"},
        )
        assert forged.status_code == 422
    finally:
        visitor.close()
        other.close()


def test_unknown_access_mode_fails_closed(monkeypatch):
    from backend.access import access_mode

    monkeypatch.setenv("ACCESS_MODE", "publci")
    with pytest.raises(ValueError, match="ACCESS_MODE"):
        access_mode()


def test_feedback_concurrent_replay_conflict_and_cursor_page(client):
    d = finish(client, post(client))
    url = f"/api/v1/reviews/{d['id']}/feedback"
    key = uuid.uuid4().hex
    payload = {"rating": "down", "reason": "other"}

    def save(_):
        return client.post(url, headers={"Idempotency-Key": key}, json=payload)

    with ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(pool.map(save, range(4)))
    assert (
        all(r.status_code == 201 for r in responses)
        and len({r.content for r in responses}) == 1
    )
    assert (
        client.post(
            url,
            headers={"Idempotency-Key": key},
            json=payload | {"reason": "wrong_grouping"},
        ).status_code
        == 409
    )
    second = client.post(
        url, headers={"Idempotency-Key": uuid.uuid4().hex}, json=payload
    ).json()
    first = client.get(url, params={"limit": 1}).json()
    assert first["object"] == "list" and first["has_more"] is True
    next_page = client.get(
        url, params={"limit": 1, "starting_after": first["next_cursor"]}
    ).json()
    assert (
        next_page["items"] == [second]
        and next_page["has_more"] is False
        and next_page["next_cursor"] is None
    )
    assert client.get(url, params={"limit": 101}).status_code == 422


def test_version_errors_and_validation_do_not_consume_keys(client):
    response = client.get("/api/v1/config", headers={"QA-Version": "2099-01-01"})
    assert (
        response.status_code == 400
        and response.json()["error"]["code"] == "UNSUPPORTED_API_VERSION"
    )
    key = uuid.uuid4().hex
    bad = client.post(
        "/api/v1/reviews", headers={"Idempotency-Key": key}, json={"report_text": " "}
    )
    assert (
        bad.status_code == 422
        and bad.json()["error"]["request_id"] == bad.headers["Request-Id"]
    )
    assert "input" not in json.dumps(bad.json()["error"].get("field_errors", []))
    assert post(client, key=key).status_code == 202


def test_public_projection_excludes_future_internal_fields(client):
    d = finish(client, post(client))
    record = store.get("vesta", d["id"])
    before = presentation.review(record)
    record["internal_storage_column"] = "PRIVATE"
    record["input"]["internal_parsing"] = "PRIVATE"
    record["provenance"]["private_policy_path"] = "PRIVATE"
    record["result"]["internal_reasoning"] = "PRIVATE"
    record["steps"][1]["metrics"]["private_cost_account"] = "PRIVATE"
    record["result"]["general_comments"][0]["internal_score"] = 0.9
    assert presentation.review(record) == before
    assert "PRIVATE" not in json.dumps(presentation.review(record))


def test_non_vesta_does_not_inherit_vesta_manual(
    client, credentials, monkeypatch, tmp_path
):
    policy = tmp_path / "vesta-policy.md"
    policy.write_text("Synthetic Vesta-only manual.")
    monkeypatch.setenv("QA_POLICY_PATH", str(policy))
    a = client.get("/api/v1/config", headers=credentials["a"]).json()
    b = client.get("/api/v1/config", headers=credentials["b"]).json()
    assert (
        a["policy_status"] == "supplied_unvalidated"
        and b["policy_status"] == "provisional_no_manual"
    )
    assert a["policy_version"] and b["policy_version"] is None


def test_committed_acceptance_recovers_dispatch_failure_without_restart(
    client, monkeypatch
):
    import backend.main as main

    calls = []
    original = main.dispatch

    def fail_once(tenant, rid):
        calls.append(rid)
        if len(calls) == 1:
            raise RuntimeError("Injected dispatch failure")
        return original(tenant, rid)

    original_pending = store.pending
    scans = []

    def transient_scan_failure():
        scans.append(True)
        if len(scans) == 1:
            raise RuntimeError("Injected scan failure")
        return original_pending()

    monkeypatch.setattr(store, "pending", transient_scan_failure)
    monkeypatch.setattr(main, "dispatch", fail_once)
    r = post(client)
    assert r.status_code == 202
    d = finish(client, r)
    assert d["execution_status"] == "completed" and len(calls) >= 2


@pytest.mark.parametrize("version", [0, 2, 999])
def test_old_database_is_rejected_without_changing_rows(tmp_path, monkeypatch, version):
    monkeypatch.setattr(store, "DATA", tmp_path)
    conn = sqlite3.connect(tmp_path / "reviews.sqlite")
    conn.execute("CREATE TABLE old_records(id TEXT PRIMARY KEY, document TEXT)")
    conn.execute("INSERT INTO old_records VALUES('original','unchanged')")
    conn.execute(f"PRAGMA user_version={version}")
    conn.commit()
    conn.close()
    with pytest.raises(RuntimeError, match="fresh QA_DATA_DIR"):
        store.init()
    conn = sqlite3.connect(tmp_path / "reviews.sqlite")
    assert conn.execute("SELECT * FROM old_records").fetchall() == [("original", "unchanged")]
    assert conn.execute("PRAGMA user_version").fetchone()[0] == version
    conn.close()
