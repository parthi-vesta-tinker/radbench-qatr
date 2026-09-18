# Prototype roadmap and validation gates

Version 0.1 · 14 September 2026 · Planned sequence; gates pending

## 1. Phase roadmap

| Phase | Primary work | Deliverable | Gate and reviewer |
|---|---|---|---|
| 1 — Contract and blueprint | Agree on input, outcomes, review steps, comments and feedback. | BLUEPRINT.md plus scenario expectations. | G1: Parthi reviews scope; representative QA/radiologist input on wording. |
| 2 — UX validation | Refine concept, show empty/running/no-observation/mixed/error/feedback states, then build a small fixture-driven browser slice. | Clickable UX, task observations and refinements. | G2: QA understands the flow and Parthi accepts the UX direction. |
| 3 — API validation | Review resource/state design, then build controlled API responses and test browser/agent clients. | OpenAPI definition, request examples and contract test results. | G3: Engineering and product agree on semantics, error behavior and usability. |
| 4 — DBOS validation | Build the smallest durable workflow with deterministic steps; interrupt and recover it. | Reproducible restart/retry experiments and findings. | G4: Engineering demonstrates durability semantics and records limitations. |
| 5 — AI review validation | Implement SDK-backed review against a reviewed small evaluation set. | Quality/error analysis, step latency and usage results. | G5: Domain reviewer assesses usefulness and critical errors; product decides trial readiness. |
| 6 — End-to-end prototype | Join browser, API, DBOS, AI and feedback; run representative tasks. | Prototype readout with priority improvements and unresolved issues. | G6: Parthi reviews results and chooses the next investment. |

G1–G6 are pending. Phase 1 artifacts are drafted; no UX, API, DBOS or model validation is claimed. A document review does not establish an execution test result. Build authorization follows the user's phase instructions; do not ask again when it has already been given for that phase.

## 2. Gate evidence

| Gate | Minimum evidence | If it fails |
|---|---|---|
| G1 | Reviewed scope and examples; definitions of no observations, critical review and feedback accepted. | Revise the contract before implementation. |
| G2 | Users paste, understand result, copy correct section and submit feedback; error and edited-input states understood. | Fix the specific interaction, then repeat affected tasks. |
| G3 | Contract examples/tests cover success, empty result, failure, duplicates, reconnect and feedback binding. | Correct semantics before attaching durable execution. |
| G4 | Process-interruption records show completed work recovery; duplicate API calls and external-call ambiguity explained. | Repair boundaries or simplify orchestration; do not hide retries as ordinary progress. |
| G5 | Reviewed expectations, false/missed observations, classification errors, wording quality, latency and usage. | Adjust checks/prompts and re-evaluate affected cases plus a held-out subset. |
| G6 | Observed end-to-end task completion; material failures listed; feedback retrievable and bound to correct result. | Resolve blocking issues or explicitly defer broader investment. |

Use suggested small cohorts initially: 2–3 QA participants for UX and at least one qualified domain reviewer for clinical comment expectations. These are planning assumptions, not statistical validation. Agree numerical targets before judging AI evaluation results; none is invented here.

## 3. What the prototype teaches the later product roadmap

| Horizon | Candidate scope | Dependency; no commitment yet |
|---|---|---|
| Supervised prototype | Manual paste, requested AI review, manual copy, feedback. | G1–G6. |
| Pilot MVP | Candidate: one intake source, limited report cohort, access controls, operational support and a supervised handoff. | Detailed MVP blueprint and implementation plan are prepared later, after prototype validation. |
| Post-deployment enhancements | Candidate: communication integration, evidence inspection, profiles, more input sources, selective automation and fleet operations. | Prioritize using observed workload, feedback and quality; each needs its own authorization and validation. |

Do not include these later capabilities in prototype code to “prepare for scale.” Preserve only useful contracts: immutable inputs, structured results, stable IDs, versioned prompts, independent feedback and a replaceable API boundary.

## 4. Progress record

| Item | Actual status |
|---|---|
| Prototype planning package | Drafted for review |
| Earlier visual concept | Available; requires five-step/status/feedback refinement |
| UX build and validation | Not started |
| API build and validation | Not started |
| DBOS proof | Not started |
| Live model evaluation | Not started |
| End-to-end trial | Not started |

Dependency setup was started in an earlier turn and stopped at the user's direction. It is not implementation or validation and is excluded from the deliverable. No app credentials, runtime database or patient data is packaged.
