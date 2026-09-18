> Next-build authority (2026-09-17): [clean-start foundation plan](../prototype/FOUNDATION_PLAN.md). This broader framework is a design reference, not extra foundation scope. Preserve the current application's history, feedback, analytics and tenant drafts. Fresh data and one-call DBOS execution supersede older implementation assumptions; historical examples are not new runtime or clinical evidence.

# Handoff for designers and coding agents

Read `FRAMEWORK.md`, then `DECISIONS.md` and `QA_COMMENTS.md`, then `GUIDED_ACTIONS.md`, `DESIGN_SYSTEM.md` and `UI_SYSTEM_DESIGN.md`. This package specifies an extensible interface, not production AI behavior. No application has been built or usability-tested in this delivery.

## Start here

1. Preserve F1–F6 and agreed D01–D11/D22–D29/D34–D35/D37/D39.
2. Treat D13–D21/D31/D33/D36/D38/D40 as explicit proposed defaults, not hidden user commitments.
3. Use `fixtures.json` for the three canonical examples. All names, IDs, snippets and events are synthetic.
4. Match the reference's panel relationships and hierarchy. Preserve the corrected This shift scope label. Do not copy ungrounded timestamps, implicit policies or decorative states.
5. For a later prototype, implement read-only selection, filtering, Studio switching, source inspection and Back to fleet first. Simulate mutations locally and label them clearly. No external messages or handoffs are authorized by the design artifact.
6. Ask about an open question only when the next implementation step depends on it. Do not block an inert prototype on clinical integration details.

## Suggested component boundaries, not stack choices

| Component | Responsibility |
|---|---|
| WorkspaceShell | Three-panel layout and narrow-width presentation |
| ScopePanel | Saved views and editable filters |
| FleetList | Stable case rows, selection and independent state labels |
| SelectedReportWorkspace | Persistent case/version/author/signature header and active tool/mode container |
| QaReview | Comments-first compact / expanded modes; no Brief/Comments tabs |
| GuidedNextStep | Immediate actor/destination/action/completion context in Studio; full continuation in expanded detail |
| CommentPacketPreview | Exact portable text, section copy, profile provenance and independent status |
| CommunicationProfile | Lightweight approved preference input; not a permission grant or settings console |
| QaBrief | Coverage, findings, limitations and next responsibility |
| FindingEvidence | Source comparison, basis, limits and source navigation |
| StudioPalette | Six stable tool selectors and active-state indication |
| ContextActions | Scoped permitted actions, owner and pending state |
| ReportView | Exact source version, annotations and changes |
| CaseTimeline | Recorded events, historical label and return to live |
| CommunicationView | External exchange and explicit response interpretation |
| FeedbackView | Targeted feedback capture and resolution history |

Minimum view state: view/filter criteria, selectedCaseId, selectedFindingId, activeStudioTool, reviewMode, returnContext, selectedPacketId, selectedCommentSection, centerMode, inspectedVersionId, optional historicalEventId, fleetScrollAnchor. Keep view state separate from source records and action outcomes. These fields are conceptual, not a prescribed framework/store/API.

## Acceptance criteria for the next prototype

