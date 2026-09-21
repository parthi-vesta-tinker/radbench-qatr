# Implementation status

Current release: application **0.13.0**, bundle **1.19**, foundation **F3**, API **2026-09-18**, SQLite schema **6**.

## Implemented

- Explicit `QA_AUTH_MODE=public` for unauthenticated remote use of the shared Vesta workspace. Local-only remains the default; API-key scopes and tenant-override rejection are preserved.
- Fresh schema-6 application storage and separate DBOS system storage. Older nonempty schemas fail with an actionable error and are never silently migrated or reset.
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
- Schema-6 `skill_workspaces`, `playground_runs` and `playground_attempts` tables, workspace fork pinning with explicit rebase, and workspace-scoped `knowledge_drafts`. Editorial drafts saved outside a workspace still never compose.
- **QA Studio Playground**: a sixth Studio tool that runs the real review against curated samples in two categories, or a pasted report, in isolation. It composes the published pack, issues the same combined request, applies the same output validation, and shows results with a phase-and-timing log. Runs are written only to `playground_runs`; there is no history, feedback, analytics or copy action, and the draft banner cannot be dismissed. Instructions are read-only, summarised with a link to Skills & knowledge. The model list is server controlled. See [PLAYGROUND_UX_SPEC.md](PLAYGROUND_UX_SPEC.md).

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

## Verification completed for the QA Studio playground

Run on 19 September 2026 for P2 of [SKILL_PACK_SPEC.md](SKILL_PACK_SPEC.md).

- **120 Python tests passed**, including 10 new playground tests: catalog shape, sample text read from the hash-pinned corpus, a full run through the real path with a mock HTTP transport, logs restricted to phases and timings, paste-your-own and its input rules, model allowlisting, idempotent replay and conflict, demo support computed rather than declared, a provider failure reported without retry, and tenant scoping.
- Isolation is asserted against the store: after a completed playground run, `review_records`, `review_results`, `observations`, `feedback`, `outcomes` and `model_attempts` are all empty, and review history, analytics and the feedback inbox return nothing.
- Live review is unaffected by the shared execution path: the full recovery and provider suites pass unchanged, including process termination before claim, after claim, after provider response, and after the application checkpoint.
- **22 React DOM tests and 10 Playwright scenarios passed**, including a browser run of a demo sample end to end, the absence of any copy control, and the run reaching no live surface.
- Generated OpenAPI gained 264 leaves for the three new routes and changed or removed none. The single pre-existing drift check still fails on the checked-in 422 wording, as it does on unmodified `main` in this container.
- Skill package validation, generated TypeScript drift, the documentation boundary check and bundle verification passed.
- No provider request was made. Recorded provider spend was **$0**.

These are controlled tests with canned or mocked provider responses. They establish no clinical claim, and the playground performs no automatic regression comparison.

## Verification completed for explicit public access

Run on 21 September 2026 after the user requested public Funnel access.

- **34 controlled Python tests passed** in `tests/test_api_design.py`, `tests/test_foundation.py`
  and `tests/test_api.py`. The targeted access subset first passed all 8 selected tests.
- Coverage includes forwarded remote clients, default/local rejection, explicit public acceptance,
  a demo review read by a second public visitor, feedback, Studio/playground reads, tenant spoofing
  rejection, invalid-mode rejection, and existing API-key scope and tenant isolation behaviour.
- Generated OpenAPI and TypeScript checks, the frontend production build, and the documentation
  boundary check passed. Wire payloads and generated TypeScript types are unchanged.
- No provider call, external Funnel verification, browser acceptance or process recovery test was
  run for this change. No running server was restarted; enable the mode using the documented
  startup command in [LOCAL_TESTING.md](../LOCAL_TESTING.md).

These are controlled access and API checks, not public deployment or clinical validation.

## Remaining phases

- **F4 — product regression and handoff:** repeat integrated acceptance on a fresh store, review operator-facing failure handling and recovery guidance, verify the distributable bundle, and record any release-blocking issue.
- **F5 — bounded evaluation:** run a predeclared live-provider evaluation and keep model behavior review separate from qualified clinical adjudication.

See [FOUNDATION_PLAN.md](FOUNDATION_PLAN.md) for gate details and [FOUNDATION_CHANGELOG.md](FOUNDATION_CHANGELOG.md) for implementation decisions.
