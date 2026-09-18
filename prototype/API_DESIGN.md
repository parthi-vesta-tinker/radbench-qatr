> Current implementation: application **0.13.0**, bundle **1.17**, foundation **F3**. [Decisions and verification](FOUNDATION_CHANGELOG.md) supersede older baseline statements below. Fresh schema 4 and API 2026-09-18 are implemented. F3 adds one combined request, guarded dispatch, durable response checkpoints and per-session spend admission. F4/F5 remain separate gates.

F2 adds `catalog` and `policy_source` knowledge document kinds, full qatr source attribution,
server-controlled tenant release profiles, and immutable complete composition snapshots.
See [foundation changelog](FOUNDATION_CHANGELOG.md) for implemented boundaries and evidence.

# Next-build API requirements — 2026-09-17

[FOUNDATION_PLAN.md](FOUNDATION_PLAN.md) sections 3–4 define the replacement; generated OpenAPI
still describes installed 0.10.0 during planning.

- Generate public OpenAPI from Pydantic and TypeScript from OpenAPI; keep private provider schemas and DB rows separate.
- Support one QA-Version after coordinated client/server cutover; no historical projections or migrated receipts.
- Preserve review/history/feedback/outcomes/analytics/knowledge resource families, scopes, error envelope and cursors.
- Keep durable tenant/operation-scoped acceptance receipts and idempotency for all new records.
- Keep queued/running/completed/needs_input/failed; show local validation, combined model review, output validation and assembly.
- Ambiguous provider attempts fail with MODEL_OUTCOME_UNKNOWN; only an explicitly authorized new review can rerun.
- Results/observations remain immutable and publicly projected; never expose prompts, drafts or DBOS internals.

Earlier sections are implemented baseline, not completion of this target.

> **Current release 1.14 / application 0.10.0:** [Workspace specification](WORKSPACE_SPEC.md) governs the current UX. [Analytics specification](ANALYTICS_SPEC.md) defines the feedback inbox, stakeholder outcomes, metric denominators and unmeasured clinical performance. [Implementation status](IMPLEMENTATION_STATUS.md) records verification; [Backlog](BACKLOG.md) records deferred work. Earlier release-specific text below is historical where it conflicts. See [Skills Studio specification](SKILLS_STUDIO_SPEC.md) for the new content review and draft editor.

## Skills Studio API — release 1.14

GET /api/v1/knowledge lists installed content metadata; GET /api/v1/knowledge/{document_id}
returns source and draft history. Both require skills:read. POST on the document's /drafts route
requires skills:read + skills:write, Idempotency-Key, expected_revision and source/package hashes.
GET /api/v1/knowledge/{document_id}/drafts/{revision}/export returns the saved JSON proposal.
Existing API keys gain no new scopes. Saved revisions do not alter runtime instructions.
See SKILLS_STUDIO_SPEC.md for the complete contract; OpenAPI includes explicit response schemas.

## Additive Studio API — release 1.13

Public QA-Version remains 2026-09-15. New routes are additive and old review/feedback receipts
are untouched. Feedback inbox and outcome reads require both reviews:read and feedback:read;
outcome writes require reviews:read and feedback:write. Analytics requires reviews:read and
omits acceptance/feedback aggregates (null) without feedback:read. Tenant is always authenticated,
never selected in a query/body.

| Route | Meaning |
|---|---|
| GET /api/v1/feedback | Paginated cross-report feedback, with q/rating/reason/source filters |
| GET /api/v1/analytics | Tenant-wide rolling-period aggregates and clinical-metric readiness |
| POST /api/v1/reviews/{id}/outcomes | Idempotent, immutable operator-recorded stakeholder decision |
| GET /api/v1/reviews/{id}/outcomes | Bounded newest-first outcome history |

