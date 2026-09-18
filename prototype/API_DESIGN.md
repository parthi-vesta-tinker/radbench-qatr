# API contract

The active public contract is `QA-Version: 2026-09-18`; omitting the header selects the same version. Other explicit versions are rejected. Generated [openapi.json](openapi.json) is the schema authority and must be regenerated from the FastAPI application.

## General rules

- `/api/v1` resources are JSON and reject unknown input fields.
- Authentication resolves the tenant. No request body or caller-controlled tenant header can select it.
- List limits and cursors are bounded and tenant/filter bound.
- Errors use the structured API error envelope with stable codes and request IDs.
- POST idempotency is scoped by tenant, operation, and key. The original request fingerprint, response status, body, and `Location` replay unchanged. Reusing a key with a different body conflicts.
- Receipt replay precedes current model/content readiness checks.
- `backend/presentation.py` is the public projection boundary. Provider prompts, exact internal snapshots, source paths, credentials, database details, and DBOS internals remain private.

## Review resources

`POST /api/v1/reviews` accepts only `report_text` and an `Idempotency-Key`. The server resolves tenant, model, policy, content release, snapshot, workflow identity, and spend session. Acceptance returns `202` and a stable resource location.

`GET /api/v1/reviews/{id}` returns one tenant-scoped resource. States are `queued`, `running`, `completed`, `needs_input`, or `failed`. Only `completed` has a result. Progress uses:

1. `input_validation`
2. `combined_review`
3. `output_validation`
4. `comment_assembly`

A result contains ordered server-validated observations, two display/copy groups, full-template copy when applicable, immutable version metadata, and safe usage/cost fields. An ambiguous provider attempt is a failed review with `MODEL_OUTCOME_UNKNOWN`, never an empty result.

`GET /api/v1/reviews` provides bounded tenant history and stable pagination. Analytics queries the whole matching database population rather than this page.

## Related resources

- Per-review feedback POST/GET and the feedback inbox preserve immutable result binding. Down feedback requires a reason.
- Per-review stakeholder outcomes are append-only, result-bound operator records. They are not verified signatures or clinical ground truth.
- Analytics returns operational and acceptance aggregates. Clinical performance remains null until an independent adjudicated reference cohort exists.
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
