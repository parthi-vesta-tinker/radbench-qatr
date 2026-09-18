> Current implementation: application **0.12.0**, bundle **1.16**, foundation **F2**. [Decisions and verification](FOUNDATION_CHANGELOG.md) supersede older baseline statements below. Fresh schema 3 and API 2026-09-17 are implemented; F2 imports the pinned qatr references and tenant-bound snapshots; single-call execution and session-spend enforcement remain F3 work.

# Next-build tests — 2026-09-17

Use [foundation acceptance](ACCEPTANCE.md) and [F1–F5 gates](FOUNDATION_PLAN.md). Begin with
contract/tenant/schema checks, controlled one-call SDK and real DBOS crash tests, then fresh-data
feature/browser regression. Include refusal/truncation, wrong IDs/anchors, inactive drafts,
context bounds and budget concurrency. Stage-level evals remain content tests, not proof of the
combined runtime. No live tests occurred here; new ones need explicit $1/session authorization.
Old test evidence below remains release-specific.

> **Current release 1.14 / application 0.10.0:** [Workspace specification](WORKSPACE_SPEC.md) governs the current UX. [Analytics specification](ANALYTICS_SPEC.md) defines the feedback inbox, stakeholder outcomes, metric denominators and unmeasured clinical performance. [Implementation status](IMPLEMENTATION_STATUS.md) records verification; [Backlog](BACKLOG.md) records deferred work. Earlier release-specific text below is historical where it conflicts. See [Skills Studio specification](SKILLS_STUDIO_SPEC.md) for the new content review and draft editor.

# Skill adoption test clarification

See IMPLEMENTATION_STATUS.md for the latest 15 September 2026 results. Earlier statements below
that no live model testing has occurred describe the baseline release and are superseded.
There are separate checks for package integrity, private source validation, API/tenant/idempotency,
controlled SDK execution, actual subprocess recovery, canned-demo browser behavior, and genuine
provider reviews. Passing one category does not establish clinical quality in another.

---

# How the sample reports were tested

14 September 2026 · Contract v0.4

**No sample report has been assessed by a live OpenAI model in this project.** No clinical accuracy, sensitivity, specificity or useful-comment rate has been established. The OpenAI path is implemented and its integration is tested using a controlled model response.

## Four distinct checks

| Check | What actually ran | What it establishes |
|---|---|---|
| Synthetic demo reports | The seven known report strings in backend/reviewer.py select prewritten observations. Actual FastAPI, DBOS, result assembly and persistence execute. | Workflow behavior, grouping, copy format and state handling for controlled cases. It does not evaluate AI judgment. |
| Browser interactions | Playwright pastes/replaces reports, clicks Review, inspects/copies results, saves feedback and injects connection/clipboard failures. | The tested user flow works against the actual backend. It does not validate the clinical comments. |
| SDK integration | The real OpenAI Agents SDK and DBOSRunner call a deterministic test Model. It returns deliberately controlled valid/malformed output or a supported/unsupported designation quote. No request reaches OpenAI. | SDK execution, typed output handling, grounding checks, failure behavior and usage plumbing work for those responses. Test token counts are synthetic. |
| Durability | Separate backend subprocesses are terminated and restarted against isolated synthetic databases. | Completed checkpoints, current input/result identity and feedback survive the tested interruption paths. |

The current demo examples cover clean text, spelling, laterality discrepancy, mixed observations, critical-only text, explicit report-documented flag and explicit report-documented no flag. Reports without designation metadata use unknown rather than assuming no flag. The demo adapter supports these exact normalized examples only; it is not a general NLP classifier and fails explicitly for arbitrary other input.

Tests assert expected software behavior against those controlled outputs. Comparing a hardcoded output with its expected copy format is useful for the formatter/UX, but it provides no evidence that a model would identify the observation in an unfamiliar report.

## Code locations

- backend/reviewer.py: SAMPLES and demo_stage contain the canned examples; openai_stage contains the actual SDK path.
- tests/test_api.py: 13 API/contract cases, including report-only input, known/unknown designation, duplicates and feedback.
- tests/test_sdk.py: four controlled SDK cases. ControlledModel is a test double, not an OpenAI service model.
- tests/test_recovery.py: two real subprocess/restart checks.
- frontend/tests/workflow.spec.ts: five browser scenarios.
- scripts/evaluate.py: exports reviews and timing for later human evaluation; does not automatically grade clinical correctness.

## Current report-only change

The backend tests now verify that report_text is the sole accepted input, the legacy flag field is rejected, source-documented flag states are used correctly, absent status stays unknown, and a fabricated flag quote fails the review. Browser checks cover zero radio controls, new report replacement, stale results, exact copying and documented flag results on mobile.

## What real evaluation still requires

Configure QA_MODE=openai, an available OPENAI_MODEL and OPENAI_API_KEY; restart the local backend. Supply the manual and critical vocabulary when available. Have a qualified reviewer establish expected observations for a small synthetic/de-identified evaluation set, then run:

```sh
uv run python scripts/evaluate.py --output .qa-data-v0.3/evaluation.json
```

The API mode determines whether this calls OpenAI. Demo-mode exports remain fixture tests. Live outputs need review for missed/false observations, negation/history, designation interpretation, concise actionable wording and unnecessary radiologist attention. The initial 12 seed cases are an evaluation starting point, not a clinically approved or statistically sufficient test set. Keep technical execution success separate from clinical usefulness.

The v0.4 revision adds 11 API design checks for tenant isolation, scopes, stable replay, cursor ownership, compatibility projections, safe migration and periodic recovery. These extend technical reliability testing; they do not add live clinical/model evaluation.
# Release 1.12 clinical-behavior evaluation

The new atomic-skill suites are evaluation inputs, not proof that a model passed them. There are
54 synthetic cases across nine skill-specific files, with development and held-out partitions.
All expected outcomes remain `proposed_not_adjudicated`.

The technical suite verifies package integrity, case uniqueness, parser agreement, no-call planner
behavior and the scorer's separation of automatic contract checks from human clinical judgment.
Stage-model execution uses the actual application instructions and structured output only when a
developer explicitly adds `--execute`. Automatic scoring can inspect ownership, expected issue type,
grounded quote, designation and narrow comment hygiene. It cannot set `clinical_pass`.

Release 1.12 ran no paid model call. A qualified reviewer still needs to adjudicate clinical
correctness, harmful overreach, routing, clarity and radiologist attention cost. Read
`qa-skills/clinical-content/evaluation/METHOD.md` before interpreting or running the suites.

---
