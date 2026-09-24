# JEV critical-finding research evaluation

This feature classifies only critical observations from completed report QA reviews. A
dataset case identifies `review_id`, `input_version`, and `observation_id` in the local
application. The `run` command submits these references to the same API and DBOS queue
used by QA Studio. It never creates a review or calls TypeSafe directly.

Dataset JSON has `version: "1.0"` and `cases`. Each case needs a unique `case_id`,
`group_id`, one of `development`, `calibration`, `threshold_tuning`, or `test` as `split`,
`cohort`, the three source fields, five `reference` labels, `label_status` (`fixture`
or `adjudicated`), and `adjudication` provenance. Related groups cannot cross splits.
Use synthetic or deidentified text for research. Fixture labels check software only.

```bash
uv run python scripts/evaluate_classification.py run --dataset cases.json --evaluation-id study-001 --output runs.json
uv run python scripts/evaluate_classification.py score --evaluation runs.json --output scores.json
uv run python scripts/evaluate_classification.py fit --evaluation runs.json --output calibrator.json
uv run python scripts/evaluate_classification.py thresholds --evaluation runs.json --artifact calibrator.json --min-recall-lower 0.9 --max-flags-per-100 5 --output thresholds.json
uv run python scripts/evaluate_classification.py compare --baseline runs-a.json --candidate runs-b.json --output comparison.json
```

`run` requires the application to be running with live JEV enabled. In API-key mode,
set `QA_EVAL_API_KEY` to an existing application credential; the TypeSafe key stays in
the server. Reuse the same evaluation ID and output path after interruption. The
manifest stores case IDs and application run IDs before polling, so a resumed command
replays the same idempotency key and cannot silently create a second provider call.

`fit` uses completed calibration cases only. A failure requires an explicit revised
dataset/evaluation rather than silently dropping it. `thresholds` requires caller
supplied recall and workload constraints, counts failed cases as misses, and returns
`no_feasible_threshold` when appropriate. A fitted artifact and a threshold are
research outputs, not evidence of clinical validity or permission for automatic
notification.
