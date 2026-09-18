# Report QA prototype blueprint

Version 0.2 · 14 September 2026 · Product decisions confirmed · Local implementation available; domain/UX acceptance pending

## 1. Purpose and boundary

QA pastes the current report into one field, selects the radiologist's existing critical-finding flag, requests review, copies the standard output when observations exist, and optionally submits feedback. The prototype accepts any radiology report category; it does not limit intake to one modality. Acceptance of a report type does not establish validated review quality for that type.

The initial boundary ends at displayed/copied comments and saved feedback. There is no review-history screen, fleet, evidence viewer, citation UI, chat, PACS/HL7 integration, image analysis, report editing, delivery tracking or automatic learning. The broader framework remains a future reference, not the prototype feature list.

The user subsequently authorized prototype implementation. The connected local implementation and observed checks are recorded in IMPLEMENTATION_STATUS.md; the broader MVP remains deferred.

## 2. Input contract

| Input | Requirement | Behavior |
|---|---|---|
| Report text | One required paste field | Must contain identifiable, substantive findings and impression sections. No separate clinical input boxes. |
| Radiologist critical-finding flag | Separate required Yes/No selector | Label: “Did the radiologist flag a critical finding?” Neither option selected initially. It is not required inside the pasted text. |
| Report category | Any pasted radiology report | No modality picker or category restriction required initially. |
| Other metadata | Not required initially | Author/signature are unknown. Do not invent patient, facility or communication information. |

Preserve the complete submitted text and supplied flag as one immutable input snapshot. Identify sections without silently changing their meaning. The implemented conservative parser accepts English colon headings Findings/Finding and Impression/Impressions/Conclusion/Conclusions, including inline headings. Unlabelled narrative currently requires clarification. If either section is missing, empty or ambiguous, ask QA to supply a report meeting the minimum requirements. Do not continue with a partial review.

Missing text or an unselected flag can be detected before submission. Identifying the sections can occur during input validation. Failed section identification yields needs_input, with a specific request such as “Please include an identifiable impression section.” Downstream review steps do not run. The separate operator flag is the prototype source for designation status. Recognition of conflicting embedded flag metadata is deferred; arbitrary narrative metadata is not parsed as a second flag.

## 3. Structured review

| Step | Responsibility | Boundary |
|---|---|---|
| Input validation | Check text/flag and identify required sections. | Stop with needs_input when minimum report requirements are not met. |
| Language review | Identify meaningful spelling, dictation and terminology issues. | Avoid unnecessary stylistic changes and changing clinical meaning. |
| Consistency review | Detect contradictions within/between findings and impression. | Ask the radiologist to reconcile; do not choose the diagnosis or correct side. |
| Critical finding review | Identify report-text critical observations using the configured policy, when available. | Respect negation, uncertainty and historical context. No image interpretation or claims that a call was missed. |
| Comment assembly | Validate, deduplicate, group, calculate missed flag and render the fixed template. | Do not invent new clinical findings or silently discard substantive concerns. |

These are five logical steps, not a commitment to five autonomous agents or model calls. Start sequentially. Derive the missed flag and copy text deterministically from validated review output. Report text is data, never instructions to the application.

The user will provide the Vesta QA manual and critical-findings vocabulary later. They are intended policy sources. Packaging as instructions, skills or a knowledge base remains an implementation decision after reviewing their content. Record policy version and provenance with a real review; distinguish provisional/example behavior from Vesta-policy-backed review. The absent manual does not block fixture-based UX/API/DBOS work, but policy-specific AI validation requires the supplied materials or an explicitly agreed provisional policy.

## 4. Critical finding and missed-flag semantics

Surface critical-finding comments whenever QA identifies a critical finding, even if the report is internally consistent or the radiologist already flagged it. This decision deliberately prioritizes visibility; measure unnecessary radiologist attention during later evaluation.

| QA identifies a critical finding | Supplied radiologist flag | Critical Findings missed flag | Critical comments |
|---|---|---|---|
| Yes | No | Yes | Included |
| Yes | Yes | No | Included |
| No | No | No | None |
| No | Yes | No | None; do not infer an incorrect radiologist flag solely from model non-detection |

For completed reviews, missed_flag = critical_finding_detected AND NOT radiologist_critical_flag. This is a comparison using QA's assessment and the operator-supplied flag, not independently verified PACS activity. A report-level flag cannot establish that every separate critical finding was individually identified. The prototype does not infer additional missed identifications beyond this agreed rule.

Critical detection/grouping and finding type are separate. Suggestions and discrepancies remain typed internally. The derived missed flag does not itself add an extra clinical observation or inflate the count. A future unmet_requirement observation requires explicit policy support; the initial prototype calculates the agreed boolean instead.

## 5. Standard comments and copying

One standard format for all radiologists. Comments are read-only; QA can copy them or suggest changes through feedback. No inline editing or radiologist-specific profile configuration.

Exact labels and ordering:

```
QA review:

General Comments:
[Numbered non-critical observations]

Critical Findings missed flag: Yes/No

Critical Findings comments:
[Numbered critical observations]
```

Mixed synthetic example:

