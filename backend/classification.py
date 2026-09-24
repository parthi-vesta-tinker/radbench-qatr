"""Versioned JEV research rubric and strict five-field output validation."""

import hashlib
import json
import math
import os
from pathlib import Path

from .contracts import ClassificationConfig
from .settings import ROOT
from . import store

FIELDS = ("finding_group", "polarity", "certainty", "temporal_status", "urgency")
RUBRIC_PATH = ROOT / "config/jev/finding-rubric-v1.json"
MODEL = "jev-1.13.0"
MAX_RESPONSE = 1024 * 1024


class ClassificationProblem(Exception):
    def __init__(self, code: str, message: str, *, retryable: bool = False):
        self.code, self.message, self.retryable = code, message, retryable
        super().__init__(message)


def rubric():
    value = json.loads(RUBRIC_PATH.read_text(encoding="utf-8"))
    if value.get("status") != "draft_research" or set(value.get("fields", {})) != set(FIELDS):
        raise ValueError("Invalid JEV finding rubric")
    if any(not isinstance(value["fields"][field].get("criteria"), dict) or
           len(value["fields"][field]["criteria"]) < 2 for field in FIELDS):
        raise ValueError("Invalid JEV rubric criteria")
    encoded = store.canonical(value)
    return value, hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def configuration():
    content, rubric_hash = rubric()
    enabled = os.environ.get("QA_JEV_ENABLED", "false").lower() == "true"
    model = os.environ.get("QA_JEV_MODEL", MODEL).strip()
    if model != MODEL:
        raise ValueError(f"QA_JEV_MODEL must be pinned to {MODEL}")
    from .access import auth_mode
    reason = None
    if not enabled:
        reason = "JEV classification is disabled."
    elif auth_mode() == "public":
        reason = "JEV classification requires local or API-key access."
    elif not os.environ.get("TYPESAFE_API_KEY"):
        reason = "Configure TYPESAFE_API_KEY to classify findings."
    calibration_path = os.environ.get("QA_JEV_CALIBRATION_PATH", "").strip()
    calibration = None
    if calibration_path:
        from .classification_calibration import load_artifact
        calibration = load_artifact(Path(calibration_path), model, rubric_hash,
                                    content["taxonomy_version"], content["preprocessing_version"])
    return ClassificationConfig(
        enabled=enabled, ready=reason is None, reason=reason, model=model,
        rubric_id=content["id"], rubric_hash=rubric_hash,
        calibration_status="research_calibration" if calibration else "uncalibrated",
        labels={field: list(content["fields"][field]["criteria"]) for field in FIELDS},
    ), content, calibration


def snapshot():
    status, content, calibration = configuration()
    if not status.ready:
        raise ClassificationProblem("JEV_NOT_CONFIGURED", status.reason or "JEV is unavailable.")
    return dict(model=status.model, rubric=content, rubric_hash=status.rubric_hash,
                calibration=calibration, workflow_version="qa.finding.classify.v1")


def request_body(input_data: dict, config: dict):
    content = config["rubric"]
    state = {
        "finding_text": input_data["finding_text"],
        "qa_comment": input_data["qa_comment"],
        "report_quotes": input_data["report_quotes"],
    }
    questions = {
        field: {
            "type": "choice",
            "instructions": content["shared_instructions"] + "\n" + content["fields"][field]["instructions"],
            "criteria": content["fields"][field]["criteria"],
        }
        for field in FIELDS
    }
    return {"model": config["model"], "state": state, "questions": questions}


def validate_response(raw: dict, config: dict, duration_ms: int | None):
    if not isinstance(raw, dict) or raw.get("model") != config["model"]:
        raise ClassificationProblem("JEV_INVALID_OUTPUT", "JEV returned an unexpected model or response.")
    answers = raw.get("answers")
    if not isinstance(answers, dict) or set(answers) != set(FIELDS):
        raise ClassificationProblem("JEV_INVALID_OUTPUT", "JEV returned incomplete classification fields.")
    result = {}
    for field in FIELDS:
        answer = answers[field]
        labels = set(config["rubric"]["fields"][field]["criteria"])
        if not isinstance(answer, dict) or answer.get("type") != "choice" or answer.get("choice") not in labels:
            raise ClassificationProblem("JEV_INVALID_OUTPUT", "JEV returned an invalid Choice answer.")
        values = answer.get("probabilities")
        if not isinstance(values, dict) or set(values) != labels:
            raise ClassificationProblem("JEV_INVALID_OUTPUT", "JEV returned an invalid probability distribution.")
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or
               not 0 <= v <= 1 for v in values.values()):
            raise ClassificationProblem("JEV_INVALID_OUTPUT", "JEV returned an invalid probability value.")
        if abs(sum(values.values()) - 1) > 1e-6:
            raise ClassificationProblem("JEV_INVALID_OUTPUT", "JEV probabilities do not sum to one.")
        ordered = sorted(values.values(), reverse=True)
        top, runner_up = ordered[:2]
        if top - values[answer["choice"]] > 1e-9:
            raise ClassificationProblem("JEV_INVALID_OUTPUT", "JEV choice conflicts with its probabilities.")
        confidence = answer.get("confidence")
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
            raise ClassificationProblem("JEV_INVALID_OUTPUT", "JEV returned invalid confidence.")
        reasons = []
        if top < 0.8 or top - runner_up < 0.15:
            reasons.append("Model distribution is uncertain; review this label.")
        if field == "urgency" and answer["choice"] == "cannot_determine":
            reasons.append("Communication priority cannot be determined from supplied text.")
        if field == "urgency" and answer["choice"] != "cannot_determine":
            reasons.append("Verify this draft communication priority against the report and local policy.")
        if field == "certainty" and answer["choice"] != "not_applicable" and answers["polarity"].get("choice") == "negated":
            reasons.append("Negated finding and certainty label need review.")
        calibrated = None
        artifact = config.get("calibration")
        if artifact and artifact["fields"].get(field, {}).get("status") == "fitted":
            from .classification_calibration import temperature_scale
            calibrated = temperature_scale(values, artifact["fields"][field]["temperature"])
        result[field] = dict(label=answer["choice"], raw_probabilities=values,
                             provider_confidence=float(confidence), top_probability=float(top),
                             margin=float(top - runner_up), calibrated_probabilities=calibrated,
                             review_reasons=reasons)
    usage = raw.get("usage")
    if not (isinstance(usage, dict) and set(usage) >= {"input_tokens", "output_tokens"} and
            all(isinstance(usage[k], int) and not isinstance(usage[k], bool) and usage[k] >= 0
                for k in ("input_tokens", "output_tokens"))):
        usage = None
    else:
        usage = {k: usage[k] for k in ("input_tokens", "output_tokens")}
    artifact = config.get("calibration")
    return dict(fields=result, calibration_status="research_calibration" if artifact else "uncalibrated",
                calibrator_id=artifact["id"] if artifact else None, human_review_required=True,
                usage=usage, duration_ms=duration_ms)
