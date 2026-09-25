"""Controlled retry, ownership and checkpoint behavior; no external requests."""
import json
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest

from test_classification import workspace, review, responses, classify, settle, enable_classification
from backend import classification_store as records, jev, main, preferences
from backend.classification import snapshot, ClassificationProblem
from backend.contracts import ClassificationInput


def reserve(client, monkeypatch):
    enable_classification()
    config = snapshot(accepted=True)
    current=preferences.read('vesta')
    disabled=current.model_copy(update={'features':current.features.model_copy(update={'classification':False})})
    monkeypatch.setattr(preferences,'read',lambda _tenant:disabled)
    source = review(client)
    payload = ClassificationInput(review_id=source['id'], input_version=source['input_version'],
                                 observation_id=source['result']['critical_comments'][0]['observation_id'])
    saved, _ = records.reserve('vesta', 'retry-test', payload, config)
    rid = saved['body']['id']
    return rid, records.job('vesta', rid)


@pytest.mark.parametrize('first', ['timeout', 408, 429, 500, 503, 529])
def test_transient_failure_then_success(workspace, monkeypatch, first):
    calls = responses(monkeypatch)
    valid_client = jev.make_client
    attempts = []
    def respond(request):
        attempts.append(request)
        if len(attempts) == 1:
            if first == 'timeout':
                raise httpx.ReadTimeout('uncertain response')
            return httpx.Response(first, json={'error':'temporary'})
        with valid_client(1) as client:
            return client.send(request)
    monkeypatch.setattr(jev, 'make_client', lambda timeout: httpx.Client(transport=httpx.MockTransport(respond)))
    monkeypatch.setattr(jev, 'retry_delay', lambda *args: 0)
    rid, (data, config) = reserve(workspace, monkeypatch)
    checkpoint = jev.dispatch_retrying('vesta', rid, data, config)
    assert checkpoint['outcome'] == 'response' and len(attempts) == 2
    assert json.loads(checkpoint['claim_id'])['count'] == 2
    assert jev.dispatch_retrying('vesta', rid, data, config) == checkpoint
    assert len(attempts) == 2  # Saved response never causes a new provider call.


def test_retry_budget_survives_reentry(workspace, monkeypatch):
    calls = responses(monkeypatch, 'timeout')
    monkeypatch.setattr(jev, 'retry_delay', lambda *args: 0)
    rid, (data, config) = reserve(workspace, monkeypatch)
    for _ in range(2):
        with pytest.raises(ClassificationProblem, match='three attempts'):
            jev.dispatch_retrying('vesta', rid, data, config)
    assert len(calls) == 3
    assert json.loads(records.attempt('vesta', rid)['claim_id'])['count'] == 3


@pytest.mark.parametrize('status,body', [(401,'{}'), (403,'{}'), (422,'{}'), (200,'invalid json')])
def test_permanent_errors_do_not_retry(workspace, monkeypatch, status, body):
    calls=[]
    def respond(request):
        calls.append(request)
        return httpx.Response(status, text=body)
    monkeypatch.setattr(jev,'make_client',lambda timeout:httpx.Client(transport=httpx.MockTransport(respond)))
    source=review(workspace)
    enable_classification()
    result=settle(workspace,classify(workspace,source).json()['id'])
    assert result['execution_status']=='failed' and result['result'] is None
    assert len(calls)==1


def test_attempt_lease_and_checkpoint_fence(workspace, monkeypatch):
    rid, _ = reserve(workspace, monkeypatch)
    with ThreadPoolExecutor(max_workers=2) as pool:
        tokens=list(pool.map(lambda _:records.acquire_retry_attempt('vesta',rid,None),range(2)))
    first=next(token for token in tokens if token)
    assert sum(token is not None for token in tokens)==1
    previous=records.attempt('vesta',rid)
    assert records.acquire_retry_attempt('vesta',rid,previous) is None
    # Expire the lease without modifying global time used by the server.
    metadata=json.loads(first);metadata['not_before']=0
    expired=records.store.canonical(metadata)
    with records.store.db() as conn:
        conn.execute('UPDATE jev_classification_attempts SET claim_id=? WHERE classification_id=?',(expired,rid))
    second=records.acquire_retry_attempt('vesta',rid,records.attempt('vesta',rid))
    assert second and json.loads(second)['count']==2
    with pytest.raises(RuntimeError,match='ownership'):
        records.checkpoint_retry_attempt('vesta',rid,first,status=200,body='{}')
    records.checkpoint_retry_attempt('vesta',rid,second,status=200,body='{}')
    assert records.attempt('vesta',rid)['outcome']=='response'


