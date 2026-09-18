# Clean-start foundation implementation plan

Decision revision: 2026-09-17. Status: F1–F3 implemented in 0.13.0; F4/F5 remain pending.
See [foundation changelog](FOUNDATION_CHANGELOG.md) for decisions and executed tests.
Baseline inspected: bundle 1.14 / application 0.10.0. This document is the authority for the
next build; [implementation status](IMPLEMENTATION_STATUS.md) remains the authority for what
has actually been built and tested.

## 1. Scope and decisions

Keep the working product; simplify its foundations. Reuse FastAPI, SQLite, DBOS, the OpenAI
Agents SDK/DBOSRunner integration, and the existing React workspace. Do not introduce a
microservice, agent platform, ORM rewrite, vector database or generic workflow engine.

| Area | Next-build decision |
|---|---|
| Existing data | Disposable prototype data. Bootstrap fresh application and DBOS databases; no historical migration, old receipt import or cross-version workflow recovery. |
| Existing capabilities | Preserve review history, feedback inbox, stakeholder outcomes, analytics, Skills Studio drafts, two-group copy and workspace interactions. Test them on fresh records. |
| Review execution | One combined model request for an admitted, valid report, orchestrated by DBOS. Invalid input can use zero requests. No parallel clinical agents, second-pass verifier or automatic repair call. |
| Skills | Preserve independently versioned modules; compose their relevant instructions into one request. Modules are knowledge/check ownership, not separate model executions. |
| Critical references | Import qatr's three pinned reference artifacts and complete 43-entry catalog. Preserve the distinction between source text, normalized catalog and proposed matching guidance. |
| Tenant isolation | Authenticated tenant owns data, draft history and explicit active-package binding. Never accept tenant/package overrides from report text. |
| Extensibility | Public API models, private model-output models and database records have separate responsibilities. Version their contracts explicitly without building legacy adapters now. |
| Spend | Not modelled in the application. Removed by explicit user decision; provider cost is managed in the OpenAI account. A request that cannot fit the context window is rejected before dispatch, never clipped. |

Old instructions to preserve completed rows, historical API projections or pending old workflows
are superseded for this cutover only. Durable recovery, receipt replay and immutability still
apply to reviews created within the new build. Disposable old data does not mean disposable
history functionality or permission to silently reset data on startup.

## 2. Architecture aligned to the current code

Use a small modular monolith. Split files when responsibilities need independent tests, not
to create layers with no behavior. Keep existing implementation until its replacement passes.

| Boundary | Responsibility and current touchpoints |
|---|---|
| HTTP contracts and routes | `backend/contracts.py`, `backend/main.py`, `backend/presentation.py`: validated inputs, public projections, status codes, error envelope, auth and idempotency. Routes delegate use cases. |
| Application services | Extract review acceptance, feedback/outcome recording and draft saving from route/store coupling into small services. Services define transaction boundaries and accepted configuration. |
| Persistence | `backend/store.py`: explicit SQLite schema, typed row mapping, tenant-scoped queries and atomic state transitions. Split review/knowledge queries only where useful; no abstract repository framework. |
| Durable orchestration | `backend/workflow.py`: queue, deterministic workflow identity, local validation, one model boundary, validation/assembly and final persistence. DBOS owns execution/recovery. |
| Content composition | `backend/skill_runtime.py`: verify installed release, resolve tenant binding, compose stable instructions, snapshot exact bytes and validate reference relationships. |
| Provider adapter | `backend/reviewer.py`: one tool-free structured request using existing Agents SDK + DBOSRunner; transport retries disabled and an at-most-once dispatch guard. |
| Browser | Generated API types and one API client; retain current Workspace, Analytics and Skills Studio. No direct DBOS, provider or database access. |

DBOS system storage is private to DBOS. Application tables remain the public resource source
of truth. Use one configured local queue with bounded concurrency; do not create one worker
or database per tenant. Every workflow argument, lookup and result write carries tenant context.
Reuse `backend/knowledge.py`, `backend/outcomes.py` and `backend/reporting.py` for their existing
feature responsibilities; adapt persistence beneath them rather than replacing these features.

## 3. API-first contract

