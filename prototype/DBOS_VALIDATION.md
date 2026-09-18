> Current implementation: application **0.13.0**, bundle **1.17**, foundation **F3**. [Decisions and verification](FOUNDATION_CHANGELOG.md) supersede older baseline statements below. Fresh schema 4 and API 2026-09-18 are implemented. F3 adds one combined request, guarded dispatch, durable response checkpoints and per-session spend admission. F4/F5 remain separate gates.

# Next-build durability contract — 2026-09-17

[FOUNDATION_PLAN.md](FOUNDATION_PLAN.md) section 6 replaces three-stage execution. Use a fresh
workflow namespace/store, retaining queue limits, accepted snapshots and outbox reconciliation.
Keep DBOS event-loop ownership.

Tests must prove zero/one dispatch across acceptance, claim, unknown outcome, response checkpoint
and final-commit crashes. Place an atomic guard immediately inside the provider method; a separately
replayable permission step is insufficient. Disable SDK retries and extra repair/verifier calls.
Claimed but uncheckpointed attempts become MODEL_OUTCOME_UNKNOWN; checkpointed output resumes
locally. DBOS alone is not an exactly-once billing guarantee. Evidence below covers the old path.

> **Current release 1.14 / application 0.10.0:** [Workspace specification](WORKSPACE_SPEC.md) and [Analytics specification](ANALYTICS_SPEC.md) govern current behavior. DBOS workflow identities and clinical skills are unchanged from 1.12. [Backlog](BACKLOG.md) records deferred Test/Production isolation and clinical metric adjudication. Earlier release-specific text below is historical where it conflicts. See [Skills Studio specification](SKILLS_STUDIO_SPEC.md) for the new content review and draft editor.

# Skill adoption durability update

Implementation 0.8.0 uses parent qa.review.v5 and child qa.openai.stage.v4. The name changes
isolate newly composed 0.2.0 skill instructions from older pending workflow code.
The actual subprocess test now also captures model-stage instruction hashes, kills execution
before consistency review, modifies the installed skill content so validation fails, then restarts.
The review completes using its original captured instructions; completed language work is reused,
remaining stages see the original bytes, and the config endpoint rejects new work with invalid content.
This test uses the real Agents SDK and DBOS with explicitly controlled model output, no provider calls.

All three subprocess recovery tests passed on 15 September 2026. Default output limit is 6000 tokens,
reasoning medium, HTTP retries zero and timeout 120 seconds. Live budget tests separately use low
reasoning and 2000 output tokens. Same-version recovery does not guarantee exactly-once provider billing.
The baseline record below remains historical.

---

# DBOS validation record

Version 0.4 · 14 September 2026 · Local technical proof completed with stated limits

FastAPI persists the input/config/resource in application SQLite before dispatch. The top-level DBOS identity includes the tenant and review ID. Startup reconciles unfinished application rows, including the commit-before-dispatch gap. DBOS stores execution checkpoints in a separate SQLite system database. Model checks are async child workflows; DBOSRunner checkpoints model responses. State updates and deterministic assembly are durable steps.

| Experiment | Observed result |
|---|---|
| D01 — Complete workflow | Passed through actual API/DBOS in the contract suite. Five accurate completed steps, deterministic copy text. |
| D02 — Restart after completed work | Passed actual subprocess kill/restart. The after-language checkpoint executed once across both processes. |
| D03 — Restart during unfinished work | Passed in the same experiment. The before-consistency checkpoint executed twice; remaining review completed. |
| D04 — Provider success before checkpoint loss | Not exercised against an external provider. A request can repeat in this gap; no exactly-once invocation or billing guarantee. |
| D05 — Transient provider retry | Not tested against a provider. OpenAI HTTP client is configured with max_retries=2 and timeout=45 seconds; no additional broad application retry loop. |
| D06 — Malformed/permanent output | Passed controlled SDK malformed JSON case; terminal failed result with no copyable output. Unsupported demo input also fails explicitly. |
| D07 — Concurrent duplicate API requests | Passed four concurrent requests with one key; one public review identity. Changed report with reused key returns 409. |
| D08 — Acceptance gap | Passed committed resource with no workflow dispatch, followed by backend startup/reconciliation. |
| D09 — Completed result restart | Passed; identical structured result and copy text after restart. |
| D10 — Feedback restart | Passed; original result binding and saved feedback retained, duplicate key returns original feedback. |

## Reproduce

```sh
uv run pytest tests/test_api.py tests/test_sdk.py tests/test_recovery.py -q
```

Tests use isolated temporary databases and synthetic reports. Recovery tests launch and kill their own backend subprocess, reuse its database directory and record test checkpoint counts. Hooks are server-environment-only and inert without QA_TEST_HOOK_DIR; no client can enable them. No database or runtime log is shipped.

Versions: DBOS 2.31.1, dbos-openai-agents 0.3.0, openai-agents 0.22.2, Python 3.12.14. APP_VERSION is prototype-0.4-code-3. Cross-code-version recovery is not supported by this proof; version workflow code deliberately before later deployment.

## Integration correction discovered by testing

Wrapping an SDK child stage in asyncio.run caused executor shutdown to wait on DBOS worker threads. The implemented async child workflow runs on DBOS's event loop and is awaited through its durable handle from the parent. Controlled SDK tests now cover valid, malformed, grounded-designation and unsupported-quote model output. Do not reintroduce a private event-loop shutdown around DBOSRunner.

The local proof supports continuing with this stack. It does not establish clinical quality, provider-side exactly-once behavior or production operational readiness. See IMPLEMENTATION_STATUS.md and the [DBOS integration guide](https://docs.dbos.dev/integrations/openai-agents).

The restart proof was rerun for report-only input. Unknown designation and its exact copy text survive restart without a manual flag. Parent workflow names use v3; the former operator-flag database is not silently replayed under this contract.

The outbox is now reconciled periodically as well as at startup, using an indexed execution-state query. API acceptance, review snapshot and receipt commit in the same transaction. Injected dispatch failure recovers without process restart. Tenant context is captured in workflow arguments and every state write; UI reads no longer mutate execution state.