def test_retry_after_respected_and_long_delay_is_terminal(workspace, monkeypatch):
    assert jev.retry_delay(httpx.Response(429,headers={'Retry-After':'2'}),1)>=2
    assert jev.retry_delay(httpx.Response(429,headers={'Retry-After':'120'}),1) is None
    calls=[]
    def respond(request):
        calls.append(request)
        return httpx.Response(429,headers={'Retry-After':'120'},json={})
    monkeypatch.setattr(jev,'make_client',lambda timeout:httpx.Client(transport=httpx.MockTransport(respond)))
    rid,(data,config)=reserve(workspace,monkeypatch)
    assert jev.dispatch_retrying('vesta',rid,data,config)['outcome']=='known_failure'
    assert len(calls)==1


def test_automatic_dispatch_does_not_need_reconciliation(workspace, monkeypatch):
    import time
    calls=responses(monkeypatch)
    monkeypatch.setattr(main,'reconcile_classifications',lambda:None)
    enable_classification()
    source=review(workspace)
    runs=[]
    for _ in range(100):
        runs=workspace.get(f'/api/v1/reviews/{source["id"]}/classifications').json()
        if runs:
            break
        time.sleep(.01)
    assert len(runs)==1
    assert settle(workspace,runs[0]['id'])['execution_status']=='completed'
    assert len(calls)==1


def test_success_uses_five_application_write_transactions(workspace, monkeypatch):
    from contextlib import contextmanager
    source=review(workspace)
    calls=responses(monkeypatch)
    enable_classification()
    original=records.store.db
    statements=[]
    @contextmanager
    def traced_db():
        with original() as conn:
            conn.set_trace_callback(statements.append)
            yield conn
    monkeypatch.setattr(records.store,'db',traced_db)
    run=settle(workspace,classify(workspace,source).json()['id'])
    assert run['execution_status']=='completed'
    assert all(phase['status']=='completed' for phase in run['steps'])
    assert sum(sql=='BEGIN IMMEDIATE' for sql in statements)==5
    assert len(calls)==1


def test_failed_enqueue_is_recovered_by_fallback(workspace, monkeypatch):
    import time
    from backend import classification_workflow
    calls=responses(monkeypatch)
    original=classification_workflow.dispatch
    def unavailable(*args):
        raise RuntimeError('controlled enqueue interruption')
    monkeypatch.setattr(classification_workflow,'dispatch',unavailable)
    enable_classification()
    source=review(workspace)
    runs=[]
    for _ in range(100):
        runs=workspace.get(f'/api/v1/reviews/{source["id"]}/classifications').json()
        if runs:break
        time.sleep(.01)
    assert len(runs)==1 and runs[0]['execution_status']=='queued'
    monkeypatch.setattr(classification_workflow,'dispatch',original)
    main.reconcile_classifications()
    assert settle(workspace,runs[0]['id'])['execution_status']=='completed'
    assert len(calls)==1


@pytest.mark.parametrize('status,error', [(401,httpx.ReadError), (200,httpx.DecodingError)])
def test_invalid_or_rejected_response_body_is_not_retried(workspace, monkeypatch, status, error):
    calls=[]

    class BrokenResponse:
        status_code=status
        headers={}

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def iter_bytes(self):
            raise error('controlled unreadable response')

    class BrokenClient:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def stream(self, *_args, **_kwargs):
            calls.append(_kwargs['json'])
            return BrokenResponse()

    monkeypatch.setattr(jev,'make_client',lambda timeout:BrokenClient())
    rid,(data,config)=reserve(workspace,monkeypatch)
    checkpoint=jev.dispatch_retrying('vesta',rid,data,config)
    assert checkpoint['outcome']=='known_failure'
    with pytest.raises(ClassificationProblem):
        jev.parsed_response(checkpoint)
    assert len(calls)==1
