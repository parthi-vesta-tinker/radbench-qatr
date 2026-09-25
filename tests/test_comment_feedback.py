"""Comment feedback is fenced to submitted input and survives replacement as context."""
import uuid

from backend import store
from backend.contracts import FeedbackInput, ReviewReplacement
from test_api import finish, post


def test_comment_feedback_version_replay_and_context(client):
    review = finish(client, post(client, 'mixed'))
    rid = review['id']
    observation = (review['result']['general_comments'] + review['result']['critical_comments'])[0]
    url = f'/api/v1/reviews/{rid}/feedback'
    payload = dict(rating='down', target='observation', observation_id=observation['observation_id'],
                   expected_input_version=review['input_version'], reason='unclear_wording',
                   suggested_comment='Optional alternative wording.')
    key = uuid.uuid4().hex
    def send(body, receipt=None):
        return client.post(url, json=body, headers={'Idempotency-Key': receipt or uuid.uuid4().hex})
    assert send({k:v for k,v in payload.items() if k != 'expected_input_version'}).status_code == 409
    assert send({k:v for k,v in payload.items() if k != 'reason'}).status_code == 422
    saved = send(payload, key)
    assert saved.status_code == 201, saved.text
    assert saved.json()['target_comment'] == observation['comment']
    # Replacement reuses observation IDs; even a valid current ID cannot accept an old version.
    store.reserve('vesta', uuid.uuid4().hex,
                  ReviewReplacement(report_text=review['input']['report_text'] + ' Revised.', expected_input_version=1),
                  {'mode':'demo'}, replace_id=rid)
    store.update('vesta', rid, execution_status='completed', result=review['result'])
    assert send(payload).status_code == 409
    assert send(payload, key).json() == saved.json()
    assert send({**payload, 'suggested_comment':'Different'}, key).status_code == 409
    assert send({**payload, 'expected_input_version':2}).status_code == 201
    history = client.get(url).json()['items']
    assert len(history) == 2 and history[0]['target_comment'] == observation['comment']
    assert history[0]['suggested_comment'] == 'Optional alternative wording.'
    assert client.get(f'/api/v1/reviews/{rid}').json()['result']['copy_text'] == review['result']['copy_text']
    counts = client.get('/api/v1/analytics?source=all&period=all').json()['feedback']['by_target']
    assert counts['observation'] == 2 and counts['result'] == 0


def test_atomic_save_rejects_missing_version_and_incomplete_result(client):
    review = finish(client, post(client, 'mixed'))
    observation = (review['result']['general_comments'] + review['result']['critical_comments'])[0]
    import pytest
    with pytest.raises(store.ReviewConflict):
        store.save_feedback('vesta', review['id'], uuid.uuid4().hex,
                            FeedbackInput(rating='up', target='observation', observation_id=observation['observation_id']))
    store.reserve('vesta', uuid.uuid4().hex,
                  ReviewReplacement(report_text=review['input']['report_text'] + ' Pending.', expected_input_version=1),
                  {'mode':'demo'}, replace_id=review['id'])
    with pytest.raises(store.ReviewConflict):
        store.save_feedback('vesta', review['id'], uuid.uuid4().hex,
                            FeedbackInput(rating='up', expected_input_version=1))
