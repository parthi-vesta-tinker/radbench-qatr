# Implementation status

Current release: application **0.15.0**, bundle **1.21**, foundation **F3**, API **2026-09-22**, SQLite schema **8**.

## Implemented

- **JEV critical finding classification (0.15.0):** A completed review with critical comments
  starts one separate five-field JEV classification per critical observation when JEV is configured
  at admission. Reviews without critical comments make no JEV call. QA Studio shows the immutable
  suggestion and records accept, edit, or reject feedback without changing report QA. One provider
  attempt has a durable checkpoint; ambiguous outcomes fail without automatic retry. The draft
  research rubric and local evaluation commands do not establish clinical accuracy. Schema 8
  requires an explicit backed-up upgrade from schema 7. A synthetic demo review completed with
  one critical comment and one successful live JEV classification on 24 September 2026.
  Verification: 28 targeted Python tests passed; the full Python run had 158 passes and one
  outdated PACS copy-label assertion, which was corrected and passed on focused rerun.
  26 frontend DOM tests, production build, generated OpenAPI check and documentation check
  passed. The live synthetic result suggested minutes without an explicit communication
  instruction; the UI now flags any nondefault priority for verification. No qualified
  clinical assessment or process crash test was performed.

- **Analytics copy cleanup:** removed the explanatory text below Review findings and
  the report-text/clinical-accuracy footer at the user's request. Verification on
  24 September 2026: frontend production build passed.

- **Finding-first Analytics:** four saved-comment categories lead, with submitted/completed/failed
  counts secondary. One rolling period selector (1/6/12/24 hours, 7/30 days, all time) replaces
  the source control; the screen includes all review sources. The API adds finding counts while
  retaining feedback, source filtering and unmeasured clinical fields for existing clients.
  Verification on 24 September 2026: 37 affected Python tests, 24 DOM tests, focused Chromium
  analytics checks, production build, generated-contract checks and documentation checks passed.
  Controlled data only; no real-provider call or clinical adjudication.

- **Review History ID presentation:** removed the second-line “AI”/“Demo” mode text from each
  Review ID cell; IDs remain clickable and provider mode remains in stored provenance.
  Verification on 24 September 2026: production build, 24 DOM tests, and the focused
  two-review browser test passed in demo mode; the populated desktop table was inspected.
  No API, storage, or provider behavior changed.

- **Unsubmitted review results presentation:** the section title is “Review Results”
  and its empty message is “Report review and comments will appear here,” aligned directly below
  the title without an icon. Verification on 24 September 2026: production build, 24 DOM tests,
  and the focused header browser check passed; desktop and 390px screenshots were inspected.
  No provider call or API change.

- **Completed empty review presentation:** the output shows only “No actionable observations,”
  aligned with the comment content; the extra icon and explanatory line are removed.
  Verification on 24 September 2026: production build, 24 DOM tests, and the focused
  replacement browser test passed in demo mode at 1536px, 390px, and 320px. No provider call
  or API change.

- **Review History table presentation:** column labels now use Review ID, Report description and
  Submitted time. Completed and Failed use the same neutral, equal-size History-table label;
  progress and system-status severity presentation is unchanged. Verification: 24 DOM tests and
  production build passed. No API, storage or provider behavior changed.

- **Review History and prior-review input:** history supports practical filters, quick submitted
  time ranges, compact IDs, operator, latest submission time, comments and feedback dialogs, and
  20-item pages. Re-review replaces the same current record. Explicit History/Comparison context
  permits a prior Findings/Impression pair while unmarked duplicate reports remain blocked before
  a provider request. New Review gives one actionable pre-check message with a warning icon.
  The reports rail is single-line and scrollable. `npm run demo` and `npm run live` are documented,
  including optional local operator configuration. Verification: 18 focused backend tests, 24 DOM
  tests, production build, generated-contract checks and documentation checks passed; no provider
  call was made.

- **Copy presentation:** aligned buttons, PACS comments naming, unnumbered comments and clipboard text, no success message. Build, 21 backend and 22 component tests plus responsive clipboard browser checks passed.

- **Service health redesign:** compact summary and timestamped refresh, actionable disclosure, consistent check rows and inline OpenAI probe. Build, 22 component tests and 5 diagnostics/header browser tests passed; responsive screenshots checked. No API change or real provider calls.

- **Combined pre-commit verification:** 135 backend and 22 component tests passed. Browser suite: 15 passed; one stale feedback-location selector corrected, then all 3 panel checks passed. Build, generated contracts, docs and bundle checks passed.

- **Review context placement:** one message below the review title, above the input; journey labels Input, Validate, AI review, Output. Build and replacement browser check passed at desktop/390px/320px.

- **Single unfinished Current review:** removed numbered drafts and delete/Undo controls; New review reuses unfinished input, including uncertain submissions. Build, 22 component tests and 9 workspace/panel browser tests passed. No API/database changes.

