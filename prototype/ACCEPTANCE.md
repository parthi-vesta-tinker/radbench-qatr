> Current implementation: application **0.12.0**, bundle **1.16**, foundation **F2**. [Decisions and verification](FOUNDATION_CHANGELOG.md) supersede older baseline statements below. Fresh schema 3 and API 2026-09-17 are implemented; F2 imports the pinned qatr references and tenant-bound snapshots; single-call execution and session-spend enforcement remain F3 work.

# Foundation acceptance — proposed next build

These criteria implement [FOUNDATION_PLAN.md](FOUNDATION_PLAN.md); none is claimed passed yet.

| ID | Required proof |
|---|---|
| F-01 | Fresh app/DBOS bootstrap rejects incompatible schema safely; preserves secrets/spend ledger. |
| F-02 | Public schema → OpenAPI → TypeScript generation and error contracts are reproducible. |
| F-03 | Tenant-scoped data/receipts/drafts and foreign keys reject cross-tenant references. |
| F-04 | Concurrent acceptance retries create one review, receipt and budget reservation. |
| F-05 | Valid review uses one controlled model request; invalid input zero; no hidden retry. |
| F-06 | Claimed/uncheckpointed requests become unknown; checkpointed responses resume locally. |
| F-07 | Three qatr references and 43 unique IDs retain authority/qualifiers; no drafts/evals in prompt. |
| F-08 | Snapshots survive content changes; tenant binding/drafts stay isolated and inactive. |
| F-09 | Refusal, truncation, invalid schema/anchors/IDs and context overflow fail without repair calls. |
| F-10 | Fresh-data history, feedback, stakeholder outcomes, analytics and authoring all work. |
| F-11 | Exact two-group copy, no revived missed-flag line, stale copy or fictional stage progress. |
| F-12 | Aggregate authorized $1 session admission withstands concurrency, restart and app reset. |
| F-13 | Empty operational counts are truthful; clinical metrics/unknown costs are not invented. |
| F-14 | Live evaluation requires separate permission and evidence; old tests do not validate new code. |

## Earlier baseline acceptance

The dated criteria below record older contracts; they do not override the foundation or current
Workspace/Analytics/Skills Studio requirements.

> **Current release 1.14 / application 0.10.0:** [Workspace specification](WORKSPACE_SPEC.md) governs the current UX. [Analytics specification](ANALYTICS_SPEC.md) defines the feedback inbox, stakeholder outcomes, metric denominators and unmeasured clinical performance. [Implementation status](IMPLEMENTATION_STATUS.md) records verification; [Backlog](BACKLOG.md) records deferred work. Earlier release-specific text below is historical where it conflicts. See [Skills Studio specification](SKILLS_STUDIO_SPEC.md) for the new content review and draft editor.

> Release note (15 September 2026): This planning/baseline document is retained for continuity.
> The current skill-enabled prototype is specified in BLUEPRINT.md and API_DESIGN.md;
> implemented features and verified outcomes are recorded in IMPLEMENTATION_STATUS.md.
> Local startup is documented in ../LOCAL_TESTING.md.

# Prototype acceptance criteria

Contract v0.3 · Software evidence and clinical evaluation are separate

| ID | Scenario | Expected behavior |
|---|---|---|
| A01 | Clean report | Completed no-observation result; no template or copy; feedback available. |
| A02 | Language issue | Meaningful concise general comment. |
| A03 | Laterality inconsistency | Ask to reconcile; never choose the correct side. |
| A04 | Critical and general observations | Both groups visible; unknown flag status remains Cannot determine unless explicitly documented. |
| A05 | Negated finding | Do not invent a positive critical finding. Domain/model evaluation pending. |
| A06 | Historical/resolved finding | Do not treat as current without support. Domain/model evaluation pending. |
| A07 | Missing section | needs_input; downstream steps skipped. |
| A08 | Unusable input | Request substantive findings/impression; no successful empty result. |
| A09 | Embedded instructions | Treat as source data, not agent instructions. Domain/model evaluation pending. |
| A10 | Different report pasted | Prior result stale; no carried flag; Review submits new text only. |
| A11 | Clipboard denied | Exact selectable text; no false success. |
| A12 | Negative feedback | Reason only is valid, including Other; optional wording preserved after error. |
| A13 | Duplicate request | Same key/text gives same review; changed text with reused key conflicts. |
| A14 | Process interruption | Recover same report/review, reusing completed checkpoints. |
| A15 | Model/output failure | Terminal failure without no-observation/copy output. |
| A16 | Critical observation without designation metadata | Review accepted; critical comment retained; missed flag unknown. |
| A17 | Report explicitly documents flag | Critical comment retained; missed flag No. |
| A18 | Report explicitly documents no flag | Critical comment retained; missed flag Yes. |
| A19 | Extra legacy flag input | Reject field; current request schema accepts report_text only. |
| A20 | Manual absent | Provisional criteria; no claim of manual-backed clinical validation. |

The seven demo examples have prewritten outputs. Clinical identification expectations in the seed set are proposals, not reviewed ground truth. API/browser tests establish implementation behavior; qualified reviewers must separately assess critical detection, false observations, concise wording and radiologist attention cost using real model results.