See [ANALYTICS_SPEC.md](ANALYTICS_SPEC.md) for fields, scopes, denominators and transaction rules.
Application package is 0.9.0; DBOS workflow version remains prototype-0.8-skill-eval-1.
No model calls occur on any of these routes. Clinical precision/recall fields are explicitly
null-only readiness fields until an adjudicated reference-cohort contract is introduced.

# Current refinement contract — v0.6 / bundle 1.10

Read [REFINEMENT_SPEC.md](REFINEMENT_SPEC.md) first. It supersedes conflicting baseline requirements below: missed-flag UI/copy is deferred; comments, progress and Studio layout are refined; inline headings, persistent review history and saved feedback are implemented. Preserve legacy API receipts and clinical instructions.

---

# API adoption update — 15 September 2026

The following changes supersede the baseline contract preserved below.

- New public version **2026-09-15**; bundled browser pins it. Omission still selects legacy **2026-09-14**.
- New creates require the new version. Existing idempotency receipts replay first, with original status/body/Location, even under the legacy version or changed model/skill configuration.
- Legacy GETs retain representable results without new copy fields. Richer section labels require the new version and produce **400 API_UPGRADE_REQUIRED** for an incompatible legacy read.
- New public report_section labels add history, indication, technique, comparison, addendum, other and multiple; both remains Findings+Impression.
- Result adds server-derived **general_copy_text** and **critical_copy_text**. Empty groups have empty copy strings. Full copy_text and all existing headings/semantics remain.
- Safe provenance adds skill content version/hash and snapshot hash. Exact instructions, policy text, private candidate bases and source offsets are never public projection fields.
- Input remains report_text only, up to 40,000 characters. Rich optional sections do not introduce new input fields or mandatory requirements.
- **503 SKILL_CONFIGURATION_INVALID** rejects new acceptance if the release is missing/drifted. **422 REVIEW_CONTEXT_TOO_LARGE** rejects configured context that exceeds the conservative prototype allowance; no clipping.
- Model output/grounding/ownership failures become failed reviews with no copyable result. Model-reported unresolved source ambiguity becomes needs_input.
- POST configuration is snapshotted transactionally before DBOS dispatch. Registered tenant authentication, idempotency, feedback and pagination remain as below.
- Implementation 0.8.0, workflow code prototype-0.8-skill-eval-1, parent qa.review.v5, OpenAI child qa.openai.stage.v4. Record schema remains 2.

The live OpenAPI schema is in openapi.json and /docs. Historical baseline statements below referring
to only one implemented API version or unchanged three-value section enums are superseded here.

---

# Report QA API contract

Contract edition v0.4 · Public QA-Version **2026-09-14** · Implementation 0.3.0

## Principles and resource boundary

The browser and coding agents use the same resource API. FastAPI owns validation, authentication and the stable public contract. DBOS owns execution. Explicit presentation functions separate public JSON from storage dictionaries. A completed clinical review is not report release or communication confirmation.

Only report_text is clinical input. There is no critical-finding selector, tenant selector, author field or flag override in the request. Tenant identity comes from server-authenticated credentials, with Vesta fixed in local mode.

| Operation | Endpoint | Scope | Success |
|---|---|---|---|
| Create review | POST /api/v1/reviews | reviews:write | 202, immutable acceptance snapshot |
| Read review | GET /api/v1/reviews/{review_id} | reviews:read | 200, current state |
| Save feedback | POST /api/v1/reviews/{review_id}/feedback | feedback:write | 201, saved feedback |
| List feedback | GET /api/v1/reviews/{review_id}/feedback | feedback:read | 200, bounded page |
| Configuration | GET /api/v1/config | reviews:read | 200, tenant-effective safe configuration |
| Health | GET /api/v1/health | Public process health | 200, no report/tenant data |

OpenAPI: /openapi.json; interactive documentation: /docs. The included openapi.json matches the live schema, including x-required-scope annotations. API errors use one documented envelope.

## Authentication and tenancy

