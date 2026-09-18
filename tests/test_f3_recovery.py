"""Kill/restart actual DBOS processes around the guarded provider boundary."""
import json
import time
import sys
import uuid
from pathlib import Path
import pytest
from test_recovery import Server, ROOT


@pytest.mark.parametrize('point,calls,success', [
    ('before_provider_claim',1,True),
    ('after_provider_claim',0,False),
    ('after_provider_response',1,False),
    ('after_response_checkpoint',1,True),
    ('after_combined_review',1,True),
    ('after_final_commit',1,True),
])
def test_single_dispatch_across_crash(tmp_path, point, calls, success):
    boot = tmp_path/'boot.py'
    boot.write_text('''
import os, sys
sys.path[:0] = [os.environ['QA_TEST_PROJECT'], os.environ['QA_TEST_PROJECT']+'/tests']
from backend import reviewer, spend
from test_sdk import ControlledModel
spend.PRICING['controlled-sdk-test'] = (1,1)
class Calls(list):
    def append(self, instructions):
        with open(os.environ['QA_CALL_LOG'], 'a') as f:
            f.write('call\\n')
reviewer.make_model=lambda config, client: ControlledModel(Calls())
import uvicorn
uvicorn.run('backend.main:app',host='127.0.0.1',port=int(os.environ['QA_PORT']),access_log=False)
''')
    server = Server(tmp_path, QA_MODE='openai', OPENAI_API_KEY='controlled-no-network',
        OPENAI_MODEL='controlled-sdk-test', QA_TEST_PROJECT=str(ROOT),
        QA_CALL_LOG=str(tmp_path/'calls.log'), QA_TEST_PAUSE_AT=point)
    server.command = [sys.executable,str(boot)]
    server.env['QA_PORT'] = str(server.port)
    key = str(uuid.uuid4())
    payload = dict(report_text='Findings: Clear lungs. Impression: No acute disease.')
    try:
        server.start()
        receipt = server.client.post('/api/v1/reviews', json=payload, headers={'Idempotency-Key':key})
        assert receipt.status_code == 202, receipt.text
        rid = receipt.json()['id']
        paused = tmp_path/'hooks/paused'
        until = time.monotonic()+20
        while not paused.exists() and time.monotonic() < until:
            time.sleep(.05)
        assert paused.exists(), (tmp_path/'server.log').read_text()
        server.kill()
        server.env.pop('QA_TEST_PAUSE_AT')
        server.start()
        until = time.monotonic()+20
        while time.monotonic() < until:
            result = server.client.get('/api/v1/reviews/'+rid).json()
            if result['execution_status'] not in ('running','queued'):
                break
            time.sleep(.05)
        assert result['execution_status'] == ('completed' if success else 'failed'), result
        if not success:
            assert result['result'] is None
            assert result['error']['code'] == 'MODEL_OUTCOME_UNKNOWN'
            assert result['error']['retryable'] is False
        replay = server.client.post('/api/v1/reviews', json=payload, headers={'Idempotency-Key':key})
        assert replay.json() == receipt.json()
        log = tmp_path/'calls.log'
        # Explicit parentheses ensure zero-call assertion is not a conditional expression.
        assert (len(log.read_text().splitlines()) if log.exists() else 0) == calls
        from backend import spend
        status = spend.status('controlled-test')
        assert 0 < status['committed_micro_usd'] <= status['ceiling']
        if not success:
            with spend.db() as conn:
                reservation = conn.execute('SELECT * FROM reservations WHERE id=?',(rid,)).fetchone()
            assert reservation['charged'] == reservation['bound']
    finally:
        server.close()
