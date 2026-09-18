> Next-build authority (2026-09-17): [clean-start foundation plan](../prototype/FOUNDATION_PLAN.md). This broader framework is a design reference, not extra foundation scope. Preserve the current application's history, feedback, analytics and tenant drafts. Fresh data and one-call DBOS execution supersede older implementation assumptions; historical examples are not new runtime or clinical evidence.

# UI system design — v0.1

13 September 2026 · Framework v1.2. This defines component, state and integration boundaries for the comments-first UX. It is a logical design, not a running frontend, selected backend stack or implemented clinical workflow.

## 1. System responsibilities

| Layer | Owns | Does not infer |
|---|---|---|
| UI shell | Scope, fleet, selected report, compact/expanded presentation and Studio | QA truth, clinical decisions or external completion |
| Read-model adapter | Maps supplied cases, versions, packets, guidance and receipts into stable UI records | A passed upstream check as universal local coverage |
| Review/workflow service boundary | Versioned QA outputs, configured routing, action availability and recorded outcomes | The UI does not implement this service or its clinical policy in this phase |
| Source/integration boundary | Report versions, provenance, external messages, corrections and configured handoff receipts | Facility reading/acceptance from an HL7 acknowledgement |

The same supplied comment packet and guidance record drive compact and expanded views. Do not call a model independently for each panel. A stronger model can improve upstream QA and guidance without changing UI state meanings or panel responsibilities.

## 2. Component tree and data direction

WorkspaceShell contains ScopePanel, FleetList, SelectedReportWorkspace and ReviewStudio. The selected workspace renders QaReview, Evidence, Report, Timeline, Communication or Feedback. QaReview renders CommentSections in both modes, and adds ReviewDetail in expanded mode. ReviewStudio renders the stable ToolPalette and the immediate GuidedNextStep. It does not duplicate the whole selected report.

Data flows from the read-model adapter to components. Selection/disclosure stays local. Consequential action intent goes through the command boundary and returns a recorded result. Transport updates change the underlying versioned records, not an independent copy in each component.

## 3. Three kinds of state

| State class | Examples | Ownership and lifetime |
|---|---|---|
| Recorded domain state | Source/version/signature, QA run/findings, packet revision, guidance, decision, delivery, correction, handoff | Supplied authoritative records; retain historical versions |
| UI navigation state | Filter, sort, selectedCaseId, activeTool, reviewMode, selectedFindingId, inspectedVersionId, fleetScrollAnchor, returnContext | Local to the user's workspace; changing mode cannot mutate domain state |
| Interaction state | Copy attempt/result, pending command, loading/error, connection freshness | Short-lived; distinguish attempted action from recorded business outcome |

