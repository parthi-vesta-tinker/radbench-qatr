> Next-build authority (2026-09-17): [clean-start foundation plan](../prototype/FOUNDATION_PLAN.md). This broader framework is a design reference, not extra foundation scope. Preserve the current application's history, feedback, analytics and tenant drafts. Fresh data and one-call DBOS execution supersede older implementation assumptions; historical examples are not new runtime or clinical evidence.

# Decisions, assumptions and open questions

Version 1.2 · 13 September 2026

“Agreed” means supported by explicit direction in this conversation. “Proposed” means a design default supplied here, available for revision. Neither status authorizes a clinical action or external integration.

## Decision register

| ID | Status | Decision | Why / consequence |
|---|---|---|---|
| D01 | Agreed | Deliver a reusable UX framework before detailed implementation. | Solve stable structure now; defer complex operational features. |
| D02 | Agreed | Use NotebookLM-inspired three-panel architecture. | Familiar places for scope, work and specialized views/actions. |
| D03 | Agreed | Use filters/favorites instead of stage-partitioned screens. | Supports 10–20 simultaneous reviews without allocating one column per stage. |
| D04 | Agreed | Keep QA findings and supporting evidence prominent. | Oversight must show actual review results, not just agent activity. |
| D05 | Agreed | Preserve timeline and evidence inspection as a distinct capability. | Supports spot checks, disputes and subsequent feedback. |
| D06 | Agreed | Scope report review to text and available context, not image interpretation. | Correct clinical side/diagnosis remains outside report-text inference. |
| D07 | Agreed | Main outbound boundary is configured integration handoff. | Facility delivery is outside the interface's current scope. |
| D08 | Agreed | Communication may remain in external chat. | System links exchanges to decisions rather than requiring new radiologist chat habits. |
| D09 | Agreed | Capture QA, radiologist and facility feedback, including after handoff. | Preserve real-world correction and improvement signals. |
| D10 | Agreed | Support manual external edits initially and greater autonomy later. | Performed and verified action states support both actors. |
| D11 | Agreed | Include Studio tools for specialized views and contextual actions. | A stable extension point is more valuable than adding an agent button per feature. |
| D12 | Superseded by D30 | Six initial Studio tools in fixed order. | QA Brief, Evidence, Report, Timeline, Communication, Feedback; exact labels remain refinable. |
| D13 | Proposed | Four stable review groups. | Inputs/context, Language, Consistency, Critical findings in text; clinical check catalogue deferred. |
| D14 | Proposed | Separate coverage, outcome, dependency and handoff states. | A complete review may still contain an unresolved issue. |
| D15 | Proposed | Selecting a tool changes center inspection; Studio retains controls. | Avoid duplicated documents and preserve fleet context; refined by D27/D32. |
| D16 | Proposed | Use This shift as the reference's initial scope. | The sketch includes an acknowledged case; Active would mislabel that collection. |
| D17 | Proposed | Keep selected content stable during live updates. | Avoid focus theft, accidental action on a different case and lost orientation. |
| D18 | Proposed | Feedback creates a linked record; no automatic retraining. | A disagreement needs interpretation and may not establish an AI error. |
| D19 | Proposed | Show concise action-specific authority, not a global autonomy slider. | Capability and permission are separate. |
| D20 | Proposed | Use compact Studio tools and purposeful optional motion. | Preserve space for evidence; static labels remain sufficient. |
| D21 | Proposed | Text specification outranks incidental image detail. | Generated mockups can contain illustrative inconsistencies. |
| D22 | Agreed | Defer complex control/recovery/evaluation consoles. | Do not eagerly solve problems beyond the framework's immediate purpose. |
| D23 | Agreed | Show authorship and signature alongside source version. | Completion does not prove signature; authorship, signer and decision owner are separate. |
| D24 | Agreed | Retain upstream QA provenance when available. | Producer, scope and input version explain what a prior check actually covers. |
| D25 | Agreed | Distinguish suggestions, discrepancies and unmet requirements. | Type remains separate from urgency and clinical confirmation. |
| D26 | Agreed | Consider radiologist attention cost in communication design. | Reduce reading, repeated requests and unnecessary context switching without delaying critical concerns. |
| D27 | Agreed | Differentiate QA assessment, source evidence and the selected-report area. | The bottom center is a container for an explicitly named view, not a second QA Brief. |
| D28 | Agreed | Make clear, concise radiologist comments a first-class QA output. | Separate critical and non-critical comments; support portable copy/paste by human or agent. |
| D29 | Agreed | Adapt comment nature, scope, template and guided action by radiologist. | Explicit profiles preserve required findings, provenance and policy authority. |
| D30 | Superseded by D34–D36 | Rename QA Brief to QA Review, with Brief and Comments subviews. | Six Studio slots remain: QA Review, Evidence, Report, Timeline, Communication, Feedback. |
| D31 | Proposed | Versioned plain-text packets with independent copy/delivery/decision/correction states. | A copied packet is not proof of PACS delivery, acceptance or amendment. |
| D32 | Superseded by D34/D36 | First case selection opens Report / Snapshot; switching tools replaces the selected-report content. | Explicit case/view header prevents duplicate summaries and cross-case residue. |
| D33 | Proposed | Use three finding types and independent critical routing/confirmation fields. | Potential critical is a confirmation label; unknown routing is visibly unresolved. |

