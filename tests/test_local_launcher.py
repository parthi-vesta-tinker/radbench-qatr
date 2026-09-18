"""Portable local-launch setup behavior; no server or provider calls."""
import subprocess

import pytest

from scripts import run_local


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


def test_existing_frontend_never_invokes_npm(monkeypatch, tmp_path):
    output = tmp_path / "frontend/dist/index.html"
    output.parent.mkdir(parents=True)
    output.write_text("built")
    monkeypatch.setattr(run_local, "ROOT", tmp_path)
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: pytest.fail("npm called"))
    run_local.ensure_frontend()
