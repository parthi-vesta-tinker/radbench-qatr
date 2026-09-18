# Foundation implementation decisions and releases

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