QA_AUTH_MODE=local is the default: loopback access only, fixed tenant vesta, no credential or tenant controls in the browser. Do not expose or proxy this mode to shared users. QA_AUTH_MODE=api_key authenticates Authorization: Bearer credentials against SHA-256 grants in QA_TENANT_KEYS_FILE. Missing/invalid credentials yield 401; insufficient scope yields 403. Each credential resolves to exactly one registered tenant. Requests cannot override it with X-Tenant-Id or a body tenant_id.

Optional QA_TENANTS_FILE is a JSON mapping of tenant IDs to model/policy_path overrides. Default: {"vesta":{}}. Vesta's global manual setting is not inherited by another tenant. Add tenant definitions and restart to register their database namespace; key revocation/rotation is evaluated from the current grants file on subsequent requests. The browser currently supports local Vesta mode; no bearer secret is embedded in frontend assets.

A resource belonging to another tenant returns the same 404 code/message as a nonexistent one. All reads/writes, feedback, receipt lookups, cursors and DBOS workflow arguments include tenant identity. Cross-tenant foreign-key references are prohibited in storage.

## Request and headers

```json
{"report_text":"Findings:\nLeft pleural effusion.\n\nImpression:\nRight pleural effusion."}
```

report_text is required, non-blank and at most 40,000 characters. Unknown request fields are rejected. Findings/impression must be identifiable; accepted requests with missing sections finish as needs_input and skip subsequent checks.

| Header | Contract |
|---|---|
| QA-Version | Pin 2026-09-14; omission uses that fixed default. Unsupported values return 400. Returned on every business API response. |
| Idempotency-Key | Required for both POST endpoints; 1–255 non-whitespace characters. Prefer a random UUID; never patient data. |
| Authorization | Required bearer credential in api_key mode; unnecessary in local mode. |
| Request-Id | Server-generated response identifier, different for each HTTP attempt, including replays. |
| Idempotency-Replayed | true/false on successful POST responses. |
| Location | Review resource URL on creation/replay. |
| Retry-After | Polling/retry hint where applicable; not a clinical service-time guarantee. |
| Cache-Control | no-store for business API responses. |

## Idempotency and acceptance

Namespace: (tenant_id, operation, key_hash). The feedback operation includes its parent review ID. Request fingerprints include validated canonical parameters and the selected public API version. Changing parameters under the same namespace/key yields 409. Credential rotation within the same tenant does not invalidate receipts.

For create review, one database transaction commits the immutable input, captured execution configuration, queued review/outbox and initial response receipt. That commit is acceptance. Dispatch then starts the durable workflow; if it fails, periodic reconciliation retries dispatch against the same tenant-qualified workflow identity. Startup also reconciles pending work.

A retry returns the original status, body bytes and Location even if GET now shows completed or failed, or provider configuration has changed. It does not invoke a second review. Request-Id is new per attempt and Idempotency-Replayed changes to true. GET is the authoritative current state.

Feedback storage and its 201 receipt commit together. Concurrent identical submissions return one feedback identity and identical body. Validation, authentication and configuration failures before acceptance are not cached. Generic failures are retried with the same key; a committed receipt wins if the caller lost acknowledgement. Receipts have no automatic expiry in this prototype. A new intentional review or different feedback uses a new key.

API idempotency prevents duplicate accepted application operations. It does not guarantee exactly-once external model invocation or billing if a provider succeeds before its local checkpoint is recorded.

## Public resources and versions

Review resources include id, object=qa_review, tenant_id, api_version, created_at, input_version, input_hash, input, execution_status, steps, result, error and provenance. New review IDs use qr_ plus an opaque random identifier. review_id remains an equal alias for existing prototype clients. Feedback uses object=qa_feedback and qf_ IDs; feedback_id remains its equal alias. Existing migrated IDs are preserved.

