> Next-build authority (2026-09-17): [clean-start foundation plan](../prototype/FOUNDATION_PLAN.md). This broader framework is a design reference, not extra foundation scope. Preserve the current application's history, feedback, analytics and tenant drafts. Fresh data and one-call DBOS execution supersede older implementation assumptions; historical examples are not new runtime or clinical evidence.

# QA review comments — output and interaction contract

Framework v1.2 · 13 September 2026

## 1. Purpose

Produce **clear, concise, well-organized comments a radiologist can act on**, and that a human or another authorized agent can copy into the appropriate PACS QA/comment field. This is a named output of QA Review, not the internal QA Brief, raw evidence, a new diagnostic report, or proof that communication happened.

Default structure: one specific concern, the minimum supporting observation, and one clear requested action per item. Usually one or two sentences; this is a brevity target, not a limit that truncates essential context. Avoid blame, filler, generic “please review,” unsupported certainty, or repeated messages for the same unresolved issue. Critical concerns take precedence over preferences for batching or fewer interruptions.

## 2. Distinct surfaces and responsibilities

| Surface or object | Audience / question | Contents |
|---|---|---|
| Selected-report workspace | Container: which case and view is open? | Persistent case/version/author/signature header; active tool content below. Not a duplicate QA summary. |
| QA Review — compact default | Operator and radiologist output: what needs attention now? | Immediately visible critical/non-critical comments, concise QA status and current next step. |
| QA Review — expanded detail | Operator: what supports this output and how is it completed? | Same comments first, followed by internal QA Brief, typed findings, limits, evidence and fuller follow-through. |
| Comment packet | Radiologist-facing deliverable in both modes | Exact recipient-adapted plain text; separate from operator routing instructions. |
| Evidence | Reviewer: what supports this concern? | Exact inputs and locations, missing-field search scope, version comparison, basis and limits. |
| Communication | Operator: what happened after composition? | Copied/prepared text versions, delivery records, replies, interpretation and follow-through. |

Studio retains **QA Review** and five other tools. QA Review opens directly to **Comments & next steps**, not a Brief tab. **Compact** and **expanded** are presentation modes for the same deliverable. Expand review reveals supporting assessment/evidence in one click; Collapse review restores fleet context. Do not add a seventh tool or a second click for Comments.

Compact comments use a shared case/version header and flat critical/non-critical rows, with readable concise wording and small copy actions. Do not replace the comments with an abstract AI summary. Expansion adds support, not a different or longer radiologist message. Full operational guidance may grow in expanded mode; the recipient text stays identical for the same packet revision.

For many/long comments, show critical priority, exact counts, visible incompleteness and an explicit “Expand to review all N comments.” Never silently hide urgent concerns. A full-section copy requires its full exact payload to be reviewable; if it cannot fit compactly, change the control to “Expand to preview and copy,” rather than invisibly copying unseen items. Do not automatically expand during live updates.

## 3. Two sections; separate type from urgency

The UI always exposes two section labels, with counts and any incomplete-assessment status. Copy actions omit an empty section by default; never insert “no critical findings” merely because there is nothing to copy.

| Section | What belongs here | Required wording |
|---|---|---|
| Critical-review comments | Concerns routed to the critical pathway by configured criteria; can be potential or confirmed | State whether confirmation is needed. Do not call a model candidate a confirmed clinical finding. |
| Non-critical QA comments | Other discrepancies, unmet requirements and optional suggestions | State the specific issue and requested correction/clarification; distinguish optional suggestions. |

Every finding carries a **type** (suggestion, discrepancy, unmet requirement), an independent **urgency/routing classification**, and an independent **decision/confirmation status**. “Potential critical finding” is a clinical confirmation label, not a fourth finding type. Type does not determine priority: a discrepancy can be critical under policy; a potential critical finding remains unconfirmed until an authorized decision. Unknown urgency remains visibly unclassified and requires routing clarification; it is not silently placed in the non-critical section. Present any required unresolved assessment even when both comment lists are empty.

The section split organizes communication. It does not by itself decide report release, clinical severity, time thresholds or a mandatory phone call. Those come from explicit organizational/facility policy. Critical review must not wait for routine wording changes. If sending the critical item alone is required, support copying only that section while leaving other comments intact.

## 4. Portable text contract

Each packet is bound to one case/accession, recipient role/identity, source report version, review run and profile version. The rendered text contains a concise case locator and report version/status so it can survive being pasted outside this UI. An explicitly configured case-bound destination may omit redundant identity, but only after the destination binding is verified. Never mix different cases or radiologists in one copied packet.

Plain text is the baseline: numbered items, line breaks and simple section headings. No reliance on colors, chips, hover citations, HTML, Markdown tables or application-only links. Include short section names/quotes when needed; store full evidence and internal IDs in the structured packet. Do not paste internal audit chatter, unneeded patient details, model reasoning, profile configuration, or unsupported findings into PACS.

Available actions: **Copy critical comments**, **Copy non-critical comments**, **Copy all comments**. Display the exact preview, selected section, case, recipient, version and resolved template before copying. The compact shared identity header supplies the same case/version information included in each standalone export; cosmetic UI labels and operator next steps are excluded. A short displayed comment and its copied body must match; expansion must not substitute a verbose hidden message. A later adapter can consume the same structured packet and exact text. Target length/character restrictions require a visible edited preview; never silently truncate a critical concern or its action.

For a draft/preliminary report, guidance can request an authorized update and re-review. For a signed report, request clarification and the approved amendment/addendum pathway if appropriate. Never offer an unauthorized overwrite. Unknown signature state requires verification before editing guidance or a consequential correction action.

## 5. Example templates

