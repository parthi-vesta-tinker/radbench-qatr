"""Tenant settings and feature gates. No external providers or workers."""
import hashlib
import json
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from backend import main, preferences, store, workflow
from backend.access import Principal, SCOPES
from backend.settings import runtime_config


@pytest.fixture
def settings_client(monkeypatch, tmp_path):
    monkeypatch.setattr(store, 'DATA', tmp_path)
    monkeypatch.setenv('RUN_MODE', 'demo')
    monkeypatch.setenv('ACCESS_MODE', 'local')
    monkeypatch.setenv('QA_JEV_ENABLED', 'false')
    monkeypatch.setenv('OPENAI_MODEL', 'gpt-6-astra')
    monkeypatch.setenv('CORE_REVIEW_MODELS', 'gpt-6-astra,controlled-second-model')
    monkeypatch.setenv('OPENAI_API_KEY', 'controlled-no-network')
    monkeypatch.setenv('TYPESAFE_API_KEY', 'controlled-no-network')
    monkeypatch.setattr(main, 'dispatch', lambda *args: None)
    monkeypatch.setattr(workflow, 'dispatch_playground', lambda *args: None)
    store.init()
    return TestClient(main.app, client=('127.0.0.1', 9000))


def update(client, **changes):
    value = client.get('/api/v1/settings').json()
    data = {k:value[k] for k in ('revision','run_mode','core_model','features')}
    data.update(changes)
    return client.put('/api/v1/settings', json=data)


def test_save_persists_and_runtime_uses_new_model(settings_client):
    client = settings_client
    first=client.get('/api/v1/settings').json()
    assert first['access_mode']=='local' and first['run_mode']=='demo'
    assert first['can_edit'] and first['revision']==0
    saved=update(client,run_mode='live',core_model='controlled-second-model')
    assert saved.status_code==200, saved.text
    assert saved.json()['revision']==1
    assert preferences.read('vesta').core_model=='controlled-second-model'
    cfg=runtime_config('vesta')
    assert cfg['mode']=='openai' and cfg['run_mode']=='live'
    assert cfg['model']=='controlled-second-model'
    public=client.get('/api/v1/config').json()
    assert public['run_mode']=='live' and 'mode' not in public
    assert 'OPENAI_API_KEY' not in saved.text and 'controlled-no-network' not in saved.text


def test_revision_conflict_and_retry(settings_client):
    client=settings_client
    value=preferences.read('vesta').model_dump()
    value['features']['skills']=False
    assert client.put('/api/v1/settings',json=value).status_code==200
    assert client.put('/api/v1/settings',json=value).json()['revision']==1
    value['features']['playground']=False
    assert client.put('/api/v1/settings',json=value).status_code==409


def test_models_credentials_and_access_are_validated(settings_client,monkeypatch):
    client=settings_client
    assert update(client,core_model='unapproved').status_code==422
    monkeypatch.delenv('OPENAI_API_KEY')
    assert update(client,run_mode='live').status_code==422
    monkeypatch.delenv('TYPESAFE_API_KEY')
    assert update(client,features={'playground':True,'skills':True,'classification':True}).status_code==422
    monkeypatch.setenv('ACCESS_MODE','public')
    assert not client.get('/api/v1/settings').json()['can_edit']
    assert update(client).status_code==403
    assert preferences.read('vesta').revision==0


def test_feature_gates_preserve_receipts_and_accepted_configuration(settings_client):
    client=settings_client
    payload={'sample_id':'critical-documented','model':'gpt-6-astra'}
    headers={'Idempotency-Key':uuid.uuid4().hex}
    accepted=client.post('/api/v1/playground/runs',json=payload,headers=headers)
    assert accepted.status_code==202,accepted.text
    assert update(client,features={'skills':False,'playground':False,'classification':False}).status_code==200
    for url in ('/api/v1/playground','/api/v1/knowledge'):
        response=client.get(url)
        assert response.status_code==403 and response.json()['error']['code']=='FEATURE_DISABLED'
    replay=client.post('/api/v1/playground/runs',json=payload,headers=headers)
    assert replay.status_code==202 and replay.json()==accepted.json()
    assert client.get('/api/v1/playground/runs/'+accepted.json()['run_id']).status_code==200
    assert client.post('/api/v1/playground/runs',json=payload,headers={'Idempotency-Key':uuid.uuid4().hex}).status_code==403
    assert runtime_config()['skill_snapshot']  # Hiding Skills never removes runtime instructions.


def test_demo_can_enable_jev_and_existing_review_keeps_snapshot(settings_client):
    client=settings_client
    assert update(client,features={'skills':True,'playground':True,'classification':True}).status_code==200
    assert client.get('/api/v1/classifications/config').json()['ready']
    assert client.get('/api/v1/config').json()['run_mode']=='demo'
    from backend.contracts import ReviewInput
    cfg=runtime_config()
    receipt,_=store.reserve('vesta',uuid.uuid4().hex,ReviewInput(report_text='Findings: Clear. Impression: Clear.'),cfg)
    rid=receipt['body']['id']
    assert update(client,run_mode='live',features={'skills':True,'playground':True,'classification':False}).status_code==200
    old=store.job('vesta',rid)[1]
    assert old['mode']=='demo' and old['jev_enabled_at_acceptance']
    assert old['jev_config_at_acceptance']['rubric']
    assert not runtime_config()['jev_enabled_at_acceptance']
    assert not client.get('/api/v1/classifications/config').json()['enabled']


def test_authenticated_settings_need_explicit_scope_and_are_tenant_scoped(settings_client,monkeypatch,tmp_path):
    client=settings_client
    tenant_file=tmp_path/'tenants.json';tenant_file.write_text(json.dumps({'vesta':{},'other':{}}))
    key_file=tmp_path/'keys.json'
    key_file.write_text(json.dumps([{'tenant_id':tenant,'key_sha256':hashlib.sha256(token.encode()).hexdigest(),'scopes':scopes} for token,tenant,scopes in [('reader','vesta',['reviews:read']),('admin','other',['reviews:read','settings:write'])]]))
    monkeypatch.setenv('QA_TENANTS_FILE',str(tenant_file));monkeypatch.setenv('QA_TENANT_KEYS_FILE',str(key_file));monkeypatch.setenv('ACCESS_MODE','api_key')
    data=preferences.defaults('vesta').model_dump();data['features']['skills']=False
    assert client.put('/api/v1/settings',json=data,headers={'Authorization':'Bearer reader'}).status_code==403
    assert client.put('/api/v1/settings',json=data,headers={'Authorization':'Bearer admin'}).status_code==200
    assert preferences.read('vesta').features.skills
    assert not preferences.read('other').features.skills


def test_concurrent_saves_cannot_overwrite_each_other(settings_client):
    principal=Principal('vesta',SCOPES)
    base=preferences.read('vesta')
    def save(model):
        try:return preferences.save(principal,base.model_copy(update={'core_model':model})).revision
        except main.AccessError as e:return e.status
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(save,['gpt-6-astra','controlled-second-model']))
    assert sorted(results)==[1,409]


def test_explicit_launcher_override_wins_once_and_features_survive(settings_client):
    client=settings_client
    assert update(client,run_mode='live',features={'playground':False,'skills':True,'classification':False}).status_code==200
    preferences.apply_launch_overrides(run_mode='demo')
    assert preferences.read('vesta').run_mode=='demo'
    assert not preferences.read('vesta').features.playground
    assert update(client,run_mode='live').status_code==200
    assert runtime_config()['run_mode']=='live'
