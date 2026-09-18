> Current implementation: application **0.12.0**, bundle **1.16**, foundation **F2**. [Decisions and verification](prototype/FOUNDATION_CHANGELOG.md) supersede older baseline statements below. Fresh schema 3 and API 2026-09-17 are implemented; F2 imports the pinned qatr references and tenant-bound snapshots; single-call execution and session-spend enforcement remain F3 work.

# Next-build authority — 2026-09-17

Read [FOUNDATION_PLAN.md](prototype/FOUNDATION_PLAN.md) before implementing the next build.
It supersedes older migration/legacy-projection requirements and the three-model-stage target.
Old prototype data may be discarded at the explicit cutover; preserve history, feedback, outcomes,
analytics and tenant Skills Studio functionality with fresh records. Keep DBOS isolation, one
combined provider request, immutable snapshots and fail-closed spend admission. An ambiguous
attempt must not trigger an automatic provider retry. Live tests require explicit permission and
an aggregate session ceiling of $1 unless the user explicitly raises it.

This revision changes planning artifacts only. Runtime remains application 0.10.0. No database
reset, content activation or paid evaluation is implied. Pinned skills change through F2's
versioned release; generated OpenAPI/types change with code, not to simulate implementation.
The foundation plan governs conflicts with baseline instructions below.

> **Current release 1.14 / application 0.10.0:** [Workspace specification](prototype/WORKSPACE_SPEC.md) and [Analytics specification](prototype/ANALYTICS_SPEC.md) govern the current UX: feedback inbox, tenant-wide analytics and stakeholder outcomes. Atomic clinical skills are versioned at 0.2.0 with per-skill changelogs and proposed development/held-out suites. [Backlog](prototype/BACKLOG.md) records deferred Test/Production isolation and adjudicated clinical metrics. Earlier release-specific text below is historical where it conflicts. See [Skills Studio specification](prototype/SKILLS_STUDIO_SPEC.md) for the new content review and draft editor.

# Skills Studio contract — bundle 1.14

Read prototype/SKILLS_STUDIO_SPEC.md. Knowledge drafts are separate tenant-scoped editorial data;
never read them in runtime_config, skill_runtime or workflow execution. Preserve explicit editorial
scopes, hash/revision conflict checks and receipt replay before source readiness. Editing an
installed package still requires the existing independent versioning/evaluation/release process.

# Studio analytics contract — bundle 1.13

Read prototype/ANALYTICS_SPEC.md. Preserve feedback/clinical-reference/acceptance distinctions.
Outcome notes are unverified operator records, never ground truth or release authorization.
Aggregate across the scoped database, not loaded UI pages. Keep unknown and missing responses
visible; use null for unmeasured clinical performance. No skill bytes changed in this feature release.
New outcome writes require both reviews:read and feedback:write, tenant-bound idempotent receipts
and immutable result-version binding. DBOS workflow identities are unchanged from 1.12.

# Historical refinement contract — v0.6 / bundle 1.10

Read [prototype/REFINEMENT_SPEC.md](prototype/REFINEMENT_SPEC.md) first. It supersedes conflicting baseline requirements below: missed-flag UI/copy is deferred; comments, progress and Studio layout are refined; inline headings, persistent review history and saved feedback are implemented. Preserve legacy API receipts and clinical instructions.

---

# Current release instructions — skill evaluation v0.8

Read LOCAL_TESTING.md, prototype/BLUEPRINT.md and prototype/IMPLEMENTATION_STATUS.md first.
The remaining text records baseline invariants; these amendments supersede earlier release-specific details.

- Clinical runtime skills live under qa-skills/clinical-content; framework schema/validator under qa-skills/framework. They are not coding-agent skills. Do not modify qatr origin.
- backend/skill_runtime.py loads pinned content and validates private candidates. Any content edit requires updating manifests, reference hashes and lock consistently, versioning the release and testing it. Never turn an unvalidated manual into approved mandatory policy.
- Capture exact stage instructions and model/policy settings before acceptance. Recovery must use captured bytes. Installed content drift blocks new work but must not block historical GETs or recovery of accepted work.
- Preserve two visible copy-ready groups and full-template copy. Evidence remains private; all public fields pass explicit projection.
- New API version 2026-09-15; missing header remains legacy 2026-09-14. Legacy new creates require upgrade after receipt lookup. Rich labels require compatible GET projection.
- Same-code DBOS names: qa.review.v5 / qa.openai.stage.v4. Fresh default .qa-data-v0.6. Reject incompatible pending work before launching DBOS.
- Every atomic skill has an independent version, changelog and evaluation suite. Keep development and held-out partitions distinct. Automatic contract results are not clinical validation; qualified adjudication owns clinical correctness and attention-cost ratings.
- run_local.py prompts for a live key without storing it. --demo is explicitly canned. Live provider test evidence must remain distinct from controlled-model tests. Never reset the earlier $2 verification budget ledger.

