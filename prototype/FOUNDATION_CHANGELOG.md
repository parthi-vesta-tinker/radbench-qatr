# Foundation implementation decisions and releases

## Critical finding JEV classification — 2026-09-24

Application 0.15.0, bundle 1.21, API 2026-09-22, schema 8. Completed report
reviews admitted with JEV enabled automatically classify each critical comment through
one five-Choice JEV request. Reviews without critical comments never call JEV. The
classification workflow, attempt checkpoint, tenant-scoped receipts and feedback are
separate from report QA; report replacement does not rewrite the prior suggestion.
Public classification reads omit the private grounded report anchors retained in the
immutable provider input.
QA Studio shows the five labels, raw distributions and human feedback actions. The
rubric is explicitly draft research, urgency is a communication suggestion rather
than a care deadline. A nondefault urgency suggestion has a visible verification cue;
the synthetic live smoke test produced one such suggestion without an explicit report
communication instruction. Calibration starts uncalibrated. Local evaluation commands
support frozen data partitions, scoring, fitting and threshold exploration.

Schema-7 storage requires the explicit backed-up `upgrade_classification_storage.py`
command with applications stopped and no pending work. Controlled API/workflow,
migration and evaluation tests passed. A synthetic critical demo review completed
with one live JEV classification using a process-only credential; no OpenAI request
or clinical assessment was performed.

## Analytics findings and rolling periods — 2026-09-24

Simplify Analytics around saved review findings. The page shows counts of accepted comments
for inconsistencies, critical findings, clinical observations and other issues, followed by
submitted, completed and failed review counts. Private accepted check identities supply the
category when available; older/demo comments use their public group and finding type.
These are comment counts, not adjudicated clinical accuracy measures. Feedback and the
unmeasured clinical-performance fields remain in the API but no longer crowd the page.

The screen has one period selector with rolling 1, 6, 12 and 24 hour, 7 and 30 day, and
all-time windows. It requests all review sources so demo records are not silently hidden.
The optional API source filter remains for existing clients. The analytics response adds
finding counts; generated OpenAPI and TypeScript are synchronized. Schema 7 and the review
execution path are unchanged.

Verification: 37 affected API/reporting tests, 24 DOM tests, and focused Chromium analytics
checks passed with controlled data; production build, generated-contract checks and
documentation checks passed. No real-provider request or clinical adjudication was performed.

## Review History table labels and status presentation — 2026-09-24

Rename the Review History columns to Review ID, Report description and Submitted time. The
History table now renders every status with one neutral, equal-size label, so Completed and Failed
do not use different colour treatments. Progress and system-status presentation are unchanged.

Verification: 24 DOM tests and production build passed. No API, storage or provider behavior
changed.

## Review history and prior-review input handling — 2026-09-23

Review History now supports text/status/result/feedback filters, the last 24 hours, 3 days,
7 days or a custom submitted-time range, compact display IDs, submitter, last submitted time,
comments and feedback dialogs, and 20-item cursor pages. Re-review replaces the same current
record and timestamp. The reports rail is scrollable and displays each entry on one line with a
timestamp.

Input validation accepts an earlier Findings/Impression pair only when it is clearly preceded by
History or Comparison context; the final pair is supplied to the model as the current pair. Two
unmarked reports, mismatched labels and addendum-separated pairs remain blocked before any model
request. The one contextual input message now gives a plain warning icon and actionable wording
for missing or unscoped repeated sections. Local setup documents `npm run demo`, `npm run live`,
and the optional local operator name used in Review History.

Verification: 18 focused backend tests, 24 DOM tests, production build, generated API/TypeScript
checks and documentation checks passed. Demo startup used no provider call.

## Copy alignment and PACS comments — 2026-09-22

