> Current implementation: application **0.13.0**, bundle **1.17**, foundation **F3**. [Decisions and verification](FOUNDATION_CHANGELOG.md) supersede older baseline statements below. Fresh schema 4 and API 2026-09-18 are implemented. F3 adds one combined request, guarded dispatch and durable response checkpoints. F4/F5 remain separate gates.

# Foundation prioritization — 2026-09-17

Implement [FOUNDATION_PLAN.md](FOUNDATION_PLAN.md) F1–F4 before product expansion. History,
feedback, outcomes, analytics and tenant drafts are retained regression requirements.
Basic server-controlled tenant release binding is foundation work; browser governance stays SK-01.

## DATA-01 — Retained-data lifecycle (deferred)

No historical migration, legacy projection or old DBOS replay at this disposable-data cutover.
Before retaining real data, add migrations, backup/restore, retention and rollback testing.
Startup must never auto-wipe an incompatible database.

## SCALE-01 — Infrastructure and advanced execution (deferred)

PostgreSQL deployment, new services, retrieval, multi-agent execution, semantic caching and large
telemetry dashboards need demonstrated requirements. Tenant isolation, budget guards, constraints
and tests are not deferred. Existing backlog follows; it does not reintroduce migration work.

# Backlog

## SK-01 — Governed content activation

Release 1.14 delivers review/edit/compare/save/export for skill and guidance proposals.
Browser activation is deferred: connect qualified content review, affected atomic evaluations,
versioned tenant package selection, validated release and rollback without changing accepted
instruction snapshots. Add document-level review ownership and knowledge ingestion only when needed.

## ENV-01 — Isolated Test and Production environments

Status: explicitly deferred by Parthi. Not implemented in release 1.13.

Test means a separate deployment using real AI, never canned responses. Share the codebase and API
contract, while isolating application data, DBOS system storage and workers, credentials, provider
projects/keys, queue limits, telemetry and configuration. Tenant identity remains orthogonal.

Proposed contract:
- Same /api/v1 resource routes on separate environment origins; separate processes/ports locally.
- Environment fixed at startup. No request field or header can choose a database or provider mode.
- Config and QA-Environment response header disclose authoritative environment identity.
- Optional QA-Expected-Environment assertion rejects a mismatch before mutation or acceptance.
- Idempotency receipts, history, feedback and workflow recovery remain in the originating environment.
- Wrong-environment credentials fail; unavailable services never fall back to another environment.
- UI switch navigates to the other workspace and never moves or submits report content automatically.
  Initially a new tab may preserve the originating unsaved draft; revisit alongside draft persistence.
- Require startup storage ownership checks, independent database credentials, isolation tests and
  restart/retry tests before enabling the switch. PostgreSQL production provisioning is separate work.
- Migrate historical records only through an explicit reviewed plan; never infer environment from
  legacy demo/openai provenance. Promote code and approved skill versions, not report data.

References: https://docs.dbos.dev/python/reference/configuration ; https://docs.stripe.com/sandboxes
These inform the architecture, not a claim that Stripe's implementation is being copied.

## WS-02 — Durable drafts and submission recovery across browser restarts

Memory-only drafts, Undo, and ambiguous POST retry survive navigation inside the current tab only.
Design authenticated, tenant-bound draft storage and retained submission intents before extending this.

## WS-03 — Fleet analytics and feedback triage

Partially delivered in 1.13: tenant-wide server aggregates, scoped feedback inbox, and append-only
stakeholder outcomes. See ANALYTICS_SPEC.md. Still deferred: feedback triage ownership/resolution,
larger active-list pagination, time trends, verified communication ingestion, and provider/facility
identity-based comparison. Current intake has no reliable radiologist or facility identifiers.

## AN-01 — Adjudicated critical-finding performance

Define an approved reference standard and representative positive/negative cohort with qualified
independent adjudication before enabling precision, recall, false-positive rate or false-alert share.
Track report-level and finding-level evaluation separately, record model/skill/policy provenance,
and display exclusions, denominators and uncertainty. Complaints and stakeholder decisions are not
ground truth. Clinical readiness cards currently return null, never fabricated percentages.

## WS-04 — UI acceptance

Run the current Playwright cases on an environment with Chromium and review desktop/mobile layouts,
copy actions, keyboard navigation, light/dark contrast and screen-reader behavior. Historical screenshots
are not evidence for release 1.13. No new live AI evaluation was performed for these UI changes.
