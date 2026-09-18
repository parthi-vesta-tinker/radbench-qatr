> Current implementation: application **0.13.0**, bundle **1.17**, foundation **F3**. [Decisions and verification](FOUNDATION_CHANGELOG.md) supersede older baseline statements below. Fresh schema 4 and API 2026-09-18 are implemented. F3 adds one combined request, guarded dispatch, durable response checkpoints and per-session spend admission. F4/F5 remain separate gates.

> Next-build authority (2026-09-17): [clean-start foundation plan](FOUNDATION_PLAN.md). This records the earlier API review. Recheck the replacement single-version contracts, typed persistence and failure semantics in F1/F3.

> **Current release 1.14 / application 0.10.0:** [Workspace specification](WORKSPACE_SPEC.md) and [Analytics specification](ANALYTICS_SPEC.md) govern current behavior. DBOS workflow identities and clinical skills are unchanged from 1.12. [Backlog](BACKLOG.md) records deferred Test/Production isolation and clinical metric adjudication. Earlier release-specific text below is historical where it conflicts. See [Skills Studio specification](SKILLS_STUDIO_SPEC.md) for the new content review and draft editor.

# API design review and decisions

14 September 2026 · API contract edition v0.4 · Implementation 0.3.0 · Bundle v1.8

## Assessment

The earlier API was a sound local demonstration contract. It was not ready to claim multi-tenant support or stable idempotent response replay. This revision implements the missing boundaries while preserving Vesta's report-only browser flow. It provides a credible foundation for the next prototype phase, not a claim of production or clinical readiness.

| Area | Earlier design | Revised implementation |
|---|---|---|
| Resource model | Review/feedback resources with immutable inputs | Retained; typed object names and prefixed IDs added, old identity fields retained as aliases. |
| Tenant isolation | No tenant ownership/authorization | Tenant-scoped tables, credentials, queries, feedback, policy, receipts and workflow identity. |
| Review retries | Same resource ID but changing POST response | Same accepted status/body/Location, even after completion or provider configuration changes. |
| Feedback retries | Per-review key matching | Atomic tenant/operation/key receipt; concurrent duplicates and mismatched payloads tested. |
| API/storage coupling | Persisted dictionaries returned directly | Explicit public projections and typed resources, independent of storage schema version. |
| Versioning | URL v1 plus workflow version | Pinned QA-Version, published response version, internal record migration and separate workflow/prompt versions. |
| Errors/diagnosis | Flat error and no request ID | Consistent error envelope, safe messages, retry hint and per-attempt Request-Id. |
| Collection growth | Unbounded feedback list | Bounded cursor pagination, with tenant/review-scoped cursor checks. |
| Acceptance gap | Reconciliation only at startup | Atomic outbox/receipt commit and periodic reconciliation; dispatch failure recovers while process stays up. |
| Read behavior | GET could update failed execution state | Reconciliation owns execution updates; GET reads resources. |

## Stripe principles adopted deliberately

Stripe documents replaying the first completed request's response and comparing retry parameters. We apply that principle to committed review acceptance and feedback creation. This is stronger than merely returning the same review ID. [Stripe idempotent requests](https://docs.stripe.com/api/idempotent_requests).

Stripe separates explicit API version selection from ordinary compatible changes. We add a pinned QA-Version header and a public presentation layer so storage refactoring can be handled behind a stable contract. Only one public version is currently implemented; future versions must have explicit adapters and compatibility tests. [Stripe versioning](https://docs.stripe.com/api/versioning).

Stripe's request identifiers, structured HTTP errors and cursor-based lists make integrations diagnosable and predictable. We adopt these patterns for correlation, consistent failures and bounded feedback retrieval. [Request IDs](https://docs.stripe.com/api/request_ids), [errors](https://docs.stripe.com/api/errors), [pagination](https://docs.stripe.com/api/pagination).

Stripe Connect provides an account-scoped API model. Our simpler design binds each key to exactly one tenant, with no caller-selected tenant header. We borrow explicit ownership and authorization principles, not Stripe's payments/account model. [Stripe Connect authentication](https://docs.stripe.com/connect/authentication).

## Intentional differences from Stripe

- Async review creation returns a durable 202 acceptance snapshot; GET returns the evolving resource. Replay does not pretend the workflow is still queued today: it repeats the original acknowledgement by design.
- Keys are required on the two mutating endpoints and scoped by tenant, operation and key, not globally across every caller action.
- Accepted receipts are retained without automatic expiry in this prototype. A future retention policy must preserve a documented replay window and protect against accidental duplicate review costs.
- Validation/authentication/configuration failures before acceptance do not consume a key. We do not cache arbitrary 500 responses. If acknowledgement is lost after commit, retry finds the committed receipt.
- There are no webhooks, metadata bags, expand parameters, billing resources or tenant-switcher UI merely to resemble Stripe. Add them only for a concrete need.

## Multi-tenant boundary

Vesta remains the only configured tenant by default. Local mode is fixed to Vesta and accepts loopback requests. API-key mode supports multiple explicitly registered tenants with scoped bearer credentials; key hashes are stored in a server-side file. Caller-supplied tenant_id is rejected in request bodies, and X-Tenant-Id overrides are rejected. Foreign and missing resource IDs both yield REVIEW_NOT_FOUND.

Every resource access and workflow update carries a tenant ID explicitly. Database foreign keys prevent cross-tenant feedback references. Idempotency is tenant scoped and survives credential rotation within the same tenant. The recovery enumerator is an internal system operation; no cross-tenant list endpoint exists. A second synthetic tenant was used to test isolation.

Vesta's optional QA_POLICY_PATH is not inherited by another tenant. Additional tenants can configure their own policy paths and models. The provider credential and compute pool remain shared infrastructure; tenant quotas, billing and dedicated storage are not implemented.

## Evolution rules

Keep four separate version concepts: public API version, internal record schema, immutable input/result revisions and workflow/prompt/model/policy versions. A database column change need not change the API. A changed public field's meaning, type, requiredness or enum requires an explicit version/adapter decision.

Completed report-only v0.3 records migrate transactionally into Vesta's namespace with identities, inputs, results and feedback preserved. Old code did not store exact original acceptance bodies; migrated keys receive a stable receipt based on the migration snapshot. That cannot reproduce an unrecorded historical response. Pending old workflows block migration without changing their records; finish them with the previous application before upgrading. Pre-report-only records still need a separate migration decision.

## Test evidence and remaining work

The focused suite exercises tenant read/write isolation, cursor isolation, scope enforcement, tenant spoofing, credential rotation, stable replay bytes, replay after model configuration changes, concurrent feedback, mismatched keys, unsupported versions, validation-before-acceptance, outbox recovery without restart, internal-field projection, tenant policy separation and completed/in-flight migration behavior.

The complete local suite and browser results are recorded in IMPLEMENTATION_STATUS.md. No live OpenAI clinical evaluation has been performed. A shared pilot still needs browser/session authentication, tenant-aware user roles, key lifecycle operations, rate/usage limits, data retention/access controls, operational monitoring and deployment design. PostgreSQL row-level security can be considered when moving beyond local SQLite; it is not needed to demonstrate the current logical tenant boundary.