| D34 | Agreed | Radiologist comments and context-specific next steps are the primary QA outputs, immediately visible on case selection. | No extra Comments tab or source-first landing. |
| D35 | Agreed | Two modes: concise default overview and one-click expanded detail. | Preserve fleet space; make richer review available without a second navigation step. |
| D36 | Proposed; replaces D30/D32 | QA Review opens Comments & next steps in compact mode; expand gives the center to the same case. | Remove Brief/Comments tabs; internal QA Brief becomes supporting Review detail. Collapse restores fleet position. |
| D37 | Agreed | Guidance varies by case, destination, radiologist and required follow-through. | Explain what/where to paste, actor, critical next steps, other scenarios and completion evidence. |
| D38 | Proposed | Compact shared identity, flat comment rows, small copy actions and immediate next step in Studio. | About 60/40 fleet/overview at reference desktop; readable text takes precedence. |

| D39 | Agreed | Move into UI system design with restrained distinct styles and lightweight component behavior. | Define design tokens, component contracts, state boundaries and performance expectations. |
| D40 | Superseded by D41 | Graphite recommended; Warm Paper and Slate are alternatives using the same component structure. | Style selection remains open; no production UI or framework stack is selected. |

Revision 1.2 source: latest user feedback, 13 September 2026. D34/D35/D37 record the request; D36/D38 are explicit visual/interaction proposals. AC02/20 revised; AC31–AC35 added.

Revision source: user request of 13 September 2026. D23–D29 capture requested provisions; D30–D33 document implementation proposals. Affected criteria: AC17–AC30.

## Assumptions

| ID | Working assumption | If false |
|---|---|---|
| A01 | Primary user is a non-clinical QA operator/supervisor on desktop. | Add role-specific tasks and layouts; do not reuse clinician permissions. |
| A02 | Report completion can trigger intake, with stable case identity. | Define reconciliation and intake behavior before connecting live sources. |
| A03 | Reviewed source versions and their locations can be retrieved. | Label evidence unavailable; do not claim auditability from transient text. |
| A04 | Communication replies can be matched to case and sender. | Require manual linkage/confirmation; never guess from ambiguous text. |
| A05 | Outbound integration exposes some verifiable receipt/status. | Specify truthful sent/unknown semantics; do not invent acknowledgement. |
| A06 | Existing organizations decide clinical ownership and action authority. | Establish these before enabling mutations; mock examples remain inert. |
| A07 | Some cases can proceed without routine human review under configured policy. | The same framework supports approval-required paths. |
| A08 | Tech-sheet requirements vary by context. | Do not hold every report merely because a sheet is missing. |
| A09 | Feedback may be entered by QA on behalf of a facility. | Add another intake path with provenance when available. |
| A10 | Operators may monitor 10–20 concurrent reviews. | Test density and filtering with representative loads before optimizing for larger fleets. |
| A11 | Sources may expose author, signer and signature metadata independently. | Preserve unknown values; do not infer signature from completion or final status. |
| A12 | Some sources may supply upstream QA records. | Show not provided, not failed or passed; local required coverage still applies. |
| A13 | Approved recipient preferences can be resolved from a documented source. | Use a labeled organizational default; do not infer permissions from behavior. |
| A14 | Destination fields may accept plain text. | Validate actual PACS field/length constraints before integration; never silently truncate. |

