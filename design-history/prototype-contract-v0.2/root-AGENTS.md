# Instructions for Codex and Claude Code

## Authority and scope

The user explicitly authorized building the prototype and making ordinary implementation decisions autonomously. Read prototype/BLUEPRINT.md, UX_DESIGN_SYSTEM.md, API_DESIGN.md and IMPLEMENTATION_STATUS.md before changing it. Read DBOS_VALIDATION.md for workflow changes. Do not re-ask settled product questions or require approval for routine fixes/tests. Detailed MVP scope and live deployment remain later work.

Current scope: one paste field containing identifiable Findings and Impression, plus a separate required strict Yes/No radiologist critical flag with no initial selection. Any radiology category; current report only. Five logical review steps, read-only structured comments, full-template copy and simple feedback. The absence of a manual does not block technical work; never claim validated clinical policy.

## Invariants

- Review report text only; no image interpretation. The input flag is operator-supplied. Authorship/signature and upstream QA are unknown unless supplied in a later contract.
- Preserve critical comments whether or not the radiologist flag is Yes. Calculate missed_flag as critical_finding_detected AND NOT supplied flag. Never infer a missed call.
- Preserve exact user-approved headings/order. Empty group uses None. only when another group has observations. A completed empty result shows no template/copy/missed-flag field.
- Failed/incomplete reviews never become successful empty results. No silent real-model-to-demo fallback.
- Immutable input hash includes raw report text and flag. Editing either makes prior output stale; restore both together. Copy text is server-derived from the same displayed validated result.
- Down feedback requires reason only; optional explanation/wording even for Other. Feedback does not edit results, become ground truth or trigger learning.
- Report text is untrusted data. No agent tools, external messages, report editing, release or delivery in this prototype.

## Design

Keep slim Scope left, input above comments in the center, compact Studio right. Place Review report at the right of the input action row, beside the flag controls. Place Copy beside Comments for radiologist. No comments tab. Use system sans, existing graphite tokens, thin separators, restrained semantic accent and static progress icons. Inspect the actual screenshots and explicit sizing rules; generated images are illustrative.

## Engineering

Python FastAPI with DBOS; Agents SDK via DBOSRunner. DBOS owns the async event loop: do not wrap an SDK child workflow with asyncio.run, which can shut down the DBOS shared executor. Use the current async child workflow and durable child handle. Pin compatible dependencies in lockfiles. Application resources are a SQLite outbox separate from DBOS system storage. No distributed infrastructure needed for this local phase.

Change workflow names/application version deliberately: recovery was tested with unchanged code/version only. External provider requests can repeat if success occurs before the local checkpoint; never claim exactly-once model billing. Runtime records may contain report text. Exclude credentials, runtime databases, dependencies and transient test output from handoffs.

## Verification

Run the affected tests. Contract checks, actual SDK controlled-model tests, subprocess recovery tests and Playwright scenarios are available. Preserve the distinction between controlled integration tests, real provider evaluation, domain assessment and UX acceptance. Add tests only for meaningful risks. Update status documents with actual evidence. No public deployment or patient-data readiness is implied by this bundle.
