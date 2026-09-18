> Current implementation: application **0.13.0**, bundle **1.17**, foundation **F3**. [Decisions and verification](FOUNDATION_CHANGELOG.md) supersede older baseline statements below. Fresh schema 4 and API 2026-09-18 are implemented. F3 adds one combined request, guarded dispatch and durable response checkpoints. F4/F5 remain separate gates.

# Revised roadmap — 2026-09-17

Follow [FOUNDATION_PLAN.md](FOUNDATION_PLAN.md) and [implementation gates](IMPLEMENTATION_PLAN.md).

| Horizon | Scope |
|---|---|
| Implemented — F1/F2 | Contract ownership, fresh schema, pinned qatr references, tenant snapshots |
| Next — F3/F4 | Single-request DBOS safety and existing feature regression |
| Separate gate — F5 | Combined-path clinical evaluation |
| Later | Migrations, PostgreSQL deployment, activation approval UI, environment switch, advanced analytics/triage, integrations |

Tenant scoping, constraints, idempotency, safe failures and tests are foundation work. Reset is a
coordinated cutover, not automatic startup behavior. Earlier roadmap notes below are baseline
history and do not add migration/three-call requirements.

> **Current release 1.14 / application 0.10.0:** [Workspace specification](WORKSPACE_SPEC.md) governs the current UX. [Analytics specification](ANALYTICS_SPEC.md) defines the feedback inbox, stakeholder outcomes, metric denominators and unmeasured clinical performance. [Implementation status](IMPLEMENTATION_STATUS.md) records verification; [Backlog](BACKLOG.md) records deferred work. Earlier release-specific text below is historical where it conflicts. See [Skills Studio specification](SKILLS_STUDIO_SPEC.md) for the new content review and draft editor.

# Analytics phase update — 1.13

Delivered: database-wide operational metrics, feedback inbox, and operator-recorded stakeholder
outcomes. Next gates: local UI acceptance; metric/cohort agreement with qualified clinical and QA
reviewers; independent adjudication including unflagged reports; then measured critical precision,
recall and false-positive rates with coverage and uncertainty. See ANALYTICS_SPEC.md and backlog AN-01.
These features do not pass clinical validation or production-readiness gates automatically.

# Skill evaluation phase update

The G5 evaluation infrastructure is implemented: independently versioned atomic skills, 54
development/held-out cases, bounded stage-level execution, automatic contract scoring and explicit
human review fields. G5 is not passed: expectations remain proposed, no new provider run was made,
and a qualified reviewer has not adjudicated clinical correctness or radiologist attention cost.

# Refinement phase update

Prototype UX refinement now covers concise comments, aligned status, inline headings,
persistent searchable review history and saved feedback. Next: user acceptance of these
changes, representative report-quality evaluation with qualified review, then MVP scope
and design approval. Production integrations, feedback adjudication, retention/access
policy and monitoring remain subsequent MVP decisions, not completed prototype features.

> Release note (15 September 2026): This planning/baseline document is retained for continuity.
> The current skill-enabled prototype is specified in BLUEPRINT.md and API_DESIGN.md;
> implemented features and verified outcomes are recorded in IMPLEMENTATION_STATUS.md.
> Local startup is documented in ../LOCAL_TESTING.md.

# Prototype roadmap and validation gates

Version 0.4 · 14 September 2026 · Build progress recorded; human/domain acceptance pending

## 1. Phase roadmap

| Phase | Primary work | Deliverable | Gate and reviewer |
|---|---|---|---|
| 1 — Contract and blueprint | Agree on report-only input, outcomes, review steps, comments and feedback. | BLUEPRINT.md plus scenario expectations. | G1: product choices confirmed; domain wording/policy expectations require later manual and reviewer input. |
| 2 — UX validation | Refine concept, show empty/running/no-observation/mixed/error/feedback states, then build a small fixture-driven browser slice. | Clickable UX, task observations and refinements. | G2: QA understands the flow and Parthi accepts the UX direction. |
| 3 — API validation | Review resource/state design, then build controlled API responses and test browser/agent clients. | OpenAPI definition, request examples and contract test results. | G3: Engineering and product agree on semantics, error behavior and usability. |
| 4 — DBOS validation | Build the smallest durable workflow with deterministic steps; interrupt and recover it. | Reproducible restart/retry experiments and findings. | G4: Engineering demonstrates durability semantics and records limitations. |
| 5 — AI review validation | Implement SDK-backed review against a reviewed small evaluation set. | Quality/error analysis, step latency and usage results. | G5: Domain reviewer assesses usefulness and critical errors; product decides trial readiness. |
| 6 — End-to-end prototype | Join browser, API, DBOS, AI and feedback; run representative tasks. | Prototype readout with priority improvements and unresolved issues. | G6: Parthi reviews results and chooses the next investment. |

G1 product decisions have been confirmed by the user; clinical-policy content is pending and will be added later. G2 user acceptance remains pending. API tests and the local DBOS proof are complete, with limits in IMPLEMENTATION_STATUS.md. G5 real provider/domain evaluation and G6 user trial remain pending. A document review does not establish an execution test result. Build authorization follows the user's phase instructions; do not ask again when it has already been given for that phase.

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
| Prototype planning package | v0.4 aligned to confirmed product decisions |
| UX concept | Revised to the earlier Scope–Work–Studio framework; visual review pending |
| UX build and validation | Implemented; five automated browser scenarios pass; QA user acceptance pending |
| API build and validation | Implemented; 13 API/contract checks pass |
| DBOS proof | Actual process recovery and controlled SDK tests pass; external-provider ambiguity documented |
| Live model evaluation | Not started |
| End-to-end trial | Connected local demo available; live model and user trial pending |

The user subsequently authorized implementation. Source code, dependency lockfiles and tests are included. No app credentials, runtime database or patient data is packaged.

The latest product decision removes the manual flag. Current report-only workflow/API tests replace earlier flag-input tests. Live provider evaluation and human UX/domain acceptance remain the next gates; reference TESTING_EXPLAINED.md before interpreting sample success as AI quality.

The requested tenant-aware API foundation is implemented and tested. This adds service authentication and API compatibility controls, while retaining the local Vesta UX and deferring browser login, tenant administration, operational quotas and detailed MVP planning. See API_REVIEW.md.
