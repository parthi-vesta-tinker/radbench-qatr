"""Single-process local launcher. Credentials stay in memory unless user supplied .env."""

import argparse
import getpass
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def npm_executable():
    """Return the platform launcher; Windows npm is commonly npm.cmd."""
    return shutil.which("npm.cmd" if os.name == "nt" else "npm") or shutil.which("npm")


def frontend_is_current():
    """True when a build exists and no frontend source is newer than it.

    frontend/dist is generated and never committed, so a pull that changes the UI
    leaves a stale bundle behind. Serving it silently shows the previous release.
    """
    built = ROOT / "frontend/dist/index.html"
    if not built.is_file():
        return False
    newest = 0.0
    for folder in ("frontend/src", "frontend/index.html", "frontend/package.json",
                   "frontend/vite.config.ts", "frontend/tsconfig.json"):
        target = ROOT / folder
        if target.is_file():
            newest = max(newest, target.stat().st_mtime)
        elif target.is_dir():
            for path in target.rglob("*"):
                if path.is_file():
                    newest = max(newest, path.stat().st_mtime)
    return newest <= built.stat().st_mtime


def ensure_frontend():
    if frontend_is_current():
        return
    stale = (ROOT / "frontend/dist/index.html").is_file()
    if stale:
        print("Browser UI is older than the frontend source. Rebuilding...", flush=True)
    npm = npm_executable()
    if npm is None:
        raise SystemExit(
            "The browser UI needs building and npm is not on PATH. Install Node.js 22 LTS, "
            "close and reopen PowerShell, then run this command again."
        )
    if not stale:
        print("Browser UI is not built. Installing locked frontend dependencies...", flush=True)
    try:
        if not (ROOT / "frontend/node_modules").is_dir():
            subprocess.run([npm, "--prefix", "frontend", "ci"], cwd=ROOT, check=True)
        print("Building browser UI...", flush=True)
        subprocess.run([npm, "--prefix", "frontend", "run", "build"], cwd=ROOT, check=True)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            f"Frontend setup failed (npm exit code {exc.returncode}). Fix the npm error above, "
            "then rerun the same uv command."
        ) from None
    if not (ROOT / "frontend/dist/index.html").is_file():
        raise SystemExit("Frontend build finished without producing frontend/dist/index.html.")


def main():
    sys.path.insert(0, str(ROOT))
    os.chdir(ROOT)
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(
        description="Build and run Vesta QA locally in demo or live OpenAI mode.",
        allow_abbrev=False,
    )
    parser.add_argument("--mode", choices=("demo", "openai"), default="openai")
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL") or "gpt-6-astra")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--jev", action="store_true", help="Enable live JEV classification of critical review findings")
    parser.add_argument("--no-prompt", action="store_true", help="Require API keys from .env or the process environment")
    parser.add_argument("--auth-mode", choices=("local", "public", "api_key"), help="Override QA_AUTH_MODE for this process")
    args = parser.parse_args()
    if args.auth_mode:
        os.environ["QA_AUTH_MODE"] = args.auth_mode
    ensure_frontend()
    os.environ["QA_MODE"] = args.mode
    if args.jev:
        os.environ["QA_JEV_ENABLED"] = "true"
        from backend.access import auth_mode
        if auth_mode() == "public":
            raise SystemExit("JEV classification requires QA_AUTH_MODE=local or api_key in .env.")
    if args.mode == "openai":
        os.environ["OPENAI_MODEL"] = args.model
        if not os.environ.get("OPENAI_API_KEY"):
            if args.no_prompt:
                raise SystemExit("Set OPENAI_API_KEY in .env or the process environment before starting live review.")
            key = getpass.getpass(
                "OpenAI API key (hidden; used only for this process): "
            ).strip()
            if not key:
                raise SystemExit("An API key is required for real AI review.")
            os.environ["OPENAI_API_KEY"] = key
        label = f"Live OpenAI: {args.model}"
    else:
        label = "Demo mode: controlled local examples; no OpenAI request"
    if args.jev:
        if not os.environ.get("TYPESAFE_API_KEY"):
            if args.no_prompt:
                raise SystemExit("Set TYPESAFE_API_KEY in .env or the process environment before enabling JEV.")
            key = getpass.getpass("TypeSafe JEV API key (hidden; used only for this process): ").strip()
            if not key:
                raise SystemExit("A TypeSafe key is required when --jev is enabled.")
            os.environ["TYPESAFE_API_KEY"] = key
        from backend.classification import configuration as jev_configuration
        jev_status = jev_configuration()[0]
        if not jev_status.ready:
            raise SystemExit(jev_status.reason or "JEV classification is unavailable.")
        label += " + live JEV classification"
    print(f"Open http://127.0.0.1:{args.port} - {label}", flush=True)
    print(f"Component status: http://127.0.0.1:{args.port}/api/v1/status", flush=True)
    print("Stop with Ctrl+C. Reports and feedback persist locally in QA_DATA_DIR.")
    import uvicorn

    uvicorn.run("backend.main:app", host="127.0.0.1", port=args.port, access_log=False)


if __name__ == "__main__":
    main()
