# DBOS execution and recovery contract

Current identities are application `foundation-f3-0.13.0`, queue `qa-reviews-f3-v1`, parent workflow `qa.review.f3.v1`, and child workflow `qa.openai.combined.f3.v1`.

## Execution boundary

DBOS owns orchestration and its asynchronous event loop. The parent validates accepted input, advances truthful phases, invokes one durable child, validates the checkpointed response, assembles canonical output, and commits the terminal resource. The child performs one combined Agents SDK request through `DBOSRunner`; it has no tools and transport retries are disabled.

Do not use `asyncio.run` around the SDK child. Do not queue the child behind the same parent concurrency gate. Application resources and idempotency receipts live in the application SQLite store; DBOS system tables remain private.

## Dispatch and checkpoints

Spend admission creates a stable reservation before execution. The actual provider method atomically claims the reservation. The claim is the no-retry boundary:

- no claim: a local failure may release an unused reservation;
- claim plus durable response checkpoint: recovery resumes local parsing, validation, and assembly;
- claim without durable response: fail `MODEL_OUTCOME_UNKNOWN`, retain the conservative charge, and never dispatch automatically again.

Provider refusal, incomplete status, unexpected tools, malformed JSON, missing coverage, ungrounded anchors, or schema failure ends the attempt without a repair request. Terminal writes and receipt state must remain idempotent.

## Recovery scope

Same-build process recovery is supported. Cross-version workflow replay is not claimed. Change application/workflow identities whenever code or captured content semantics would make replay unsafe. Reject incompatible pending work before starting a new build.

Required controlled recovery boundaries are before claim, after claim, after provider response, after the application checkpoint, after combined completion, and after final commit. Tests must also cover concurrent admission, same-key POST replay, child failures, and restart from durable response without another provider call.

Exactly-once provider billing cannot be guaranteed because external success may precede every local checkpoint.