Design Pydantic request/response models and endpoint examples before changing persistence or UI.
Generate OpenAPI from those models and TypeScript types from OpenAPI. Commit generated artifacts;
CI regenerates them and rejects drift. Do not hand-edit `prototype/openapi.json` to advertise
unimplemented behavior. Keep private provider schemas outside the public API models.

Keep `/api/v1` resource families. Select a single new `QA-Version` at implementation cutover,
pin it in the bundled browser, reject unsupported explicit versions and use that same version
when the header is omitted. No legacy default/projection branch in the fresh build. Use one
canonical `id` per resource; remove redundant aliases only with coordinated client/test changes.

| Resource | Contract to retain or establish |
|---|---|
| `POST /api/v1/reviews` | `report_text` only; request-level idempotency key; server-resolved tenant, model and release. Return durable `202`, `Location` and immutable original receipt. |
| `GET /api/v1/reviews/{id}` | Stable resource with execution status, truthful progress, safe provenance, error and nullable result. Never expose DBOS internals or full prompts. |
| `GET /api/v1/reviews` | Tenant-scoped filtered history; bounded, stable cursor pagination. Whole-database analytics must not reuse this page as its denominator. |
| Feedback and outcomes | Retain existing per-review routes, feedback inbox and append-only stakeholder outcomes; references bind to the immutable review/result/observation. |
| Knowledge and drafts | Retain installed-content view, tenant drafts, optimistic revision/hash checks and export. Draft writes never activate runtime instructions. |
| Analytics | Keep operational aggregates and explicitly unmeasured clinical metrics; include real review-level calls, tokens and cost where known. |
| Health/config/diagnostics | Retain safe health/configuration surfaces; model probes count against the same authorized spend and are not automatic startup checks. |

Resource states remain `queued`, `running`, `completed`, `needs_input`, `failed`. A completed
result is immutable; all other states have `result: null`. An ambiguous provider attempt is
`failed` with `MODEL_OUTCOME_UNKNOWN`, not an empty successful review. Do not replay it implicitly.
Transport failure while fetching a resource is different from a resource whose execution failed.

Retain the existing structured error envelope, request IDs, authorization scopes, bounded list
limits and tenant/filter-bound cursors. Reject unknown request fields. Define nullable versus
omitted fields and UTC timestamps explicitly. Schema changes must update fixtures, examples,
frontend types and errors together; do not return arbitrary stored dictionaries as API responses.

Idempotency is scoped to tenant + operation + key, with a canonical request/version fingerprint.
Look up an existing receipt before rechecking mutable content/model readiness. Same key and body
returns the original status/body/Location; changed body yields conflict. A POST retry must not
create another review, reserve additional spend or invoke the provider again.

## 4. Small, explicit data model

Use SQLite now. Keep a single bootstrap DDL and `schema_version`; startup opens a matching schema
or fails with an actionable reset/version error. No automatic destructive recreation, startup
ALTER chains, historical migrations or dual database implementation. Add a migration tool when
retained data becomes a product requirement. Portability comes from clear queries and contracts,
not implementing PostgreSQL before it is needed.

Proposed logical tables below are the starting schema, not an instruction to copy old serialized
API resources. Most extend existing concepts; snapshots and attempts make important boundaries explicit.

| Table/group | Important fields and invariants |
|---|---|
| `tenants` | Tenant ID and configured active release binding. Binding is server-controlled and references verified installed content; initially configured explicitly, not browser-published. |
| `reviews` | Tenant + ID, raw report/hash, snapshot ID, optional predecessor review ID, state, phase, timestamps, safe failure code, API version, dispatch state. Queued rows also serve as the transactional outbox. |
| `review_snapshots` | Tenant + ID/hash; exact composed instructions, selected skill/reference bytes, catalog/source hashes, tenant binding, schema version, model/settings and budget-reservation reference. Immutable after acceptance. |
| `review_results` | Tenant + result ID, unique review ID, result-schema version, summary/coverage and completion metadata. No result row until validation succeeds. |
| `observations` | Tenant + observation ID, result ID, ordered group, comment, finding type, section and private validated source/rule/check attribution. Canonical observation data lives here, not in a duplicate result JSON list. |
| `feedback` | Immutable feedback ID, review/result and optional observation target, reason/text, actor and timestamp. Not a clinical reference label. |
| `outcomes` | Append-only stakeholder decision with result/observation target, actor and timestamp; latest applicable event determines the current view. Retractions remain explicit. |
| `knowledge_drafts` | Tenant/document/revision, immutable draft bytes, parent revision, source/package hash, author and time. Unique revision and compare-and-swap save. |
| `idempotency` | Tenant/operation/key uniqueness, request fingerprint, original response and acceptance metadata. No cross-tenant receipt reads. |
| `model_attempts` | Unique tenant/review attempt, dispatch claim, provider request/response ID if available, usage, output/checkpoint reference and terminal outcome. Never a general event-sourcing framework. |

