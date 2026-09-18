"""Real DBOS admission test; no clinical output or provider request is evaluated."""
import threading
import time
import uuid


def test_dbos_limits_parent_reviews_and_admits_waiting_work(client, monkeypatch):
    from backend import workflow
    release = threading.Event()
    entered = []
    original = workflow.validate
    def hold(payload):
        entered.append(payload['report_text'])
        assert release.wait(15), 'Test gate timed out'
        return original(payload)
    monkeypatch.setattr(workflow, 'validate', hold)
    ids = []
    try:
        for i in range(workflow.REVIEW_CONCURRENCY + 1):
            response = client.post('/api/v1/reviews', json={'report_text':f'Incomplete input {i}'}, headers={'Idempotency-Key':str(uuid.uuid4())})
            assert response.status_code == 202
            ids.append(response.json()['id'])
        deadline = time.monotonic() + 10
        while len(entered) < workflow.REVIEW_CONCURRENCY and time.monotonic() < deadline:
            time.sleep(.05)
        assert len(entered) == workflow.REVIEW_CONCURRENCY
        states = [client.get('/api/v1/reviews/'+rid).json()['execution_status'] for rid in ids]
        assert states.count('running') == workflow.REVIEW_CONCURRENCY
        assert states.count('queued') == 1
    finally:
        release.set()
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            states = [client.get('/api/v1/reviews/'+rid).json()['execution_status'] for rid in ids]
            if all(s not in ('queued','running') for s in states):
                break
            time.sleep(.05)
    assert states == ['needs_input'] * len(ids)
