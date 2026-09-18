> Current implementation: application **0.12.0**, bundle **1.16**, foundation **F2**. [Decisions and verification](prototype/FOUNDATION_CHANGELOG.md) supersede older baseline statements below. Fresh schema 3 and API 2026-09-17 are implemented; F2 imports the pinned qatr references and tenant-bound snapshots; single-call execution and session-spend enforcement remain F3 work.

# Revised starting point

Read [FOUNDATION_PLAN.md](prototype/FOUNDATION_PLAN.md) for API/data design, single-call DBOS,
safe bootstrap and F1–F5 gates. [IMPLEMENTATION_STATUS.md](prototype/IMPLEMENTATION_STATUS.md)
distinguishes installed/tested behavior from the target. Existing Workspace, Analytics and Skills
Studio features stay; old migration and three-call targets are superseded. No runtime reset occurred.

> **Current release 1.14 / application 0.10.0:** [Workspace specification](prototype/WORKSPACE_SPEC.md) and [Analytics specification](prototype/ANALYTICS_SPEC.md) govern the current UX: feedback inbox, tenant-wide analytics and stakeholder outcomes. Atomic skill evaluation is documented in [the evaluation method](qa-skills/clinical-content/evaluation/METHOD.md). [Backlog](prototype/BACKLOG.md) records deferred Test/Production isolation and adjudicated clinical metrics. Earlier release-specific text below is historical where it conflicts. See [Skills Studio specification](prototype/SKILLS_STUDIO_SPEC.md) for the new content review and draft editor.

# Start here

For local use, follow [LOCAL_TESTING.md](LOCAL_TESTING.md).
For the current product contract, read [prototype/BLUEPRINT.md](prototype/BLUEPRINT.md).
For implementation and tests, read [prototype/IMPLEMENTATION_STATUS.md](prototype/IMPLEMENTATION_STATUS.md).
For subsequent coding, read [AGENTS.md](AGENTS.md).