Budget authorizations/reservations belong to a small durable spend ledger outside disposable
review and DBOS storage; see section 7. Installed packages remain immutable files with a manifest,
not a new content registry service or dozens of database rows for the 43 catalog entries.

Use relational columns for identities, joins, permissions, states, timestamps and frequent filters.
Use versioned JSON for variable snapshot/model metadata and source anchors, not a copy of the
entire mutable HTTP resource. Derive clipboard strings and public arrays through one presenter
from persisted canonical results; pin its result/presentation version for accepted reviews.

Enable foreign keys on every connection, use tenant-inclusive composite foreign keys, uniqueness
constraints and guarded state updates. Index tenant/time/ID history, tenant/state dispatch,
feedback targets and outcome subject/time. Use transactions and appropriate SQLite busy timeout/WAL
settings; validate concurrent acceptance and draft saves. Do not hold a SQL transaction while
waiting on OpenAI or DBOS dispatch. Test query plans on a moderately sized synthetic fixture.

## 5. qatr content and tenant-scoped authoring

Pin the reviewed source revision `b906151a2bdef8c206325de64d46b61cdf5b7ad7`; do not pull latest at
runtime. The three source files were checked through GitHub for this plan:

| Artifact under `qa-critical-match/references/` | Authority |
|---|---|
| `critical-result-notification-source.txt` | Supplied source wording; controls interpretation when derived annotations conflict. Preserve raw bytes and hash. |
| `critical-rules.json` | Structured catalog with 43 entries, source labels/locators and shared requirements. Preserve identifiers and approval/uncertainty metadata; it is marked `draft_for_review`. |
| `matching-guardrails.md` | Proposed matching guidance, expressly not policy. Preserve qualifiers, uncertainty and known-finding exception handling without inventing thresholds. |

The catalog has 43 entries, not 43 independently approved source documents. Clinical approver,
effective date and source version are absent in the inspected metadata. Import for explicitly
labeled prototype evaluation; do not label it clinically approved or activate it for real care
merely because it is in the repository. Verify source terms and obtain clinical-owner approval
before production use.

The runtime prompt includes the complete source, catalog and matching guidance, with authority
labels, alongside the applicable existing skills and whole report. No runtime retrieval, keyword
catalog pruning, summarizing model or hidden second call. Deduplicate shared instructions; exclude
evaluation cases, changelogs and draft documents. If the complete request cannot fit context or
budget, reject it before dispatch rather than clipping report or catalog entries.

Treat `qa-input-adequacy` as a local structural gate; combine language, consistency, clinical
question, recommendation, critical matching, drafting and verification modules in one instruction
bundle. Preserve check IDs and independent content versions even though runtime stages collapse.
The Agents SDK does not discover these files: the host loader sends their selected bytes as
trusted instructions; the report/section index is separately delimited untrusted input.

For critical observations retain catalog ID when applicable, match confidence, exact source
anchors and exception evidence privately. Unknown IDs, invalid ownership or ungrounded quotes
fail deterministic validation. Clinical equivalence, qualifier meaning and semantic duplicates
require evaluation; local validation cannot prove them. Out-of-catalog concerns stay visible as
radiologist-review questions, never silently promoted to confirmed policy violations.

Notification timing/documentation clauses are preserved source context, not new SLA checks,
proof of a missed call or permission to notify anyone. This follows the source catalog's explicit
runtime exclusions. The known-finding exception must not cause invented doctor judgment or an
automatic repeat-call instruction. Preserve two comment groups; do not restore the retired
missed-flag selector or clipboard line as a side effect of importing qatr.

Retain tenant draft editing, comparison, revisions and export. Add reference/catalog document
kinds to the same knowledge model; no separate policy-management product. Initial activation is
an explicit server-controlled tenant-to-immutable-release binding. Browser publishing/approval
and rollback UI can wait. Drafts and feedback never enter runtime automatically. Accepted reviews
keep their snapshot even when a binding changes. Test two tenants with distinct bindings/drafts.

