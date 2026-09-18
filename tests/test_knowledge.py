"""Editorial storage and access tests. No model or clinical-content changes."""
import json
import os
import uuid
import pytest
from backend import store, knowledge, skill_runtime
from test_api_design import credentials


@pytest.fixture
def editorial_db(client, monkeypatch, tmp_path):
    monkeypatch.setattr(store, 'DATA', tmp_path / 'data')
    store.init()
    return client


def body(client, document_id='skill_qa-critical-match', headers=None):
    result=client.get('/api/v1/knowledge/'+document_id, headers=headers or {})
    assert result.status_code==200, result.text
    doc=result.json()
    return dict(expected_revision=doc['document']['latest_revision'], source_sha256=doc['document']['source_sha256'],
                package_sha256=doc['package_sha256'], content=doc['installed_content']+'\nEditorial proposal.\n', change_note='Explain the proposed change.')


def save(client, payload, document_id='skill_qa-critical-match', key=None, headers=None):
    return client.post('/api/v1/knowledge/'+document_id+'/drafts', json=payload,
                       headers={'Idempotency-Key':key or uuid.uuid4().hex, **(headers or {})})


def test_catalog_truthful_runtime_mapping_and_private_sources(editorial_db, monkeypatch, tmp_path):
    client=editorial_db
    manual=tmp_path/'private-manual.txt';manual.write_text('Tenant guidance only.')
    monkeypatch.setenv('QA_POLICY_PATH', str(manual))
    page=client.get('/api/v1/knowledge').json()
    assert page['can_edit'] and len(page['items'])==16
    gate=next(d for d in page['items'] if d['document_id']=='skill_qa-input-adequacy')
    assert gate['runtime_use']=='host_reference' and gate['stages']==[]
    critical=next(d for d in page['items'] if d['document_id']=='skill_qa-critical-match')
    assert critical['stages']==['critical_finding_review']
    response=client.get('/api/v1/knowledge/guidance_tenant')
    assert response.json()['installed_content']=='Tenant guidance only.'
    assert str(manual) not in response.text
    assert 'content' not in critical  # list carries metadata only


def test_draft_replay_conflicts_export_and_runtime_unchanged(editorial_db, monkeypatch):
    client=editorial_db
    before=skill_runtime.load_snapshot()
    payload=body(client);key=uuid.uuid4().hex
    first=save(client,payload,key=key)
    assert first.status_code==201,first.text
    replay=save(client,payload,key=key)
    assert replay.content==first.content and replay.headers['Idempotency-Replayed']=='true'
    assert save(client,payload|{'content':'different'},key=key).status_code==409
    assert save(client,payload).json()['error']['code']=='KNOWLEDGE_REVISION_CONFLICT'
    detail=client.get('/api/v1/knowledge/skill_qa-critical-match').json()
    assert detail['document']['has_changes'] and detail['draft']['revision']==1
    assert '+Editorial proposal.' in detail['saved_diff']
    exported=client.get('/api/v1/knowledge/skill_qa-critical-match/drafts/1/export').json()
    assert exported['draft']['content']==payload['content']
    assert exported['draft']['status']=='draft_not_active'
    store.init()
    assert client.get('/api/v1/knowledge/skill_qa-critical-match').json()['draft']['revision']==1
    assert skill_runtime.load_snapshot()==before
    monkeypatch.setattr(knowledge,'sources',lambda *_, **kwargs: (_ for _ in ()).throw(ValueError('drift')))
    assert save(client,payload,key=key).content==first.content  # accepted receipt survives unavailable source


def test_source_change_blank_and_unknown_document(editorial_db):
    client=editorial_db
    data=body(client)
    assert save(client,data|{'source_sha256':'0'*64}).json()['error']['code']=='KNOWLEDGE_SOURCE_CHANGED'
    assert save(client,data|{'package_sha256':'0'*64}).status_code==409
    assert save(client,data|{'content':' '}).status_code==422
    assert save(client,data|{'change_note':' '}).status_code==422
    assert save(client,data|{'content':'\x00'}).status_code==422
    assert save(client,data|{'tenant_id':'tenant_b'}).status_code==422
    assert save(client,data,document_id='arbitrary-file').status_code==404
    assert client.get('/api/v1/knowledge/skill_qa-critical-match/drafts/0/export').status_code==422


def test_restore_revision_is_append_only(editorial_db):
    client=editorial_db
    first=body(client);save(client,first)
    second=body(client)|{'content':'Revised proposal.'};save(client,second)
    restore=body(client)|{'content':first['content'],'change_note':'Restore first proposal.'};save(client,restore)
    doc=client.get('/api/v1/knowledge/skill_qa-critical-match').json()
    assert [d['revision'] for d in doc['recent_revisions']]==[3,2,1]
    assert doc['draft']['content']==first['content']
    assert client.get('/api/v1/knowledge/skill_qa-critical-match/drafts/2/export').json()['draft']['content']=='Revised proposal.'


def test_tenant_drafts_and_permissions_are_independent(editorial_db, credentials, monkeypatch, tmp_path):
    client=editorial_db
    assert client.get('/api/v1/knowledge', headers=credentials['a']).status_code==403
    # Explicitly grant editorial rights to two test tenants, and read-only catalog access to a third key.
    path=os.environ['QA_TENANT_KEYS_FILE'];grants=json.loads(open(path).read())
    grants[0]['scopes']+=['skills:read','skills:write'];grants[1]['scopes']+=['skills:read','skills:write'];grants[2]['scopes']+=['skills:read']
    with open(path,'w') as handle:json.dump(grants,handle)
    manual=tmp_path/'vesta-private.txt';manual.write_text('Vesta-only manual')
    monkeypatch.setenv('QA_POLICY_PATH',str(manual))
    payload=body(client,headers=credentials['a'])
    assert save(client,payload,headers=credentials['a']).status_code==201
    assert client.get('/api/v1/knowledge/skill_qa-critical-match',headers=credentials['b']).json()['draft'] is None
    assert client.get('/api/v1/knowledge/skill_qa-critical-match/drafts/1/export',headers=credentials['b']).status_code==404
    assert client.get('/api/v1/knowledge/guidance_tenant',headers=credentials['b']).json()['installed_content']==''
    assert client.get('/api/v1/knowledge',headers=credentials['read']).json()['can_edit'] is False
    assert save(client,payload,headers=credentials['read']).status_code==403
    grants[2]['scopes']=['skills:write']
    with open(path,'w') as handle:json.dump(grants,handle)
    assert save(client,payload,headers=credentials['read']).status_code==403


def test_source_drift_fails_closed_but_saved_export_survives(editorial_db, monkeypatch):
    client=editorial_db
    save(client,body(client))
    monkeypatch.setattr(skill_runtime,'load_snapshot',lambda *_, **kwargs: (_ for _ in ()).throw(ValueError('Broken package')))
    assert client.get('/api/v1/knowledge').status_code==503
    assert client.get('/api/v1/knowledge/skill_qa-critical-match/drafts/1/export').status_code==200
