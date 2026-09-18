"""Studio read/record contracts with synthetic storage fixtures, not clinical model tests."""

import json
import uuid
from datetime import datetime, timedelta, timezone
import pytest
from backend import store
from backend.contracts import FeedbackInput
from test_api_design import credentials


@pytest.fixture
def reporting_db(client, monkeypatch, tmp_path):
    monkeypatch.setattr(store, "DATA", tmp_path)
    store.init()
    return client


def seed(tenant="vesta", source="openai", status="completed", days=0, critical=False):
    rid = "qr_" + uuid.uuid4().hex
    doc = dict(review_id=rid, tenant_id=tenant, created_at=(datetime.now(timezone.utc)-timedelta(days=days)).isoformat(),
               input_hash="controlled-hash", input={"report_text": "Controlled source report."},
               execution_status=status, provenance={"mode": source},
               result={"result_version": 1, "outcome": "observations" if critical else "no_observations",
                       "critical_finding_detected": critical, "general_comments": [],
                       "critical_comments": [{"observation_id": "obs-1", "comment": "Controlled comment."}] if critical else []})
    with store.db() as conn:
        conn.execute("INSERT OR IGNORE INTO tenants(id) VALUES(?)", (tenant,))
        conn.execute("INSERT INTO review_snapshots VALUES(?,?,?,?)", (tenant, rid, 'controlled', '{}'))
        conn.execute("INSERT INTO review_records(tenant_id,id,snapshot_id,report_text,input_hash,created_at,execution_status,steps,provenance,api_version) VALUES(?,?,?,?,?,?,?,?,?,?)",
                     (tenant, rid, rid, doc['input']['report_text'], doc['input_hash'], doc['created_at'], 'queued', '[]', store.canonical(doc['provenance']), '2026-09-18'))
    store.update(tenant, rid, execution_status=status, result=doc['result'] if status == 'completed' else None)
    return rid


def feedback(rid, tenant="vesta", rating="down", note="Please be concise.", target="result"):
    data = FeedbackInput(result_version=1, rating=rating, reason="unclear_wording" if rating == "down" else None,
                         explanation=note, target=target, observation_id="obs-1" if target == "observation" else None)
    return store.save_feedback(tenant, rid, uuid.uuid4().hex, data)[0]["body"]


def outcome(client, rid, decision="accepted", stakeholder="qa", subject="report", key=None, headers=None):
    return client.post(f"/api/v1/reviews/{rid}/outcomes", headers={"Idempotency-Key": key or uuid.uuid4().hex, **(headers or {})},
                       json=dict(result_version=1, stakeholder=stakeholder, subject=subject,
                                 decision=decision, source_note="Controlled QA note, not a clinical adjudication."))


def test_inbox_filters_pagination_projection_and_source(reporting_db):
    client = reporting_db
    rid = seed(critical=True)
    first = feedback(rid, note="Unique%literal", target="observation")
    second = feedback(rid, rating="up", note="Useful")
    feedback(seed(source="demo"), note="Legacy")
    page = client.get('/api/v1/feedback?limit=1').json()
    assert page['items'][0]['feedback']['id'] == second['id']
    assert page['has_more']
    next_page = client.get('/api/v1/feedback', params={'starting_after': page['next_cursor']}).json()
    assert next_page['items'][0]['feedback']['id'] == first['id']
    assert next_page['items'][0]['target_comment'] == 'Controlled comment.'
    assert 'input_hash' not in next_page['items'][0]  # only nested public feedback exposes its binding hash
    assert 'provenance' not in next_page['items'][0]
    assert len(client.get('/api/v1/feedback?source=all').json()['items']) == 3
    assert len(client.get('/api/v1/feedback?q=%25').json()['items']) == 1
    assert len(client.get('/api/v1/feedback?rating=down&reason=unclear_wording').json()['items']) == 1
    assert client.get('/api/v1/feedback?starting_after=absent').status_code == 400
    assert client.get('/api/v1/feedback?reason=invented').status_code == 422


def test_analytics_database_totals_not_page_counts_and_period(reporting_db):
    client = reporting_db
    for _ in range(23):
        seed()
    old = seed(days=10, critical=True)
    feedback(old)
    seed(source="demo")
    seed(status="failed")
    week = client.get('/api/v1/analytics').json()
    assert week['reviews']['total'] == 24
    assert week['reviews']['statuses']['completed'] == 23
    assert week['reviews']['statuses']['failed'] == 1
    assert week['feedback']['total'] == 1  # feedback event time, not report submission time
    month = client.get('/api/v1/analytics?period=30d').json()
    assert month['reviews']['critical'] == 1
    assert month['reviews']['total'] == 25
    assert client.get('/api/v1/analytics?source=all&period=all').json()['reviews']['total'] == 26
    assert week['critical_evaluation']['recall'] is None
    assert week['critical_evaluation']['fp'] is None
    assert all(row['acceptance_rate'] is None for row in week['acceptance'])


