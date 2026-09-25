"""Real DBOS process kill/restart with isolated storage and a mocked JEV transport."""
import json
import sys
import time
import uuid
import pytest
from test_recovery import Server, ROOT


@pytest.mark.parametrize('point,calls,crashes,success',[
    ('jev_after_claim',1,1,True), ('jev_after_response',2,1,True),
    ('jev_after_checkpoint',1,1,True), ('jev_after_final_commit',1,1,True),
    ('jev_after_response',3,3,False),
])
def test_classification_restart(tmp_path,point,calls,crashes,success):
    boot=tmp_path/'boot.py'
    boot.write_text('''
import os,sys,json
sys.path.insert(0,os.environ['QA_TEST_PROJECT'])
import httpx
from backend import jev,classification_store
classification_store.ATTEMPT_LEASE_SECONDS=.1

def respond(request):
    with open(os.environ['QA_CALL_LOG'],'a') as f:f.write('call\\n')
    payload=json.loads(request.content)
    choices={'finding_group':'thoracic','polarity':'affirmed','certainty':'definite',
             'temporal_status':'not_stated','urgency':'cannot_determine'}
    answers={}
    for field,q in payload['questions'].items():
        chosen=choices[field]
        answers[field]={'type':'choice','choice':chosen,'confidence':.93,
            'probabilities':{key:float(key==chosen) for key in q['criteria']}}
    return httpx.Response(200,json={'model':'jev-1.13.0','answers':answers})
jev.make_client=lambda timeout:httpx.Client(transport=httpx.MockTransport(respond))
import uvicorn
uvicorn.run('backend.main:app',host='127.0.0.1',port=int(os.environ['QA_PORT']),access_log=False)
''')
    server=Server(tmp_path,TYPESAFE_API_KEY='controlled-no-network',
                  OPENAI_API_KEY='',QA_TEST_PROJECT=str(ROOT),QA_CALL_LOG=str(tmp_path/'calls.log'),
                  QA_TEST_PAUSE_AT=point)
    server.command=[sys.executable,str(boot)]
    server.env['QA_PORT']=str(server.port)
    try:
        server.start()
        samples=server.client.get('/api/v1/config').json()['samples']
        report=next(s['report_text'] for s in samples if s['id']=='critical')
        accepted=server.client.post('/api/v1/reviews',json={'report_text':report},headers={'Idempotency-Key':str(uuid.uuid4())})
        assert accepted.status_code==202,accepted.text
        rid=accepted.json()['id']
        for crash in range(crashes):
            deadline=time.monotonic()+20
            while not (tmp_path/'hooks/paused').exists() and time.monotonic()<deadline:time.sleep(.05)
            assert (tmp_path/'hooks/paused').exists(),(tmp_path/'server.log').read_text()
            server.kill()
            (tmp_path/'hooks/paused').unlink()
            if crash == crashes-1:server.env.pop('QA_TEST_PAUSE_AT')
            server.start()
        deadline=time.monotonic()+20
        runs=[]
        while time.monotonic()<deadline:
            runs=server.client.get(f'/api/v1/reviews/{rid}/classifications').json()
            if runs and runs[0]['execution_status'] in ('completed','failed'):break
            time.sleep(.05)
        assert len(runs)==1 and runs[0]['execution_status']==('completed' if success else 'failed'),runs
        if not success:
            assert runs[0]['error']['code']=='JEV_RETRIES_EXHAUSTED'
            assert runs[0]['result'] is None
        assert len((tmp_path/'calls.log').read_text().splitlines())==calls
        assert server.client.get('/api/v1/reviews/'+rid).json()['execution_status']=='completed'
    finally:server.close()
