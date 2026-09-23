"""Portable local-launch setup behavior; no server or provider calls."""
import os
import subprocess
import sys

import pytest

from scripts import run_local


def test_demo_mode_never_prompts_for_an_api_key(monkeypatch, capsys):
    """The convenient demo command must remain a provider-free local flow."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.setattr(run_local, "ensure_frontend", lambda: None)
    monkeypatch.setattr(sys, "argv", ["run_local.py", "--mode", "demo", "--port", "9123"])
    monkeypatch.setattr(
        "getpass.getpass", lambda *_args, **_kwargs: pytest.fail("demo mode requested an API key")
    )
    calls = []
    monkeypatch.setattr("uvicorn.run", lambda *args, **kwargs: calls.append((args, kwargs)))

    run_local.main()

    assert os.environ["QA_MODE"] == "demo"
    assert calls == [
        (("backend.main:app",), {"host": "127.0.0.1", "port": 9123, "access_log": False})
    ]
    assert "Demo mode: controlled local examples; no OpenAI request" in capsys.readouterr().out


def test_missing_frontend_builds_with_windows_npm_launcher(monkeypatch, tmp_path):
    monkeypatch.setattr(run_local, "ROOT", tmp_path)
    monkeypatch.setattr(run_local, "npm_executable", lambda: r"C:\Program Files\nodejs\npm.cmd")
    calls = []

    def execute(command, **kwargs):
        calls.append((command, kwargs))
        if command[-1] == "build":
            output = tmp_path / "frontend/dist/index.html"
            output.parent.mkdir(parents=True)
            output.write_text("built")

    monkeypatch.setattr(subprocess, "run", execute)
    run_local.ensure_frontend()
    assert [call[0][3:] for call in calls] == [["ci"], ["run", "build"]]
    assert all(call[1]["cwd"] == tmp_path and call[1]["check"] for call in calls)


def test_missing_frontend_explains_node_path(monkeypatch, tmp_path):
    monkeypatch.setattr(run_local, "ROOT", tmp_path)
    monkeypatch.setattr(run_local, "npm_executable", lambda: None)
    with pytest.raises(SystemExit, match="npm is not on PATH"):
        run_local.ensure_frontend()


def test_current_frontend_never_invokes_npm(monkeypatch, tmp_path):
    source = tmp_path / "frontend/src/App.tsx"
    source.parent.mkdir(parents=True)
    source.write_text("source")
    output = tmp_path / "frontend/dist/index.html"
    output.parent.mkdir(parents=True)
    output.write_text("built")
    os.utime(source, (1000, 1000))
    os.utime(output, (2000, 2000))
    monkeypatch.setattr(run_local, "ROOT", tmp_path)
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: pytest.fail("npm called"))
    run_local.ensure_frontend()


def test_stale_frontend_rebuilds_without_reinstalling_dependencies(monkeypatch, tmp_path):
    """A pull that changes the UI must not leave the previous bundle being served."""
    source = tmp_path / "frontend/src/App.tsx"
    source.parent.mkdir(parents=True)
    source.write_text("source")
    output = tmp_path / "frontend/dist/index.html"
    output.parent.mkdir(parents=True)
    output.write_text("stale")
    (tmp_path / "frontend/node_modules").mkdir()
    os.utime(output, (1000, 1000))
    os.utime(source, (2000, 2000))
    monkeypatch.setattr(run_local, "ROOT", tmp_path)
    monkeypatch.setattr(run_local, "npm_executable", lambda: "npm")
    assert run_local.frontend_is_current() is False
    calls = []

    def execute(command, **kwargs):
        calls.append(command[3:])
        output.write_text("rebuilt")
        os.utime(output, (3000, 3000))

    monkeypatch.setattr(subprocess, "run", execute)
    run_local.ensure_frontend()
    # Dependencies are already installed, so only the build runs.
    assert calls == [["run", "build"]]
    assert output.read_text() == "rebuilt"
    assert run_local.frontend_is_current() is True
