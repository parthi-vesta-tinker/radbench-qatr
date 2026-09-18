> Next-build authority (2026-09-17): [clean-start foundation plan](../prototype/FOUNDATION_PLAN.md). This broader framework is a design reference, not extra foundation scope. Preserve the current application's history, feedback, analytics and tenant drafts. Fresh data and one-call DBOS execution supersede older implementation assumptions; historical examples are not new runtime or clinical evidence.

# Contextual next steps — framework v1.2

The review produces two primary deliverables: **comments for the radiologist** and **guidance for the person or agent progressing the case**. Keep them connected and visibly distinct.

## Presentation

Selecting a report opens compact QA Review immediately. The center shows concise critical/non-critical comments and a small outcome/coverage line. Studio shows the immediate next step. One-click expansion reveals assessment, evidence and fuller follow-through below the same comments. There is no Comments tab.

Use concrete guidance: “Copy the critical section; paste into Demo PACS → QA comments for R-209; request RAD-DEMO-B's designation confirmation.” Avoid a generic “Action required.” The example destination is fictional; real system names, navigation paths and fields must come from a documented mapping.

## Minimal guidance contract

| Field | Meaning |
|---|---|
| Case / input / output | Case, reviewed source version, relevant finding or comment packet revision |
| Next action | One concrete immediate action, including which comment section when relevant |
| Actor / recipient | Who performs it and whose response is needed; these may be different people |
| Destination | Named system/channel, location/field and case/thread binding when supplied |
| Preconditions / authority | Recorded prerequisites and applicable permission/policy reference, not inferred model permission |
| Completion evidence | What makes this action performed or verified; not the whole case's completion |
| State / dependency | Ready, waiting, blocked, performed, verified, or not applicable, with a specific reason |
| Conditional follow-through | The relevant next branch, such as confirmation, rejection, ambiguous reply or external correction |
| Provenance | Mapping/policy/profile version supporting the guidance; unknown or stale stays explicit |

This extends the existing Action and Decision concepts. Do not build a general workflow editor or an agent topology view merely to render guidance.

## Scenario patterns

| Case context | Immediate guidance | What completes that step |
|---|---|---|
| Routine QA, no flags | Show actual handoff state; no unnecessary radiologist comment | Configured integration acknowledgement, not facility delivery |
| Non-critical discrepancy | Copy applicable comments into the configured QA field or linked channel; request a precise clarification | Recorded delivery; the clinical decision and correction remain separate |
| Potential critical concern | Use the required critical contact route and identified actor; allow critical comments to proceed independently | Designation decision and required clinician communication have separate evidence/status |
| Ambiguous “Already handled” reply | Ask only for the unresolved detail in the existing thread; identify the corrected version if an edit is claimed | Unambiguous authorized decision and, separately, a verified source update |
| Signed report needs correction | Ask the authorized actor to use the approved amendment/addendum path, then obtain the resulting source version | Applied correction is performed; source comparison and relevant re-review establish verification |
| Destination or recipient is unknown | Identify the missing mapping and the role who can resolve it; retain draft comments | Verified destination/recipient binding; do not fabricate a PACS field or silently reroute |
| Required input unavailable | Request the specific input from the configured source/contact and state what cannot yet be assessed | Input received and relevant check rerun; not merely a sent request |

An organizational critical-result route can require action before a designation dispute is settled. Render the applicable rule and parallel obligations; do not universally gate all urgent communication on confirmation or wait for a routine paste task. The simple R-209 branch is illustrative, not that rule.

## Compact versus expanded guidance

Compact Studio shows one immediate action with actor, destination/field, selected section and dependency/completion cue. Expanded Review detail shows the current step and relevant conditional continuation. Both render the same guidance record, not separately generated answers. Avoid duplicating all guidance in both places.

If destination or authorization is unresolved, the next action is to resolve that specific dependency; consequential actions remain unavailable. Draft preparation and inspection can continue. A profile controls presentation and references authority; it does not choose a new destination or grant send/edit privileges on its own.

The default compact text is intentionally short, but it must retain urgent routing, uncertainty, unmet prerequisites and the actual requested action. Long instructions expand; important conditions do not disappear into a tooltip.

## Boundary between comment and guidance

“Please confirm critical designation” belongs in radiologist-facing comments. “Paste this section into the configured PACS QA field” is operator guidance and is not copied into that comment. Copying changes transfer state only. A recorded PACS paste is not proof of a physician conversation. A radiologist decision can be accepted while a communication task remains open. Report edit verification and handoff retain their own states.

Source, packet, destination or policy changes can invalidate dependent guidance. Preserve the old record, make the affected next step require review, and never silently reuse a completed action against another version or case.

## Example artifacts

`guidance-examples.json` binds three synthetic guidance records to the canonical cases. `fleet-rows.json` supplies eight display rows for the compact reference: three canonical case summaries and five explicitly illustrative rows. Neither file claims a live integration or actual QA execution.
