"""Evaluation harness tests; these do not call a model or claim clinical validation."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

from backend.contracts import ReviewProblem, parse_sections
from backend.skill_runtime import load_snapshot
from scripts.score_skill_evaluations import load_cases, score

ROOT = Path(__file__).resolve().parents[1]
SUITES = ROOT / "qa-skills/clinical-content/evaluation/suites"


def test_atomic_suites_are_versioned_partitioned_and_unique():
    registry = json.loads(
        (ROOT / "qa-skills/clinical-content/registry.json").read_text(encoding="utf-8")
    )
    cases = load_cases()
    assert len(cases) == 54
    assert len(list(SUITES.glob("*.json"))) == len(registry["skill_versions"]) == 9
    for name, version in registry["skill_versions"].items():
        suite = json.loads((SUITES / f"{name}.json").read_text(encoding="utf-8"))
        assert suite["skill"] == name
        assert suite["skill_version"] == version
        assert {case["partition"] for case in suite["cases"]} == {
            "development",
            "held_out",
        }
        assert all(case["expectation_status"] == "proposed_not_adjudicated" for case in suite["cases"])


def test_input_gate_suite_matches_application_contract():
    suite = json.loads((SUITES / "qa-input-adequacy.json").read_text(encoding="utf-8"))
    for case in suite["cases"]:
        expected = case["expected"]
        try:
            parse_sections(case["input"]["report_text"])
            observed = {"execution_status": "accepted"}
        except ReviewProblem as exc:
            observed = {
                "execution_status": "needs_input" if exc.needs_input else "failed",
                "error_code": exc.code,
            }
        assert observed["execution_status"] == expected["execution_status"], case["id"]
        if "error_code" in expected:
            assert observed["error_code"] == expected["error_code"], case["id"]


def test_scorer_separates_contract_result_from_clinical_judgment():
    export = {
        "created_at": "2026-09-16T00:00:00+00:00",
        "model": "controlled-no-network",
        "reasoning_effort": "medium",
        "skill_snapshot_sha256": "synthetic",
        "skill_versions": {"qa-comment-drafting": "0.2.0"},
        "results": [
            {
                "case_id": "CM01",
                "status": "completed",
                "private_candidates": [
                    {
                        "issue_code": "TERM",
                        "finding_type": "suggestion",
                        "comment": "Findings: please correct ‘silhoutte’ to ‘silhouette’.",
                        "grounded_anchors": [{"quote": "silhoutte"}],
                    }
                ],
            }
        ],
    }
    result = score(export)
    row = result["results"][0]
    assert row["automatic_contract_pass"] is True
    assert row["clinical_pass"] is None
    assert row["human_review"]["radiologist_attention_cost"] is None
    assert result["clinical_validation"] is False


def test_snapshot_exposes_atomic_versions_and_stage_composition():
    snapshot = load_snapshot()
    assert snapshot["content_version"] == "0.3.0"
    assert set(snapshot["skill_versions"]) == {
        "clinical-report-qa",
        "qa-input-adequacy",
        "qa-terminology-errors",
        "qa-internal-consistency",
        "qa-clinical-question",
        "qa-recommendations",
        "qa-critical-match",
        "qa-comment-drafting",
        "qa-final-verification",
    }
    assert snapshot["stage_skills"]["critical_finding_review"][1] == "qa-critical-match"


def test_evaluation_runner_defaults_to_no_provider_calls(tmp_path):
    output = tmp_path / "should-not-exist.json"
    env = dict(os.environ)
    env.pop("OPENAI_API_KEY", None)
    result = subprocess.run(
        [
            sys.executable,
            "scripts/evaluate_skills.py",
            "--skill",
            "qa-critical-match",
            "--partition",
            "held_out",
            "--max-cases",
            "2",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "No provider calls were made" in result.stdout
    assert not output.exists()
