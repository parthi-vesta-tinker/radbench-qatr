# Implementation and verification record

Contract v0.3 · Implementation 0.2.0 · Bundle v1.7 · 14 September 2026

## Current build

The connected local browser/FastAPI/DBOS prototype now accepts report_text only. The critical Yes/No selector, client state and API field are removed. Report-only designation assessment preserves unknown status instead of inventing a missed flag. Critical comments remain visible regardless of whether the report documents a flag.

| Area | Implemented behavior |
|---|---|
| Input | One paste field; minimum findings/impression; no metadata selector. |
| Review | Five logical steps, three model checks; immutable report snapshot and truthful errors. |
| Critical designation | Typed report-derived state; exact source quote required for known status; absent/unclear status remains unknown. |
| Comments | Standard general/critical template; missed flag Yes/No/Cannot determine; exact full-template copy. |
| Feedback | Up or down; reason-only negative feedback accepted; optional details; persistent result binding. |
| Replacement | Changed report makes old results stale; restore original text or run a new review. No carried flag. |
| Durability | Actual DBOS, API outbox recovery, same-version restart and persistent feedback. |
| Handoff | Locked dependencies, OpenAPI, agent instructions, updated blueprint and testing transparency. |

## Verification

The Python suite passed **19 tests**: 13 API/contract, four actual SDK/DBOS tests using controlled model responses, and two actual subprocess-recovery tests. The production TypeScript/Vite build passed. All **five Playwright browser scenarios passed** for the revised report-only flow.

No API key/model was configured for a live provider evaluation. No clinical quality claim follows from these tests. See TESTING_EXPLAINED.md for the exact distinction between prewritten demo outputs, controlled SDK responses, durable recovery and real model assessment.

The current OpenAI client configuration has bounded retries, disabled SDK tracing and store=False. Model response interpretation, report quoting semantics and provider latency/cost remain unmeasured against OpenAI. Quote containment is a source-grounding check, not clinical validation.

## UX validation environment and evidence

Target flow: local app → paste/replace report → Review → visible comments → copy/feedback. The earlier cloud Browser route was blocked from localhost (net::ERR_BLOCKED_BY_CLIENT); this revision uses the already established local Playwright route. Chromium headless shell was reinstalled because its runtime cache was unavailable. Tests use 1536×1024 desktop and 390×844 mobile viewports at http://127.0.0.1:8765, with an isolated backend.

Checks cover page identity/nonblank content, absence of application runtime errors in the primary flow, exact visible/clipboard text, no radio controls, stale replacement and restore, feedback/retry, missing input, demo failure, reconnect and mobile overflow. The actual desktop and mobile screenshots from that run were visually inspected; they do not establish a full accessibility audit or human usability acceptance.

![Actual report-only prototype — synthetic example](assets/implementation-desktop.png)

The input action row is reduced to a short hint and compact Review report action. Center comments remain the deliverable; Studio provides progress and next steps. Unknown flag status is neutral and explained outside the clipboard template. The previous generated image with radios is archived under design-history/prototype-contract-v0.2.

## Upgrade and remaining scope

Application version prototype-0.3-code-2, prompt version qa-prompts-2, and v2 workflow names separate the revised semantics. Default storage is .qa-data-v0.3, with a new browser current-review namespace. A configured directory containing pre-v0.3 requests is rejected with a clear request to choose a fresh directory; existing data is not deleted. Cross-version migration was not implemented.

The local app has no authentication, production data lifecycle, integrations, evidence UI or image interpretation. It remains a synthetic/de-identified prototype. Manual-backed criteria, live AI evaluation, qualified domain review and QA participant acceptance are the next gates before detailed MVP planning.
