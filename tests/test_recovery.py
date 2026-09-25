"""Actual subprocess termination/restart with isolated synthetic SQLite databases."""

import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import uuid

import httpx

ROOT = Path(__file__).resolve().parents[1]


class Server:
    def __init__(self, root, **overrides):
        self.root = root
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            self.port = sock.getsockname()[1]
        self.env = (
            os.environ
            | {
                "RUN_MODE": "demo",
                "ACCESS_MODE": "local",
                "DATA_DIR": str(root / "data"),
                "QA_POLICY_PATH": "",
                "QA_TEST_HOOK_DIR": str(root / "hooks"),
            }
            | overrides
        )
        self.client = httpx.Client(
            base_url=f"http://127.0.0.1:{self.port}",
            trust_env=False,
            timeout=2,
            headers={"QA-Version": "2026-09-22"},
        )
        self.process = None
        self.log = (root / "server.log").open("a")

    def start(self):
        self.process = subprocess.Popen(
            getattr(self, "command", None)
            or [
                sys.executable,
                "-m",
                "uvicorn",
                "backend.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(self.port),
                "--no-access-log",
            ],
            cwd=ROOT,
            env=self.env,
            stdout=self.log,
            stderr=self.log,
        )
        until = time.monotonic() + 20
        while time.monotonic() < until:
            try:
                if self.client.get("/api/v1/health").status_code == 200:
                    return
            except httpx.HTTPError:
                pass
            if self.process.poll() is not None:
                break
            time.sleep(0.05)
        raise AssertionError((self.root / "server.log").read_text())

    def kill(self):
        if self.process and self.process.poll() is None:
            self.process.kill()
            self.process.wait(timeout=5)

    def close(self):
        self.kill()
        self.client.close()
        self.log.close()

    def completed(self, rid):
        until = time.monotonic() + 20
        while time.monotonic() < until:
            d = self.client.get("/api/v1/reviews/" + rid).json()
            if d.get("execution_status") not in ("queued", "running"):
                assert d["execution_status"] == "completed", d
                return d
            time.sleep(0.05)
        raise AssertionError((self.root / "server.log").read_text())


def test_restart_preserves_completed_steps_result_and_feedback(tmp_path):
    server = Server(tmp_path, QA_TEST_PAUSE_AT="after_output_validation")
    try:
        server.start()
        sample = server.client.get("/api/v1/config").json()["samples"][0]
        payload = {
            "report_text": sample["report_text"],
        }
        r = server.client.post(
            "/api/v1/reviews",
            json=payload,
            headers={"Idempotency-Key": str(uuid.uuid4())},
        )
        assert r.status_code == 202, r.text
        rid = r.json()["id"]
        until = time.monotonic() + 15
        paused = tmp_path / "hooks/paused"
        while not paused.exists() and time.monotonic() < until:
            time.sleep(0.05)
        assert paused.read_text() == rid
        server.kill()
        server.env.pop("QA_TEST_PAUSE_AT")
        server.start()
        d = server.completed(rid)
        assert d["input"] == payload
        assert d["result"]["critical_comments"] and d["result"]["missed_flag"] is None
        events = (tmp_path / "hooks/executions.log").read_text().splitlines()
        # Completed side-effect checkpoint reused; interrupted checkpoint executes again.
        assert events.count(rid + " after_combined_review") == 1
        assert events.count(rid + " after_output_validation") == 2
        data = {"rating": "down", "reason": "other"}
        key = str(uuid.uuid4())
        feedback = server.client.post(
            f"/api/v1/reviews/{rid}/feedback",
            json=data,
            headers={"Idempotency-Key": key},
        )
        assert feedback.status_code == 201
        server.kill()
        server.start()
        reread = server.completed(rid)
        assert reread["result"] == d["result"]
        assert server.client.get(f"/api/v1/reviews/{rid}/feedback").json()["items"] == [
            feedback.json()
        ]
        assert (
            server.client.post(
                f"/api/v1/reviews/{rid}/feedback",
                json=data,
                headers={"Idempotency-Key": key},
            ).json()
            == feedback.json()
        )
    finally:
        server.close()


