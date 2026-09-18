> Current implementation: application **0.13.0**, bundle **1.17**, foundation **F3**. [Decisions and verification](FOUNDATION_CHANGELOG.md) supersede older baseline statements below. Fresh schema 4 and API 2026-09-18 are implemented. F3 adds one combined request, guarded dispatch and durable response checkpoints. F4/F5 remain separate gates.

## F3 implementation — 2026-09-18

One combined OpenAI request, atomic dispatch protection and durable response checkpoints are
implemented. Spend authorization was removed by explicit user decision; reviews are admitted on
configuration readiness and context size alone. API 2026-09-18 / schema 4 requires fresh
`.qa-data-foundation-v3` storage. Existing data is preserved and older schemas fail closed.
See [F3 decisions and executed checks](FOUNDATION_CHANGELOG.md) and
[current startup instructions](../LOCAL_TESTING.md#f3-startup).

Verification: final full Python run **107 passed**;
TypeScript/build and React DOM passed; 8 Playwright scenarios passed, including desktop/mobile
inspection. No paid provider requests ($0), clinical adjudication or deployment. F4/F5 remain
separate gates. Historical evidence below is scoped to its named release.

F2 adds `catalog` and `policy_source` knowledge document kinds, full qatr source attribution,
server-controlled tenant release profiles, and immutable complete composition snapshots.
See [foundation changelog](FOUNDATION_CHANGELOG.md) for implemented boundaries and evidence.

# Planning revision — 2026-09-17

Documentation-only revision: [FOUNDATION_PLAN.md](FOUNDATION_PLAN.md) defines the proposed next
build. Runtime remains application 0.10.0 / bundle baseline 1.14. No database reset, content
activation, API/runtime change or paid provider request occurred. Historical test counts below
belong only to their named releases; new F1–F5 gates are not passed by those tests.
Documentation checks: all local Markdown links in the 39 revised/new documents resolve;
both reading editions regenerate deterministically; `git diff --check` passes. The existing
framework artifact verifier passes. The unchanged installed skill package validator passes
9 skills / 44 artifacts / 54 atomic cases / 25 cross-stage cases (artifact contracts only).
Runtime source, frontend, tests, OpenAPI and pinned skill bytes are unchanged. No runtime or
browser tests were rerun, and none of these checks validates the planned one-call implementation.

# Skills Studio release 1.14 / application 0.10.0

Implemented: fifth QA Studio tool, installed catalog (nine skills, three shared references and
effective local guidance), actual stage usage, plain-text/Markdown draft editor, installed-content
comparison, change summaries, saved revision history/restoration and JSON draft export. Unsaved edits
remain mounted across Studio navigation. Installed content and report workflow remain unchanged.

New tenant-scoped draft storage has explicit skills:read/skills:write permissions, source hashes,
optimistic revision checks and atomic idempotent receipts. Drafts never enter model prompts.
No clinical skill bytes, framework locks, DBOS workflow names or APP_VERSION changed this release.
The tool supports editorial proposals; browser activation and clinical release adjudication are deferred.

Executed verification: **73 Python tests passed**, including six new catalog/edit/security tests;
**19 React DOM tests passed**, including navigation persistence, read-only state, conflicting edits
and exact-key retry. TypeScript and production build passed. No paid model calls or clinical
evaluation were performed. Browser navigation to http://127.0.0.1:8774 was blocked by
ERR_BLOCKED_BY_CLIENT; visual layout, browser console and accessibility checks remain unverified.
No fallback or policy bypass was attempted. See LOCAL_TESTING.md for local acceptance steps.

Artifacts: SKILLS_STUDIO_SPEC.md, generated OpenAPI, static App-derived blueprint and built frontend.
The source package/blueprint exposes the new tool; interactive inspection requires running the app.

---

# Studio analytics release 1.13 / application 0.9.0

Implemented: dedicated feedback inbox; tenant-wide Analytics queried from stored records; rolling
7-day/30-day/all-time and provenance filters; report versus QA-comment acceptance for QA,
radiologist and facility; append-only operator-recorded outcomes with result binding and atomic
idempotent receipts. Unknown withdraws an earlier decision without erasing it. No new intake fields,
clinical output changes, provider calls, auto-learning or external delivery were introduced.

Critical recall, precision, false-positive rate and false-alert share have explicit definitions and
readiness cards, not fabricated values. An independent adjudicated reference cohort is not connected;
feedback and stakeholder acceptance are not ground truth. The metric framework and research source
are in ANALYTICS_SPEC.md. There is no composite quality score or individual doctor/facility ranking.

Verification on Linux: full Python suite **67 passed**; React DOM suite **15 passed**; TypeScript and
production build passed. New coverage exercises database-wide counts, time/source filters, pagination,
permissions, tenant isolation, outcome receipt replay/conflict, decision history/retraction, null
denominators, late responses and exact-key retry after ambiguous failures. DOM uses explicit API
doubles; backend uses controlled storage fixtures. Neither claims clinical AI validation.

Browser navigation to the local app was blocked with ERR_BLOCKED_BY_CLIENT. No workaround or browser
layout pass is claimed; local visual/accessibility acceptance remains necessary. No paid OpenAI calls
were made; the earlier live-verification budget ledger remains unchanged. Test/Production separation
remains deferred. Skill content, DBOS identities and default .qa-data-v0.6 are unchanged from 1.12.

Reproduce: uv run pytest -q; npm --prefix frontend run test:dom; npm --prefix frontend run build.
The current static BLUEPRINT.html is generated from actual App components with inactive controls and
no invented results. Run the application to inspect the new interactive Studio pages.

---

# Skill evaluation release 1.12 / application 0.8.0

The workspace UX remains unchanged from 1.11. This release makes the clinical instruction package
incrementally evolvable and adds a bounded clinical-behavior evaluation harness.

- All nine atomic skills are 0.2.0 with independent changelogs and focused instruction refinements.
- Nine suites contain 54 unique synthetic cases: six per skill with development and held-out splits.
- Deterministic gates, stage-model execution, private candidate export, automatic contract scoring
  and explicit human adjudication fields are separated. Clinical pass remains unset by automation.
- Runtime provenance includes every atomic skill version and stage composition. Accepted work still
  pins exact instruction bytes and hashes.
- Package validation checks suite/version/stage/changelog integrity and produces a pinned manifest.
- The provider runner plans by default and performs no call without `--execute`; it enforces case,
  output-token and total-token bounds and checkpoints each result.

Executed evidence: skill/package validation passed (9 skills, 44 artifacts, 54 atomic cases and 25
cross-stage regression cases). The complete Python suite passed 60 tests, including controlled
Agents SDK, tenant/idempotency, queue admission and three subprocess restart/recovery cases. React
DOM passed 8 tests; TypeScript and the Vite production build passed; `uv lock --check` passed.
The evaluation planner was verified to make no provider call by default. No paid provider calls,
browser-layout run or clinical adjudication were performed for 1.12.

---

# Workspace release 1.11 / application 0.7.0

Implemented: multi-report workspace; immutable submitted input; New report while another submission
or review runs; draft trash icon with Undo; duplicate empty-draft avoidance; exact-key retry after
ambiguous acceptance; QA Studio tools; header Health; light/dark theme; DBOS parent-review queue.
The clinical skill package and two-group copy contract are unchanged.

Test/Production environment separation is explicitly deferred as ENV-01 in BACKLOG.md. The unfinished
QA-Mode routing and toggle were removed. No alternate provider selection is exposed. The launcher and
example configuration use real OpenAI only; the UI has no canned-example picker. Internal pre-existing
technical fixtures remain in automated tests and historical design references, separate from live AI.

Executed verification on Linux:
- Existing Python regression suite: 54 passed, including actual DBOS/SDK controlled integration,
  tenant/idempotency contracts, component diagnostics and three subprocess restart cases.
- Added real DBOS queue test: 1 passed. At concurrency 2, two parent reviews run while a third stays
  queued; releasing the validation gate admits the third. Inputs terminate at deterministic minimum
  input validation, before clinical/model stages. This test does not fabricate clinical results.
- React DOM interaction suite: 8 passed. Covers draft delete/Undo, empty-draft reuse, immutable input,
  concurrent submissions, late acceptance without selection takeover, exact-key network retry,
  theme persistence, absence of environment/sample selectors, health failure and Studio navigation.
  These tests use Happy DOM and explicit API doubles; they are not browser layout or AI tests.
- TypeScript check and production frontend build passed. uv lock --check --offline passed.
  Launcher --help passed; real key/inference startup was not invoked for this release.

Browser rendering remains unverified for this release. Prior Cloud Browser navigation was blocked
by URL policy; local Chromium was absent and its download returned HTTP 403. No policy workaround was
used. Five current Playwright scenarios are supplied for local execution, but were not run here.
Historical v1.10 browser cases are archived under design-history/browser-tests-v1.10 as text.
Earlier screenshots and browser pass counts below are historical, not v1.11 evidence.

No paid OpenAI calls were made. The previous live-verification budget ledger remains unchanged.
No Windows runtime, new clinical evaluation, screen-reader audit or production deployment is claimed.
The current static BLUEPRINT.html is generated from App components and contains no invented reviews.

Reproduce: uv run pytest -q; npm --prefix frontend run test:dom; npm --prefix frontend run build.
For browser validation: install Chromium for Playwright, then npm --prefix frontend run test:browser.
Regenerate the static blueprint from frontend with node scripts/render-blueprint.mjs.

---

# Refinement release 1.10 / application 0.6.0

The nine requested improvements are implemented; see REFINEMENT_SPEC.md for current decisions.
QA comments and copy controls are aligned; a compact five-step summary replaces the observation
count sentence; missed-flag UI and current clipboard content are deferred. Inline section parsing,
review history/filtering/reopening and persistent feedback display are included.

Verification: **54 Python tests passed**, including new parser, source-offset, historical-copy,
history pagination, feedback permission and tenant-isolation checks. **10 Playwright scenarios
passed** at http://127.0.0.1:8765, with desktop 1536×1024 and mobile 390×844 coverage.
Page identity, meaningful rendering, no framework overlay, console checks, exact clipboard,
alignment, draft preservation, reload, history filters, reopening, feedback and failure recovery
were exercised. Production frontend build and dependency lock validation passed.

Cloud Browser could not navigate localhost (net::ERR_BLOCKED_BY_CLIENT); the existing local
Playwright test route succeeded with installed Chromium. Current screenshots are
assets/refinement-comments.png, assets/refinement-history.png and assets/refinement-mobile.png.
The initial new browser test used an unsuitable exact label selector for the history filter;
using the rendered combobox role resolved the test failure. No clinical responses were simulated
as live AI: these UI tests use explicitly labeled demo cases. No paid provider calls were made.

The user reported successful Windows testing of **1.9.1**. This release was tested on Linux,
not Windows, and still needs user acceptance. Clinical quality, full accessibility, large-scale
history performance and production data lifecycle remain unvalidated. Prior release findings
below are historical. Skill contents remain unchanged at 0.1.1.

---

## Patch 1.9.1 / application 0.5.1: Windows and diagnostics

Fixed Windows inventory paths (`\` versus `/`) and locale-dependent skill/configuration
reads. Updated framework/content release metadata to 0.1.1; clinical instructions and
references are unchanged. Added safe terminal diagnostics, actionable configuration errors,
retry without reload, component status in Studio and an explicit OpenAI metadata check.

Verification for this patch: 46 Python tests passed, including Windows path-object regression,
explicit UTF-8 reads, real local database/DBOS checks, configuration failure codes, safe logging
and controlled provider success/authentication/unexpected-failure branches. Production frontend
build passed. No paid model requests were made for this patch. Provider probe tests use a
controlled client and do not claim live OpenAI connectivity. Tests ran on Linux; an actual
Windows machine was not available.

Three browser regression tests were added. Browser execution in this session was blocked by
an absent Chromium executable and an unavailable browser download; the eight browser tests
must be rerun with `npm --prefix frontend run test:browser` after installing Playwright Chromium.
The prior five-test browser results below describe release 1.9, not this patch.

The existing API version and durable workflow identity are retained: clinical processing,
step sequence and accepted snapshot semantics have not changed. Status is a snapshot of
local prerequisites, not continuous monitoring or a guarantee that inference will succeed.

# Skill-enabled prototype: implementation and verification

15 September 2026 · implementation 0.5.0 · bundle v1.9 · API 2026-09-15.

## Implemented

- Separate `qa-skills/framework` and `qa-skills/clinical-content` artifacts, with nine SKILL.md modules, references, registry and pinned digests. The qatr origin repository is unchanged.
- Stage-specific instructions replace embedded BASE/TASKS. Three model calls retain the five logical workflow steps.
- Full raw report and a source section index support required findings/impression plus optional history, indication, technique, comparison and addenda. Ambiguous multiple reports request clearer input. No summarization or clipping substitutes for the source.
- Private typed candidates enforce issue ownership, exact source quotes, unique IDs, critical basis and provisional policy boundaries. Public observations retain concise comments; source offsets and candidate mapping remain private.
- Exact instruction bytes, model settings, policy and skill versions are captured transactionally before durable dispatch. Changed installed content cannot silently affect an accepted review.
- Two independent group-copy buttons plus full-template copy. Original headings and flag semantics remain. Stale/disconnected output blocks copy and feedback.
- Versioned API cutover preserves historical receipts and compatible GETs. New creates and richer section labels require the new version. Tenant isolation and feedback idempotency remain.
- Local launcher prompts for a live key without saving it, defaults to Astra, and supports explicit demo mode. Built frontend is included.

## Technical verification

| Check | Result |
|---|---|
| Python suite | 39 passed: API/tenants/idempotency, skill grounding and integrity, controlled SDK, input/context limits and subprocess recovery |
| Actual process recovery | 3 passed, including original instruction hashes after installed content is changed to an invalid release |
| Browser scenarios | 5 passed: complete review, full/group clipboard equality, feedback, stale/restore, reload, missing input, failures, connection recovery and mobile |
| Production frontend | TypeScript/Vite build passed |
| Local launcher | Starts on loopback and serves built UI, configuration and API docs |
| Dependency lock | `uv sync --locked --offline` passed in the installed environment |

Python emitted one upstream Starlette/AnyIO deprecation warning. Browser setup required reinstalling a missing Chromium cache; the download mirror succeeded. Cloud Browser returned `net::ERR_BLOCKED_BY_CLIENT` for localhost, so the established local Playwright route was used. No relevant app console errors were recorded in successful live browser runs. Desktop 1440×1100/1536×1024 and mobile 390×844 were exercised; no horizontal mobile overflow was observed. This is not a complete accessibility audit.

## Genuine model evaluation

All provider tests used synthetic reports, actual OpenAI responses through FastAPI → DBOS → Agents SDK → DBOSRunner, with no mocked clinical responses. Test settings: low reasoning, 2,000 maximum output tokens per stage, standard service tier, zero HTTP retries. Interactive defaults are medium reasoning and 6,000 output tokens; those defaults were technically exercised with controlled SDK tests, not evaluated against the provider under this budget.

| Synthetic case | Sol | Astra |
|---|---|---|
| Clean chest report | Passed, no comments | Passed, no comments |
| Small-effusion laterality discrepancy | Passed, general only | Passed, general only |
| Tension pneumothorax + spelling correction | Passed on focused retest | Passed initially and on focused retest |
| Rich report with correcting addendum | Not run | Passed after parser fix, no actionable observations |

There were **25 new successful provider HTTP responses**, including the response associated with a rejected candidate. Ten application submissions were exercised: eight completed and met their proposed case checks; one initial Sol review failed source validation, and one rich report initially required input because of the parser bug. Failed attempts are preserved in the evidence bundle.

The initial Sol candidate failure did not produce copyable output. Host instructions were clarified to require null critical fields in noncritical stages; focused genuine Sol and Astra retests passed. The original rejected candidate was not retained, so its exact invalid field is not established. Later focused tests retain parsed private candidates for diagnosis.

The addendum case exposed a deterministic bug: prose saying “Correction to the Impression:” was parsed as a second heading. Recognition now anchors headings to line starts while retaining deliberate one-line Findings/Impression support. A regression test and a genuine Astra rerun passed.

The earlier live suite's general-to-critical misrouting was not observed in either model's current laterality case. This is evidence for those examples, not a precision/recall estimate or general clinical validation. The complete 25-case clinical-development set, long-report placement variants, qualified domain adjudication and prospective QA-user testing remain unperformed.

## Budget and evidence

The ledger preserves the earlier 20 attempts and adds 25 new ones. Across both testing periods:

- Base-rate token estimate for received responses: **$0.830038**.
- Conservative cumulative accounting, including higher cache-write rates and reservations for the earlier transport failures: **$1.263935**.
- Original user ceiling: **$2.00**; fail-closed transport admission threshold: **$1.80**. No additional paid requests after these tests.

These are ledger estimates, not an invoice reconciliation. Rates were checked against [official OpenAI pricing](https://developers.openai.com/api/docs/pricing). The separate evidence bundle includes synthetic inputs, API results, screenshots, provider request/response identifiers, token usage and the unchanged prior ledger entries. Credentials and runtime databases are excluded.

## Remaining boundaries

The prototype is ready for local UX and engineering trials. Clinical content remains provisional; no approved manual or catalog has been supplied. There is no image interpretation, report editing, external message/PACS/HL7 delivery, evidence UI, production data lifecycle or automatic learning. Source containment checks do not establish clinical truth. Same-code DBOS recovery does not establish arbitrary code-version replay or exactly-once provider billing.

Start with [LOCAL_TESTING.md](../LOCAL_TESTING.md). Review the original adoption proposal in WEB_APP_SKILL_ADOPTION.md alongside the current BLUEPRINT.md and API_DESIGN.md.