Release the adapted content as a new package with updated registry, schema, lock, provenance,
changelog and affected evaluations. Fix stale 0.1.0/three-stage adoption wording during that release,
not by editing hashed files beneath the installed 0.2.0 release in a planning-only change.

## 6. One-call DBOS workflow and failure semantics

Acceptance resolves the authenticated tenant, validates request structure, verifies content and
model readiness, composes a bounded snapshot and obtains budget reservation. One application
transaction saves review + snapshot + queued dispatch state + original 202 receipt. Dispatch
after commit; the existing reconciler can redispatch queued work with the same workflow ID.
An accepted resource must remain discoverable after a process crash.

DBOS sequences local input validation, combined model review, deterministic output validation,
assembly and final commit. Visible progress follows these real phases; skill names are check
coverage, not fabricated independently timed stages. Completed result/observations and terminal
review state commit atomically. Repeated local finalization must be idempotent.

Retain Agents SDK `OpenAIResponsesModel` through `DBOSRunner`, one turn, no tools/handoffs or
model-backed guardrails, and transport retries disabled. The private output model contains all
check coverage and candidate observations in one response. Refusal, incomplete/truncated output,
schema/grounding failure or unknown provider outcome is an explicit non-success, not a request
to call another model to repair the answer. Keep tracing/report storage controls explicit.

One model call is also a failure-policy requirement, not just `max_turns=1`. DBOS durability by
itself does not guarantee exactly-once external billing. Add an atomic unique dispatch claim in
the provider adapter immediately before sending. It must execute whenever the actual provider
method is entered, including recovery of an uncheckpointed DBOS model step; a separately replayed
"permission granted" workflow step is insufficient. Concurrent workers cannot both claim it.

| Failure point | Required behavior |
|---|---|
| Before acceptance commit | No accepted review; retries recover any matching budget reservation without doubling it. |
| Accepted, not yet dispatched | Reconciler starts the same DBOS workflow; no extra resource or spend reservation. |
| Before provider claim | Recovery may proceed to the single request. |
| After provider claim but before durable response checkpoint | Never send again automatically. Mark outcome unknown after safe recovery/reconciliation; keep conservative spend reserved. This can sacrifice a review even if no request reached the provider. |
| Response durably checkpointed | Resume validation/assembly without another provider call, using accepted snapshot bytes. |
| Final application commit complete | Reads/replays return the persisted result; no duplicate observations or receipts. |

A deliberate rerun is a new review linked to its predecessor, with explicit operator authorization
and budget admission; it never silently changes the old result. Use a new workflow namespace at
this incompatible cutover and an empty DBOS store. Prove same-build recovery; arbitrary old-code
replay is out of scope. Keep DBOS in control of the event loop.

## 7. Request admission and diagnostics

Spend authorization, pricing snapshots and the session ledger were removed by explicit user
decision and must not be reintroduced. A review is admitted on configuration readiness and
context size alone: the composed instructions plus the report plus the bounded output must fit
the context allowance, or the request is rejected before dispatch with `REVIEW_CONTEXT_TOO_LARGE`.
Instructions and report text are never clipped to make a request fit.

Record actual provider usage when it is available and leave it null when it is not. Usage is
observability, not accounting. The application makes no claim about provider billing.

Structured operational logs carry request/review/workflow/attempt IDs, tenant-safe identifiers,
phase, latency, usage and safe errors. Redact report text, prompts, API keys and policy contents
by default. Exposed test keys must be rotated before future live use. No paid probes on startup.

## 8. Clean bootstrap, not migration

Prefer a new, explicitly named development data directory over deleting the old one. During
implementation, stop old workers, verify the exact configured application and DBOS locations,
and point the new build at fresh stores together. Re-seed only synthetic demo records and explicit
tenant/content bindings. Do not copy old reviews, receipts, drafts or pending workflow records.

A later reset helper must preview exact paths, refuse broad/root/repository targets, require
explicit confirmation, stop or reject active workers and preserve secrets, installed releases,
source files and the independent spend ledger. A reset also invalidates local browser review IDs;
clear or reject stale identities without re-submitting their report text. No reset was performed
while writing this plan. Backup/restore and migrations become gates before retained real data.

