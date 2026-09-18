import os
import tempfile

os.environ["QA_MODE"] = "demo"
os.environ["QA_AUTH_MODE"] = "local"
os.environ["QA_DATA_DIR"] = tempfile.mkdtemp(prefix="qa-tests-")
os.environ["QA_POLICY_PATH"] = ""
import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(
        app, headers={"QA-Version": "2026-09-18"}, client=("127.0.0.1", 50000)
    ) as c:
        yield c


@pytest.fixture(autouse=True)
def controlled_spend(monkeypatch, tmp_path):
    import time
    from backend import spend
    monkeypatch.setenv('QA_SPEND_LEDGER', str(tmp_path / 'spend.sqlite'))
    monkeypatch.setenv('QA_SPEND_SESSION', 'controlled-test')
    monkeypatch.setitem(spend.PRICING, 'controlled-sdk-test', (1, 1))
    spend.authorize('controlled-test', 1_000_000, time.time()+3600, authorization='Controlled tests only; no network')