```
QA review:

General Comments:
1. Findings: “silhoutte” → “silhouette”. Please correct if appropriate.

Critical Findings missed flag: Yes

Critical Findings comments:
1. Impression describes acute right pneumothorax. Please review critical designation and the applicable communication pathway.
```

The selected input flag for this example is No. With Yes, only the derived missed-flag value changes to No; critical comments remain. Illustrative wording is not an approved clinical template beyond the user-confirmed section structure.

Implemented display convention: whenever at least one observation exists, retain the entire standard template; write “None.” in a comment section with no observations. This maintains stable copy formatting without asking another low-impact question. Number observations within their own sections. A single Copy QA review action copies the complete visible template; manual text selection remains available. Section-specific copy actions are deferred from the earlier concept to keep this first UX minimal.

When both observation groups are empty after a successful review, show “No actionable observations” with supporting text “In the supplied report.” Do not display or export the template, missed-flag field, empty sections or any copy action. Feedback remains available. The internal completed missed-flag value can still be No; its absence from the no-observation UI is intentional.

Failed, incomplete and needs_input reviews never produce a successful empty result or a copyable partial template. No-observation output is not a release or clinical correctness decision.

## 6. UX reference and state contract

| Area | Contents |
|---|---|
| Left Scope | Slim current-report context; no history or fleet navigation. |
| Center workspace | Report input above comments; inline flag and Review action row; exact read-only template or no-observation result, Copy beside output, feedback. |
| Right Studio | Compact QA Review and Feedback controls, five truthful step states and a short next step outside copied text. |

![Updated single-field review concept — synthetic result, UX review pending](assets/paste-review-concept.png)

This reference uses the selected neutral light style: white surfaces, thin separators, readable typography and restrained attention cues. The No radio is selected only because this is a completed synthetic example; the initial screen must have no default. Generated image spacing and typography are illustrative; the text/data contract governs. There is no live QA execution behind the image.

Detailed empty/running/error/feedback states are specified in UX_STATES.md. No comments tab, history screen, disabled future tools or animated agent diagrams are required. UX_DESIGN_SYSTEM.md specifies the restored Scope–Work–Studio architecture, typography and action placement. The generated image has an incidental “No displayed evidence” caption; omit that implementation-facing sentence in the actual UI. Drawn dimensions do not override the explicit component sizing contract.

| Situation | Required interaction |
|---|---|
| Input edited after submission | Treat any report-text or flag change as a new draft. Mark old results stale and disable copying against the changed draft. |
| Restore submitted input | Restore both report text and flag; old result becomes correctly bound again. |
| New intentional review | New immutable snapshot/run. Reset result-specific copy and feedback UI. |
| Clipboard failure | Do not claim copied; offer selectable plain text. Copy never records delivery. |
| Connection loss | Retain known run identity and show unknown/reconnecting status; do not fabricate completion or a new job. |
| Current report only | No list/history navigation. Retain backend records for evaluation as a proposed storage default; do not expose past reviews as a product feature. |

## 7. Lightweight feedback

Thumbs-up saves a positive rating in one action. Thumbs-down opens a short in-context form. Only reason is required; explanation and suggested wording are optional, including for “Other.” Reasons: missed observation, unnecessary observation, incorrect observation, wrong grouping, unclear wording, other.

Default scope is the whole result. Optional observation selection allows feedback on a specific comment; the missed-flag field can be targeted as a result-field option. Feedback is also available on no-observation results to report a miss. Automatically bind feedback to the exact review/result/input; do not ask QA for IDs. Save success requires acknowledgement; preserve form content after a save failure.

Feedback does not edit the existing comments, automatically establish ground truth or update prompts/models. Model and manual/policy versions must remain resolvable from the reviewed result for later investigation.

## 8. Decisions and remaining dependencies

| ID | Status | Decision |
|---|---|---|
| P01 | Confirmed | Any pasted radiology report; current report only. |
| P02 | Confirmed | One paste field; identifiable findings and impression required; ask QA to repair input before review. |
| P03 | Confirmed | Explicit separate required Yes/No flag; no initial default; not part of the copy/paste requirement. |
| P04 | Confirmed | Surface critical comments whenever identified; calculate missed flag using the truth table. |
| P05 | Confirmed | User-specified standard comment format; copy-only; no template/copy action when no observations. |
| P06 | Confirmed | Thumbs-down requires reason only; explanation and suggested wording optional. |
| P07 | Confirmed | Vesta QA manual/vocabulary to be added later; packaging not yet chosen. |
| P08 | User preference | Python, FastAPI, DBOS, OpenAI Agents SDK; compatible installed versions checked; real provider evaluation pending. |
| P09 | Implemented defaults under build authorization | React/TypeScript/Vite, local prototype, sequential workflow, polling, full-template copy, “None.” for an empty group when another group is populated. |
| P10 | Preserved boundary | Evidence UI, fleet, integration, editing, history and detailed MVP planning remain deferred. |

Product scope is confirmed through the conversation. Clinical policy content, exact check catalogue, final user acceptance and real provider quality remain unvalidated. Installed SDK/DBOS compatibility has passed controlled integration checks. Do not reopen settled product questions while proceeding with the authorized design work.
