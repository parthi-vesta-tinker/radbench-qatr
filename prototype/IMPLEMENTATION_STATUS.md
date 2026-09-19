# Implementation status

Current release: application **0.13.0**, bundle **1.18**, foundation **F3**, API **2026-09-18**, SQLite schema **5**.

## Implemented

- Fresh schema-5 application storage and separate DBOS system storage. Older nonempty schemas fail with an actionable error and are never silently migrated or reset.
- Tenant-scoped review history, feedback, outcomes, analytics, and Skills Studio draft revisions.
- Server-controlled tenant release binding with immutable complete content snapshots. Vesta can use `vesta-qatr-0.3.0`; other tenants use the generic profile unless explicitly configured.
- Byte-pinned qatr source references, the 43-entry catalog, independently versioned skills, package manifests, reference hashes, and lock validation.
- One combined tool-free structured provider request per admitted valid review. Local input rejection makes zero provider calls.
- Durable DBOS dispatch claim and private response checkpoint. A claimed attempt without a durable response fails as `MODEL_OUTCOME_UNKNOWN` and never retries automatically.
- Complete output validation for skill coverage, candidate identity, check ownership, exact source anchors, report grounding, grouping, and server-derived copy.
- Four truthful phases: input validation, combined report review, output validation, and comment assembly.
- Atomic dispatch claims and durable response checkpoints. Admission is bounded by the context window only; spend authorization was removed on 2026-09-18 by explicit user decision.
- Generated OpenAPI and TypeScript contracts, React workspace, history, direct comment copy, feedback inbox, analytics, stakeholder outcomes, Skills Studio, health details, and responsive/light/dark behavior.
- Pack references (`published` and `draft:<workspace>`), draft pack composition from workspace-scoped drafts, and pack identity derived from the installed package rather than constants in code. This is P1 of [SKILL_PACK_SPEC.md](SKILL_PACK_SPEC.md); it adds no HTTP endpoint and no interface change.
- Schema-5 `skill_workspaces` and `playground_runs` tables, workspace fork pinning with explicit rebase, and workspace-scoped `knowledge_drafts`. Editorial drafts saved outside a workspace still never compose.

## Verification completed for F3

- **100 Python tests passed** after the spend removal, including contract, store, tenant isolation, controlled SDK/HTTP adapter, concurrency, and subprocess recovery tests. One OpenAPI drift check is deselected: it fails identically on the unmodified tree in the current container, where FastAPI renders 422 as "Unprocessable Entity" against the checked-in "Unprocessable Content".
- Recovery covered process termination before claim, after claim, after provider response, after the application response checkpoint, after combined completion, and after final commit.
- Controlled adapter tests covered HTTP 500, incomplete response, refusal, missing usage, unknown tools, malformed/invalid coverage, and replay behavior.
- **19 React DOM tests passed** and the TypeScript/Vite production build passed.
- **8 Playwright scenarios passed** with local Chromium, including phase labels, exact copy groups, reload, narrow layout, draft handling, Skills Studio saves, and analytics. Desktop and mobile screenshots were inspected.
- Dependency lock, generated OpenAPI/TypeScript drift, skill package validation, qatr source hashes, and source bundle verification passed.
- No paid OpenAI request was made for implementation verification: recorded provider spend was **$0**.

These checks establish technical behavior with controlled data. They do not establish clinical correctness, patient-data readiness, public deployment readiness, or exactly-once external billing.

## Verification completed for the pack reference change

Run on 19 September 2026 for P1 of [SKILL_PACK_SPEC.md](SKILL_PACK_SPEC.md).

- **110 Python tests passed**, including 10 new controlled tests for pack-reference parsing and stamping, derived pack identity, live refusal of a draft pack, workspace draft composition, editorial drafts that never compose, frozen content that cannot be drafted, fork staleness and rebase, tenant scoping, and playground-run isolation from every live table.
- The same single OpenAPI drift check still fails, and was confirmed to fail identically on unmodified `origin/main` in this container. It is the checked-in 422 wording, not this change: no HTTP route, schema or response was added or altered.
- Skill package validation, generated TypeScript contract drift, and the documentation boundary check passed.
- **20 React DOM tests, the TypeScript/Vite production build, and 9 Playwright scenarios passed** on the merged tree, with the schema-5 store bootstrapped fresh. No frontend file changed by this work.
- No provider request was made. Recorded provider spend was **$0**.

These are controlled storage and composition checks. They establish no clinical claim, and the playground has no user interface yet.

## Remaining phases

- **F4 — product regression and handoff:** repeat integrated acceptance on a fresh store, review operator-facing failure handling and recovery guidance, verify the distributable bundle, and record any release-blocking issue.
- **F5 — bounded evaluation:** run a predeclared live-provider evaluation and keep model behavior review separate from qualified clinical adjudication.

See [FOUNDATION_PLAN.md](FOUNDATION_PLAN.md) for gate details and [FOUNDATION_CHANGELOG.md](FOUNDATION_CHANGELOG.md) for implementation decisions.