Templates use placeholders for design illustration only. Exported ready-to-copy examples must have all placeholders resolved from supplied data.

### Concise non-critical discrepancy

```text
QA review | {case_locator} | Report {version} ({signature_status})
NON-CRITICAL QA COMMENTS
1. {location_a} states "{quote_a}"; {location_b} states "{quote_b}". Please {specific_authorized_request}.
```

### Structured non-critical suggestion

```text
QA review | {case_locator} | Report {version} ({signature_status})
NON-CRITICAL QA COMMENTS
1. Suggestion: {specific_wording_issue}.
   Action: {permitted_optional_next_step}.
```

### Potential critical finding / missing flag

```text
QA review | {case_locator} | Report {version} ({signature_status})
CRITICAL-REVIEW COMMENTS — CONFIRMATION NEEDED
1. {source_location} states "{quoted_finding}"; {inspected_flag_field} is {observed_value} in the reviewed input. Please confirm the critical designation and follow the applicable critical-result communication pathway if confirmed.
```

The critical example is a synthetic communication design example, not a clinical detection rule. It does not prove that a call failed to happen; an unset flag and absent communication evidence are different facts. Do not invent absence from an inaccessible PACS field.

## 6. Radiologist-specific adaptation without changing authority

A small **communication profile** may vary nature, scope, template and guided action. This is a reference object, not a new settings console to build now. Show the resolved profile name/version and provenance beside the preview. If none is available, use a labeled conservative organizational default; never infer permission from a doctor's terse reply or historical writing style.

| Dimension | May vary | Must remain invariant |
|---|---|---|
| Nature/tone | Concise question, direct correction request, structured issue/action wording | Factual support, uncertainty and respectful language |
| Scope | All actionable concerns; optional suggestions when requested; one issue or case-level bundle | Required concerns cannot be hidden; critical routing cannot be downgraded |
| Template | Section headings, numbering, short vs structured wording, local field constraints | Case/version binding, material evidence and requested action |
| Guided action | Ask doctor to correct; ask doctor to clarify; record a separately authorized QA correction | Permissions and signed-report restrictions must come from explicit policy |
| Attention preference | Bundle compatible routine comments; suppress duplicate notifications | Do not delay time-sensitive critical communication or conceal unresolved work |

Precedence: organizational/facility requirements and role permissions first; explicit approved case instructions within those boundaries next; documented radiologist communication preference next; default last. A profile can reference an authorization policy but cannot create edit/send privileges. If preferences conflict with a requirement, preserve the requirement and explain the adjustment internally.

Avoid a style preference being promoted to an “error.” Optional suggestions can be omitted from outbound text when a profile requests that, but remain in the internal QA record. Do not omit discrepancies or requirements merely to shorten a packet.

## 7. Composition, copying and follow-through

Keep independent states rather than treating the following as automatic successive approvals:

- Content: draft, ready for authorized use, needs re-review, superseded.
- Transfer: not copied, copied; optional export/delivery record.
- Delivery: unknown, recorded by human, confirmed by integration.
- Decision: pending, needs clarification, accepted, rejected.
- Correction: not performed, performed, verified.

Copying does not transmit to PACS and does not change delivery, decision, correction or handoff state. A user recording “pasted into PACS” supplies a destination/time/actor and optional evidence; label that as human-recorded delivery until independently confirmed. Sending to a QA comment field is not proof of critical-result communication to a physician.

Source or finding changes invalidate the relevant composed text. Preserve the old packet and create a revised version; flag stale text visibly and require regeneration/review before routine current-case copy actions. Historical text may be inspected, but is not presented as a current ready-to-send comment. If the source changes after copying, warn that the copied version is stale and offer a revised packet; do not imply you can recall the clipboard or remote paste.

Human edits create a new comment revision with actor and reason when supplied. Do not allow an edit to silently detach the evidence link. If editing adds a material unsupported claim, flag it for review. Avoid re-sending an already outstanding concern; a clarification packet explicitly links to the earlier exchange and asks only what remains unresolved.

## 8. Radiologist attention cost

Evaluate communication by the time and mental effort it asks of the radiologist: reading length, repeated contacts, number of distinct decisions, unnecessary context switching, ambiguity requiring another reply, and avoidable low-value suggestions. These are design criteria, not an invented numeric score or production target.

A useful review asks: can the radiologist identify the issue and requested action from the first item? Are related routine concerns grouped? Is an already-sent concern being repeated? Is a critical concern clearly separated and allowed to progress immediately? Is a short reply sufficient to resolve the actual question, or will it be ambiguous?

## 9. Context-specific next steps

Comments answer the radiologist's question: what should I clarify, correct or confirm? Guidance answers the operator/agent's question: who does what next, in which system/field, and what proves it happened? Both are primary outputs of review. Studio shows the immediate next step; expanded review exposes the conditional continuation and its supporting basis. Guidance can identify a PACS destination and paste field, an existing chat thread, a critical-result pathway, or a signed-report amendment and verification task. It is not limited to copy/paste.

Keep these two audiences separate. “Paste critical comments into the configured PACS QA field for R-209” is an operator instruction and does not belong in the radiologist comment. “Please confirm the critical designation” belongs in the comment. See `GUIDED_ACTIONS.md` and `guidance-examples.json` for the minimal contract and scenarios.

## 10. Minimal example artifacts

`comment-packets.json` supplies structured packets with profile provenance and target binding. `comment-examples/` supplies exact plain-text exports. Examples include two hypothetical alternative profiles for R-207 (not two simultaneously active preferences) and separate critical/non-critical outputs for R-209. These are drafts for demonstration; they have not been copied into PACS, delivered, clinically confirmed or executed.