Execution statuses: queued, running, completed, needs_input, failed. The five logical steps are unchanged. Result remains null outside completed. Results include result_version, outcome, critical_finding_detected, critical_flag_status, critical_flag_quote, missed_flag, grouped comments and exact copy_text. Known designation requires a report quote; unknown designation with critical comments yields null missed_flag / Cannot determine. No-observation results omit the UI template/copy action. Report-only clinical semantics are unchanged by this API revision.

Do not confuse api_version with storage schema_version, input_version/result_version or workflow/prompt/model/policy versions. Internal record schema 2 is migrated independently. presentation.py explicitly projects public fields and excludes future internal fields in records, input parsing, provenance, metrics, results and observations. Preserve existing public semantics when changing storage. Breaking public changes require a new supported version and projection; only one public version is implemented today. Clients should ignore unknown additive response fields.

## Feedback and pagination

Payload fields remain result_version, rating (up/down), target (result/observation/missed_flag), optional observation_id, reason, explanation and suggested_comment. Down requires reason; other text remains optional, including Other. Validate the result version and target before saving. Feedback does not edit comments or train models.

List parameters: limit defaults to 20, bounded 1–100; starting_after is a feedback ID from the same tenant and review. Results are in insertion order:

```json
{"object":"list","items":[],"has_more":false,"next_cursor":null,"url":"/api/v1/reviews/qr_example/feedback"}
```

Use next_cursor as starting_after for the next page. Invalid or foreign cursors return 400. The items field is retained for the current client contract; this intentionally differs from Stripe's data naming. No fleet/review-list endpoint or history UI is introduced.

## Errors and support

```json
{"error":{"type":"idempotency_error","code":"IDEMPOTENCY_CONFLICT","message":"This key was already used for different parameters or an API version in this tenant and operation.","retryable":false,"request_id":"req_example"}}
```

Validation errors can add param and field_errors. Do not parse message prose for application decisions; use code, type and HTTP status. The browser understands this envelope; a review resource's error remains its separate execution failure field. Raw input, provider stack traces, keys and private policy paths are not returned in API error bodies. Logs correlate request IDs and tenant/status without logging report bodies or credentials.

| Condition | Status/code |
|---|---|
| Missing/invalid credential | 401 AUTHENTICATION_REQUIRED / INVALID_API_KEY |
| Insufficient scope | 403 INSUFFICIENT_SCOPE |
| Unsupported version / tenant override | 400 UNSUPPORTED_API_VERSION / TENANT_OVERRIDE_NOT_ALLOWED |
| Invalid input or feedback binding | 422 INVALID_INPUT / specific binding code |
| Missing or foreign review | 404 REVIEW_NOT_FOUND |
| Same key with different parameters | 409 IDEMPOTENCY_CONFLICT |
| Provider not configured before acceptance | 503 MODEL_NOT_CONFIGURED |
| Unhandled request failure | 500 INTERNAL_ERROR with request ID; retry same key |
| Accepted workflow fails | GET remains 200; execution_status=failed and result=null |

## Example

Local Vesta mode:

```sh
curl -X POST http://127.0.0.1:8000/api/v1/reviews \
  -H 'QA-Version: 2026-09-14' \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: example-review-1' \
  -d '{"report_text":"Findings:\nLeft pleural effusion.\n\nImpression:\nRight pleural effusion."}'
```

In api_key mode, add Authorization: Bearer with the credential from the provisioning helper. Keep secrets outside source control and frontend code. Poll Location to read the current review. See README.md for setup and API_REVIEW.md for the Stripe references and design rationale.

## Operational diagnostics patch (1.9.1)

`GET /api/v1/status` returns local component snapshots with existing tenant/read authorization.
`POST /api/v1/diagnostics/openai` performs an explicit, bounded, zero-retry model metadata request;
no report or generation is sent. Repeating it has no application mutation and needs no idempotency key.
`GET /api/v1/health` remains public liveness only. Status HTTP 200 does not imply ready; inspect the body.
No clinical output, API version, durable workflow identity or accepted snapshot contract changed.