## 9. Implementation sequence and gates

| Phase | Deliverable | Gate before moving on |
|---|---|---|
| F1 — Contracts and fresh schema | Public/private Pydantic models, endpoint examples, bootstrap DDL, typed persistence, schema/version checks, generated OpenAPI/TS and existing feature fixtures. | Contract/error/pagination/tenant/FK/idempotency tests; no legacy projection/migration branches. All current feature routes represented. |
| F2 — Content and snapshots | Pinned three references/43 entries, authority-aware composer, tenant release binding, immutable snapshots, draft document support and new versioned package. | Exact source/catalog inventory and hash tests; qualifier/ID/exception fixtures; no draft leakage; distinct tenant composition; context/budget refusal tests. |
| F3 — Durable single-call execution | One combined SDK boundary, unique dispatch claim, durable attempt/budget records, truthful phases, output validation and idempotent finalization. | Controlled provider counter proves zero/one calls; real DBOS subprocess crash tests cover the failure table, concurrency and unknown outcomes. No paid calls needed. |
| F4 — Product regression and handoff | Reconnect existing history, feedback, outcomes, analytics and Skills Studio; clean-start instructions; regenerated artifacts and evidence. | Python/contract tests, TS/build, DOM/browser copy/state tests, whole-DB analytics and two-tenant isolation; documented actual results. |
| F5 — Authorized evaluation | Small scoped synthetic/held-out evaluation of the combined path and imported policy interpretation. | Explicit user authorization and $1 session admission; record failures/usage and qualified review. No claim that older three-call tests validate this design. |

F1–F4 are the foundation implementation. F5 is a separate authorization/quality gate, not
permission granted by this plan. Avoid a full codebase rewrite: change one boundary at a time,
keep tests runnable with controlled outputs, then retire superseded code at the coordinated cutover.

## 10. Deferred deliberately

Later: historical data migration, dual API versions, PostgreSQL deployment, browser activation
workflows, approval/rollback UI, Test/Production switching, durable unsent browser drafts, advanced
feedback triage, adjudicated clinical metrics, external integrations, evidence explorer, multi-agent
review, retrieval, semantic caching and large observability dashboards. Do not defer tenant scoping,
immutable snapshots, idempotency, database constraints, safe failures, spend enforcement or tests.

## 11. Artifact ownership and consistency

| Artifact family | This planning revision | During implementation |
|---|---|---|
| This plan, implementation plan and roadmap | Establish one foundation direction and sequenced gates. | Update phase status with actual evidence. |
| API, blueprint, DBOS, acceptance, UX and Studio specs | Add scoped next-build requirements; mark conflicting old text as baseline/history. | Replace superseded implementation sections as code lands. |
| Root README/start/handoff/local testing and framework entrypoints | Point agents and humans to this authority; distinguish prototype from future fleet concepts. | Update startup/reset commands only after they exist. |
| OpenAPI, frontend types and runtime fixtures | Keep truthful to installed 0.10.0; no fake target schema export. | Regenerate from implemented contracts and test together. |
| Reading editions and manifest | Regenerate from updated source docs; refresh affected hashes without claiming a new application release. | Regenerate after each implementation release. |
| Skill source/registry/lock/evaluations | Leave pinned runtime bytes intact; record new release work in F2. | Release new content and update provenance, manifests and evals atomically. |
| Archived screenshots, historical contracts and past test results | Preserve as dated evidence, with current index/scope notices. | Add new evidence; never relabel old evidence as a new run. |

Reference entrypoints: [API design](API_DESIGN.md), [DBOS validation](DBOS_VALIDATION.md),
[acceptance](ACCEPTANCE.md), [Workspace](WORKSPACE_SPEC.md), [Analytics](ANALYTICS_SPEC.md),
[Skills Studio](SKILLS_STUDIO_SPEC.md), [backlog](BACKLOG.md).

Sources: [pinned qatr references](https://github.com/parthi-vesta-tinker/qatr/tree/b906151a2bdef8c206325de64d46b61cdf5b7ad7/src/qatr/_vendor/qa_skills/skills/qa-critical-match/references)
and [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs).
Structured schemas constrain shape, not clinical correctness; refusal and incomplete output need
explicit handling. Runtime/DBOS claims must be checked against installed code and F3 tests.
