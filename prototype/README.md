> Current implementation: application **0.12.0**, bundle **1.16**, foundation **F2**. [Decisions and verification](FOUNDATION_CHANGELOG.md) supersede older baseline statements below. Fresh schema 3 and API 2026-09-17 are implemented; F2 imports the pinned qatr references and tenant-bound snapshots; single-call execution and session-spend enforcement remain F3 work.

> Next-build authority (2026-09-17): [clean-start foundation plan](FOUNDATION_PLAN.md). Startup details below describe installed application 0.10.0; the foundation revision is documentation only.

> **Current release 1.14 / application 0.10.0:** [Workspace specification](WORKSPACE_SPEC.md) governs the current UX. [Analytics specification](ANALYTICS_SPEC.md) defines the feedback inbox, stakeholder outcomes, metric denominators and unmeasured clinical performance. [Implementation status](IMPLEMENTATION_STATUS.md) records verification; [Backlog](BACKLOG.md) records deferred work. Earlier release-specific text below is historical where it conflicts. See [Skills Studio specification](SKILLS_STUDIO_SPEC.md) for the new content review and draft editor.

> Release note (15 September 2026): This planning/baseline document is retained for continuity.
> The current skill-enabled prototype is specified in BLUEPRINT.md and API_DESIGN.md;
> implemented features and verified outcomes are recorded in IMPLEMENTATION_STATUS.md.
> Local startup is documented in ../LOCAL_TESTING.md.

# Current prototype artifacts

Contract v0.4 · implementation 0.3.0 · bundle v1.8

Run the prototype using ../README.md. This folder documents the current narrow scope; the broader framework is a future reference.

- BLUEPRINT.md / BLUEPRINT.html: product contract and consolidated reading edition.
- UX_DESIGN_SYSTEM.md and UX_STATES.md: architecture, visual rules and interaction states.
- API_DESIGN.md / openapi.json: implemented API semantics and schema snapshot.
- IMPLEMENTATION_STATUS.md: actual build/test evidence and remaining limits.
- DBOS_VALIDATION.md: restart, idempotency and SDK findings.
- ROADMAP.md / IMPLEMENTATION_PLAN.md: prototype progress and next bounded work.
- ACCEPTANCE.md: product acceptance scenarios; automation is partial evidence, not human/domain sign-off.
- REVIEW_NOTES.md: decisions, corrections and consistency review.
- assets/: generated concept and actual implementation screenshots.
- examples/: synthetic seeds and standard comment fixtures; not a clinically approved evaluation set.

- TESTING_EXPLAINED.md: what sample-report testing proves, how canned outputs are used, and what has not been evaluated by a live model.

- API_REVIEW.md: audit findings, Stripe reference principles, implemented changes and scope limits.