- **Compact monochrome workspace:** stakeholder outcomes removed from UI/API/analytics; dormant storage retained for schema compatibility. Copy excludes the QA review prefix. Four-stage journey beside Review with one contextual message below; only progress warnings use color. Validation: 33 affected backend, 22 component and 16 browser tests passed; production build and generated contract checks passed.

- **Latest-state report reviews (0.14.0):** PUT replaces the selected terminal review in place with concurrency fencing; feedback stays review-scoped, history/analytics use latest state. API 2026-09-22 and schema 7 are generated/synchronized. Explicit backed-up schema-6 upgrade; no automatic migration.
- **Single review journey:** four compact stages beside the Review button, with one contextual message below, with completed/warning/blocker indicators. Report reviews/Current review labels; no Report text only badge, permanent hint, or duplicate progress list.
- **Verification for this change:** build and generated contract checks passed; 24 direct DOM and 16 browser tests passed. Full Python run had 134 passes and one outdated assertion subsequently corrected/passed; final 10 replacement/storage checks passed. Includes controlled process recovery, migration, concurrent replacement, stale worker fencing, feedback retention and outcome invalidation. No live-provider calls. See the current changelog entry for precise scope.

- Shared typography and responsive filter/control layouts across Review history, Feedbacks, Analytics, Skills and Playground; labelled history entries on mobile. Build and DOM checks passed; 14 existing browser checks passed, plus the separate keyboard-navigation/layout check at desktop and 390/320px. See the changelog for the initial pointer-tooltip obstruction.

- Application title Radiology Report Review, secondary Vesta brand, New review draft heading and Studio tool, and consistent responsive typography. Production build, DOM suite and four targeted header/panel browser checks passed on 2026-09-22; desktop/mobile screenshots inspected using demo fixtures.

- Explicit `QA_AUTH_MODE=public` for unauthenticated remote use of the shared Vesta workspace. Local-only remains the default; API-key scopes and tenant-override rejection are preserved.
- Schema-7 application storage and separate DBOS system storage. Older schemas fail closed. The explicit backed-up schema-6 upgrade preserves terminal reviews and feedback; pending work must finish with the previous application.
- Tenant-scoped review history, feedback, analytics, and Skills Studio draft revisions.
- Server-controlled tenant release binding with immutable complete content snapshots. Vesta can use `vesta-qatr-0.3.0`; other tenants use the generic profile unless explicitly configured.
- Byte-pinned qatr source references, the 43-entry catalog, independently versioned skills, package manifests, reference hashes, and lock validation.
- One combined tool-free structured provider request per admitted valid review. Local input rejection makes zero provider calls.
- Durable DBOS dispatch claim and private response checkpoint. A claimed attempt without a durable response fails as `MODEL_OUTCOME_UNKNOWN` and never retries automatically.
- Complete output validation for skill coverage, candidate identity, check ownership, exact source anchors, report grounding, grouping, and server-derived copy.
- Four truthful phases: input validation, combined report review, output validation, and comment assembly.
- Atomic dispatch claims and durable response checkpoints. Admission is bounded by the context window only; spend authorization was removed on 2026-09-18 by explicit user decision.
- Generated OpenAPI and TypeScript contracts, React workspace, history, direct comment copy, feedback inbox, analytics, Skills Studio, health details, and responsive/light/dark behavior.
- Pack references (`published` and `draft:<workspace>`), draft pack composition from workspace-scoped drafts, and pack identity derived from the installed package rather than constants in code. This is P1 of [SKILL_PACK_SPEC.md](SKILL_PACK_SPEC.md); it adds no HTTP endpoint and no interface change.
- Schema-6 `skill_workspaces`, `playground_runs` and `playground_attempts` tables, workspace fork pinning with explicit rebase, and workspace-scoped `knowledge_drafts`. Editorial drafts saved outside a workspace still never compose.
- **QA Studio Playground**: a sixth Studio tool that runs the real review against curated samples in two categories, or a pasted report, in isolation. It composes the published pack, issues the same combined request, applies the same output validation, and shows results with a phase-and-timing log. Runs are written only to `playground_runs`; there is no history, feedback, analytics or copy action, and the draft banner cannot be dismissed. Instructions are read-only, summarised with a link to Skills. The model list is server controlled. See [PLAYGROUND_UX_SPEC.md](PLAYGROUND_UX_SPEC.md).

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

## Verification for collapsible workspace panels

Implemented 22 September 2026: Skills naming and equal Studio tiles, independent desktop
rails with hover/focus tooltips, compact-screen expansion, and mobile panel drawers.

- **24 controlled DOM/state tests passed**, including report and unsaved Skills content
  preservation across panel toggles, saved desktop preferences, and focus/Escape tooltip behaviour.
- TypeScript/Vite production build passed. No API or provider behavior changed.
- **13 Playwright browser tests passed** against the isolated demo server at
  `http://127.0.0.1:8765`, using local Chromium with user-approved fallback because the in-app
  browser was unavailable. The initial sandboxed server-connect timeout was resolved by
  running the suite outside the sandbox.