Align all three copy buttons with their headings using consistent sizing at desktop and
phone widths. Rename General comments to PACS comments in the workspace, playground and
copy formatting; omit display/copy numbering. Successful copy no longer emits a message.
Clipboard failure still exposes a manual fallback. Historical UI copy projection regenerates
text from observations, excluding old QA review prefixes and numbering without changing stored
results or replay receipts. Internal general_comments field names remain compatible.
Verification: production build, 21 affected backend tests, 22 component tests and the
clipboard/reload browser scenario passed, including all three copy actions and alignment at
1536/390/320px. Mobile screenshot inspected. No real-provider calls.

## Service health presentation redesign — 2026-09-22

Apply the supplied Service Health Redesign Spec: timestamped header refresh, actionable
check disclosure, compact name/status rows, and an inline OpenAI check icon. Remove routine
row descriptions and diagnostic disclaimers. Explicit probe results update the OpenAI pill
and summary, while failures retain actionable detail. No backend or API behavior changed.
Verification: production build, 22 component tests and 5 diagnostics/header browser tests
passed. Browser fixtures cover explicit-only probes, failure/retry, refresh timestamp and
probe reset, keyboard expansion and 1280/390/320px light/dark layouts. Screenshot inspection
caught inherited button sizing, which was corrected and verified against the rebuilt UI.
No real OpenAI requests or clinical evaluation.

## Combined release verification before commit — 2026-09-22

Full backend suite: 135 passed. Direct component suite: 22 passed. Full browser suite:
15 passed and one outdated feedback-location selector failed after the requested move below
the title; corrected that selector and all three panel checks passed on rerun. Production
build, generated contracts, documentation and source bundle checks passed. Controlled fixtures
only; no real-provider calls or clinical assessment. Release remains 0.14.0 / bundle 1.20.

## Review context placement and shorter stages — 2026-09-22

Rename Awaiting inputs to Input and Input check to Validate. Move the single contextual
message below the review title and above the report field, preserving its live status/alert
semantics and restore action. The journey stays beside Review. Production build and the
replacement browser scenario passed, including placement/alignment checks at 1536, 390 and
320px. Mobile screenshot inspected. No backend or contract changes.

## Single unfinished Current review — 2026-09-22

Remove numbered draft rows, draft deletion and Undo. Keep one unfinished report per tab,
reusing it when New review is selected again. Current review restores that unfinished input
when returning from a saved report. Pending and uncertain submissions retain their original
text and idempotency key. Saved review history and Skills editorial drafts are unchanged.
Production build, 22 direct component tests and 9 targeted workspace/panel browser tests
passed. No backend, API or database changes, and no provider calls.

## Compact monochrome review journey and outcome removal — 2026-09-22

Remove stakeholder outcome controls, endpoints, contract schemas and acceptance analytics.
Legacy outcome storage stays dormant for schema-7 compatibility; no additional migration.
Copy projections omit the UI-only QA review prefix. The four stages Awaiting inputs,
Input check, AI review and Output sit beside Review, with a single contextual message below.
The interface is monochrome, with warning color reserved for progress problems.

Verification: 33 affected backend tests, 22 direct component tests and all 16 browser tests
passed, as did the production build and generated OpenAPI/TypeScript checks. Browser checks
cover four stages, button alignment at desktop/390px/320px, removed outcome controls and
copy without the title prefix. Mobile screenshot inspected. No real-provider calls or
clinical evaluation were performed.

## Latest-state report reviews and single journey — 2026-09-22

Application 0.14.0, bundle 1.20, API 2026-09-22, schema 7. Explicit user decision
supersedes immutable report-resource/history behavior: Review again replaces the same
review ID with the latest report text, submission time and outcome. No parent-linked
report snapshots or additional draft/history entry are created. Acceptance clears the
old result, observations, configuration snapshot and provider checkpoint atomically.
Review-level feedback survives; prior stakeholder outcomes are cleared so old acceptance
cannot apply to corrected text. History and analytics read the single current projection.
An internal input_version counter fences stale submissions/workers; queued/running work
cannot be replaced. Idempotency receipts and DBOS operational checkpoints remain for safe
replay and recovery, not as a report version-history feature. Comment-specific feedback
retains its quoted comment as feedback context without a result foreign key.

