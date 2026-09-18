import asyncio
from pathlib import Path, PureWindowsPath
from unittest.mock import AsyncMock, MagicMock
import httpx
from openai import AuthenticationError
from backend import diagnostics, skill_runtime
from backend.main import app


def test_status_checks_real_local_components(client):
    result = client.get("/api/v1/status")
    assert result.status_code == 200
    data = result.json()
    assert data["status"] == "ready"
    assert data["components"]["dbos"]["status"] == "ok"
    assert data["components"]["skills"]["status"] == "ok"
    assert data["components"]["openai"]["status"] == "not_required"


def test_failed_config_is_not_reported_as_network_down(client, monkeypatch):
    import backend.main as main

    def broken(*args):
        raise ValueError("Package inventory mismatch")

    monkeypatch.setattr(main, "runtime_config", broken)
    result = client.get("/api/v1/config")
    assert result.status_code == 503
    assert result.json()["error"]["code"] == "SKILL_INVENTORY_MISMATCH"
    assert result.headers["Request-Id"]


def test_liveness_does_not_claim_dbos_readiness(client, monkeypatch):
    monkeypatch.setattr(app.state, "dbos_ready", False)
    assert client.get("/api/v1/health").status_code == 200
    data = client.get("/api/v1/status").json()
    assert data["status"] == "not_ready"
    assert data["components"]["dbos"]["status"] == "error"


def test_package_reads_are_explicit_utf8(monkeypatch):
    original = Path.read_text

    def windows_read(self, encoding=None, errors=None):
        assert encoding == "utf-8", f"Locale-dependent read: {self.name}"
        return original(self, encoding=encoding, errors=errors)

    monkeypatch.setattr(Path, "read_text", windows_read)
    skill_runtime.load_snapshot()


def test_windows_inventory_separator():
    # Execute the actual validator inventory expression with Windows path objects.
    import ast

    source = Path("qa-skills/framework/tools/validate.py").read_text(encoding="utf-8")
    node = next(
        n
        for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "actual" for t in n.targets)
    )

    class File(PureWindowsPath):
        def is_file(self):
            return True

    class Root(PureWindowsPath):
        def rglob(self, pattern):
            return [File("C:/qa/skills/example/SKILL.md")]

    root = Root("C:/qa")
    actual = eval(
        compile(ast.Expression(node.value), "<inventory>", "eval"), {"root": root}
    )
    assert actual == ["skills/example/SKILL.md"]


def test_openai_probe_only_explicit_metadata(monkeypatch):
    monkeypatch.setattr(
        diagnostics,
        "runtime_config",
        lambda _: dict(mode="openai", ready=True, model="test-model"),
    )
    model_api = MagicMock()
    model_api.models.retrieve = AsyncMock()
    factory = MagicMock()
    factory.return_value.__aenter__ = AsyncMock(return_value=model_api)
    factory.return_value.__aexit__ = AsyncMock(return_value=False)
    monkeypatch.setattr(diagnostics, "AsyncOpenAI", factory)
    result = asyncio.run(diagnostics.check_openai("vesta"))
    assert result["status"] == "accessible"
    assert "Inference has not been tested" in result["message"]
    model_api.models.retrieve.assert_awaited_once_with("test-model")
    response = httpx.Response(
        401, request=httpx.Request("GET", "https://api.openai.com/v1/models/test-model")
    )
    model_api.models.retrieve.side_effect = AuthenticationError(
        "private text", response=response, body=None
    )
    result = asyncio.run(diagnostics.check_openai("vesta"))
    assert result["code"] == "OPENAI_AUTHENTICATION_FAILED"
    model_api.models.retrieve.side_effect = RuntimeError("private text")
    result = asyncio.run(diagnostics.check_openai("vesta"))
    assert result["code"] == "OPENAI_CHECK_FAILED"
    assert "private text" not in str(result)


def test_safe_logs_omit_exception_payload():
    handler = MagicMock()
    logger = diagnostics.log
    logger.addHandler(handler)
    handler.level = 0
    try:
        try:
            raise RuntimeError("private report and secret key")
        except RuntimeError as exc:
            diagnostics.record_failure("test.failure", exc, request_id="req_test")
        message = handler.handle.call_args.args[0].getMessage()
        assert "RuntimeError" in message and "req_test" in message
        assert "private report" not in message and "secret key" not in message
    finally:
        logger.removeHandler(handler)