- Browser coverage includes independent panel widths, hoverable and keyboard-focus tooltips,
  Escape dismissal, mobile focus trapping/return and backdrop/navigation dismissal, desktop
  preference restoration, preserved unsaved edits, and actual review phases. Existing report,
  feedback, Skills, analytics, diagnostics and Playground browser regressions also passed.
- Screenshots were inspected at 1536×1024, 900×900 and 390×844. Visual review caught and fixed
  a cross-panel heading alignment rule and excess spacing from collapsed Studio grid rows.
  The tested desktop navigation flow had no uncaught browser errors. Other browser engines
  and real mobile devices have not been tested.
- No provider calls, clinical evaluation, backend recovery tests, deployment or remote push
  were performed for this change.

## Verification for header and Studio notice

Run on 22 September 2026 after the supplied Vesta logo and navigation refinements.

- **24 DOM/state tests and 14 Playwright tests passed**, plus the TypeScript/Vite build.
- Browser checks cover loaded logo artwork, Share/Settings coming-soon semantics and tooltips,
  icon-triggered Health with focus return, feature-notice dismissal across reload, and a one-row
  header with no horizontal overflow at 390px and 320px. Opening Health made no provider probe.
- Light/dark desktop and mobile screenshots were inspected. Existing panel, report, Skills,
  feedback, diagnostics, analytics and Playground browser regressions passed unchanged in scope.
- Local Chromium used the previously authorized fallback at `http://127.0.0.1:8765` with isolated
  demo storage. No paid provider call, deployment or remote push was performed. Other browser
  engines and real mobile devices remain unverified.

## Verification for state-specific panel icons

On 22 September 2026, replaced the shared panel glyph with rounded vectors matching the
user's expanded and collapsed close-ups, including inset bars, inward chevrons and left-side
mirroring. The production build and all **3 targeted panel browser tests passed**. Expanded
and collapsed screenshots were inspected; existing tooltip and drawer interactions remain intact.
This is a visual correction only. No provider calls, deployment or remote push were performed.

## Remaining phases

- **F4 — product regression and handoff:** repeat integrated acceptance on a fresh store, review operator-facing failure handling and recovery guidance, verify the distributable bundle, and record any release-blocking issue.
- **F5 — bounded evaluation:** run a predeclared live-provider evaluation and keep model behavior review separate from qualified clinical adjudication.

See [FOUNDATION_PLAN.md](FOUNDATION_PLAN.md) for gate details and [FOUNDATION_CHANGELOG.md](FOUNDATION_CHANGELOG.md) for implementation decisions.

## Review history investigation — 24 September 2026

- Added `frontend/tests/history-retention.spec.ts`: two submissions through New review
  retain distinct IDs and input version 1, appear in the sidebar and history after reload,
  and reopen with their original text. The controlled browser test reported no page errors;
  its desktop screenshot was inspected at 1536×1024.
- The new retention test and existing replacement test both passed (**2 Playwright tests**)
  against isolated demo storage at `http://127.0.0.1:8765`. The frontend production build
  passed. Playwright used local Chromium because the Browser plugin was not available;
  sandbox server connectivity timed out, then the approved outside-sandbox run passed.
- The inspected configured local store contained one review at input version 4; request
  receipts included one create operation and replacement operations. This supports repeated
  replacement as the local explanation, but does not establish behavior on a different server.
  Review again intentionally retains one history entry under the workspace contract.
- No application behavior, live records, or provider execution changed. No deployment or
  clinical evaluation was performed. The new retention flow was checked on desktop only.

## Applied local history recovery — 24 September 2026

- Explicitly restored 39 terminal reviews from `.qa-data-foundation-v5` into the active
  `.qa-data-local` store, preserving its existing review: **40 reviews total**. Imported
  associated snapshots, results, observations, three feedback records, provider checkpoints
  and 49 review-related idempotency receipts. Original review projections match exactly.
- Both application and DBOS databases were backed up in each folder under
  `history-backup-20260924T154948978537Z` before importing with the application stopped.
  No DBOS workflows, Playground records or Studio drafts were imported. Source data and
  current tenant bindings remain intact. SQLite integrity and foreign-key checks passed.
- Added the explicit offline `scripts/restore_review_history.py` utility and documented
  its use. **4 controlled recovery tests passed**, covering preservation, repeat import,
  rollback on conflicts, and refusing pending work in either store. A rehearsal against
  copies of the actual stores verified all 40 original review projections before recovery.
- **1 isolated demo browser regression passed**: New review creates distinct entries,
  retained after reload and accessible from history. No provider calls were made.
- The live app required its interactive API key to be re-entered on restart. After restart,
  read-only Chromium checks at `http://localhost:8000` passed: 40 distinct reviews across
  API and UI pagination, newest/oldest records reopen with matching text, New review opens
  blank, and returning to history retains the records. Page identity, rendered content,
  absence of a framework overlay and browser console/page errors were checked. Desktop
  screenshot inspected at 1536×1024. No live submissions or provider probes were performed.
- Documentation link/inventory validation passed. This recovery does not imply clinical
  validation or production readiness; mobile recovery verification was not repeated.