## Open questions — not blockers for visual prototyping

| ID | Question | Needed before |
|---|---|---|
| O01 | Which exact checks and sources are required for each report type? | Real QA execution and coverage calculation |
| O02 | Which issues or communications block outbound handoff? | Live release/handoff behavior |
| O03 | Who can edit text, reject a concern or approve an action? | Any consequential action |
| O04 | What exact HL7 acknowledgement constitutes this integration's completion? | Connector implementation |
| O05 | Which messaging channels, recipient policies and response deadlines apply? | External communication |
| O06 | How is an external edit verified and when must checks rerun? | Edit verification/re-review |
| O07 | Who adjudicates disputed feedback and sets its resolution? | Operational feedback workflow |
| O08 | What time window defines This shift, and in which timezone? | Real workspace filtering |
| O09 | What retention/access rules apply to reports, messages and evidence? | Production data handling |
| O10 | What requires an urgent indicator outside a selected filter? | Real escalation behavior |
| O11 | How are signature state and approved amendment workflows exposed? | Live correction actions |
| O12 | Who owns/approves communication profiles and conflict resolution? | Live personalized communication |
| O13 | Which PACS field, case binding and text limits apply? | PACS copy workflow validation or adapter |
| O14 | Which upstream checks may satisfy which local requirements? | Reuse of upstream QA coverage |
| O15 | Which criteria route a concern into critical review or leave it unclassified? | Clinical routing and time-sensitive communication |

| O16 | Which destination and field mapping is authoritative for each case and workflow? | Contextual live routing; unknown paths stay visibly unresolved |

## Deliberately deferred

Autonomy policy editor; fleet pause/bulk recovery; shared incident clustering; model performance dashboards; formal sampling programs; automatic learning; multi-agent topology views; API/DB choices; production connector setup; predictive SLA scoring; voice call orchestration UI. Add these only for an explicit subsequent requirement.

## Changes from prior concepts

- Stage columns were rejected in favor of intelligent scope selection.
- The exception-only screen was rejected as the default fleet experience.
- Timeline/evidence remains valuable as a case tool.
- The matrix became an optional detailed view; the primary fleet rows lead with coverage, QA outcome and next step.
- Studio gained a stable palette and a separate contextual action area.
- Broad future operational controls were moved out of the initial scope.
- Final image corrected: All active became This shift; completed handoffs are not mislabeled active.

To amend a decision, retain its ID, mark it superseded, and add the replacement with rationale, date, source and affected acceptance criteria. Do not silently change a prior agreed constraint.

## Revision 1.1 changes

D12 is superseded, not silently overwritten. D15 is refined. The current image now shows R-209 Comments; the previous evidence image remains history. Communication profiles are lightweight reference objects, not a new configuration console. Critical/non-critical grouping does not define a clinical severity taxonomy.

## Revision 1.2 changes

D30 and D32 are superseded by the comments-first compact/expanded design. Contextual guidance is a primary deliverable alongside comments. D39 begins UI system/design-system work; D40 was a style proposal, now superseded by the user selection in D41. The latest reference pair has no Brief/Comments tabs.

## Approved visual direction

| ID | Status | Decision | Implication |
|---|---|---|---|
| D41 | Agreed — user selected recommended combination | Fleet-first Linear-inspired center plus Attio-inspired compact vertical Studio; contextual next-step guidance remains prominent. | Supersedes D40. Graphite neutral light token baseline; alternate palettes are studies only. |
| D42 | Agreed — continuity | Comments remain visible below fleet by default; single-click expansion; six fixed Studio tools. | No additional comments tab, stage columns or case-first default. Existing evidence, authority and communication contracts remain unchanged. |

Assumptions: desktop-first operational use, 10–20 concurrent studies, no chosen frontend stack, and no clinical policy or live connector implied by the synthetic reference. Earlier expanded image is a behavior reference only. User validation of task speed, density and actual rendering performance remains future work.
