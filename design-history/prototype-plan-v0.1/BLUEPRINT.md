# Report QA prototype blueprint

Version 0.1 · 14 September 2026 · Draft for review · No application implemented

## 1. Purpose and current boundary

Prove that QA can paste a simple report, request a structured review, understand the outcome, copy concise comments for a radiologist, and submit useful feedback. The first prototype starts at manual input and ends at displayed/copied comments and saved feedback. It does not end at HL7, PACS delivery or clinical communication.

This document narrows the broader framework for the first prototype; it does not replace the longer-term product vision. The user requested planning before building. This package provides a reviewable plan. Gates are not marked passed by document creation.

## 2. What is included

| Capability | Prototype behavior |
|---|---|
| Manual input | Two fields: findings and impression. Preserve exactly submitted text in an immutable input snapshot. No patient identifier required. |
| Requested review | One explicit Review report action. No background review while typing. |
| Structured execution | Input validation, language review, consistency review, critical-finding review, comment assembly. |
| Completed outcome | No actionable observations, or observations to communicate. |
| Comment output | Critical-review and non-critical sections, concise numbered comments, copy per section or all. |
| Guidance | One short next step outside copied comments. No invented PACS destination or recipient. |
| Feedback | Thumbs-up; thumbs-down opens a brief form. Feedback also available on no-observation results. |
| Recovery visibility | Distinguish queued, running, completed, needs input and failed. Never substitute an empty successful result for an error. |

Deferred: citations and evidence UI, images, tech sheets, upstream QA ingestion, fleet management, chat, recipient profiles, report amendment, release decisions, HL7/PACS integrations, voice calls, operational analytics, automated learning and production deployment. Basic internal input/run provenance remains necessary even while citations are deferred.

## 3. Report review contract

| Step | Responsibility | Boundary |
|---|---|---|
| Input validation | Validate presence/length and whether sections can be reviewed. | Empty input is rejected before enqueue. Apparently unusable text can lead to needs_input; not a no-observation result. |
| Language review | Identify meaningful spelling, dictation and terminology issues. | Avoid preference-only rewrites and changing clinical meaning. |
| Consistency review | Identify conflicting statements within or between sections. | Ask the radiologist to reconcile; do not decide which diagnosis or side is correct. |
| Critical-finding review | Surface potentially critical observations actually expressed in the input. | Respect negation, uncertainty and historical context. Do not infer an absent PACS flag, call or unmet local requirement from missing metadata. |
| Comment assembly | Deduplicate, group and validate concise radiologist-facing output. | Preserve substantive concerns and uncertainty. Do not introduce a new clinical judgment or silently remove unresolved concerns. |

These are logical responsibilities, not a commitment to five agents or five model calls. Start sequentially. Evaluate the simplest suitable agent arrangement during the AI phase. A conservative assembly routine can be deterministic; exact allocation is a technical validation decision.

Text inside the report is data, not instructions to the application or model. No tools that send messages, modify reports or access unrelated data are needed.

## 4. Result meaning

Execution status and review outcome are separate fields. Outcome is null until the complete review has succeeded. On success it is either no_observations or observations. Empty comment groups on a failed run do not mean no observations.

A critical-review observation can be worth communicating even when the report already describes it correctly. It is not automatically a discrepancy or confirmed critical designation. Grouping (critical_review/non_critical) remains separate from finding type (suggestion/discrepancy/unmet_requirement). In this prototype, do not emit unmet_requirement unless a defined requirement and the necessary input support that assertion; no local clinical requirement is supplied initially.

No-observation wording: “No actionable observations identified in the supplied text.” This means no comments from the completed checks, not a clearance or diagnostic guarantee.

Comments should name the issue or report location and ask for one clear action. Do not copy internal workflow status, provider/model details, cost, feedback metadata or operator routing instructions. Source quotations can occur naturally in a comment; there is no evidence viewer in this phase.

Illustrative mixed output:

```
CRITICAL REVIEW — RADIOLOGIST CONFIRMATION NEEDED
1. Impression describes acute right pneumothorax. Please review critical designation and the applicable communication pathway.

NON-CRITICAL OBSERVATIONS
1. Findings: “silhoutte” → “silhouette”. Please correct if appropriate.
```

This synthetic wording is a design example, not an approved clinical template. Comment quality must be assessed with appropriate reviewers during evaluation.

## 5. UX blueprint

