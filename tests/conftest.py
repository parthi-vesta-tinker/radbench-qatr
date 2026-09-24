import os
import tempfile

# Never inherit provider credentials from a developer shell or .env in controlled tests.
os.environ["OPENAI_API_KEY"] = ""
os.environ["TYPESAFE_API_KEY"] = ""
os.environ["QA_JEV_ENABLED"] = "false"
os.environ["RUN_MODE"] = "demo"
os.environ["ACCESS_MODE"] = "local"
os.environ["QA_DATA_DIR"] = tempfile.mkdtemp(prefix="qa-tests-")
os.environ["QA_POLICY_PATH"] = ""
import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(
        app, headers={"QA-Version": "2026-09-22"}, client=("127.0.0.1", 50000)
    ) as c:
        yield c