def test_resource_committed_before_dispatch_is_reconciled(tmp_path):
    server = Server(tmp_path)
    try:
        # Commit the actual API resource without calling DBOS: the crash gap.
        seed = "from backend import store; from backend.settings import runtime_config; from backend.contracts import ReviewInput; from backend.reviewer import SAMPLES; store.init(); print(store.reserve('vesta','gap-test', ReviewInput(report_text=SAMPLES[1]['report_text']),runtime_config())[0]['body']['id'])"
        rid = (
            subprocess.check_output(
                [sys.executable, "-c", seed], cwd=ROOT, env=server.env, text=True
            )
            .strip()
            .splitlines()[-1]
        )
        server.start()
        d = server.completed(rid)
        assert d["result"]["outcome"] == "no_observations"
        assert all(step["status"] == "completed" for step in d["steps"])
    finally:
        server.close()


def test_skill_snapshot_survives_restart_with_invalid_installed_content(tmp_path):
    import hashlib
    import json
    import shutil
    from backend.skill_runtime import ROOT as SKILLS
    from backend.settings import runtime_config

    package = tmp_path / "package"
    shutil.copytree(SKILLS, package)
    bootstrap = tmp_path / "bootstrap.py"
    bootstrap.write_text("""
import sys, os, json, hashlib
from pathlib import Path
sys.path[:0] = [os.environ['QA_TEST_PROJECT'], os.environ['QA_TEST_PROJECT']+'/tests']
from backend import reviewer
from test_sdk import ControlledModel
class Calls(list):
    def append(self, instructions):
        with open(os.environ['QA_CALL_LOG'], 'a') as f:
            f.write(hashlib.sha256(instructions.encode()).hexdigest()+'\\n')
reviewer.make_model=lambda config,client: ControlledModel(Calls())
import uvicorn
uvicorn.run('backend.main:app', host='127.0.0.1', port=int(os.environ['QA_PORT']), access_log=False)
""")
    server = Server(
        tmp_path,
        RUN_MODE="live",
        OPENAI_API_KEY="controlled-no-network",
        OPENAI_MODEL="controlled-sdk-test",
        QA_TEST_PAUSE_AT="before_provider_claim",
        QA_SKILL_PACKAGE_DIR=str(package),
        QA_TEST_PROJECT=str(ROOT),
        QA_CALL_LOG=str(tmp_path / "calls.log"),
    )
    server.command = [sys.executable, str(bootstrap)]
    server.env["QA_PORT"] = str(server.port)
    try:
        server.start()
        r = server.client.post(
            "/api/v1/reviews",
            json={
                "report_text": "Findings: Lungs clear. Impression: No acute disease."
            },
            headers={"Idempotency-Key": str(uuid.uuid4())},
        )
        assert r.status_code == 202, r.text
        rid = r.json()["id"]
        paused = tmp_path / "hooks/paused"
        until = time.monotonic() + 20
        while not paused.exists() and time.monotonic() < until:
            time.sleep(0.05)
        assert paused.read_text() == rid
        server.kill()
        import sqlite3

        with sqlite3.connect(tmp_path / "data/reviews.sqlite") as conn:
            cfg = json.loads(
                conn.execute(
                    "SELECT config FROM reviews WHERE id=?", (rid,)
                ).fetchone()[0]
            )
        (package / "clinical-content/references/critical-boundaries.md").write_text(
            "INVALID CHANGED CONTENT"
        )
        server.env.pop("QA_TEST_PAUSE_AT")
        server.start()
        d = server.completed(rid)
        assert d["result"]["outcome"] == "no_observations"
        assert server.client.get("/api/v1/config").status_code == 503
        used = (tmp_path / "calls.log").read_text().splitlines()
        expected = [hashlib.sha256(cfg['combined_task'].encode()).hexdigest()]
        assert used == expected
    finally:
        server.close()