| ID | Given / action | Observable result |
|---|---|---|
| AC01 | Open This shift | R-201, R-207 and R-209 are visible with truthful independent state labels. |
| AC02 | Select R-207 | Compact QA Review immediately shows R-207 comments and next step, version/author/signature; no additional click and no stale R-201 content. |
| AC03 | Open F-207 Evidence | Exact E-1/E-2 text and report v1 locations appear with the correct-side limitation. |
| AC04 | Open full source | The referenced section/version appears; back restores the selected finding. |
| AC05 | Switch Report → Timeline → Evidence | Selection/filter/scroll remain recoverable; no external action occurs. |
| AC06 | Inspect R-201 | No flags detected and integration acknowledgement are distinct; no clinical correctness claim. |
| AC07 | Inspect R-207 | Coverage complete coexists with one unresolved finding and demo-policy hold. |
| AC08 | Inspect “Already handled” reply | Decision remains unclear/awaiting clarification; no automatic acceptance or release. |
| AC09 | Record an external correction in a mock continuation | Mark performed; verification requires new-version evidence. Original report remains accessible. |
| AC10 | Submit feedback in a local mock | Target IDs/versions are retained; new record is Received; original decision is unchanged. |
| AC11 | Simulate unavailable evidence | Display unavailable/limited state; never fabricate a citation or show no flags as clearance. |
| AC12 | Simulate a new report/version while inspecting | No focus theft; relevant version change is explicit; old evidence stays bound to old input. |
| AC13 | Change filter so selected case disappears | Clear selection and disable stale actions under proposed I5 behavior. |
| AC14 | No selected case | Studio has a useful empty state; case-specific actions are unavailable. |
| AC15 | Keyboard and reduced-motion use | Tools/rows are operable, focus visible, states readable without color or animation. |
| AC16 | Enter historical inspection | Historical event/time/version are explicit; current mutation requires returning to live. |
| AC17 | Signature metadata missing or author differs from signer | Show each known value and explicit unknown; completion/final does not imply signed. |
| AC18 | Upstream language check received; version later changes | Scope/version/trust stay visible; no blanket QA pass. Old provenance is stale for the new input. |
| AC19 | Inspect R-209 | Missing flag is an unmet requirement under DEMO policy, critical routing needs confirmation; spelling is an optional non-critical suggestion. |
| AC20 | Select case → expand QA Review → Evidence / Report | Comments and next steps appear first. Expansion adds assessment and proof; source inspection remains distinct. No Comments tab. |
| AC21 | Copy either section or all R-209 comments | Exact preview matches plain-text exports; identity/version retained; empty sections omitted without a clearance statement. |
| AC22 | Copy, then record a mock PACS paste | Copy alone changes transfer only. Paste record is human-recorded delivery; decision/correction/critical-call status do not auto-complete. |
| AC23 | Compare two R-207 alternative profiles | Wording changes; issue, evidence, recipient, unresolved request and signed-report constraints remain. |
| AC24 | Critical and routine comments coexist | Critical section can progress independently; batching preferences never delay required critical communication. |
| AC25 | Signed report or unknown signature | No overwrite action inferred from preference; use approved amendment guidance or verify status first. |
| AC26 | Source/finding changes after drafting or copying | Packet is marked needs re-review; preserve old revision; current copy requires reviewed replacement. Already copied text cannot be recalled. |
| AC27 | Profile omits optional suggestions | Internal QA finding remains; required concerns are retained in recipient output. |
| AC28 | Critical checks incomplete and comment section empty | Show assessment incomplete; do not display no-critical-findings clearance. |
| AC29 | Compose after “Already handled” | Link the prior exchange; ask only for missing clarification/correction evidence, without re-sending the original request unchanged. |
| AC30 | Urgency cannot be classified | Show an unresolved routing item outside the two classified lists; do not silently treat it as non-critical. |

| AC31 | Select a case, then expand and collapse once each | Compact comments/next step are default; one click exposes detail. Collapse restores fleet selection/filter/scroll; packet text and workflow state are unchanged. |
| AC32 | Inspect guidance for routine, disputed and critical examples | See action, actor, system/field when supplied, section/recipient binding, prerequisite, status and completion evidence. Operator instructions are excluded from copied text. |
| AC33 | Destination, case binding or permission is unknown | Show what is unresolved and how to resolve it. Do not invent a PACS path or enable a live paste/send action. Review and draft preparation remain inspectable. |
| AC34 | Compact content exceeds available space | Preserve urgency and counts; disclose hidden items. Expand offers the full preview in one click; no silently truncated or unseen full-packet copy. |
| AC35 | Clinical designation is confirmed, then communication is pending | Clinical decision can be accepted while the communication task remains open. Guidance changes accordingly; no automatic completion from paste, reply or expansion. |

AC01–AC08 and AC17–AC24 are the first focused walkthrough; include AC31–AC35 for the compact/detail and guided-action changes. AC09–AC16 cover state and navigation risks when interactive behavior is introduced. Passing these is UX behavior verification, not model or clinical validation.

## Do not infer

- No model provider, backend, database, API, repository or hosting platform is selected.
- No clinical threshold, severity taxonomy, release rule, recipient list or message schedule is approved.
- No exact four-check catalogue exists; fixtures use one illustrative check per group.
- No global autonomy level controls the entire workflow.
- A sent message, an accepted concern, an applied edit and an acknowledged handoff are different facts.
- Feedback is not an automatic training label.
- Avoid exposing agent internals or hidden model reasoning as user-facing evidence.
- Do not add operational consoles just because future extension points exist.

## Suggested subsequent phases

**Design walkthrough:** refine routine, disputed and mixed-comment cases with the user, using the same shell. **Inert interaction prototype:** implement the focused criteria above with fixtures. **Targeted refinements:** resolve navigation/density issues from review. **Integration planning:** answer only the relevant open questions before connecting one capability at a time. These are suggested next phases, not work already performed.

## Package checks

`python3 verify_package.py` checks plain-text export equality, profile/packet binding, finding types, signature and upstream metadata, in addition to the synthetic examples' reference integrity, exact quoted evidence, state invariants, and required files. It does not run an AI model, send messages, validate clinical findings, or test a rendered app.

## Selected visual baseline — design system v0.2

Apply D41–D42: fleet above compact comments, single-column six-item Studio, contextual next step, neutral routine states. The current compact image is the appearance anchor. The expanded image is an earlier behavior reference only; use current tokens and Studio list when implementing it. Preserve selection and fleet scroll through expansion. No new comment tab or case-first default.