Rename the sidebar and mobile controls to Report reviews and Current review. Remove the
Report text only badge and permanent input instruction. Contextual feedback reports pasted
text, edits and uncertain submission; stale output cannot be copied. The single horizontal
journey below it is New review, Awaiting inputs, Input check, AI review, Output. Output covers
output validation and comment assembly; those remain separate backend phases. Complete,
needs-input and failed states use ticks, warning and blocker icons. Remove both duplicate
progress displays; Studio guidance remains.

Schema-6 storage is upgraded only with scripts/upgrade_review_storage.py while stopped,
with no pending live/playground work. It backs up SQLite, retains existing independent
reviews and feedback, and validates foreign keys. Existing records are not inferred or
merged. No running user database was upgraded during implementation.

Verification: production build, generated OpenAPI/TypeScript drift checks, 24 directly
executed DOM tests and all 16 browser tests passed. Full Python suite: 134 passed with one
legacy configuration-equality assertion updated for the concurrency counter and passed on
rerun. Final 10 targeted replacement/storage tests passed, including the additional pending
upgrade refusal, outcome invalidation and foreign-key checks. The full suite included
controlled DBOS process-recovery tests. Desktop, 390px and 320px journey screenshots checked.
All execution used demo fixtures or provider doubles; no real-provider or clinical evaluation.

## Secondary workspace typography — 2026-09-22

Extend the shared hierarchy to history, Feedbacks, Analytics, Skills and Playground.
Group filter controls, increase metadata readability, standardize empty states, and
stack history entries with column labels on phones. Keep source editors monospace and
all saved-review, feedback, editorial and playground boundaries unchanged.

Verification: production build and DOM suite passed. All 14 existing browser tests passed;
the additional section navigation/layout check passed separately at 1536, 390 and 320px
using keyboard activation after its first pointer-based run encountered an overlapping
tooltip. Desktop/mobile screenshots inspected. Demo fixtures only, no provider calls.

## Application identity and typography — 2026-09-22

Promote Radiology Report Review as the application title with a secondary Vesta label beside
the supplied logo. Rename the draft heading and Studio action to New review, including collapsed
tooltips. Keep the system font with consistent work/panel/subsection sizes, larger tool labels
and report input, and aligned panel heading spacing. At narrow widths, header actions move to
a second row so the full application name stays readable.

Verification: frontend production build, DOM suite and four targeted Playwright header/panel
checks passed. Desktop and mobile screenshots inspected. Demo fixtures only; no provider calls.

## Branded header and Studio notice — 2026-09-22

Use the user-supplied Vesta icon in the header and favicon. Group Share and Settings placeholders,
Health and appearance as top-right icons; the first two have no functional action. Health keeps
its existing read-only diagnostics and dismissal behaviour behind an icon trigger. Add a
single-line dismissible Studio feature notice without a Try it action. Panel artwork was subsequently
corrected against the user's close-up references: rounded outline and inset bar when expanded,
inset opposite-side bar and inward chevron when collapsed, mirrored for the left panel. The shared
Google glyph was removed. No external font request, backend contract or workflow changes.

## Collapsible workspace panels — 2026-09-22

By user request, rename the QA Studio tool and destination to Skills and give it the same tile
placement as the other tools. Reports and QA Studio gain independent desktop rails and
responsive mobile drawers. Collapsed controls retain explicit hover/focus tooltips and accessible
names. Collapse preserves mounted editorial state and the selected report; the center retains
review status when the full phases are hidden. Desktop preferences persist separately from
temporary compact/mobile layout state. This changes presentation only; no API, clinical content,
storage schema or workflow identity changes. See [WORKSPACE_SPEC.md](WORKSPACE_SPEC.md).

## Explicit public access — 2026-09-21

