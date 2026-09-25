# DBOS execution and recovery contract

Current identities are application `foundation-f3-0.15.0`, queue `qa-reviews-f3-v2`, parent workflow `qa.review.f3.v2`, and child workflow `qa.openai.combined.f3.v2`.

## Execution boundary

DBOS owns orchestration and its asynchronous event loop. The parent validates accepted input, advances truthful phases, invokes one durable child, validates the checkpointed response, assembles canonical output, and commits the terminal resource. The child performs one combined Agents SDK request through `DBOSRunner`; it has no tools and transport retries are disabled.

Do not use `asyncio.run` around the SDK child. Do not queue the child behind the same parent concurrency gate. Application resources and idempotency receipts live in the application SQLite store; DBOS system tables remain private.

## Dispatch and checkpoints

Review admission captures the current configuration before execution. The actual provider method atomically claims dispatch. The claim is the no-retry boundary:

- no claim: the provider has not been called;
- claim plus durable response checkpoint: recovery resumes local parsing, validation, and assembly;
- claim without durable response: fail `MODEL_OUTCOME_UNKNOWN`, never dispatch automatically again.

Provider refusal, incomplete status, unexpected tools, malformed JSON, missing coverage, ungrounded anchors, or schema failure ends the attempt without a repair request. Terminal writes and receipt state must remain idempotent.

## Recovery scope

Same-build process recovery is supported. Cross-version workflow replay is not claimed. Change application/workflow identities whenever code or captured content semantics would make replay unsafe. Reject incompatible pending work before starting a new build.

Required controlled recovery boundaries are before claim, after claim, after provider response, after the application checkpoint, after combined completion, and after final commit. Tests must also cover concurrent admission, same-key POST replay, child failures, and restart from durable response without another provider call.

Exactly-once provider billing cannot be guaranteed because external success may precede every local checkpoint.

## Latest-state replacement

A workflow identity includes tenant, stable review ID and input_version. The counter is
concurrency fencing, not a stored report-version history. Explicit terminal replacement
clears the old provider checkpoint and config snapshot. Every live workflow state write
and provider checkpoint operation checks its captured input_version atomically before
writing. A superseded execution cannot dispatch or overwrite a newer review. Queued or
running reviews cannot be replaced. Playground retains isolated storage and the same
four-phase execute implementation.


## Classification v1 compatibility

The legacy `qa.finding.classify.v1` workflow remains registered on
`qa-finding-classifications-v1`. The UI now presents its status after Results;
classification does not block or rewrite the completed review. Its steps remain
input validation, JEV classification, output validation and result assembly.
The visible Results label combines the review's output validation and comment
assembly without renaming persisted step IDs or changing recovery identities.
Classification inspection is read-only. For accepted v1 work, ambiguous provider
outcomes still require an explicit new request; viewing details and polling never
retry dispatch. The v2 policy below applies only to newly admitted classifications.


## Classification v2 — bounded duplicate inference

By explicit user decision, new JEV classifications use `qa.finding.classify.v2`
with one durable `qa.finding.execute.v2` step on the existing independent
`qa-finding-classifications-v1` queue. The v1 workflow and adapter remain available
for previously captured v1 configurations; their no-retry policy is unchanged.
Clinical review and Playground still use their existing one-dispatch rules.

On the ordinary success path classification performs five application write
transactions: admission, running state, attempt reservation, response checkpoint,
and terminal result. Phase timings accumulate in memory and are committed with
terminal state, preserving the four public phase records without eight state writes.
A restart may repeat local phase work; checkpointed responses and completed results
are reused. No claim of exactly-once inference or billing is made.

The schema-8 attempt row is retained as a bounded-attempt checkpoint. For v2 its
opaque claim_id contains a version, count, ownership token and not-before timestamp.
A compare-and-swap reservation increments the count before each possible request;
checkpoint writes require that token. Active leases expire after 60 seconds.
Transient retry checkpoints remain claimed while more attempts are permitted;
response, final failure and exhausted uncertainty remain immutable terminal rows.
No schema migration, reset, or alteration of the existing immutability trigger occurs.

Transport errors, HTTP 408/429 and 5xx receive at most three attempts across
restarts, with exponential backoff and jitter. Retry-After is honored up to 30
seconds; longer waits fail explicitly rather than retrying early. Invalid input,
credentials, other HTTP errors, malformed JSON and invalid output never trigger
repair calls. Exhausted transport uncertainty reports JEV_RETRIES_EXHAUSTED.
Each retry may incur provider usage and return a different prediction; only the
validated, durably accepted result is published. Tenant and input-version boundaries,
request-bound receipts and classification feedback are preserved.

After committing a completed review, its existing state step sets an in-process
wakeup event. The application outbox worker immediately admits/enqueues eligible
classifications outside DBOS step context. Lost wakeups and interrupted enqueueing
are recovered by startup reconciliation and a 30-second classification sweep.
The review outbox retains its one-second sweep. Failure to classify never changes
the completed review. Playground completion never sets this event.
