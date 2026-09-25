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


def configuration(tenant_id="vesta", *, accepted=False):
    content, rubric_hash = rubric()
    from .preferences import read
    enabled = accepted or read(tenant_id).features.classification
    model = MODEL
    from .access import access_mode
    reason = None
    if not enabled:
        reason = "JEV classification is disabled."
    elif access_mode() == "public":
        reason = "JEV classification requires local or API-key access."
    elif not os.environ.get("TYPESAFE_API_KEY"):
        reason = "Configure TYPESAFE_API_KEY to classify findings."
    calibration_path = os.environ.get("JEV_CALIBRATION_PATH", "").strip()
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


def snapshot(tenant_id="vesta", *, accepted=False):
    status, content, calibration = configuration(tenant_id, accepted=accepted)
    if not status.ready:
        raise ClassificationProblem("JEV_NOT_CONFIGURED", status.reason or "JEV is unavailable.")
    return dict(model=status.model, rubric=content, rubric_hash=status.rubric_hash,
                calibration=calibration, workflow_version="qa.finding.classify.v2")


def request_body(input_data: dict, config: dict):
    content = config["rubric"]
    state = {
        "finding_text": input_data["finding_text"],
        "qa_comment": input_data["qa_comment"],
        "report_quotes": input_data["report_quotes"],
    }
    if config["rubric"].get("preprocessing_version") == "review-critical-context-v2":
        state = {"target": input_data["target"], "report_context": input_data["report_context"],
                 "qa_comment": input_data["qa_comment"]}
    questions = {
        field: {
            "type": "choice",
            "instructions": content["shared_instructions"] + "\n" + content["fields"][field]["instructions"],
            "criteria": content["fields"][field]["criteria"],
        }
        for field in FIELDS
    }
    return {"model": config["model"], "state": state, "questions": questions}


def validate_context_size(body):
    """Conservative UTF-8 byte upper bound; reject instead of clipping report context."""
    state_size = len(store.canonical(body["state"]).encode("utf-8"))
    sizes = [len(store.canonical(question).encode("utf-8")) for question in body["questions"].values()]
    if state_size + max(sizes) + 1024 > 32000 or state_size + sum(sizes) + 1024 > 64000:
        raise ClassificationProblem("CLASSIFICATION_INPUT_TOO_LARGE", "Report context exceeds the JEV limit.")


def consistency_reasons(labels):
    """Flag related predictions; never rewrite model labels or probabilities."""
    reasons = {field: [] for field in FIELDS}
    def flag(fields, message):
        for field in fields:
            reasons[field].append(message)
    if ((labels["polarity"] == "negated") != (labels["certainty"] == "not_applicable")):
        flag(("polarity", "certainty"), "Polarity and certainty disagree about whether the finding is absent; review both labels.")
    priority = labels["urgency"] != "cannot_determine"
    if priority and labels["polarity"] in {"negated", "unclear"}:
        flag(("polarity", "urgency"), "Communication priority was assigned to an absent or unclear finding; review the report evidence.")
    if priority and labels["finding_group"] == "insufficient_context":
        flag(("finding_group", "urgency"), "Communication priority was assigned without a clear target finding; review the target and context.")
    if labels["temporal_status"] == "historical" and labels["urgency"] in {"minutes", "hours", "days"}:
        flag(("temporal_status", "urgency"), "Historical status and nonroutine priority need review against the current report context.")
    if labels["temporal_status"] == "not_stated":
        reasons["temporal_status"].append("Temporal status is unresolved; check for missing, ambiguous or conflicting comparison/history evidence.")
    return reasons


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
        calibrated = None
        artifact = config.get("calibration")
        if artifact and artifact["fields"].get(field, {}).get("status") == "fitted":
            from .classification_calibration import temperature_scale
            calibrated = temperature_scale(values, artifact["fields"][field]["temperature"])
        result[field] = dict(label=answer["choice"], raw_probabilities=values,
                             provider_confidence=float(confidence), top_probability=float(top),
                             margin=float(top - runner_up), calibrated_probabilities=calibrated,
                             review_reasons=reasons)
    if config["rubric"].get("preprocessing_version") == "review-critical-context-v2":
        checks = consistency_reasons({field: value["label"] for field, value in result.items()})
        for field in FIELDS:
            result[field]["review_reasons"].extend(checks[field])
    elif result["certainty"]["label"] != "not_applicable" and result["polarity"]["label"] == "negated":
        result["certainty"]["review_reasons"].append("Negated finding and certainty label need review.")
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