Retain the chosen neutral light visual language: readable typography, thin separators, compact controls and restrained attention color. Adapt the three-panel structure to the smaller task rather than recreating the fleet.

| Area | Contents | User benefit |
|---|---|---|
| Report input | Two labeled text fields, synthetic sample selector, Review report button | Clear starting point and straightforward testing |
| Comments for radiologist | Result summary, populated comment groups, copy actions and feedback | Main deliverable is visible without a tab |
| Review progress and guidance | Five truthful step states; one next step and scope note | Understand progress and what to do next |

Do not fill unused space with disabled future tools. On narrow screens stack input, results and progress while keeping the running state visible near results. No animated agent activity diagram is needed.

![Earlier paste-and-review concept — layout reference, not final validated UX](assets/paste-review-concept.png)

The concept above predates this contract: it shows four steps and omits comment assembly. The next UX revision must show all five logical steps, distinguish failed/needs-input states and demonstrate the feedback form. Its completed observations and checkmarks are synthetic, not real review output. The earlier fleet reference remains the broader product reference only.

## 6. Interaction contract

| Situation | Expected behavior |
|---|---|
| Empty or whitespace-only section | Inline field explanation; no request submitted. |
| Review requested | Freeze submitted snapshot; prevent accidental duplicate submission; display actual execution state. |
| Input edited after submission | Mark the draft as different. Retain old result identity, but disable copying it while the edited draft is shown. Allow restoring reviewed input or requesting a new review. |
| Review completed with observations | Show only populated groups; no Comments tab. Copy controls select exact final text. |
| Review completed without observations | Show scoped no-observation message, no empty comment boxes/copy controls, feedback still available. |
| Clipboard succeeds/fails | Confirm only on success. On failure provide selectable text and a clear explanation. Copy does not record delivery. |
| Connection lost | Preserve known run ID and show reconnecting/unknown state. Do not fabricate failure or successful completion. |
| Failed or needs-input review | Explain recovery action; do not expose partial text as final copyable comments. |
| New review finishes | Switch to its result and reset result-specific UI state. Never attach prior feedback to the new review. |

## 7. Feedback contract

Thumbs-down opens a form in context. Default scope is the whole review; selecting a specific observation is optional. Required: one reason and a short explanation. Optional: suggested replacement comment. Thumbs-up can be saved in one action.

Reasons: missed observation, unnecessary observation, incorrect observation, wrong critical/non-critical grouping, unclear wording, other. “Other” still requires an explanation. Allow a missed-observation report against a no-observation result.

Automatically bind feedback to review ID, result version, input hash, and observation ID when selected. Store prompt/workflow/model versions with the review so they can be resolved later. Do not ask users to enter these. Show save success only after acknowledgement; preserve form content on failure. Feedback remains an allegation or suggestion for review, not an automatic gold label, prompt update or model training signal.

## 8. Assumptions and decisions

| ID | Status | Decision or assumption |
|---|---|---|
| P01 | User requirement | Browser UI, manual findings/impression input, requested multi-step review, copyable comments, simple feedback. |
| P02 | User preference | Python backend, FastAPI boundary, DBOS durable execution, OpenAI Agents SDK. Technical fit must be demonstrated. |
| P03 | User constraint | Evidence/citations later; validate UX, API and DBOS before preparing the detailed MVP blueprint/implementation plan. |
| P04 | Proposed default | React, TypeScript and Vite for the browser prototype; neutral light tokens from the selected design. No final stack lock yet. |
| P05 | Proposed default | Sequential workflow and polling first; introduce parallelism or streaming only if validation identifies a benefit. |
| P06 | Scope interpretation | Critical-review candidates are distinct from incorrect text and missing communication. No facility-specific policy is available. |
| P07 | Proposed default | Local development and synthetic/de-identified test material; no public hosting or production patient-data workflow in prototype. |
| P08 | Agreed sequencing | Plan first. Build phase by phase against reviewed contracts; do not leap from this package to a live product. |
| P09 | Unknown, explicit | Author, signature, PACS flags and prior communication are unknown for pasted text. No fabricated metadata or negative assertions. |

Open before relevant phases: UX layout acceptance (G1), API details and storage boundaries (G2/G3), specific DBOS/SDK versions (G3), model choice and evaluation expectations (G4), trial participants (G5). No calendar dates, budget or clinical acceptance thresholds have been agreed.
