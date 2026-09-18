> Next-build authority (2026-09-17): [clean-start foundation plan](../prototype/FOUNDATION_PLAN.md). This broader framework is a design reference, not extra foundation scope. Preserve the current application's history, feedback, analytics and tenant drafts. Fresh data and one-call DBOS execution supersede older implementation assumptions; historical examples are not new runtime or clinical evidence.

> **Current release 1.14 / application 0.10.0:** [Workspace specification](../prototype/WORKSPACE_SPEC.md) governs the current UX; [Analytics specification](../prototype/ANALYTICS_SPEC.md) adds feedback inbox, stakeholder outcomes and evidence-aware metrics. Atomic clinical skills remain independently versioned and evaluated. [Backlog](../prototype/BACKLOG.md) records deferred work. This broader framework remains a future reference, not a claim that every capability is implemented. See [Skills Studio specification](../prototype/SKILLS_STUDIO_SPEC.md) for the new content review and draft editor.

# Report QA UX framework — v1.2

Open BLUEPRINT.html for the self-contained human reading edition. Start with FRAMEWORK.md for canonical text.

| File | Purpose |
|---|---|
| FRAMEWORK.md | UX structure, source context, evidence, state and interaction contracts |
| DECISIONS.md | Agreed decisions, explicit proposals, assumptions and open questions |
| QA_COMMENTS.md | First-class radiologist comments, profiles, copy contract and attention cost |
| DESIGN_SYSTEM.md | Selected fleet-first/vertical-Studio design, tokens, density and component behaviors |
| UI_SYSTEM_DESIGN.md | State/rendering architecture, adapter/command boundaries and performance targets |
| design-tokens.json / design-tokens.css | Semantic palettes and shared sizing/motion inputs |
| GUIDED_ACTIONS.md | Context-specific next-step contract and scenario guidance |
| guidance-examples.json | Three case-bound guidance examples with synthetic destination mapping |
| fleet-rows.json | Eight illustrative fleet rows; three backed by canonical case fixtures |
| AGENT_HANDOFF.md | Component responsibilities and 35 acceptance criteria |
| fixtures.json | Three canonical synthetic cases |
| comment-packets.json | Three profile-bound structured comment packets |
| comment-examples/ | Seven exact plain-text exports for copy/paste design |
| assets/reference-ui.png | Current compact default visual anchor |
| assets/reference-expanded.png | Earlier expanded behavior reference; apply selected styling |
| REVISION_REVIEW.md | Request mapping, resolved inconsistencies and remaining design limits |
| PACKAGE_CHECKS.md | Actual package verification and its limits |
| verify_package.py | Offline artifact/reference checks |
| render_blueprint.py | Rebuilds the reading edition from the Markdown and reference image |
| BLUEPRINT.html | Standalone reading edition; no app or external integration |

Run `python3 verify_package.py` for artifact consistency. Run `python3 render_blueprint.py` after editing source documents. All patient-like examples, identities, policies and responses are synthetic. No model, live messaging, clinical policy or production stack is selected or authorized by this package.
