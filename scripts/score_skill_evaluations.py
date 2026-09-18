"""Score grounded stage exports without claiming unadjudicated expectations are clinical truth."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SUITES = ROOT / "qa-skills/clinical-content/evaluation/suites"


def load_cases() -> dict[str, tuple[dict, dict]]:
    cases = {}
    for path in sorted(SUITES.glob("*.json")):
        suite = json.loads(path.read_text(encoding="utf-8"))
        for case in suite["cases"]:
            if case["id"] in cases:
                raise ValueError("Duplicate case ID: " + case["id"])
            cases[case["id"]] = (suite, case)
    return cases


def anchors(candidate: dict) -> list[str]:
    rows = candidate.get("grounded_anchors") or candidate.get("anchors") or []
    return [str(row.get("quote", "")) for row in rows]


def matches(candidate: dict, required: dict) -> bool:
    if candidate.get("issue_code") != required["issue_code"]:
        return False
    if required.get("finding_type") and candidate.get("finding_type") != required["finding_type"]:
        return False
    haystack = "\n".join(anchors(candidate)).casefold()
    return all(quote.casefold() in haystack for quote in required.get("anchor_quotes", []))


def automatic_comment_checks(candidates: list[dict], requested: list[str]) -> dict[str, bool]:
    comments = [str(row.get("comment", "")).strip() for row in candidates]
    checks = {}
    if "comment_concise" in requested:
        checks["comment_concise"] = all(0 < len(value) <= 400 for value in comments)
    if "comment_standalone" in requested:
        checks["comment_standalone"] = all(value and not re.search(r"\b(the model|the ai|this analysis)\b", value, re.I) for value in comments)
    if "requested_action" in requested:
        checks["requested_action"] = all(re.search(r"\b(correct|reconcile|clarify|confirm|review)\b", value, re.I) for value in comments)
    if "request_reconciliation" in requested:
        checks["request_reconciliation"] = all(re.search(r"\breconcil", value, re.I) for value in comments)
    if "no_comment_heading" in requested:
        checks["no_comment_heading"] = all(not re.match(r"^(qa review|general comments|critical findings)\s*:", value, re.I) for value in comments)
    if "no_treatment_instruction" in requested:
        checks["no_treatment_instruction"] = all(not re.search(r"\b(treat|therapy|chest tube|anticoagulat|administer)\b", value, re.I) for value in comments)
    if "no_boilerplate" in requested:
        checks["no_boilerplate"] = not comments
    return checks


def score_case(suite: dict, case: dict, observed: dict) -> dict:
    expected = case["expected"]
    result = {
        "case_id": case["id"],
        "skill": suite["skill"],
        "partition": case["partition"],
        "expectation_status": case["expectation_status"],
        "execution_status": observed.get("status", "missing"),
        "automatic_checks": {},
        "human_review": {
            "clinical_correctness": None,
            "harmful_overreach": None,
            "routing": None,
            "comment_clarity": None,
            "radiologist_attention_cost": None,
            "notes": None,
        },
    }
    checks = result["automatic_checks"]
    if case["evaluation_mode"] == "deterministic_gate":
        checks["execution_status"] = observed.get("status") == expected["execution_status"]
        if expected.get("error_code"):
            checks["error_code"] = observed.get("error_code") == expected["error_code"]
    elif expected.get("input_problem"):
        checks["input_problem"] = observed.get("status") == "needs_input"
    else:
        candidates = observed.get("private_candidates") or []
        remaining = list(range(len(candidates)))
        matched = 0
        for required in expected.get("required", []):
            found = next((index for index in remaining if matches(candidates[index], required)), None)
            if found is not None:
                matched += 1
                remaining.remove(found)
        count = expected.get("observation_count", {})
        checks.update(
            required_candidates=matched == len(expected.get("required", [])),
            observation_count=count.get("min", 0) <= len(candidates) <= count.get("max", 10**6),
            no_unmatched_candidates=not remaining,
            forbidden_issue_codes=not (set(expected.get("forbidden_issue_codes", [])) & {row.get("issue_code") for row in candidates}),
        )
        designation = expected.get("designation")
        if designation is not None:
            output = observed.get("output") or {}
            checks["designation_status"] = output.get("flag_status") == designation["status"]
            checks["designation_quote"] = output.get("flag_quote") == designation.get("anchor_quote")
        checks.update(automatic_comment_checks(candidates, expected.get("behavior_checks", [])))
        automated = set(checks)
        result["manual_behavior_checks"] = [
            name for name in expected.get("behavior_checks", []) if name not in automated
        ]
        result["candidate_counts"] = {
            "expected": len(expected.get("required", [])),
            "matched": matched,
            "observed": len(candidates),
            "unmatched": len(remaining),
        }
    result["automatic_contract_pass"] = bool(checks) and all(checks.values())
    result["clinical_pass"] = None
    return result


def score(export: dict) -> dict:
    cases = load_cases()
    results = []
    for observed in export.get("results", []):
        case_id = observed.get("case_id")
        if case_id not in cases:
            raise ValueError("Unknown case ID in export: " + str(case_id))
        suite, case = cases[case_id]
        results.append(score_case(suite, case, observed))
    by_skill = defaultdict(lambda: Counter(total=0, automatic_contract_pass=0, adjudicated=0))
    for row in results:
        bucket = by_skill[row["skill"]]
        bucket["total"] += 1
        bucket["automatic_contract_pass"] += int(row["automatic_contract_pass"])
        bucket["adjudicated"] += int(row["expectation_status"] == "adjudicated")
    return {
        "evaluation_kind": "diagnostic_skill_evaluation",
        "clinical_validation": False,
        "source_export": {key: export.get(key) for key in ("created_at", "model", "reasoning_effort", "skill_snapshot_sha256", "skill_versions")},
        "summary": {key: dict(value) for key, value in sorted(by_skill.items())},
        "results": results,
        "interpretation": "Automatic checks cover execution, ownership, grounding expectations and comment hygiene. Clinical pass remains null until qualified adjudication.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    value = score(json.loads(args.export.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(f"Scored {len(value['results'])} diagnostic cases; clinical pass remains unset.")


if __name__ == "__main__":
    main()
