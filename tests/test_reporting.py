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


def seed(tenant="vesta", source="openai", status="completed", days=0, hours=0,
         critical=False, result=None):
    rid = "qr_" + uuid.uuid4().hex
    doc = dict(review_id=rid, tenant_id=tenant, created_at=(datetime.now(timezone.utc)-timedelta(days=days, hours=hours)).isoformat(),
               input_hash="controlled-hash", input={"report_text": "Controlled source report."},
               execution_status=status, provenance={"mode": source},
               result=result or {"result_version": 1, "outcome": "observations" if critical else "no_observations",
                       "critical_finding_detected": critical, "general_comments": [],
                       "critical_comments": [{"observation_id": "obs-1", "comment": "Controlled comment."}] if critical else []})
    with store.db() as conn:
        conn.execute("INSERT OR IGNORE INTO tenants(id) VALUES(?)", (tenant,))
        conn.execute("INSERT INTO review_snapshots VALUES(?,?,?,?)", (tenant, rid, 'controlled', '{}'))
        conn.execute("INSERT INTO review_records(tenant_id,id,snapshot_id,report_text,input_hash,created_at,execution_status,steps,provenance,api_version) VALUES(?,?,?,?,?,?,?,?,?,?)",
                     (tenant, rid, rid, doc['input']['report_text'], doc['input_hash'], doc['created_at'], 'queued', '[]', store.canonical(doc['provenance']), '2026-09-22'))
    store.update(tenant, rid, execution_status=status, result=doc['result'] if status == 'completed' else None)
    return rid


def feedback(rid, tenant="vesta", rating="down", note="Please be concise.", target="result"):
    data = FeedbackInput( rating=rating, reason="unclear_wording" if rating == "down" else None,
                         explanation=note, target=target, observation_id="obs-1" if target == "observation" else None)
    return store.save_feedback(tenant, rid, uuid.uuid4().hex, data)[0]["body"]


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
    assert 'acceptance' not in week


def test_analytics_finding_categories_and_short_periods(reporting_db):
    client = reporting_db
    comments = [
        {"observation_id": "obs-1", "finding_type": "discrepancy", "comment": "Conflicting sides."},
        {"observation_id": "obs-2", "finding_type": "discrepancy", "comment": "Question unanswered."},
        {"observation_id": "obs-3", "finding_type": "suggestion", "comment": "Correct terminology."},
        {"observation_id": "obs-5", "finding_type": "discrepancy", "comment": "Recommendation conflicts with report."},
    ]
    result = {
        "result_version": 1, "outcome": "observations", "critical_finding_detected": True,
        "general_comments": comments,
        "critical_comments": [{"observation_id": "obs-4", "finding_type": "suggestion", "comment": "Critical concern."}],
        "_candidate_mapping": [
            {"observation_id": "obs-1", "candidates": [{"check_id": "qa-internal-consistency"}]},
            {"observation_id": "obs-2", "candidates": [{"check_id": "qa-clinical-question"}]},
            {"observation_id": "obs-3", "candidates": [{"check_id": "qa-terminology-errors"}]},
            {"observation_id": "obs-4", "candidates": [{"check_id": "qa-critical-match"}]},
            {"observation_id": "obs-5", "candidates": [{"check_id": "qa-recommendations"}]},
        ],
    }
    seed(result=result)
    seed(hours=2, source="demo", result={
        "result_version": 1, "outcome": "observations", "critical_finding_detected": False,
        "general_comments": [{"observation_id": "obs-1", "finding_type": "discrepancy", "comment": "Demo discrepancy."}],
        "critical_comments": [],
    })
    seed(hours=8, status="failed")
    seed(hours=18)
    seed(days=10, critical=True)
    seed(tenant="tenant_b", critical=True)
    hour = client.get('/api/v1/analytics?period=1h&source=all').json()
    assert hour['reviews']['total'] == 1
    assert hour['findings'] == {
        'inconsistencies': 1, 'critical_findings': 1,
        'clinical_observations': 2, 'other_issues': 1,
    }
    assert client.get('/api/v1/analytics?period=6h&source=all').json()['findings']['inconsistencies'] == 2
    assert client.get('/api/v1/analytics?period=12h&source=all').json()['reviews']['statuses']['failed'] == 1
    assert client.get('/api/v1/analytics?period=24h&source=all').json()['reviews']['total'] == 4
    assert client.get('/api/v1/analytics?period=7d&source=all').json()['reviews']['total'] == 4
    assert client.get('/api/v1/analytics?period=30d&source=all').json()['findings']['critical_findings'] == 2
    assert client.get('/api/v1/analytics?period=all&source=all').json()['reviews']['total'] == 5
    assert client.get('/api/v1/analytics?period=6h').json()['reviews']['total'] == 1


def test_stakeholder_outcomes_removed(reporting_db):
    client = reporting_db
    assert '/api/v1/reviews/{review_id}/outcomes' not in client.get('/openapi.json').json()['paths']
    assert 'acceptance' not in client.get('/api/v1/analytics').json()


