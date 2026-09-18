# Phased prototype implementation plan

Version 0.1 · Planning only · 14 September 2026

## 1. Architecture hypothesis to validate

Browser UI calls a small FastAPI review API. FastAPI accepts a versioned input snapshot and starts durable review execution. DBOS sequences review steps and recovery. OpenAI Agents SDK performs the model-backed review responsibilities. The application validates structured output and derives exact copy text. Feedback is stored against the completed result and does not enter the model workflow automatically.

| Boundary | Responsibility | What it does not imply |
|---|---|---|
| Browser | Input, progress, comments, clipboard, feedback form | No release or delivery authority |
| FastAPI | Public schema, validation, idempotency and resources | No clinical reasoning in route handlers |
| DBOS workflow | Step order, durable execution and recovery | No blanket exactly-once guarantee for external effects |
| Review adapter | SDK calls, bounded output, prompt/model version records | No image analysis or external tools |
| Result formatter | Validated grouping, deduplication, exact text exports | No fresh unsupported clinical judgment |
| Persistence | Input/result/feedback identity and durable state | No production retention or access-control solution yet |

The user prefers Python, FastAPI, DBOS and OpenAI Agents SDK. React/TypeScript/Vite is a proposed frontend choice, to accept in UX planning. Local SQLite is a proposed low-friction starting point for the DBOS proof; choose durable-system and application-storage boundaries explicitly after inspecting the installed version. Do not add PostgreSQL, Redis, queues or microservices without a concrete prototype requirement.

DBOS documents a supported OpenAI Agents SDK integration through DBOSRunner. Evaluate it first against the chosen SDK version. Do not layer independent broad retry loops around both SDK and workflow execution without understanding resulting attempts and costs. Reference: [DBOS OpenAI Agents integration](https://docs.dbos.dev/integrations/openai-agents).

The SDK supports typed agent output. Use validated structured results rather than parsing free-form prose as business state. Reference: [OpenAI Agents SDK agent configuration](https://openai.github.io/openai-agents-python/agents/). Recheck the installed APIs and pin compatible versions during the actual technical phase; this plan does not claim tested compatibility.

## 2. Work packages

| ID | Work | Dependency | Reviewable completion evidence |
|---|---|---|---|
| W1 | Review blueprint and scenario expectations; resolve scope/wording issues. | None | Accepted G1 contract and updated decision notes. |
| W2 | Refine the concept into empty, running, completed, failed, needs-input and feedback states. | G1 | Screens showing all five logical steps and exact copy boundaries. |
| W3 | Build fixture-driven browser interactions using a small review-client interface. | W2 visual review | Task walkthroughs, responsive/keyboard checks and clipboard/feedback behavior. |
| W4 | Review the API brief, then define OpenAPI and controlled responses. | UX result semantics stable | Request/response examples and contract checks; G3 review. |
| W5 | Implement the minimum durable workflow with deterministic test steps. | G3 | DBOS experiment results in DBOS_VALIDATION.md. |
| W6 | Implement SDK-backed checks and structured output validation. | G4 | Real model runs clearly distinguished from controlled fixtures. |
| W7 | Review a small evaluation set, then run and analyze it. | W6 and agreed expectations | Errors, usage and latency; domain review for G5. |
| W8 | Connect and trial the complete local prototype. | G2–G5 | End-to-end task observations, feedback retrieval and G6 readout. |

No production code is included in this planning package. Build one work package at a time after the applicable user review. Once a work package is authorized, complete ordinary implementation and verification without repeated permission requests. Pause on a material contract change, not every routine engineering choice.

## 3. Proposed future code organization

| Area | Small initial responsibility |
|---|---|
| backend/api | FastAPI routes and public schemas |
| backend/review | Review contracts, prompts, adapters and formatter |
| backend/workflows | DBOS workflow and durability boundaries |
| backend/storage | Review/feedback persistence and idempotency |
| frontend | Browser workspace and typed review client |
| tests | Contract, state and recovery checks |
| evals | Reviewed examples, run metadata and result comparison |

These are conceptual boundaries, not an instruction to create an elaborate package hierarchy. Keep them as a few modules until actual code size justifies more structure. Keep fixture and real-model modes explicit; never fall back silently from OpenAI to fixtures when a key or call fails.

## 4. AI review validation

Begin with approximately 12–20 diverse synthetic/de-identified examples, including clean text, meaningful language issues, contradictions, critical candidates, negation, historical/uncertain statements, unusable input and instructions embedded in report text. This is a diagnostic starter set, not a clinical validation sample.

Domain reviewers establish expected observations and unacceptable behavior before evaluation. Allow semantically equivalent wording; exact string comparisons alone are insufficient. Separate a development subset from a small held-out subset and report any reuse during tuning.

Capture actionable observation precision/recall with explicit denominators, critical-review false/missed flags, meaning-changing comments, unsupported metadata assertions and unnecessary rewrites. Also capture total/step latency, failures, attempt counts and actual token usage. Estimate cost only when a verified pricing basis is recorded; missing usage stays unknown. Report examples of errors alongside counts.

Set quality and acceptable-attention thresholds with the reviewer before using results to pass G5. A tiny set cannot establish clinical safety. Technical success, reviewer usefulness and suitability for live use are different conclusions.

## 5. Practical verification boundaries

Use meaningful checks: failed/incomplete cannot become no_observations; copy matches displayed result; edited inputs cannot inherit old results; feedback targets an existing result; duplicate requests map correctly; restart/retry retains identity. Broaden tests only to resolve a concrete risk or phase gate.

For UX, assess actual task completion, copy mistakes and unnecessary clicks. For performance, measure the built interface and model pipeline separately. For DBOS, use real process restarts, not only mocked exceptions. For real AI, report provider/model/version and whether the run actually called the provider.

Initial development uses synthetic material. Before real patient-data use, separately decide access, retention, logging/tracing, provider configuration and deployment controls. This is an explicit later boundary, not a request to implement a compliance platform now.

## 6. Handoff after each phase

Record: what was built or reviewed; observed evidence; failures and limitations; decisions changed; whether the phase gate passed; exact next bounded task. Do not turn a successful UI demo into an unqualified statement that QA accuracy or durable recovery is validated.

Only after UX/API/DBOS and the prototype readout should the detailed MVP blueprint, roadmap and implementation plan be prepared. Later integrations and autonomy remain candidates in ROADMAP.md, not implementation tasks.
