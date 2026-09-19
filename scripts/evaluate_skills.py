"""Run bounded per-skill diagnostics with exact application instructions.

Planning is the default and makes no provider call. Add --execute to call the configured OpenAI
model. Expectations are never included in model input. Results still require clinical adjudication.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]
SUITES = ROOT / "qa-skills/clinical-content/evaluation/suites"


def selected_cases(skill: str, partition: str) -> list[tuple[dict, dict]]:
    paths = sorted(SUITES.glob("*.json")) if skill == "all" else [SUITES / f"{skill}.json"]
    rows = []
    for path in paths:
        if not path.is_file():
            raise SystemExit("Unknown skill suite: " + skill)
        suite = json.loads(path.read_text(encoding="utf-8"))
        rows.extend((suite, case) for case in suite["cases"] if partition == "all" or case["partition"] == partition)
    return rows


async def execute(args, rows):
    raise SystemExit('Direct three-stage evaluation is retired. Run scripts/evaluate.py against the running API; it shares the guarded one-call review path.')


def write_export(path, config, args, results, used):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "evaluation_kind": "diagnostic_skill_evaluation",
                "clinical_validation": False,
                "model": config["model"],
                "reasoning_effort": args.reasoning_effort,
                "max_output_tokens_per_call": args.max_output_tokens,
                "max_total_tokens": args.max_total_tokens,
                "observed_total_tokens": used,
                "skill_snapshot_sha256": config["skill_snapshot_sha256"],
                "skill_versions": config["skill_snapshot"].get("skill_versions", {}),
                "results": results,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", default="all")
    parser.add_argument("--partition", choices=("development", "held_out", "all"), default="development")
    parser.add_argument("--max-cases", type=int, default=3)
    parser.add_argument("--max-total-tokens", type=int, default=20000)
    parser.add_argument("--max-output-tokens", type=int, default=3000)
    parser.add_argument("--reasoning-effort", choices=("low", "medium", "high"), default="medium")
    parser.add_argument("--model")
    parser.add_argument("--output", type=Path, default=ROOT / ".qa-data/evaluation/skill-results.json")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.max_cases < 1 or args.max_total_tokens < 1 or not 1000 <= args.max_output_tokens <= 16000:
        raise SystemExit("Invalid evaluation limits.")
    rows = selected_cases(args.skill, args.partition)
    planned = rows[: args.max_cases]
    print(json.dumps({"execute": args.execute, "selected": len(planned), "model_cases": sum(c["evaluation_mode"] == "stage_model" for _, c in planned), "case_ids": [c["id"] for _, c in planned], "max_total_tokens": args.max_total_tokens}, indent=2))
    if not args.execute:
        print("Plan only. No provider calls were made. Add --execute to run.")
        return
    config, results, used = asyncio.run(execute(args, planned))
    print(f"Recorded {len(results)} cases for {config['model']}; observed {used} tokens. Clinical adjudication remains required.")


if __name__ == "__main__":
    main()
