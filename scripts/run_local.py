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


def ensure_frontend():
    if (ROOT / "frontend/dist/index.html").is_file():
        return
    npm = npm_executable()
    if npm is None:
        raise SystemExit(
            "The browser UI is not built and npm is not on PATH. Install Node.js 22 LTS, "
            "close and reopen PowerShell, then run this command again."
        )
    print("Browser UI is not built. Installing locked frontend dependencies...", flush=True)
    try:
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
        description="Build and run Vesta QA locally with real OpenAI reviews."
    )
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL") or "gpt-6-astra")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    ensure_frontend()
    os.environ["QA_MODE"] = "openai"
    os.environ["OPENAI_MODEL"] = args.model
    if not os.environ.get("OPENAI_API_KEY"):
        key = getpass.getpass(
            "OpenAI API key (hidden; used only for this process): "
        ).strip()
        if not key:
            raise SystemExit("An API key is required for real AI review.")
        os.environ["OPENAI_API_KEY"] = key
    print(
        f"Open http://127.0.0.1:{args.port} - Live OpenAI: {args.model}", flush=True
    )
    print(f"Component status: http://127.0.0.1:{args.port}/api/v1/status", flush=True)
    print("Stop with Ctrl+C. Reports and feedback persist locally in QA_DATA_DIR.")
    import uvicorn

    uvicorn.run("backend.main:app", host="127.0.0.1", port=args.port, access_log=False)


if __name__ == "__main__":
    main()
