# Current prototype documentation

This directory contains the current application contract and generated artifacts for application **0.13.0** / foundation **F3** / schema **6**. Older plans, screenshots, and design studies are under `../design-history/` and are not implementation authority.

## Read by task

| Task | Current document |
|---|---|
| Implement the next phase | [FOUNDATION_PLAN.md](FOUNDATION_PLAN.md) |
| Review completed decisions and evidence | [FOUNDATION_CHANGELOG.md](FOUNDATION_CHANGELOG.md) |
| Check current implementation and limits | [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) |
| Change an HTTP contract | [API_DESIGN.md](API_DESIGN.md) and generated [openapi.json](openapi.json) |
| Change durable execution or recovery | [DBOS_VALIDATION.md](DBOS_VALIDATION.md) |
| Change workspace behavior | [WORKSPACE_SPEC.md](WORKSPACE_SPEC.md) |
| Change analytics or outcomes | [ANALYTICS_SPEC.md](ANALYTICS_SPEC.md) |
| Change Skills Studio | [SKILLS_STUDIO_SPEC.md](SKILLS_STUDIO_SPEC.md) |
| Review gates or deferred work | [ACCEPTANCE.md](ACCEPTANCE.md) and [BACKLOG.md](BACKLOG.md) |
| Review UI problems and proposed enhancements | [UI_ENHANCEMENT_RESEARCH.md](UI_ENHANCEMENT_RESEARCH.md) |

## Proposals under review

These are not implementation authority. They describe target behavior that changes nothing until accepted.

| Proposal | Document |
|---|---|
| Skill pack reorganization and playground | [SKILL_PACK_SPEC.md](SKILL_PACK_SPEC.md) |
| Playground interaction model | [PLAYGROUND_UX_SPEC.md](PLAYGROUND_UX_SPEC.md) |
| Feedback comment classification | [FEEDBACK_CLASSIFICATION_SPEC.md](FEEDBACK_CLASSIFICATION_SPEC.md) |
| Feedback inbox triage order | [FEEDBACK_TRIAGE_ORDER_SPEC.md](FEEDBACK_TRIAGE_ORDER_SPEC.md) |
| QA comment actionability | [COMMENT_ACTIONABILITY_SPEC.md](COMMENT_ACTIONABILITY_SPEC.md) |

`BLUEPRINT.html` is a generated reading edition of this current set. Rebuild it with:

```sh
uv run python prototype/render_blueprint.py
```

`UI_ENHANCEMENT_RESEARCH.md` records observed UI problems, gated enhancement proposals and their verdicts. It is research and a decision log, not implementation authority; the specifications above govern.

`examples/` contains synthetic scenarios used by evaluation tooling. These examples are technical fixtures, not clinical validation.

## Documentation boundary

Active root entrypoints and the current documents above must not link to archived files. Run `uv run python scripts/check_docs.py` after documentation changes. The check verifies the allowlist, local links, and archive boundary.
