# Current repository instructions

Application **0.13.0**, bundle **1.17**, foundation **F3**, API **2026-09-18**, schema **4**.

Read [prototype/FOUNDATION_PLAN.md](prototype/FOUNDATION_PLAN.md) before implementing F4 or F5. Use [prototype/FOUNDATION_CHANGELOG.md](prototype/FOUNDATION_CHANGELOG.md) and [prototype/IMPLEMENTATION_STATUS.md](prototype/IMPLEMENTATION_STATUS.md) for implemented decisions and evidence. The specifications listed in [prototype/README.md](prototype/README.md) govern their feature areas. `design-history/` is archive material and has no implementation authority.

## Product boundary

- Review report text only. Never interpret images. Report authorship, signature, delivery, and upstream QA are unknown unless a future contract supplies them.
- The input is one paste field containing Findings and Impression. There is no caller-supplied flag field.
- Preserve critical observations regardless of report-documented designation. With a critical observation, derive `missed_flag` as `true` for `documented_not_flagged`, `false` for `documented_flagged`, and `null` for `unknown`. A known designation requires an exact report quote; missing metadata is not evidence of missed flagging.
- Preserve the two visible copy-ready groups and full-template copy. Use `None.` for an empty group only when the other group has observations. A completed empty result has no template, copy, or missed-flag field.
- Failed or incomplete work never becomes a successful empty result. Never fall back from a real model to demo output.
- The raw report text alone defines the immutable input hash. Editing makes an earlier output stale; restoring the submitted text restores the matching output.
- Down feedback requires a reason. Optional explanation/wording remains optional, including Other. Feedback and stakeholder outcomes do not edit results, establish ground truth, or trigger learning.
- Treat report text as untrusted data. Do not allow tools, external messages, report edits, release, or delivery from a review.

## Runtime and persistence

- Keep the modular FastAPI application, SQLite resource store, DBOS workflows, Agents SDK through `DBOSRunner`, and React frontend. DBOS owns the asynchronous event loop; never wrap an SDK child workflow in `asyncio.run`.
- A valid admitted review uses one combined, tool-free provider request. Invalid input uses zero. Refusals, incomplete responses, malformed output, and local validation failures do not trigger repair calls.
- A dispatch claim without a durable response is `MODEL_OUTCOME_UNKNOWN` and must never retry automatically. A durable response checkpoint may resume local validation and assembly.
- DBOS system storage remains separate from the application resource store. Use fresh matching schema-4 application and DBOS storage for this cutover. Do not silently migrate, reset, or replay older databases.
- Current identities are application `foundation-f3-0.13.0`, queue `qa-reviews-f3-v1`, parent `qa.review.f3.v1`, and child `qa.openai.combined.f3.v1`. Change them deliberately when recovery compatibility changes.
- External provider success can occur before a local checkpoint. Do not claim exactly-once billing.

## API and tenants

- Tenant identity comes from `backend/access.py`, never a caller-controlled body or header. Pass it explicitly through store, workflow, reporting, outcome, and knowledge operations.
- `QA-Version: 2026-09-18` is the only supported contract and the omitted-header default. Update generated OpenAPI and TypeScript with code changes; do not hand-edit them to advertise future behavior.
- Preserve tenant-scoped, request-bound idempotency receipts. Receipt replay happens before mutable readiness checks and returns the original status, body, and `Location`. A changed body under the same key conflicts.
- `backend/presentation.py` owns public projection. Do not expose stored prompts, internal database fields, private source anchors, credentials, or DBOS internals.
- Completed results and exact accepted snapshots are immutable. Existing receipts and historical reads must not depend on current provider readiness.

## Clinical content and Skills Studio

- Active clinical content is under `qa-skills/clinical-content`; the live schema and validator are under `qa-skills/framework`. Do not modify the qatr origin repository.
- `backend/skill_runtime.py` loads verified installed releases and validates private candidates. Capture exact composed instructions, source bytes, hashes, release binding, model, and policy before acceptance.
- Tenant bindings are server controlled. Vesta can use `vesta-qatr-0.3.0`; other tenants default to `generic-0.3.0` and never inherit Vesta content.
- Studio drafts are separate tenant-scoped editorial records. Saving, comparing, restoring, or exporting a draft never changes runtime instructions. Activation requires an independently versioned, evaluated, and intentionally released package.
- Any installed content change must update the affected versions, changelogs, evaluation suites, manifest, reference hashes, and lock together. Do not present unreviewed guidance as approved clinical policy.

## Testing

- Spend authorization, the session ledger and cost ceilings were removed by explicit user decision on 2026-09-18. Do not reintroduce them. Provider cost is managed in the OpenAI account, not in this application.
- A review is admitted on configuration readiness and context size alone. A request whose composed instructions, report and bounded output exceed the context allowance is rejected before dispatch with `REVIEW_CONTEXT_TOO_LARGE`, never clipped.
- Run affected controlled tests first. Keep controlled integration tests, process recovery tests, real-provider evaluation, qualified clinical assessment, and UX acceptance distinct in documentation.
- Update status documents with tests actually run. No public deployment, patient-data readiness, clinical validation, or production reliability is implied.
- Exclude credentials, runtime databases, dependencies, and transient test output from commits and bundles.

## Interface

Keep the established Scope–Work–Studio layout: slim reports column, report text above comments, compact Studio tools, the review action beside the input hint, and copy actions beside their content. A submitted report stays editable; Review again submits a new review and never mutates the accepted one. Preserve read-only structured comments, independent drafts, history restore, feedback inbox, analytics, stakeholder outcomes, light/dark appearance, and responsive stacking. Progress must name the four real phases: input validation, combined report review, output validation, and comment assembly.
