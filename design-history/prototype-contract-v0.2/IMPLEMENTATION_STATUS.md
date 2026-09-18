# Implementation and verification record

14 September 2026 · Implementation 0.1.0 · Contract v0.2 · Project bundle v1.6

## Built

The browser, FastAPI API, DBOS durable execution, structured result formatter and feedback persistence are connected. The default synthetic mode exercises the actual backend/workflow, with explicitly canned review observations. OpenAI mode uses three Agents SDK agents through DBOSRunner and typed output. The user authorized implementation after the UX correction.

| Area | Implemented behavior |
|---|---|
| Input | One paste field, explicit flag with no default; conservative English section-heading recognition; missing/ambiguous sections request input. |
| Execution | Five sequential logical steps; three model checks; immutable text/flag snapshot; truthful step/error states. |
| Result | General and critical comments, calculated missed flag, deterministic exact copy text; completed empty result has no template/copy. |
| UX | Scope–Work–Studio; input above comments; compact Review beside flag; Copy beside result; comments visible without a tab; responsive layout. |
| Feedback | Up in one action; down opens inline form; reason required, other text optional; result/observation/field targets; persisted and idempotent. |
| Recovery | API outbox reconciliation, stable DBOS workflow identity, durable completed-step reuse, browser resume by current review ID. |
| Provenance | Input hash/version; manual-paste source version; unknown author/signature; absent upstream QA; workflow/prompt/model/policy identity. |
| Developer use | Locked dependencies, documented start commands, OpenAPI, tests, evaluation export harness and agent handoff. |

## Observed verification

| Check | Result and limits |
|---|---|
| Python suite | 19 tests passed: 15 API/contract, 2 actual SDK/DBOS controlled-model cases, 2 subprocess-recovery cases. |
| Browser suite | 5 Playwright scenarios passed: complete/copy/feedback/stale/restore/reload, empty result, missing input/explicit demo failure, narrow viewport and flag-Yes critical comments; reconnection, clipboard fallback and feedback retry. |
| Evaluation harness | Exported all 12 synthetic seed cases in demo mode, including expected transport/input errors and unsupported-demo failures. Export includes no automated clinical score. |
| Build | TypeScript check and Vite production build passed. No external fonts, canvas, agent animations or large UI component framework. |
| Visual inspection | Actual desktop and 390px mobile screenshots inspected; no horizontal overflow observed in tested viewports. This is not a full accessibility audit or user usability study. |
| SDK integration | Real installed Agents SDK + DBOS adapter executed with a deterministic Model implementation; malformed structured output failed rather than clearing the report. No provider request made. |
| Crash recovery | Process killed after language review and during the next checkpoint. Completed checkpoint executed once; interrupted checkpoint executed twice; same review/input, remaining work completed. |
| Persistence | Exact result survived restart; saved feedback and its idempotency identity survived another restart. |
| Acceptance gap | An actual resource committed without DBOS dispatch was recovered on application startup. |

Tested with Python 3.12.14, DBOS 2.31.1, dbos-openai-agents 0.3.0, openai-agents 0.22.2, FastAPI 0.141.1 and Playwright 1.56.1 Chromium. Lockfiles define the complete installed dependency set. A dependency emits a non-blocking Starlette/AnyIO deprecation warning.

## Visual fidelity decisions

| Framework anchor | Actual implementation |
|---|---|
| Three-panel architecture | Slim Scope, flexible center work area, compact Studio. At narrow widths, secondary content stacks. |
| Deliverable prominence | Comments remain directly below input with Copy in their heading; no tab or inspector click. |
| Input action | Compact Review report belongs to the same action row as the required flag. |
| Typography | System sans; restrained 22/18/15/12–13px hierarchy; text-first report content. |
| Color and motion | Graphite neutrals, blue selected/action states and a small amber missed-flag cue; static step indicators. |
| Studio role | Specialized QA Review and Feedback actions, actual progress and contextual next step; no duplicate comment editor. |
| Intentional prototype addition | Demo-only example selector makes controlled behavior discoverable. It disappears in OpenAI mode. |

![Actual implemented browser workspace — synthetic example](assets/implementation-desktop.png)

Screenshots: assets/implementation-desktop.png, assets/implementation-feedback.png and assets/implementation-mobile.png. These show real UI rendering; assets/paste-review-concept.png remains the earlier generated target.

## Remaining limits and gates

- No API key/model was configured for live evaluation. Clinical correctness, useful wording, latency/cost under a real model and robustness to adversarial report text remain unmeasured.
- No Vesta manual or critical vocabulary was provided. QA_POLICY_PATH supports a versioned plain-text policy snapshot; no knowledge-base ingestion or approved clinical catalogue is claimed.
- Recognition supports English heading variants with colons, including inline Findings/Impression and Conclusion. Unlabelled narrative and arbitrary embedded flag metadata need clarification or later parser work. Input limit is 40,000 characters.
- Outgoing comments are capped by schema per observation, but concision and unnecessary radiologist attention need domain evaluation; schema validity does not establish usefulness.
- SQLite, no authentication, no deletion/retention UI, no access isolation and no production deployment. Use the local synthetic prototype only until those decisions are made for a pilot.
- Same-version process recovery is proven locally. Cross-version migrations, distributed workers and provider-success/checkpoint-loss ambiguity are not validated. HTTP client retries are bounded; transient provider behavior was not exercised against OpenAI.
- QA participants have not yet accepted the revised UX. Browser automation provides implementation evidence, not product or domain sign-off.

## Next

Review the running UX, configure a model for synthetic evaluation, add manual/vocabulary when available, agree expected comments with a domain reviewer, and record results using scripts/evaluate.py. Then decide the detailed MVP scope from that evidence.