By user request, `QA_AUTH_MODE=public` permits unauthenticated remote access through Funnel
to the shared Vesta tenant with all scopes. The default remains loopback-only `local`;
`api_key` keeps credential-scoped tenant access. Caller-controlled tenant overrides remain
rejected. Forwarded client addresses are preserved rather than disguised as loopback.
This is an access configuration change; API payloads, schema and workflow identities are unchanged.
See [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for controlled verification.

## QA Studio playground — schema 6 / bundle 1.19

Implemented 2026-09-19 as P2 of [SKILL_PACK_SPEC.md](SKILL_PACK_SPEC.md). The shipped contract is
Part one of [PLAYGROUND_UX_SPEC.md](PLAYGROUND_UX_SPEC.md). Application version, API version and
workflow identities for live review are unchanged.

Scope was set by explicit user decision: curated samples in two categories plus paste-your-own,
run the real review, show results and a phase log. No editing, no output comparison, no history,
feedback or analytics. Skills are presented as one read-only set.

- A sixth Studio tool. `GET /api/v1/playground`, `POST /api/v1/playground/runs` and
  `GET /api/v1/playground/runs/{id}` are additive; the generated OpenAPI gained 264 leaves and
  changed or removed none.
- Live review and the playground now share one execution path, `workflow.py:execute`. Only the
  state sink differs, so a playground run exercises the real four phases instead of a copy that
  could drift from them. `run_review` behaviour is unchanged.
- A separate `qa-playground-f3-v1` queue and the `qa.playground.f3.v1` workflow. A test run
  cannot consume live review concurrency.
- `playground_attempts` mirrors the live provider checkpoint, because `model_attempts`
  references `review_records` and a playground run has none. `attempts.py` takes the table as a
  parameter rather than being duplicated, so both paths keep one implementation of the
  claim/response/unknown rules.
- Schema 6 reshapes `playground_runs` for this design: the workspace link and the draft-only
  `pack_ref` constraint from schema 5 are gone, and model, mode, phase log and error are stored.
  Runs regain a workspace link when editing arrives. Fresh default `.qa-data-foundation-v5`.
- Sample text is read from the hash-pinned `evaluation/cases.json` rather than copied, and
  `demo_supported` is computed from the text the canned demo path matches rather than declared,
  so the catalog cannot advertise support that does not exist.
- The playground model list is server controlled and offers `gpt-6-astra` only; choosing it never
  changes the live model, and the screen says so when the two differ.

Not built, by decision: no baseline or output diff, so regression is read by a person; no
instruction editing, so P1's draft pack composition is still unexercised.

## Pack references and skill workspaces — schema 5 / bundle 1.18

Implemented 2026-09-19 as P1 of [SKILL_PACK_SPEC.md](SKILL_PACK_SPEC.md), with the interaction
model in [PLAYGROUND_UX_SPEC.md](PLAYGROUND_UX_SPEC.md). Application version, API version and
workflow identities are unchanged: no workflow shape, recovery semantic or public contract moved.

- `load_snapshot` takes a pack reference. `published` is today's verified read. `draft:<workspace>`
  overlays that tenant workspace's saved skill drafts and is stamped
  `draft:<workspace>@<pack-hash>`. Live report QA resolves `published` only, and `packs.py` refuses
  a draft reference on that path.
- Pack identity is derived, not hardcoded. A tenant binds a *profile* (`vesta-qatr`, `generic`);
  the version is read from the installed package. Bindings still resolve to `vesta-qatr-0.3.0` and
  `generic-0.3.0`, and a configured pin is refused when the installed pack does not carry it.
  The three hardcoded `0.3.0` constants are gone.
- Schema 5 adds `skill_workspaces` and `playground_runs` and scopes `knowledge_drafts` by
  workspace. A draft saved outside a workspace is an editorial record that still never composes.
  The default store moves to `.qa-data-foundation-v4`; a schema-4 store is refused, never migrated.
- A workspace pins the published pack it forked from. When live moves past that pin, composition is
  refused until an explicit rebase, which preserves saved revisions, clears stored runs, and returns
  a submitted workspace to open.
- Only skill instructions are composable. A workspace draft targeting the frozen catalog or pinned
  source wording is refused at composition rather than silently dropped.

There is no playground interface, no run endpoint and no output diff yet; those are P2.

# Spend removal — 2026-09-18

Removed by explicit user decision: "spending is not a problem", after the running application
rejected a review with `SPEND_LIMIT_EXCEEDED`.

Deleted `backend/spend.py`, `scripts/authorize_spend.py` and `tests/test_spend.py`. Removed the
reservation step from review acceptance, claim/settle from the guarded dispatch path,
`release_unclaimed` from failure handling, the `--spend-session` requirement from the launcher,
and `cost_upper_bound_micro_usd` from reported metrics. `model_attempts.reservation_id` is now
`attempt_id`; the column is written positionally, so existing databases are unaffected and
`SCHEMA_VERSION` is unchanged.

Retained: the context-window guard (`REVIEW_CONTEXT_TOO_LARGE`), at-most-once dispatch claims,
durable response checkpoints, `MODEL_OUTCOME_UNKNOWN` with no automatic retry, and observed
token usage as observability. `attempts.uncertain()` now decides from the attempt checkpoint
alone: the claim is written before dispatch, so no row means the provider was never called.

Verification: 100 passed, 1 deselected. The deselected case,
`test_public_schema_and_generated_client_do_not_drift`, fails identically on the unmodified
tree in this container — FastAPI renders 422 as "Unprocessable Entity" where the checked-in
`prototype/openapi.json` says "Unprocessable Content". Unrelated to this change and left alone.

## F3 — Durable single-call execution — application 0.13.0 / bundle 1.17

Implemented 2026-09-18. API **2026-09-18**, SQLite schema **4**, workflow application
`foundation-f3-0.13.0`, queue `qa-reviews-f3-v1`, parent `qa.review.f3.v1`, child
`qa.openai.combined.f3.v1`. Fresh default `.qa-data-foundation-v3`; no existing databases
were reset or migrated. Pinned clinical content remains 0.3.0 and its hashes are unchanged.

The session spend ledger described below was removed on 2026-09-18; see **Spend removal** above.
Everything else in this entry still describes the installed behavior.

### Behavior and recovery

- One combined, tool-free structured request through the existing Agents SDK/DBOSRunner.
  Complete source/catalog bytes, all selected skill instructions and the output contract
  are captured before acceptance. Local input rejection makes zero model calls.
- Atomic session-ledger claim executes inside the actual model method, beneath DBOS's
  checkpoint boundary. Transport retries are disabled. A claim without a saved response
  fails `MODEL_OUTCOME_UNKNOWN`; no automatic retry or repair call is permitted.
- Private immutable model response checkpoints precede parsing and retain usage/response IDs.
  Recovery reuses them even if the DBOS model checkpoint was interrupted. Completed response
  status is checked before the SDK drops it. Refusal, tool output, malformed JSON, missing
  coverage and invalid grounding are non-successful results, never empty successes.
- Deterministic validation requires complete skill coverage and globally unique candidate IDs,
  validates check ownership and exact source anchors, and preserves the two copy groups.
  Canonical results and terminal state still commit atomically and finalize idempotently.
- Four truthful phases replace three separately timed model stages: input validation,
  combined report review, output validation and comment assembly. Skills Studio shows
  combined usage; saved drafts still never activate instructions. Unknown usage/cost is null.
- A separate `.qa-spend/ledger.sqlite` records explicit expiring per-test-session authorization,
  stable reservations, dispatch claims and conservative charges. API retries recover original
  receipts; orphan admission reservations are reused without doubling or silently refunding.
  Resetting review/DBOS storage cannot renew authority. Missing ledgers/sessions fail closed.
- Each session has its own ceiling, currently capped at $1. All concurrent calls within that
  session share it. New sessions require separate authorization. Prices verified against
  https://developers.openai.com/api/docs/pricing on 2026-09-18 expire 2026-10-18. Standard
  endpoint/tier only; complete serialized request/schema, output/reasoning limit, maximum
  long-context/cache-write rates and 10% headroom determine admission. These are conservative
  cost bounds, not invoice reconciliation or an account-wide provider billing guarantee.
- `authorize_spend.py` creates explicit authority; `run_local.py --spend-session ...` reuses it.
  The old direct three-stage evaluation executor is retired so it cannot bypass this ledger.
  The API-driven evaluation runner uses the guarded path. Metadata diagnostics run no inference.

### Verification and remaining gates

Final full regression run: **107 Python tests passed** after checkpoint/error hardening.
Real process termination/restart covered before claim,
after claim, after provider response, after application response checkpoint, after combined
completion and after final commit. Controlled concurrency tests verified session admission and
same-key POST replay. The actual HTTP adapter was exercised with a local mock, including HTTP
500, incomplete response, refusal, missing usage, unknown tools and invalid check coverage.

Dependency lock, generated OpenAPI/TypeScript, clinical-package hashes and bundle validation passed.
TypeScript/Vite production build and the React DOM suite passed. Eight Playwright scenarios
passed using local Chromium, including F3 phase labels, exact copy groups, reload, narrow layout,
drafts, Skills Studio saves and analytics. Two historical exact-label selectors were updated
using observed accessible roles; no product behavior was changed to satisfy them. Desktop/mobile
screenshots were inspected. These are controlled/canned tests, not clinical evaluation.

No paid OpenAI requests were made: actual provider spend **$0**. A key supplied in chat was not
saved or used; the foundation plan requires rotation of exposed keys before future live use.
F4 handoff/product acceptance and F5 authorized clinical/model evaluation remain separate gates.
Same-build recovery is established; no arbitrary cross-version recovery or clinical quality claim.

## Windows source-checkout launcher fix — application 0.12.0

The Git source archive excludes generated `frontend/dist`, while earlier startup wording said
the built UI was included. The local launcher now detects a missing UI and runs the locked npm
install and production build before prompting for the API key. It resolves `npm.cmd` on Windows,
does not invoke npm when a build exists, and reports PATH or npm failures directly. This changes
local setup only; it makes no model call and does not alter the F2 content or runtime contract.

## F2 — Content and snapshots — application 0.12.0 / bundle 1.16

Implemented 2026-09-17. Content/framework 0.3.0; API 2026-09-17 and SQLite schema 3.
Workflow application identity `foundation-f2-0.12.0`; fresh default `.qa-data-foundation-v2`.
No existing database was reset. User explicitly requested proceeding while F1 publication
was pending; this supersedes the publication-before-next-phase sequencing note below.

### Key decisions

- Import the three qatr references byte-for-byte at commit
  `b906151a2bdef8c206325de64d46b61cdf5b7ad7`. Preserve CRLF in the catalog using Git attributes.
  Check original Git blob IDs, SHA-256 inventory, 43 ordered source labels and shared-rule IDs.
- Separate source wording, draft catalog and proposed guidance authority. No new clinical
  approval, thresholds, notification SLA checks or automatic external actions are introduced.
- Use two immutable content profiles over one verified package: `vesta-qatr-0.3.0` includes
  Vesta references; `generic-0.3.0` excludes them. Backend tenant configuration controls binding;
  the local Vesta default selects qatr, all other tenant defaults select generic.
- Preserve independently versioned skills. Shared scope, critical match and verification move
  to 0.3.0; unchanged modules remain 0.2.0. Fix stale provenance/adoption claims in this release.
- Capture exact selected reference bytes, hashes, profile and deduplicated combined instructions
  in immutable review snapshots. Gate/evaluation/changelog/draft content is not sent as instructions.
  Current runtime still performs three stages; F3 owns combined dispatch and spend enforcement.
- Extend Skills Studio with catalog/source document kinds through existing revision, draft,
  comparison and export APIs. Tenant drafts never change installed instructions or old snapshots.
- Validate catalog ownership, exact source label, rule IDs and report exception anchors privately.
  These checks prove attribution only; model interpretation still needs qualified evaluation.
- Bound the complete combined request without clipping. A reusable allowance check rejects
  insufficient input budgets, but authorization, pricing and durable ledger integration remain F3.
- Add six proposed catalog interpretation fixtures spanning qualifiers, exceptions, negation
  and compound diagnoses, with separate development/held-out partitions. None is adjudicated.

### Verification

- 83 Python tests passed, including controlled SDK and real DBOS subprocess recovery checks.
- 19 React DOM tests passed; TypeScript and Vite production build passed.
- Exact upstream Git blob identities, source/catalog inventory, tenant/draft isolation,
  attribution/exception grounding and complete-request bounds passed.
- Dependency lock and generated OpenAPI/TypeScript checks passed. Skill package contains
  48 verified artifacts, 54 proposed atomic cases and 25 cross-stage fixtures; six new
  catalog interpretation expectations are proposed and were not model-evaluated.
- No paid model calls, clinical evaluation, browser-layout acceptance or production deployment.

## F1 — Contracts and fresh schema — application 0.11.0 / bundle 1.15

Implemented 2026-09-17. API version 2026-09-17; SQLite schema 3; workflow application
identity `foundation-f1-0.11.0`. F2 content and F3 single-call execution are not included.

### Key decisions

- Bootstrap empty storage; reject any nonempty older schema without rewriting its records.
  Default data directory is `.qa-data-foundation-v1`. No existing database was deleted.
- Store accepted input/state in `review_records`, exact hashed configuration in
  `review_snapshots`, immutable result metadata in `review_results`, and canonical ordered
  observations in `observations`. `reviews` is a read-only SQL view, not a stored API document.
  This preserves existing reporting modules without retaining a historical storage adapter.
- Keep flexible metadata as JSON, with relational tenant identities, result/observation foreign
  keys, state checks and indexes. Snapshot, input and completed-result updates are guarded.
  Snapshot decoding checks exact stored-byte integrity through a private typed record.
- Store result-specific copy strings with immutable metadata to pin formatting; public current
  copy remains server-derived. Canonical observation lists are not duplicated in result metadata.
- Use one supported public API version, including the omitted-header default. Remove old
  projection/upgrade branches and duplicate review/feedback ID aliases; `id` is canonical.
  Parent references remain `review_id`; observation/outcome/draft identifiers keep their distinct
  existing names. This is a coordinated client/server prototype cutover, not a compatibility layer.
- Generate TypeScript from actual OpenAPI. UI aliases contain no duplicated wire shapes.
  The strict small generator covers this contract's JSON Schema subset and rejects unsupported
  constructs. CI checks OpenAPI/type drift and runs controlled backend/DOM/build checks.
- Source manifests exclude ignored build outputs; build the frontend from its lockfile after
  checkout. All `.qa-*` runtime directories are ignored by Git and excluded from source packages.
- Preserve current UI features and the existing three-call workflow until F3. Skill package
  bytes remain 0.2.0. This phase does not claim the future spend guard is installed.

### Executed verification

- 78 Python tests passed, including actual SDK controlled-output integration and DBOS
  subprocess restart tests, schema rejection, tenant/result/observation foreign keys,
  concurrent receipt/snapshot acceptance, immutable finalization and generated contract drift.
- 19 React DOM tests passed; TypeScript and Vite production build passed.
- Dependency lock check and unchanged installed skill-package validator passed.
- No live model calls, clinical evaluation, browser-layout acceptance or production deployment.

The GitHub workflow is supplied, not claimed executed remotely. Phase publication is recorded
by its Git commit; the next phase must not start before successful publication. No force push.

## Next gates

F2 is implemented; see the current release above.
F3: one combined DBOS request, at-most-once dispatch and independent session-spend ledger.
F4: integrated product/browser regression and operational handoff.
F5: separate explicit authorization for bounded live evaluation and qualified review.