def test_inbox_and_outcome_tenant_isolation_and_scope(reporting_db, credentials):
    client = reporting_db
    a, b = seed(), seed(tenant='tenant_b')
    fa, fb = feedback(a), feedback(b, tenant='tenant_b')
    assert client.get('/api/v1/feedback', headers=credentials['read']).status_code == 403
    assert client.get('/api/v1/feedback', params={'starting_after': fb['id']}, headers=credentials['a']).status_code == 400
    assert [x['feedback']['id'] for x in client.get('/api/v1/feedback', headers=credentials['a']).json()['items']] == [fa['id']]
    read_stats = client.get('/api/v1/analytics', headers=credentials['read']).json()
    assert read_stats['reviews']['total'] == 1
    assert read_stats['feedback'] is None and 'acceptance' not in read_stats


def test_empty_analytics_and_no_model_dependency(reporting_db, monkeypatch):
    monkeypatch.setenv('RUN_MODE', 'live')
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


def classification(rid, *, tenant='vesta', observation='obs-1', group='thoracic', priority='hours', status='completed', version=1):
    cid = 'jc_' + uuid.uuid4().hex
    result = {'fields': {'finding_group': {'label': group}, 'urgency': {'label': priority},
                         'certainty': {'label': 'definite'}, 'polarity': {'label': 'affirmed'},
                         'temporal_status': {'label': 'new'}}} if status == 'completed' else None
    with store.db() as conn:
        conn.execute('''INSERT INTO finding_classifications
          (tenant_id,id,review_id,input_version,observation_id,input_hash,input,config,workflow_id,
           execution_status,steps,result,created_at,updated_at)
          VALUES(?,?,?,?,?,'hash','{}','{}',?,?,'[]',?,?,?)''',
          (tenant,cid,rid,version,observation,cid,status,store.canonical(result) if result else None,store.now(),store.now()))
    return cid


def test_history_and_analytics_capture_only_current_group_and_priority(reporting_db):
    client = reporting_db
    rid = seed(critical=True)
    classification(rid, group='neurological', priority='minutes')
    classification(rid, group='vascular_cardiac', priority='hours')  # latest replaces earlier labels
    failed = seed(critical=True)
    classification(failed)
    classification(failed, status='failed')  # never resurrect an older successful attempt
    obsolete = seed(critical=True)
    classification(obsolete, version=2)  # not the currently submitted version
    classification(seed(critical=True, days=10), priority='days')
    classification(seed(critical=True, source='demo'), priority='routine')
    classification(seed(critical=True, tenant='tenant_b'), tenant='tenant_b', priority='minutes')
    # A noncritical report cannot acquire a classification in these projections.
    classification(seed(), priority='minutes')
    expected = {'finding_group':'vascular_cardiac','communication_priority':'hours'}
    history = client.get('/api/v1/reviews', params={'q':rid}).json()['items']
    assert history[0]['classification_overview'] == [expected]
    for absent in (failed, obsolete):
        assert client.get('/api/v1/reviews', params={'q':absent}).json()['items'][0]['classification_overview'] == []
    counts = client.get('/api/v1/analytics?period=1h').json()['classification']
    assert counts == {'finding_groups':{'vascular_cardiac':1},'communication_priorities':{'hours':1}}
    all_sources = client.get('/api/v1/analytics?period=all&source=all').json()['classification']
    assert all_sources == {'finding_groups':{'vascular_cardiac':1,'thoracic':2},
                           'communication_priorities':{'hours':1,'days':1,'routine':1}}
    # Replacement removes old-version labels from both surfaces immediately.
    with store.db() as conn:
        conn.execute('UPDATE review_records SET input_version=2 WHERE tenant_id=? AND id=?',('vesta',rid))
    assert client.get('/api/v1/reviews', params={'q':rid}).json()['items'][0]['classification_overview'] == []
    assert client.get('/api/v1/analytics?period=1h').json()['classification'] == {'finding_groups':{},'communication_priorities':{}}


def test_classification_counts_multiple_findings_without_page_or_readiness_dependency(reporting_db, monkeypatch):
    result = {'result_version':1,'outcome':'observations','critical_finding_detected':True,'general_comments':[],
              'critical_comments':[{'observation_id':f'obs-{i}','comment':f'Controlled finding {i}.'} for i in (1,2)]}
    rid = seed(result=result)
    classification(rid, observation='obs-1', group='thoracic', priority='cannot_determine')
    classification(rid, observation='obs-2', group='neurological', priority='minutes')
    for _ in range(21):
        seed()
    monkeypatch.delenv('TYPESAFE_API_KEY', raising=False)
    monkeypatch.setenv('QA_JEV_ENABLED','false')
    history = reporting_db.get('/api/v1/reviews', params={'q':rid}).json()['items'][0]
    assert history['classification_overview'] == [
        {'finding_group':'thoracic','communication_priority':'cannot_determine'},
        {'finding_group':'neurological','communication_priority':'minutes'}]
    assert all(set(value) == {'finding_group','communication_priority'} for value in history['classification_overview'])
    counts = reporting_db.get('/api/v1/analytics?period=all').json()['classification']
    assert counts == {'finding_groups':{'thoracic':1,'neurological':1},
                      'communication_priorities':{'cannot_determine':1,'minutes':1}}