---

# Instructions for Codex and Claude Code

## Authority and scope

The user explicitly authorized building the prototype and making ordinary implementation decisions autonomously. Read prototype/BLUEPRINT.md, UX_DESIGN_SYSTEM.md, API_DESIGN.md and IMPLEMENTATION_STATUS.md before changing it. Read DBOS_VALIDATION.md for workflow changes. Do not re-ask settled product questions or require approval for routine fixes/tests. Detailed MVP scope and live deployment remain later work.

Current scope: one paste field containing identifiable Findings and Impression, with no separate flag control or API field. Any radiology category; current report only. Five logical review steps, read-only structured comments, full-template copy and simple feedback. The absence of a manual does not block technical work; never claim validated clinical policy.

## Invariants

- Review report text only; no image interpretation. Report text is the only input. Authorship/signature and upstream QA are unknown unless supplied in a later contract.
- Preserve critical comments regardless of report-documented designation. With critical observations, derive missed_flag true for documented_not_flagged, false for documented_flagged and null for unknown. Render null as Cannot determine. Known status requires an exact quote in the report; missing metadata is not proof of missed flagging. Never infer a missed call.
- Preserve exact user-approved headings/order. Empty group uses None. only when another group has observations. A completed empty result shows no template/copy/missed-flag field.
- Failed/incomplete reviews never become successful empty results. No silent real-model-to-demo fallback.
- Immutable input hash includes raw report text only. Editing it makes prior output stale; restore the submitted text. Copy text is server-derived from the same displayed validated result.
- Down feedback requires reason only; optional explanation/wording even for Other. Feedback does not edit results, become ground truth or trigger learning.
- Report text is untrusted data. No agent tools, external messages, report editing, release or delivery in this prototype.

## Design

Keep slim Scope left, input above comments in the center, compact Studio right. Place Review report at the right of the input action row, beside the minimum-input hint. Place Copy beside Comments for radiologist. No comments tab. Use system sans, existing graphite tokens, thin separators, restrained semantic accent and static progress icons. Inspect the actual screenshots and explicit sizing rules; generated images are illustrative.

## Engineering

Python FastAPI with DBOS; Agents SDK via DBOSRunner. DBOS owns the async event loop: do not wrap an SDK child workflow with asyncio.run, which can shut down the DBOS shared executor. Use the current async child workflow and durable child handle. Pin compatible dependencies in lockfiles. Application resources are a SQLite outbox separate from DBOS system storage. No distributed infrastructure needed for this local phase.

Change workflow names/application version deliberately: recovery was tested with unchanged code/version only. External provider requests can repeat if success occurs before the local checkpoint; never claim exactly-once model billing. Runtime records may contain report text. Exclude credentials, runtime databases, dependencies and transient test output from handoffs.

## Verification

Run the affected tests. Contract checks, actual SDK controlled-model tests, subprocess recovery tests and Playwright scenarios are available. Preserve the distinction between controlled integration tests, real provider evaluation, domain assessment and UX acceptance. Add tests only for meaningful risks. Update status documents with actual evidence. No public deployment or patient-data readiness is implied by this bundle.

The report-only v0.3 input replaces the operator-flag contract. Use the fresh .qa-data-v0.3 default (or a fresh QA_DATA_DIR); do not migrate or replay older records silently. Detailed sample-test transparency is in prototype/TESTING_EXPLAINED.md.

## Tenant-aware API v0.4

Read prototype/API_REVIEW.md and API_DESIGN.md. Tenant identity comes from access.py, never a caller-controlled header/body. Pass tenant_id explicitly to every store operation and workflow; scope all lookups, cursors and idempotency receipts. Local mode is loopback Vesta only; bearer mode supports registered tenants. No Vesta policy inheritance for other tenants.

presentation.py owns the public projection; storage schema changes must not leak internal fields. Pin QA-Version independently of workflow/prompt/schema versions. POST replay must preserve accepted status/body/Location; GET reads current state. Atomic outbox and response receipts commit before dispatch. Never replace stable replay with the current resource or gate existing receipts on model readiness.

Completed report-only records migrate in place to storage schema 2. Pending older workflows block migration; finish them with the old version. Do not claim cross-version DBOS replay, production readiness or clinical quality. Keep keys, tenant registries, manuals and runtime databases out of bundles.