def test_outcome_idempotency_latest_decision_and_retraction(reporting_db):
    client = reporting_db
    rid = seed()
    key = uuid.uuid4().hex
    first = outcome(client, rid, key=key)
    assert first.status_code == 201, first.text
    again = outcome(client, rid, key=key)
    assert first.content == again.content
    assert again.headers['Idempotency-Replayed'] == 'true'
    assert outcome(client, rid, decision='rejected', key=key).status_code == 409
    outcome(client, rid, decision='rejected')
    outcome(client, rid, stakeholder='radiologist', subject='qa_comments')
    stats = client.get('/api/v1/analytics').json()['acceptance']
    qa = next(x for x in stats if x['stakeholder'] == 'qa' and x['subject'] == 'report')
    assert qa['recorded'] == 1 and qa['rejected'] == 1 and qa['accepted'] == 0
    assert qa['acceptance_rate'] == 0
    outcome(client, rid, decision='unknown')
    qa = next(x for x in client.get('/api/v1/analytics').json()['acceptance'] if x['stakeholder'] == 'qa' and x['subject'] == 'report')
    assert qa['acceptance_rate'] is None and qa['unknown'] == 1
    page = client.get(f'/api/v1/reviews/{rid}/outcomes?limit=2').json()
    assert len(page['items']) == 2 and page['has_more']
    tail = client.get(f'/api/v1/reviews/{rid}/outcomes', params={'starting_after': page['next_cursor']}).json()
    assert len(tail['items']) == 2  # append-only history: no duplicate from replay
    store.init()
    assert len(client.get(f'/api/v1/reviews/{rid}/outcomes').json()['items']) == 4
    assert store.get('vesta', rid)['result']['outcome'] == 'no_observations'


def test_outcome_validation_and_indeterminate_denominators(reporting_db):
    client = reporting_db
    rid = seed()
    outcome(client, rid, decision='review_requested')
    seed()
    rows = client.get('/api/v1/analytics').json()['acceptance']
    qa = next(x for x in rows if x['stakeholder'] == 'qa' and x['subject'] == 'report')
    assert qa['review_requested'] == 1 and qa['not_recorded'] == 1 and qa['acceptance_rate'] is None
    assert outcome(client, seed(status='failed')).status_code == 422
    assert outcome(client, 'absent').status_code == 404
    body = dict(result_version=2, stakeholder='qa', subject='report', decision='accepted', source_note='x')
    endpoint = f'/api/v1/reviews/{rid}/outcomes'
    assert client.post(endpoint, headers={'Idempotency-Key': uuid.uuid4().hex}, json=body).status_code == 422
    body.update(result_version=1, source_note='  ')
    assert client.post(endpoint, headers={'Idempotency-Key': uuid.uuid4().hex}, json=body).status_code == 422


def test_inbox_and_outcome_tenant_isolation_and_scope(reporting_db, credentials):
    client = reporting_db
    a, b = seed(), seed(tenant='tenant_b')
    fa, fb = feedback(a), feedback(b, tenant='tenant_b')
    outcome(client, a, headers=credentials['a'])
    b_outcome = outcome(client, b, headers=credentials['b']).json()
    assert client.get('/api/v1/feedback', headers=credentials['read']).status_code == 403
    assert outcome(client, a, headers=credentials['read']).status_code == 403
    assert outcome(client, b, headers=credentials['a']).status_code == 404
    assert client.get(f'/api/v1/reviews/{b}/outcomes', headers=credentials['a']).status_code == 404
    assert client.get('/api/v1/feedback', params={'starting_after': fb['id']}, headers=credentials['a']).status_code == 400
    assert client.get(f'/api/v1/reviews/{a}/outcomes', params={'starting_after': b_outcome['outcome_id']}, headers=credentials['a']).status_code == 400
    assert [x['feedback']['id'] for x in client.get('/api/v1/feedback', headers=credentials['a']).json()['items']] == [fa['id']]
    read_stats = client.get('/api/v1/analytics', headers=credentials['read']).json()
    assert read_stats['reviews']['total'] == 1
    assert read_stats['feedback'] is None and read_stats['acceptance'] is None


def test_empty_analytics_and_no_model_dependency(reporting_db, monkeypatch):
    monkeypatch.setenv('QA_MODE', 'openai')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    client = reporting_db
    body = client.get('/api/v1/analytics').json()
    assert body['reviews']['total'] == 0 and body['feedback']['total'] == 0
    assert body['critical_evaluation']['precision'] is None
    assert client.get('/api/v1/feedback').json()['items'] == []
    assert client.get('/api/v1/analytics?period=invalid').status_code == 422
    assert client.get('/api/v1/feedback?source=test').status_code == 422


def test_completed_result_cannot_change_under_feedback(reporting_db):
    rid = seed(critical=True)
    feedback(rid, target='observation')
    import sqlite3
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        with store.db() as conn:
            conn.execute("UPDATE review_results SET result_version=2 WHERE review_id=?", (rid,))
    assert reporting_db.get('/api/v1/feedback').json()['items'][0]['target_comment'] == 'Controlled comment.'
