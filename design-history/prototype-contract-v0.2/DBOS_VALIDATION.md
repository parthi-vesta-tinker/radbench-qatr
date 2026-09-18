# DBOS validation record

Version 0.2 · 14 September 2026 · Local technical proof completed with stated limits

FastAPI persists the input/config/resource in application SQLite before dispatch. The review ID is also the top-level DBOS workflow ID. Startup reconciles unfinished application rows, including the commit-before-dispatch gap. DBOS stores execution checkpoints in a separate SQLite system database. Model checks are async child workflows; DBOSRunner checkpoints model responses. State updates and deterministic assembly are durable steps.

| Experiment | Observed result |
|---|---|
| D01 — Complete workflow | Passed through actual API/DBOS in the contract suite. Five accurate completed steps, deterministic copy text. |
| D02 — Restart after completed work | Passed actual subprocess kill/restart. The after-language checkpoint executed once across both processes. |
| D03 — Restart during unfinished work | Passed in the same experiment. The before-consistency checkpoint executed twice; remaining review completed. |
| D04 — Provider success before checkpoint loss | Not exercised against an external provider. A request can repeat in this gap; no exactly-once invocation or billing guarantee. |
| D05 — Transient provider retry | Not tested against a provider. OpenAI HTTP client is configured with max_retries=2 and timeout=45 seconds; no additional broad application retry loop. |
| D06 — Malformed/permanent output | Passed controlled SDK malformed JSON case; terminal failed result with no copyable output. Unsupported demo input also fails explicitly. |
| D07 — Concurrent duplicate API requests | Passed four concurrent requests with one key; one public review identity. Changed flag with reused key returns 409. |
| D08 — Acceptance gap | Passed committed resource with no workflow dispatch, followed by backend startup/reconciliation. |
| D09 — Completed result restart | Passed; identical structured result and copy text after restart. |
| D10 — Feedback restart | Passed; original result binding and saved feedback retained, duplicate key returns original feedback. |

## Reproduce

```sh
uv run pytest tests/test_api.py tests/test_sdk.py tests/test_recovery.py -q
```

Tests use isolated temporary databases and synthetic reports. Recovery tests launch and kill their own backend subprocess, reuse its database directory and record test checkpoint counts. Hooks are server-environment-only and inert without QA_TEST_HOOK_DIR; no client can enable them. No database or runtime log is shipped.

Versions: DBOS 2.31.1, dbos-openai-agents 0.3.0, openai-agents 0.22.2, Python 3.12.14. APP_VERSION is prototype-0.2-code-1. Cross-code-version recovery is not supported by this proof; version workflow code deliberately before later deployment.

## Integration correction discovered by testing

Wrapping an SDK child stage in asyncio.run caused executor shutdown to wait on DBOS worker threads. The implemented async child workflow runs on DBOS's event loop and is awaited through its durable handle from the parent. Controlled SDK tests now cover both valid and malformed model output. Do not reintroduce a private event-loop shutdown around DBOSRunner.

The local proof supports continuing with this stack. It does not establish clinical quality, provider-side exactly-once behavior or production operational readiness. See IMPLEMENTATION_STATUS.md and the [DBOS integration guide](https://docs.dbos.dev/integrations/openai-agents).
