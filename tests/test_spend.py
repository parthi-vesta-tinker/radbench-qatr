"""Session admission and replay safety; no provider/network calls."""
import time
from concurrent.futures import ThreadPoolExecutor
import pytest
from backend import spend, store
from backend.contracts import ReviewProblem


def cfg():
    return dict(model='controlled-sdk-test', model_max_output_tokens=1000)


def test_no_authority_missing_expired_and_unsupported(monkeypatch, tmp_path):
    monkeypatch.setenv('QA_SPEND_SESSION', 'missing')
    with pytest.raises(ReviewProblem, match='missing or expired'):
        spend.reserve('vesta','x','f',cfg(),100)
    monkeypatch.setenv('QA_SPEND_SESSION', 'controlled-test')
    with pytest.raises(ReviewProblem, match='pricing'):
        spend.reserve('vesta','x','f',dict(cfg(), model='unpriced'),100)
    with spend.db() as conn:
        conn.execute('UPDATE sessions SET expires=0')
    with pytest.raises(ReviewProblem, match='expired'):
        spend.reserve('vesta','x','f',cfg(),100)
    monkeypatch.setenv('QA_SPEND_LEDGER', str(tmp_path/'missing.sqlite'))
    with pytest.raises(ReviewProblem, match='existing authorized'):
        spend.reserve('vesta','x','f',cfg(),100)
    assert not (tmp_path/'missing.sqlite').exists()


def test_concurrent_admission_never_exceeds_session_ceiling():
    def reserve(i):
        try:
            return spend.reserve('vesta',str(i),'f',cfg(),100000)
        except ReviewProblem as exc:
            assert exc.code == 'SPEND_LIMIT_EXCEEDED'
    with ThreadPoolExecutor(max_workers=12) as pool:
        admitted = [x for x in pool.map(reserve,range(20)) if x]
    assert len(admitted) == 9
    assert spend.status('controlled-test')['committed_micro_usd'] == 999900
    assert len({x['spend']['reservation_id'] for x in admitted}) == 9


def test_orphan_replay_claim_settlement_and_reset(monkeypatch, tmp_path):
    first = spend.reserve('vesta','same','f',cfg(),100)
    # Accepted config survives a crash before app commit, even if model settings change.
    assert spend.reserve('vesta','same','f',dict(cfg(), model='unpriced'),100) == first
    with pytest.raises(ReviewProblem, match='different input'):
        spend.reserve('vesta','same','other',cfg(),100)
    def claim(_):
        try:
            spend.claim('vesta',first)
            return True
        except ReviewProblem:
            return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(claim, range(8))) == 1
    before = spend.status('controlled-test')
    spend.release_unclaimed('vesta',first)
    assert spend.status('controlled-test') == before
    assert spend.settle('vesta',first,None) is None
    assert spend.status('controlled-test') == before
    monkeypatch.setattr(store, 'DATA', tmp_path/'new-reviews')
    store.init()
    assert spend.status('controlled-test') == before
    with pytest.raises(ReviewProblem, match='already used'):
        spend.reserve('vesta','same','f',cfg(),100)
    with pytest.raises(Exception):
        spend.authorize('controlled-test',1_000_000,time.time()+3600,authorization='Must not reset')
    assert spend.status('controlled-test') == before


def test_known_usage_and_unclaimed_release():
    c = spend.reserve('vesta','known','f',cfg(),100)
    spend.claim('vesta',c)
    assert spend.settle('vesta',c,dict(input_tokens=20,output_tokens=10,total_tokens=30)) == 33
    spend.settle('vesta',c,dict(input_tokens=20,output_tokens=10,total_tokens=30))
    assert spend.status('controlled-test')['committed_micro_usd'] == 33
    other = spend.reserve('vesta','not-sent','f',cfg(),100)
    spend.release_unclaimed('vesta',other)
    assert spend.status('controlled-test')['committed_micro_usd'] == 33


def test_tenants_and_sessions_do_not_share_claims():
    a = spend.reserve('vesta','same','f',cfg(),100)
    b = spend.reserve('other','same','f',cfg(),100)
    assert a['spend']['reservation_id'] != b['spend']['reservation_id']
    with pytest.raises(ReviewProblem):
        spend.claim('other',a)
    spend.claim('vesta',a)
    spend.claim('other',b)
