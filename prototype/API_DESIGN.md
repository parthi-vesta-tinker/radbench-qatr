# API contract

The active public contract is `QA-Version: 2026-09-22`; omitting the header selects the same version. Other explicit versions are rejected. Generated [openapi.json](openapi.json) is the schema authority and must be regenerated from the FastAPI application.

## General rules

- `/api/v1` resources are JSON and reject unknown input fields.
- Server access configuration or authentication resolves the tenant. No request body or caller-controlled tenant header can select it.
- List limits and cursors are bounded and tenant/filter bound.
- Errors use the structured API error envelope with stable codes and request IDs.
- POST idempotency is scoped by tenant, operation, and key. The original request fingerprint, response status, body, and `Location` replay unchanged. Reusing a key with a different body conflicts.
- Receipt replay precedes current model/content readiness checks.
- `backend/presentation.py` is the public projection boundary. Provider prompts, exact internal snapshots, source paths, credentials, database details, and DBOS internals remain private.

## Access modes

`QA_AUTH_MODE=local` is the default: unauthenticated loopback clients share the Vesta tenant.
`QA_AUTH_MODE=public` explicitly permits unauthenticated remote clients, including proxy-forwarded
addresses, with all scopes in that same shared Vesta tenant. Public visitors can read existing
reports and use review, feedback, outcomes, analytics, Studio and playground actions.
`QA_AUTH_MODE=api_key` requires a valid bearer key and applies its tenant and scope grants.
Local and public modes reject supplied Authorization credentials rather than implying that a
key selected another tenant. All modes reject `X-Tenant-Id`; unknown modes fail closed.

## Review resources

`POST /api/v1/reviews` accepts only `report_text` and an `Idempotency-Key`. The server resolves tenant, model, policy, content release, snapshot, workflow identity, and spend session. Acceptance returns `202` and a stable resource location.

`GET /api/v1/reviews/{id}` returns one tenant-scoped resource. States are `queued`, `running`, `completed`, `needs_input`, or `failed`. Only `completed` has a result. Progress uses:

1. `input_validation`
2. `combined_review`
3. `output_validation`
4. `comment_assembly`

A result contains ordered server-validated observations, two display/copy groups, full-template copy when applicable, current input-version metadata, and safe usage/cost fields. An ambiguous provider attempt is a failed review with `MODEL_OUTCOME_UNKNOWN`, never an empty result.

`GET /api/v1/reviews` provides bounded tenant history and stable pagination. Analytics queries the whole matching database population rather than this page.

## Related resources

- Per-review feedback POST/GET and the feedback inbox belong to the review, without a result-version or input-hash binding. Down feedback requires a reason.
- Analytics returns operational and feedback aggregates. Clinical performance remains null until an independent adjudicated reference cohort exists.
- Knowledge catalog/detail/draft/export routes expose verified installed content and tenant-scoped draft history. Draft writes use optimistic revision and source/package hash checks and never activate runtime instructions.
- Config, health, status, and explicit diagnostics expose safe operational state. Provider diagnostics do not perform inference.

## Change process

Change Pydantic contracts and implementation together, then run:

```sh
uv run python scripts/export_openapi.py
uv run python scripts/export_contracts.py
uv run pytest -q tests/test_foundation.py tests/test_api.py
npm --prefix frontend run build
```

Do not hand-edit generated files or add a compatibility projection without an explicit version decision.

## Critical finding classification (0.15.0)

A completed review with critical comments can produce separate JEV finding
classifications. `GET /api/v1/classifications/config` reports readiness;
`POST /api/v1/classifications` admits a single critical observation with the current
review ID and input version. `GET /api/v1/classifications/{id}` and
`GET /api/v1/reviews/{review_id}/classifications` expose status and immutable
suggestions. Classification feedback has its own POST and GET routes under the
classification ID. Automatic admission occurs only for completed critical reviews
accepted while JEV was configured. API version remains 2026-09-22; application
storage is schema 8 with an explicit backed-up schema-7 upgrade.

## Same-review replacement (0.14.0)

`PUT /api/v1/reviews/{id}` accepts `report_text`, `expected_input_version` and an
Idempotency-Key. It returns 202 with the same ID and an incremented concurrency counter.
Missing tenant-scoped IDs return 404; queued/running reviews or stale versions return
409 REVIEW_CONFLICT. Receipt replay precedes readiness and concurrency checks.
Acceptance atomically replaces current text, submission timestamp, status, config snapshot
and result; feedback is retained, prior outcomes and provider checkpoints are cleared.
A new workflow identity includes the counter, fencing all old state/checkpoint writes.
GET and history return only latest state. `created_at` is the latest submission time.
Feedback requests no longer accept result_version; resources no longer expose input_hash.
Comment-target feedback keeps its quoted comment as feedback context, without a result FK.
Operational idempotency receipts and DBOS checkpoints remain for safe replay/recovery;
they are not a user-facing report-version history.

Stakeholder outcome endpoints and schemas are retired; analytics no longer returns acceptance counts. All copy projections start with their content group, without the UI-only QA review prefix. Dormant outcome storage is retained for schema-7 compatibility; no application path reads it.
