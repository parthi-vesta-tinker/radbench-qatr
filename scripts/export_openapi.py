"""Regenerate the checked-in API artifact without starting DBOS or calling a model."""

import json
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.main import app

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = ROOT / "prototype" / "openapi.json"
    content = json.dumps(app.openapi(), indent=2) + "\n"
    if args.check:
        if target.read_text(encoding="utf-8") != content:
            raise SystemExit("OpenAPI drift. Run scripts/export_openapi.py.")
    else:
        target.write_text(content, encoding="utf-8")
    print(f"Exported {len(app.openapi()['paths'])} API paths to {target}")
