"""Reproducible research evaluation of review-gated JEV classifications.

The run operation calls the application API, not TypeSafe directly. Dataset cases
must identify completed critical observations; no QA review is created by this tool.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.classification import FIELDS, rubric
from backend.classification_calibration import fit_temperature, score_field, temperature_scale, wilson_lower
from backend.contracts import ClassificationLabels


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dataset(path):
    value = read(path)
    if value.get("version") != "1.0" or not isinstance(value.get("cases"), list):
        raise ValueError("Dataset needs version 1.0 and cases")
    ids, exact, groups = set(), set(), {}
    allowed = {"development", "calibration", "threshold_tuning", "test"}
    for row in value["cases"]:
        if not isinstance(row.get("case_id"), str) or row["case_id"] in ids:
            raise ValueError("Duplicate or missing case ID")
        ids.add(row["case_id"])
        if row.get("split") not in allowed or not isinstance(row.get("group_id"), str) or not row["group_id"]:
            raise ValueError("Case needs a supported split and group ID")
        if row["group_id"] in groups and groups[row["group_id"]] != row["split"]:
            raise ValueError("Related group crosses evaluation splits")
        groups[row["group_id"]] = row["split"]
        if row.get("label_status") not in ("adjudicated", "fixture") or not row.get("adjudication"):
            raise ValueError("Reference labels require fixture or adjudication provenance")
        ClassificationLabels.model_validate(row["reference"])
        source = (row.get("review_id"), row.get("input_version"), row.get("observation_id"))
        if not all(source) or source in exact:
            raise ValueError("Missing or duplicate critical observation source")
        exact.add(source)
    return value


def evaluation(path):
    value = read(path)
    if value.get("format") != "jev-evaluation-v1":
        raise ValueError("Not a JEV evaluation manifest")
    if not isinstance(value.get("labels"), dict):
        raise ValueError("Evaluation is missing frozen taxonomy labels")
    tuples = {(row.get("model"), row.get("rubric_hash")) for row in value["cases"] if row.get("probabilities")}
    if len(tuples) > 1 or (tuples and tuples != {(value["model"], value["rubric_hash"]) }):
        raise ValueError("Mixed model/rubric evaluation")
    return value


def api_client(base):
    token = os.environ.get("QA_EVAL_API_KEY", "")
    headers = {"QA-Version": "2026-09-22"}
    if token:
        headers["Authorization"] = "Bearer " + token
    return httpx.Client(base_url=base.rstrip("/"), headers=headers, timeout=20)


def run(args):
    source = dataset(args.dataset)
    source_hash = digest(source)
    previous = evaluation(args.output) if args.output.exists() else None
    if previous and (previous["evaluation_id"] != args.evaluation_id or previous["dataset_hash"] != source_hash):
        raise ValueError("Existing evaluation manifest belongs to a different run or dataset")
    with api_client(args.api_base) as client:
        cfg = client.get("/api/v1/classifications/config")
        cfg.raise_for_status()
        config = cfg.json()
        if not config["ready"]:
            raise ValueError(config.get("reason") or "JEV is not ready")
        rubric_content, _ = rubric()
        manifest = previous or {"format": "jev-evaluation-v1", "evaluation_id": args.evaluation_id,
            "dataset_hash": source_hash, "model": config["model"], "rubric_hash": config["rubric_hash"],
            "rubric_id": config["rubric_id"], "taxonomy_version": rubric_content["taxonomy_version"],
            "preprocessing_version": rubric_content["preprocessing_version"],
            "labels": config["labels"], "cases": []}
        if manifest["model"] != config["model"] or manifest["rubric_hash"] != config["rubric_hash"]:
            raise ValueError("Pinned model/rubric changed during evaluation")
        saved = {row["case_id"]: row for row in manifest["cases"]}
        for case in source["cases"]:
            row = saved.get(case["case_id"], dict(case))
            if row.get("probabilities") or row.get("execution_status") == "failed":
                continue
            key = hashlib.sha256((args.evaluation_id + ":" + case["case_id"]).encode()).hexdigest()
            payload = {field: case[field] for field in ("review_id", "input_version", "observation_id")}
            if not row.get("classification_id"):
                response = client.post("/api/v1/classifications", json=payload,
                                       headers={"Idempotency-Key": key})
                if response.status_code != 202:
                    row.update(execution_status="failed", error_code=response.json().get("error", {}).get("code", "ADMISSION_FAILED"))
                    saved[case["case_id"]] = row
                    manifest["cases"] = [saved[item["case_id"]] for item in source["cases"] if item["case_id"] in saved]
                    write(args.output, manifest)
                    continue
                row["classification_id"] = response.json()["id"]
                saved[case["case_id"]] = row
                manifest["cases"] = [saved[item["case_id"]] for item in source["cases"] if item["case_id"] in saved]
                write(args.output, manifest)
            deadline = time.monotonic() + args.poll_seconds
            while True:
                response = client.get("/api/v1/classifications/" + row["classification_id"])
                response.raise_for_status()
                item = response.json()
                if item["execution_status"] in ("completed", "failed"):
                    break
                if time.monotonic() >= deadline:
                    raise TimeoutError("Classification remains pending; rerun with the same evaluation ID")
                time.sleep(1)
            row.update(execution_status=item["execution_status"], input_hash=item["input_hash"],
                       model=item["provenance"]["model"], rubric_hash=item["provenance"]["rubric_hash"])
            if item["execution_status"] == "completed":
                row["probabilities"] = {field: item["result"]["fields"][field]["raw_probabilities"] for field in FIELDS}
                row["predicted"] = {field: item["result"]["fields"][field]["label"] for field in FIELDS}
            else:
                row["error_code"] = item["error"]["code"]
            saved[case["case_id"]] = row
            manifest["cases"] = [saved[item["case_id"]] for item in source["cases"] if item["case_id"] in saved]
            write(args.output, manifest)
    return manifest


def scores(value, cases):
    labels = value["labels"]
    completed = [row for row in cases if row.get("probabilities")]
    actual_minutes = [row for row in cases if row["reference"]["urgency"] == "minutes"]
    caught_minutes = sum(row.get("predicted", {}).get("urgency") == "minutes" for row in actual_minutes)
    return {"submitted": len(cases), "completed": len(completed), "failed": len(cases)-len(completed),
        "failure_rate": (len(cases)-len(completed))/len(cases) if cases else None,
        "fields": {field: score_field(cases, field, labels[field]) for field in FIELDS},
        "end_to_end_minutes_recall": caught_minutes/len(actual_minutes) if actual_minutes else None,
        "reference_minutes": len(actual_minutes)}


def score(args):
    value = evaluation(args.evaluation)
    cohorts = sorted({(row["split"], row.get("cohort", "main")) for row in value["cases"]})
    result = {"evaluation_id": value["evaluation_id"], "model": value["model"],
              "rubric_hash": value["rubric_hash"], "overall": scores(value, value["cases"]),
              "by_partition": {f"{split}:{cohort}": scores(value, [row for row in value["cases"]
                    if row["split"] == split and row.get("cohort", "main") == cohort]) for split, cohort in cohorts}}
    write(args.output, result)
    markdown = [f"# JEV classification evaluation {value['evaluation_id']}", "",
        "Research metrics; selected critical findings only. No clinical performance claim.", "",
        f"Submitted: {result['overall']['submitted']}; completed: {result['overall']['completed']}; failed: {result['overall']['failed']}.", "",
        "| Field | Accuracy | Macro F1 | Brier | Log loss |", "| --- | ---: | ---: | ---: | ---: |"]
    for field, metric in result["overall"]["fields"].items():
        show = lambda number: "undefined" if number is None else f"{number:.3f}"
        markdown.append(f"| {field} | {show(metric['accuracy'])} | {show(metric['macro_f1'])} | {show(metric['brier'])} | {show(metric['log_loss'])} |")
    args.output.with_suffix(".md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    return result


def fit(args):
    value = evaluation(args.evaluation)
    cases = [row for row in value["cases"] if row["split"] == "calibration"]
    if not cases or any(not row.get("probabilities") for row in cases):
        raise ValueError("Calibration partition must be complete; revise the evaluation explicitly after failures")
    artifact = {"id": "jev-cal-" + digest([row["case_id"] for row in cases])[:16],
        "model": value["model"], "rubric_hash": value["rubric_hash"],
        "taxonomy_version": value["taxonomy_version"],
        "preprocessing_version": value["preprocessing_version"],
        "dataset_hash": value["dataset_hash"], "fit_case_ids": [row["case_id"] for row in cases],
        "fit_groups": sorted({row["group_id"] for row in cases}),
        "label_provenance": sorted({row["adjudication"] for row in cases}),
        "method": "grid search on log loss; T in [0.25,5] at 0.01 intervals",
        "fields": {field: fit_temperature(cases, field) for field in FIELDS}}
    write(args.output, artifact)
    return artifact


def thresholds(args):
    value = evaluation(args.evaluation)
    artifact = read(args.artifact)
    if artifact["model"] != value["model"] or artifact["rubric_hash"] != value["rubric_hash"]:
        raise ValueError("Calibrator does not match model and rubric")
    cases = [row for row in value["cases"] if row["split"] == "threshold_tuning" and row.get("cohort", "main") == "main"]
    if not cases:
        raise ValueError("No prevalence-representative threshold tuning cases")
    positives = sum(row["reference"]["urgency"] == "minutes" for row in cases)
    if not positives:
        result = {"candidate_threshold": None, "reason": "no_reference_minutes_cases", "thresholds": []}
        write(args.output, result)
        return result
    temperature = artifact["fields"]["urgency"].get("temperature")
    if temperature is None:
        raise ValueError("Urgency field has no fitted calibrator")
    rows = []
    for index in range(101):
        cutoff = index / 100
        tp = fp = 0
        unscored = 0
        for row in cases:
            if not row.get("probabilities"):
                unscored += 1
                continue
            probability = temperature_scale(row["probabilities"]["urgency"], temperature)["minutes"]
            if probability >= cutoff:
                if row["reference"]["urgency"] == "minutes": tp += 1
                else: fp += 1
        flagged = tp + fp
        lower = wilson_lower(tp, positives)
        rows.append({"threshold": cutoff, "tp": tp, "fp": fp, "fn": positives-tp,
            "recall": tp/positives, "recall_lower_95": lower,
            "precision": tp/flagged if flagged else None,
            "flags_per_100": flagged/len(cases)*100, "unscored": unscored,
            "flag_plus_unscored_per_100": (flagged+unscored)/len(cases)*100})
    feasible = [row for row in rows if row["recall_lower_95"] >= args.min_recall_lower and
                row["flags_per_100"] <= args.max_flags_per_100]
    result = {"model": value["model"], "rubric_hash": value["rubric_hash"],
        "calibrator_id": artifact["id"], "unscored_action": "review",
        "candidate_threshold": feasible[-1]["threshold"] if feasible else None,
        "reason": None if feasible else "no_feasible_threshold", "thresholds": rows}
    write(args.output, result)
    return result


def compare(args):
    before, after = evaluation(args.baseline), evaluation(args.candidate)
    first = {row["case_id"]: row for row in before["cases"]}
    second = {row["case_id"]: row for row in after["cases"]}
    if set(first) != set(second):
        raise ValueError("Paired comparison requires identical case IDs")
    details = []
    for case_id in sorted(first):
        a, b = first[case_id], second[case_id]
        if a["reference"] != b["reference"]:
            raise ValueError("Reference labels changed between paired evaluations")
        fixed = [field for field in FIELDS if a.get("predicted", {}).get(field) != a["reference"][field]
                 and b.get("predicted", {}).get(field) == b["reference"][field]]
        regressed = [field for field in FIELDS if a.get("predicted", {}).get(field) == a["reference"][field]
                     and b.get("predicted", {}).get(field) != b["reference"][field]]
        details.append({"case_id": case_id, "fixed": fixed, "regressed": regressed,
                        "baseline_failed": not bool(a.get("probabilities")),
                        "candidate_failed": not bool(b.get("probabilities"))})
    result = {"baseline": before["evaluation_id"], "candidate": after["evaluation_id"],
              "baseline_scores": scores(before, before["cases"]),
              "candidate_scores": scores(after, after["cases"]), "cases": details}
    write(args.output, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    p = sub.add_parser("run")
    p.add_argument("--dataset", type=Path, required=True)
    p.add_argument("--evaluation-id", required=True)
    p.add_argument("--api-base", default="http://127.0.0.1:8000")
    p.add_argument("--poll-seconds", type=int, default=120)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("score")
    p.add_argument("--evaluation", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("fit")
    p.add_argument("--evaluation", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("thresholds")
    p.add_argument("--evaluation", type=Path, required=True)
    p.add_argument("--artifact", type=Path, required=True)
    p.add_argument("--min-recall-lower", type=float, required=True)
    p.add_argument("--max-flags-per-100", type=float, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("compare")
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.operation == "thresholds" and not (0 <= args.min_recall_lower <= 1 and 0 <= args.max_flags_per_100 <= 100):
        parser.error("Threshold constraints must be between 0 and 1 / 0 and 100")
    globals()[args.operation](args)


if __name__ == "__main__":
    main()
