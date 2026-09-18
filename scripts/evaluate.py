"""Export prototype review runs for human evaluation; never assign clinical pass/fail.
Example: uv run python scripts/evaluate.py --output .qa-data/evaluation.json
Run the API first. Its configured mode decides whether real provider calls occur.
"""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
import uuid
import httpx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "prototype/examples/scenarios.json",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=600)
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text())["cases"]
    rows = []
    headers = {"QA-Version": "2026-09-18"}
    token = os.environ.get("QA_API_KEY", "")
    if token:
        headers["Authorization"] = "Bearer " + token
    with httpx.Client(
        base_url=args.base_url, timeout=20, trust_env=False, headers=headers
    ) as client:
        config_response = client.get("/api/v1/config")
        config_response.raise_for_status()
        config = config_response.json()
        if not config["ready"]:
            raise SystemExit(
                "Backend model is not configured; no evaluation run started."
            )
        print(
            f"Mode: {config['mode']}; model: {config['model']}; policy: {config['policy_status']}"
        )
        for case in cases:
            started = time.monotonic()
            row = {k: v for k, v in case.items() if k not in ("report_text",)}
            # Expectations are reviewer prompts, not an approved clinical gold set.
            payload = {k: case[k] for k in ("report_text",)}
            response = client.post(
                "/api/v1/reviews",
                json=payload,
                headers={"Idempotency-Key": str(uuid.uuid4())},
            )
            if response.status_code != 202:
                row["acceptance_error"] = response.json()
            else:
                review = response.json()
                deadline = started + args.timeout
                while (
                    review["execution_status"] in ("queued", "running")
                    and time.monotonic() < deadline
                ):
                    time.sleep(0.25)
                    response = client.get("/api/v1/reviews/" + review["id"])
                    response.raise_for_status()
                    review = response.json()
                row["review"] = review
                row["timed_out_waiting"] = review["execution_status"] in (
                    "queued",
                    "running",
                )
            row["elapsed_seconds"] = round(time.monotonic() - started, 3)
            row["domain_assessment"] = None
            rows.append(row)
            # Checkpoint after each case so partial evaluation work is retained.
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(
                    {
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "mode": config["mode"],
                        "clinical_validation": False,
                        "cases": rows,
                    },
                    indent=2,
                )
            )
            print(
                case["acceptance_id"],
                row.get("review", {}).get("execution_status", "acceptance_error"),
            )
    print(
        f"Exported {len(rows)} cases to {args.output}. Domain assessment remains required."
    )


if __name__ == "__main__":
    main()
