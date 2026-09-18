"""Exercise the actual OpenAI HTTP adapter with a local transport; zero network spend."""
import json
import re
import uuid
import httpx
import pytest
from openai import AsyncOpenAI
from backend import reviewer, spend, attempts
from test_api import finish, post


@pytest.mark.parametrize('outcome', ['valid','incomplete','refusal','http_error','missing_usage','bad_coverage','tool_call'])
def test_actual_http_adapter_is_single_call(client, monkeypatch, outcome):
    calls = []
    def respond(request):
        body = json.loads(request.content)
        calls.append(body)
        assert body['service_tier'] == 'default'
        assert body['max_output_tokens'] == 6000
        assert not body.get('tools') and body['store'] is False
        checks = json.loads(re.search(r'checked_skills must contain each of these exactly once: (\[.*?\])',body['instructions']).group(1))
        output = dict(input_problem=None,checked_skills=checks,observations=[],designation=dict(status='unknown',anchor=None))
        if outcome == 'bad_coverage':
            output['checked_skills'] = []
        content = [{'type':'output_text','text':json.dumps(output),'annotations':[]}]
        if outcome == 'refusal':
            content = [{'type':'refusal','refusal':'Controlled refusal'}]
        if outcome == 'http_error':
            return httpx.Response(500,json={'error':{'message':'Controlled error','type':'server_error','code':'server_error'}})
        result = dict(id='resp_controlled',object='response',created_at=1,model='controlled-sdk-test',
            status='incomplete' if outcome == 'incomplete' else 'completed',
            output=[dict(id='msg_controlled',type='message',role='assistant',status='completed',content=content)],
            usage=dict(input_tokens=20,output_tokens=10,total_tokens=30))
        if outcome == 'tool_call':
            result['output'] = [dict(type='function_call',id='fc',call_id='fc',name='unconfigured',arguments='{}')]
        if outcome == 'missing_usage':
            result.pop('usage')
        return httpx.Response(200,json=result)
    def factory(**kwargs):
        return AsyncOpenAI(**kwargs, api_key='controlled-never-transmitted', http_client=httpx.AsyncClient(transport=httpx.MockTransport(respond)))
    monkeypatch.setattr(reviewer,'AsyncOpenAI',factory)
    monkeypatch.setenv('QA_MODE','openai')
    monkeypatch.setenv('OPENAI_API_KEY','controlled-never-transmitted')
    monkeypatch.setenv('OPENAI_MODEL','controlled-sdk-test')
    receipt = post(client,key=uuid.uuid4().hex,sample='clean')
    assert receipt.status_code == 202, receipt.text
    result = finish(client,receipt)
    assert len(calls) == 1
    assert result['execution_status'] == ('completed' if outcome in ('valid','missing_usage') else 'failed'), result
    with spend.db() as conn:
        r = conn.execute('SELECT * FROM reservations WHERE id=?',(result['id'],)).fetchone()
    if outcome in ('http_error','incomplete','missing_usage'):
        assert r['charged'] == r['bound']
    else:
        assert r['charged'] == 33
    if outcome in ('valid','refusal','tool_call'):
        metrics = result['steps'][1]['metrics']
        assert metrics['model_calls'] == 1 and metrics['cost_upper_bound_micro_usd'] == 33


def test_invalid_input_uses_zero_calls_and_releases_reservation(client,monkeypatch):
    monkeypatch.setenv('QA_MODE','openai')
    monkeypatch.setenv('OPENAI_API_KEY','controlled-only')
    monkeypatch.setenv('OPENAI_MODEL','controlled-sdk-test')
    monkeypatch.setattr(reviewer,'make_model',lambda *args: pytest.fail('Invalid input reached provider'))
    receipt = client.post('/api/v1/reviews',json={'report_text':'No identifiable report sections'},headers={'Idempotency-Key':uuid.uuid4().hex})
    assert receipt.status_code == 202, receipt.text
    result = finish(client,receipt)
    assert result['execution_status'] == 'needs_input'
    assert spend.status('controlled-test')['committed_micro_usd'] == 0


def test_concurrent_post_replay_uses_one_attempt(client,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from test_sdk import ControlledModel
    calls=[]
    monkeypatch.setenv('QA_MODE','openai')
    monkeypatch.setenv('OPENAI_API_KEY','controlled-only')
    monkeypatch.setenv('OPENAI_MODEL','controlled-sdk-test')
    monkeypatch.setattr(reviewer,'make_model',lambda *args: ControlledModel(calls))
    key=uuid.uuid4().hex
    with ThreadPoolExecutor(max_workers=8) as pool:
        responses=list(pool.map(lambda _: post(client,key=key,sample='clean'),range(8)))
    assert all(r.status_code==202 for r in responses), [r.text for r in responses]
    assert all(r.json()==responses[0].json() for r in responses)
    result=finish(client,responses[0])
    assert result['execution_status']=='completed'
    assert len(calls)==1
    with spend.db() as conn:
        assert conn.execute('SELECT count(*) FROM reservations').fetchone()[0]==1
    monkeypatch.delenv('QA_SPEND_SESSION')
    monkeypatch.delenv('OPENAI_API_KEY')
    assert post(client,key=key,sample='clean').json()==responses[0].json()


def test_missing_session_blocks_acceptance(client,monkeypatch):
    monkeypatch.setenv('QA_MODE','openai')
    monkeypatch.setenv('OPENAI_API_KEY','controlled-only')
    monkeypatch.setenv('OPENAI_MODEL','controlled-sdk-test')
    monkeypatch.delenv('QA_SPEND_SESSION')
    monkeypatch.setattr(reviewer,'make_model',lambda *args: pytest.fail('Unauthorized request reached model'))
    response=post(client,key=uuid.uuid4().hex,sample='clean')
    assert response.status_code==409
    assert response.json()['error']['code']=='SPEND_NOT_AUTHORIZED'
    with spend.db() as conn:
        assert conn.execute('SELECT count(*) FROM reservations').fetchone()[0]==0
