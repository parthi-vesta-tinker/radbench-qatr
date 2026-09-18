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
    os.environ["QA_MODE"] = "openai"
    if args.model:
        os.environ["OPENAI_MODEL"] = args.model
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is required only with --execute.")
    if os.environ.get("QA_POLICY_PATH"):
        raise SystemExit("These no-policy suites require QA_POLICY_PATH to be empty.")

    from agents import Agent, ModelSettings, RunConfig, Runner
    from backend.contracts import ReviewProblem, parse_sections, section_index
    from backend.reviewer import make_model
    from backend.settings import runtime_config
    from backend.skill_runtime import SkillStageOutput, adapt
    from openai import AsyncOpenAI
    from openai.types.shared import Reasoning

    config = runtime_config("vesta")
    if not config["ready"] or config["mode"] != "openai":
        raise SystemExit("OpenAI model configuration is not ready.")
    config["model_reasoning_effort"] = args.reasoning_effort
    config["model_max_output_tokens"] = args.max_output_tokens
    results, used = [], 0
    async with AsyncOpenAI(max_retries=0, timeout=120.0) as client:
        for suite, case in rows[: args.max_cases]:
            started = time.monotonic()
            observed = {"case_id": case["id"], "skill": suite["skill"], "stage": case["stage"]}
            report = case["input"]["report_text"]
            if case["evaluation_mode"] == "deterministic_gate":
                try:
                    parse_sections(report)
                    observed["status"] = "accepted"
                except ReviewProblem as exc:
                    observed.update(status="needs_input" if exc.needs_input else "failed", error_code=exc.code)
            else:
                stage = case["stage"]
                agent = Agent(
                    name=stage,
                    instructions=config["stage_instructions"][stage],
                    model=make_model(config, client),
                    output_type=SkillStageOutput,
                    model_settings=ModelSettings(
                        store=False,
                        max_tokens=args.max_output_tokens,
                        reasoning=Reasoning(effort=args.reasoning_effort),
                    ),
                )
                try:
                    answer = await Runner.run(
                        agent,
                        json.dumps({"report_text": report, "section_index": section_index(report)}),
                        max_turns=1,
                        run_config=RunConfig(tracing_disabled=True, trace_include_sensitive_data=False),
                    )
                    parsed = SkillStageOutput.model_validate(answer.final_output)
                    output, private = adapt(parsed, stage, report, config["skill_snapshot"])
                    usage = answer.context_wrapper.usage
                    used += usage.total_tokens
                    observed.update(
                        status="completed",
                        output=output,
                        private_candidates=private,
                        metrics={
                            "requests": usage.requests,
                            "input_tokens": usage.input_tokens,
                            "output_tokens": usage.output_tokens,
                            "total_tokens": usage.total_tokens,
                        },
                    )
                except ReviewProblem as exc:
                    observed.update(status="needs_input" if exc.needs_input else "failed", error_code=exc.code)
                except Exception as exc:
                    observed.update(status="failed", error_code=type(exc).__name__)
            observed["elapsed_seconds"] = round(time.monotonic() - started, 3)
            results.append(observed)
            write_export(args.output, config, args, results, used)
            if used >= args.max_total_tokens:
                break
    return config, results, used


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
