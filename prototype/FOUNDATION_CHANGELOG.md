# Foundation implementation decisions and releases

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
