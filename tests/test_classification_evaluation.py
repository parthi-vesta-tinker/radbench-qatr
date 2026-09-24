"""Hand-checkable metric, split, calibration and threshold software fixtures."""

from argparse import Namespace
import json

import pytest

from backend.classification import FIELDS, rubric
from backend.classification_calibration import temperature_scale, wilson_lower
from scripts.evaluate_classification import dataset, score, fit, thresholds, compare


def manifest():
    content, hash_value = rubric()
    labels = {field: list(content["fields"][field]["criteria"]) for field in FIELDS}
    cases = []
    for index in range(12):
        reference = {"finding_group": "thoracic", "polarity": "affirmed", "certainty": "definite",
                     "temporal_status": "not_stated", "urgency": "minutes" if index < 6 else "hours"}
        probabilities = {}
        predicted = {}
        for field in FIELDS:
            options = labels[field]
            chosen = reference[field]
            values = {key: .1 / (len(options)-1) for key in options}
            values[chosen] = .9
            probabilities[field] = values
            predicted[field] = chosen
        cases.append({"case_id": f"c-{index}", "group_id": f"g-{index}", "split": "calibration" if index < 10 else "threshold_tuning",
                      "cohort": "main", "reference": reference, "probabilities": probabilities, "predicted": predicted,
                      "adjudication": "fixture", "label_status": "fixture", "model": "jev-1.13.0", "rubric_hash": hash_value})
    return {"format": "jev-evaluation-v1", "evaluation_id": "fixture", "dataset_hash": "fixture",
            "model": "jev-1.13.0", "rubric_hash": hash_value, "rubric_id": content["id"],
            "taxonomy_version": content["taxonomy_version"], "preprocessing_version": content["preprocessing_version"],
            "labels": labels, "cases": cases}


def test_temperature_ranking_and_wilson():
    raw = {"minutes": .7, "hours": .2, "days": .1}
    changed = temperature_scale(raw, 2)
    assert sorted(raw, key=raw.get) == sorted(changed, key=changed.get)
    assert abs(sum(changed.values())-1) < 1e-12
    assert 0 < wilson_lower(8, 10) < .8


def test_split_group_overlap_is_rejected(tmp_path):
    example = json.loads((__import__("pathlib").Path(__file__).resolve().parents[1] / "evals/classification/example-cases.json").read_text())
    other = dict(example["cases"][0], case_id="second", split="test", review_id="other")
    example["cases"].append(other)
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps(example))
    with pytest.raises(ValueError, match="crosses"):
        dataset(path)


def test_score_fit_threshold_and_compare(tmp_path):
    source = tmp_path / "runs.json"
    source.write_text(json.dumps(manifest()))
    scored = score(Namespace(evaluation=source, output=tmp_path / "score.json"))
    assert scored["overall"]["fields"]["urgency"]["accuracy"] == 1
    assert scored["overall"]["fields"]["urgency"]["brier"] > 0
    assert (tmp_path / "score.md").exists()
    artifact = fit(Namespace(evaluation=source, output=tmp_path / "artifact.json"))
    assert artifact["fields"]["urgency"]["status"] == "fitted"
    no_candidate = thresholds(Namespace(evaluation=source, artifact=tmp_path / "artifact.json",
        min_recall_lower=1.0, max_flags_per_100=0.0, output=tmp_path / "thresholds.json"))
    assert no_candidate["candidate_threshold"] is None
    paired = compare(Namespace(baseline=source, candidate=source, output=tmp_path / "compare.json"))
    assert all(not row["regressed"] for row in paired["cases"])