Keep canonical entities keyed by ID and retain their version. Derive display labels/counts from those records. Do not separately store a copied selected-case object that can become stale. This follows the general principle of avoiding duplicate and contradictory state in [React's state-structure guidance](https://react.dev/learn/choosing-the-state-structure); the principle is useful even if a different framework is selected.

A practical starting implementation is TypeScript with React and CSS custom properties, subject to the next build decision. No animation framework, chart library or global state library is required by this design. Select dependencies when implementing, not from the images.

## 4. Read and command contracts

These are logical operations, not prescribed URLs or a finalized API schema.

| Operation | Input / returned data | UX consequence |
|---|---|---|
| Read fleet | Explicit scope/filter; case ID, exam, independent coverage/outcome/dependency/handoff, revision | Render summaries without loading every report/evidence body |
| Read selected review | Case ID; exact source refs, packet/guidance revisions, findings, current action availability | Show compact comments and next step; clear old case content while pending |
| Read detail/source | Case, source version or finding/check ID | Load complete evidence/history as requested; never silently substitute latest source |
| Read updates | Last known revision/cursor when supported | Update affected records; identify stale or unavailable connection state |
| Copy text | Packet revision and section; local clipboard result | Record transfer only after success; no external message command |
| Submit action intent | Case/source/packet/guidance revision, action type, target, actor session and idempotency key | Server rechecks authority, binding and freshness before consequential work |
| Receive action outcome | Request identity, performed/failed/pending state and supplied receipt | Show only the outcome actually established; reconcile unknown results before retry |

Capability/permission fields are presentation hints from an authority boundary; server-side checks remain necessary for real actions. Version conflict returns a stale-state response and refreshed context instead of silently acting on a newer report. Sending the same request twice must not create duplicate communications; define idempotency at the action service when integrating.

For initial prototypes, a fixture adapter implements reads and explicitly simulated outcomes. For later integration, swap the adapter and keep the UI contracts. Backend orchestration, model selection, persistence technology, deployment topology and production clinical rules remain separate design decisions.

## 5. Core interaction sequences

**Selection:** select stable case ID → clear prior packet/action context → read/select the case record → show compact comments plus guidance. A slow response for a previously selected case cannot overwrite the current selection. If review is still running, show Pending or partial coverage; do not fabricate comments or present absence as clearance.

**Expansion:** set reviewMode to expanded → keep the same packet/guidance → reveal assessment/evidence and fuller follow-through in the center. Detail can show a local loading state while comments remain usable. Collapse restores the prior fleet anchor. Neither operation invokes AI or modifies the report.

**Copy and delivery:** verify the named section/payload is current and previewable → attempt clipboard write → announce copied only on success. Recording a PACS paste is a separate action with actor/time/destination and available evidence. An accepted designation decision can coexist with pending clinician communication and an unverified correction.

**Live update:** apply newer records by ID/revision → update affected rows and counts → retain selected inspection context → mark changed source/packet/guidance stale when applicable. A history view stays historical. Urgent information is visible without automatic navigation or repeated notification for the same event.

## 6. Rendering and loading strategy

- Start with ordinary semantic rows for the expected 10–20 concurrent reviews. Do not add virtualization merely because this is a fleet UI. Measure larger lists before introducing it; preserve keyboard/navigation semantics if later needed.
- Fleet queries return summaries. Fetch full report/evidence/history for the selected case or explicit inspection. Bound caches by case/version and avoid preloading every historical report.
- Subscribe/select data narrowly so one case update does not rerender every report body. Batch bursts of ordinary status changes at a short cadence if profiling demonstrates a need; urgent state must not wait behind a long cosmetic batch.
- Keep stable row/component keys. Do not resort a focused list automatically. Use explicit refresh/reorder affordances where needed.
- For a connected implementation, a single workspace update channel is preferable to one timer per case. Choose polling or streaming from actual adapter capabilities; do not add infrastructure solely for animation.
- Avoid per-row second-by-second clocks. Display elapsed waiting time at an appropriate shared cadence; exact timestamps remain available.
- Use system fonts, a small reusable icon set and CSS tokens. Do not ship generated reference screenshots as UI backgrounds or recreate controls with image assets.
- No default heavy animation/chart dependency. Long historical documents may use deferred rendering when measured necessary; comments and the immediate next action remain the first useful content.

## 7. Proposed performance checks for the first prototype

These are acceptance targets to measure, not results already achieved. Record browser, device and dataset with each result.

| Scenario | Proposed target / observation |
|---|---|
| Select or expand already-loaded case | Visible response within about 100ms on the agreed test desktop; no network requirement for disclosure itself |
| Load missing detail | Show local pending state promptly; latency of the backend remains separately measured |
| Twenty concurrent synthetic cases | Smooth selection, scrolling and text copy; no full-list remount or focus jump on one-row update |
| Burst of ordinary updates | UI stays responsive; no growing pending-update queue or repeated alerts for one event |
| Repeated case switching | Superseded requests cannot overwrite current case; memory/cache growth stays bounded |
| Reduced motion / zoom | Meaning and task completion preserved without animation or smaller text |

Profile before optimizing. Avoid long main-thread tasks and continuous background rendering, but do not invent a universal bundle-size or frame-rate claim for an unbuilt app.

## 8. Evolution without losing familiarity

New checks populate the existing review groups and finding/evidence objects. New destinations enrich guidance and adapters. More autonomous actions still expose actor, authority, state and receipts. Additional capabilities should live within existing Studio tools before adding another primary surface. Themes change tokens, not component behavior or semantic state.

## 9. Next development phases

1. Select a visual direction and confirm the default density through a small walkthrough.
2. Build the fixture-based shell with compact/expanded review and one concrete guidance scenario. Include a 20-row synthetic stress fixture; no clinical execution.
3. Validate keyboard use, comments/copy integrity, stale-case handling, independent workflow states and measured responsiveness.
4. Connect one read-only source adapter. Define real action authority, destination mapping, version conflict and receipts before enabling a consequential action.

These phases extend the existing framework. They do not require a full backend or autonomous orchestration platform before testing the core UX.
