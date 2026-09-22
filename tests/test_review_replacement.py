"""Latest-state review replacement; synthetic inputs only, no provider calls."""
import uuid
from concurrent.futures import ThreadPoolExecutor
import pytest
from backend import store, reporting, attempts
from backend.contracts import ReviewInput, ReviewReplacement, FeedbackInput, ReviewProblem
from backend.settings import APP_VERSION
from test_api import post, finish

TEXT = 'Findings: Clear lungs. Impression: No acute disease.'

@pytest.fixture
def current_store(monkeypatch, tmp_path):
    monkeypatch.setattr(store, 'DATA', tmp_path)
    store.init()
    return {'mode':'demo', 'workflow_version':APP_VERSION}

def reserve(cfg, text=TEXT):
    return store.reserve('vesta', uuid.uuid4().hex, ReviewInput(report_text=text), cfg)[0]['body']['id']

def replace(cfg, rid, version=1, key=None):
    return store.reserve('vesta', key or uuid.uuid4().hex, ReviewReplacement(report_text=TEXT+' Corrected.', expected_input_version=version), cfg, replace_id=rid)

def complete(rid):
    store.update('vesta', rid, execution_status='completed', result={'result_version':1,'outcome':'no_observations','general_comments':[], 'critical_comments':[], 'critical_finding_detected':False})

def test_replace_discards_old_result_and_snapshot_preserves_feedback(current_store):
    cfg = current_store
    rid = reserve(cfg)
    complete(rid)
    f = store.save_feedback('vesta', rid, 'feedback', FeedbackInput(rating='up'))[0]['body']
    original_time = store.get('vesta', rid)['created_at']
    accepted, created = replace(cfg, rid, key='replace')
    assert created and accepted['body']['id'] == rid
    current = store.get('vesta', rid)
    assert current['result'] is None and current['execution_status'] == 'queued'
    assert current['input_version'] == 2 and current['created_at'] > original_time
    store.update('vesta', rid, input_version=1, execution_status='failed', error={'code':'OLD'})
    assert store.get('vesta', rid)['execution_status'] == 'queued'
    with pytest.raises(ReviewProblem, match='replaced'):
        attempts.claim('vesta', rid, 'obsolete', generation=1)
    complete(rid)
    assert store.get('vesta', rid)['result']['result_version'] == 2
    assert store.feedback('vesta', rid)[0][0]['feedback_id'] == f['id']
    assert reporting.analytics('vesta', 'all', 'all', True)['reviews']['total'] == 1
    assert reporting.feedback_inbox('vesta', '2026-09-22', source='all')[0][0]['feedback']['id'] == f['id']
    with store.db() as conn:
        for table in ('review_records','review_snapshots','review_results'):
            assert conn.execute(f'SELECT count(*) FROM {table}').fetchone()[0] == 1
        assert conn.execute('SELECT count(*) FROM outcomes').fetchone()[0] == 0
        assert not conn.execute('PRAGMA foreign_key_check').fetchall()
    replay, created = replace(cfg, rid, key='replace')
    assert not created and replay == accepted

def test_busy_stale_concurrent_and_tenant_replacements(current_store):
    cfg = current_store
    rid = reserve(cfg)
    with pytest.raises(store.ReviewConflict): replace(cfg, rid)
    complete(rid)
    def competing(_):
        try: return replace(cfg, rid)[1]
        except store.ReviewConflict: return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(competing, range(2))) == [False, True]
    complete(rid)
    with pytest.raises(store.ReviewConflict): replace(cfg, rid)
    with pytest.raises(KeyError):
        store.reserve('other', 'key', ReviewReplacement(report_text=TEXT, expected_input_version=2), cfg, replace_id=rid)

def test_history_orders_by_latest_submission(current_store):
    first = reserve(current_store); complete(first)
    second = reserve(current_store); complete(second)
    replace(current_store, first)
    rows, more = store.list_reviews('vesta', limit=1)
    assert rows[0]['id'] == first and more
    assert store.list_reviews('vesta', starting_after=first)[0][0]['id'] == second

def test_api_failure_then_corrected_success_is_one_review(client):
    failed = finish(client, post(client, text='Findings: only findings.'))
    assert failed['execution_status'] == 'needs_input'
    from backend.reviewer import SAMPLES
    text = next(s['report_text'] for s in SAMPLES if s['id']=='clean')
    payload = {'report_text':text,'expected_input_version':failed['input_version']}
    key = uuid.uuid4().hex
    url = '/api/v1/reviews/'+failed['id']
    accepted = client.put(url, json=payload, headers={'Idempotency-Key':key})
    done = finish(client, accepted)
    assert done['id'] == failed['id'] and done['input']['report_text'] == text
    assert done['execution_status'] == 'completed' and done['input_version'] == 2
    assert client.put(url, json=payload, headers={'Idempotency-Key':key}).json() == accepted.json()
    assert client.put(url, json=payload, headers={'Idempotency-Key':uuid.uuid4().hex}).status_code == 409
    rows = client.get('/api/v1/reviews', params={'q':failed['id']}).json()['items']
    assert len(rows) == 1 and rows[0]['execution_status'] == 'completed'

@pytest.mark.parametrize("pending", [False, True])
def test_explicit_upgrade_preserves_reviews_and_feedback(tmp_path, pending):
    import sqlite3
    import json
    from pathlib import Path
    from scripts.upgrade_review_storage import upgrade
    path = tmp_path/'reviews.sqlite'
    with sqlite3.connect(path) as conn:
        conn.executescript((Path(__file__).parent/'fixtures/schema6.sql').read_text())
        conn.execute('PRAGMA user_version=6')
        conn.execute("INSERT INTO tenants VALUES('vesta',NULL)")
        conn.execute("INSERT INTO review_snapshots VALUES('vesta','qs','hash','{}')")
        conn.execute("INSERT INTO review_records VALUES('vesta','qr','qs','old text','hash','now','now',?,'[]','{}',NULL,'2026-09-18')", ("queued" if pending else "completed",))
        conn.execute("INSERT INTO review_results VALUES('vesta','qr',1,'{}')")
        conn.execute('INSERT INTO feedback(tenant_id,id,review_id,document,schema_version) VALUES(?,?,?,?,6)',
                     ('vesta','qf','qr',json.dumps({'feedback_id':'qf','review_id':'qr','result_version':1,'input_hash':'hash','rating':'up'})))
    if pending:
        with pytest.raises(SystemExit, match='Pending work'):
            upgrade(tmp_path)
        with sqlite3.connect(path) as conn:
            assert conn.execute('PRAGMA user_version').fetchone()[0] == 6
        assert not list(tmp_path.glob('*.bak'))
        return
    upgrade(tmp_path)
    with sqlite3.connect(path) as conn:
        assert conn.execute('PRAGMA user_version').fetchone()[0] == 7
        assert conn.execute('SELECT report_text,input_version FROM review_records').fetchone() == ('old text',1)
        doc = json.loads(conn.execute('SELECT document FROM feedback').fetchone()[0])
        assert 'input_hash' not in doc and 'result_version' not in doc
        assert not conn.execute('PRAGMA foreign_key_check').fetchall()
    assert len(list(tmp_path.glob('*.bak'))) == 1
