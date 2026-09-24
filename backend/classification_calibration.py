"""Pure research calibration and scoring; no clinical action is taken here."""

import json
import math
from pathlib import Path


def temperature_scale(probabilities: dict[str, float], temperature: float):
    if not math.isfinite(temperature) or temperature <= 0:
        raise ValueError("Temperature must be positive")
    scores = {key: math.log(max(value, 1e-12)) / temperature for key, value in probabilities.items()}
    peak = max(scores.values())
    weights = {key: math.exp(value - peak) for key, value in scores.items()}
    total = sum(weights.values())
    return {key: value / total for key, value in weights.items()}


def load_artifact(path: Path, model: str, rubric_hash: str, taxonomy: str, preprocessing: str):
    artifact = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(artifact, dict) or any(artifact.get(key) != value for key, value in (
        ("model", model), ("rubric_hash", rubric_hash),
        ("taxonomy_version", taxonomy), ("preprocessing_version", preprocessing),
    )):
        raise ValueError("JEV calibration artifact is incompatible with the pinned model and rubric")
    if not isinstance(artifact.get("id"), str) or not isinstance(artifact.get("fields"), dict):
        raise ValueError("Invalid JEV calibration artifact")
    for value in artifact["fields"].values():
        if value.get("status") == "fitted" and not 0.25 <= value.get("temperature", 0) <= 5:
            raise ValueError("Invalid JEV temperature")
    return artifact


def log_loss(cases, field: str, temperature=1.0):
    return sum(-math.log(max(temperature_scale(row["probabilities"][field], temperature)[row["reference"][field]], 1e-12))
               for row in cases) / len(cases)


def fit_temperature(cases, field):
    if len(cases) < 10 or len({row["reference"][field] for row in cases}) < 2:
        return {"status": "insufficient_data", "temperature": None}
    baseline = log_loss(cases, field)
    candidates = [0.25 + index * 0.01 for index in range(476)]
    best = min(candidates, key=lambda t: log_loss(cases, field, t))
    candidate_loss = log_loss(cases, field, best)
    if candidate_loss >= baseline:
        best, candidate_loss = 1.0, baseline
    return {"status": "fitted", "temperature": round(best, 4),
            "baseline_log_loss": baseline, "fit_log_loss": candidate_loss}


def wilson_lower(successes: int, total: int, z=1.96):
    if total <= 0:
        return None
    p = successes / total
    denom = 1 + z*z/total
    center = p + z*z/(2*total)
    margin = z * math.sqrt(p*(1-p)/total + z*z/(4*total*total))
    return (center - margin) / denom


def score_field(cases, field, labels):
    completed = [row for row in cases if row.get("probabilities")]
    counts = {actual: {pred: 0 for pred in labels} for actual in labels}
    brier = loss = 0.0
    bins = [{"count": 0, "correct": 0, "confidence_sum": 0.0} for _ in range(10)]
    for row in completed:
        actual = row["reference"][field]
        probs = row["probabilities"][field]
        pred = max(probs, key=probs.get)
        counts[actual][pred] += 1
        brier += sum((probs[label] - int(label == actual))**2 for label in labels)
        loss -= math.log(max(probs[actual], 1e-12))
        confidence = probs[pred]
        bucket = bins[min(9, int(confidence * 10))]
        bucket["count"] += 1
        bucket["correct"] += int(pred == actual)
        bucket["confidence_sum"] += confidence
    support = {label: sum(counts[label].values()) for label in labels}
    precision = {}
    recall = {}
    f1 = {}
    for label in labels:
        tp = counts[label][label]
        predicted = sum(counts[actual][label] for actual in labels)
        precision[label] = tp / predicted if predicted else None
        recall[label] = tp / support[label] if support[label] else None
        p, r = precision[label], recall[label]
        f1[label] = 2*p*r/(p+r) if p is not None and r is not None and p+r else 0.0 if p is not None and r is not None else None
    n = len(completed)
    ece = sum(abs(bucket["correct"]/bucket["count"] - bucket["confidence_sum"]/bucket["count"]) * bucket["count"]/n
              for bucket in bins if bucket["count"]) if n else None
    return {"completed": n, "failed": len(cases)-n, "accuracy": sum(counts[label][label] for label in labels)/n if n else None,
            "macro_f1": sum(value or 0 for value in f1.values())/len(labels) if n else None,
            "precision": precision, "recall": recall, "support": support, "f1": f1,
            "confusion": counts, "brier": brier/n if n else None, "log_loss": loss/n if n else None,
            "ece": ece, "reliability_bins": bins}
