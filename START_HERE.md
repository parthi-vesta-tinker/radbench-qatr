> Current implementation: application **0.13.0**, bundle **1.17**, foundation **F3**. [Decisions and verification](prototype/FOUNDATION_CHANGELOG.md) supersede older baseline statements below. Fresh schema 4 and API 2026-09-18 are implemented. F3 adds one combined request, guarded dispatch and durable response checkpoints. F4/F5 remain separate gates.

F3 startup requires fresh `.qa-data-foundation-v3` storage. See [current startup instructions](LOCAL_TESTING.md#f3-startup). Earlier release commands below are historical.


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
