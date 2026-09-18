# DBOS validation plan

Version 0.1 · Phase 4 experiments · All experiments not run

## Purpose

Prove the smallest durable review workflow behind FastAPI before adding real model variability. Use deterministic steps and controlled failure injection in an isolated local environment. Record installed versions, database configuration and workflow-version policy with every experiment.

| ID | Experiment | Required observation |
|---|---|---|
| D01 | Complete all five steps normally. | One completed result; accurate step states and immutable input identity. |
| D02 | Stop process after a step result is durably recorded; restart. | Recorded progress is reused as supported; remaining work resumes; same review ID. Count actual step invocations. |
| D03 | Stop process while a step is executing, before its completion record. | Determine whether it re-executes; no claimed final output until the workflow completes. |
| D04 | Simulate external success followed by loss of local acknowledgement. | Document possible duplicate external calls and implications. Do not claim exactly-once external invocation. |
| D05 | Return a transient service error, then succeed. | Bounded retry/backoff; attempt counts captured; UI stays running until terminal. |
| D06 | Return a permanent failure or malformed output. | Terminal failed state with useful safe error; no successful empty result. |
| D07 | Submit identical requests concurrently with one idempotency key. | Same public review identity and recoverable workflow; no unrelated second result. |
| D08 | Crash between resource creation and workflow start/acceptance. | Show that the acceptance design cannot leave an acknowledged review permanently orphaned. |
| D09 | Complete, restart and reread the result. | Exact result and copy exports are retained without regenerating the review. |
| D10 | Save feedback, restart and retrieve it. | Feedback still references the original result; duplicate submission is controlled. |

## Decisions the proof must resolve

Where is review identity persisted? When is API acceptance durable? How are pending jobs recovered? What belongs in a DBOS step versus deterministic workflow code? Which side effects need idempotency? How are retry limits and timeouts set? What happens to in-flight workflows after a workflow-code change?

Start with one process and one isolated database setup. Test restarts against the same code/version first. Do not promise compatibility of in-flight execution across arbitrary code changes; record a supported change/recovery policy before later deployments.

## Experiment record template

| Field | Record |
|---|---|
| Experiment and date | Not run |
| Library versions/configuration | To be recorded |
| Input/review/workflow identity | Synthetic only |
| Interruption point and method | To be recorded |
| Observed execution counts and state transitions | To be recorded |
| Expected vs actual | To be recorded |
| Logs or reproducible commands | To be added during implementation |
| Result | Not run / pass / fail / limitation |

DBOS fit is established by these observations, not by successful import, dependency installation or a normal happy-path example. Read the [supported integration guide](https://docs.dbos.dev/integrations/openai-agents) and inspect installed APIs during implementation; no engine is claimed validated in this package.
