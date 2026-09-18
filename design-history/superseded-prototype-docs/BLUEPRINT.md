> Current implementation: application **0.13.0**, bundle **1.17**, foundation **F3**. [Decisions and verification](FOUNDATION_CHANGELOG.md) supersede older baseline statements below. Fresh schema 4 and API 2026-09-18 are implemented. F3 adds one combined request, guarded dispatch and durable response checkpoints. F4/F5 remain separate gates.

# Next-build architecture — 2026-09-17

[FOUNDATION_PLAN.md](FOUNDATION_PLAN.md) supersedes three-call, generic-only and migration targets.
Reuse FastAPI/SQLite/DBOS/Agents SDK and the current workspace as a modular monolith. Add one
combined request, immutable snapshots and a fresh explicit app schema with a fresh DBOS store.
Preserve history, feedback, outcomes, analytics and Skills Studio. Import all three pinned qatr
references/43 entries with authority labels. Tenant drafts stay separate from active content.
Two comment groups, report-only scope and no automatic clinical actions remain. Baseline below
is not evidence that the replacement has been implemented.

> **Current release 1.14 / application 0.10.0:** [Workspace specification](WORKSPACE_SPEC.md) governs the current UX. [Analytics specification](ANALYTICS_SPEC.md) defines the feedback inbox, stakeholder outcomes, metric denominators and unmeasured clinical performance. [Implementation status](IMPLEMENTATION_STATUS.md) records verification; [Backlog](BACKLOG.md) records deferred work. Earlier release-specific text below is historical where it conflicts. See [Skills Studio specification](SKILLS_STUDIO_SPEC.md) for the new content review and draft editor.

# Current refinement contract — v0.6 / bundle 1.10

Read [REFINEMENT_SPEC.md](REFINEMENT_SPEC.md) first. It supersedes conflicting baseline requirements below: missed-flag UI/copy is deferred; comments, progress and Studio layout are refined; inline headings, persistent review history and saved feedback are implemented. Preserve legacy API receipts and clinical instructions.

---

# Report QA prototype blueprint

Contract **v0.5** · implementation **0.5.0** · bundle **v1.9** · 15 September 2026.

QA pastes one current report and selects **Review report**. Keep the Scope–Work–Studio layout,
one input field, five truthful workflow steps and comments directly below the input.
There is no separate critical flag control and no comments tab.

## Input and review

Report text is immutable once accepted; maximum 40,000 characters. Require substantive Findings
and Impression/Conclusion. Support colon or standalone headings and optional history, indication,
technique, comparison and addenda. Retain the full raw report in every model call, with an exact-offset
section index. Repeated required sections request clarification instead of merging separate studies.
More subtle report identity/addendum ambiguity can be returned by the model as needs_input.
Absence of optional context is not a mandatory-field error.

Five logical steps: deterministic input validation; language review; consistency review; critical
finding review; deterministic comment assembly. Three sequential model calls use the separate
skill package, including stage-specific drafting and self-verification. No tools or image interpretation.
A review is not a medical diagnosis or release authorization.

## Main deliverable

Two concise, read-only groups for radiologists, each with a copy button. Full copy remains:

```text
QA review:

General Comments:
1. [Issue, location, requested correction or clarification.]

Critical Findings missed flag: Yes/No/Cannot determine

Critical Findings comments:
1. [Report-supported potential critical finding and requested review/action.]
```

Use None. for an empty group only when the other group has observations. Both groups empty after
a completed review means No actionable observations, with feedback and no template/copy buttons.
Failed, ambiguous or truncated reviews never become successful empty results.

Copy general includes QA review and General Comments only. Copy critical includes QA review,
the missed-flag metadata and Critical Findings comments. Copy QA review includes the complete
template. All text is server-derived; internal anchors, rationale, provenance and Studio guidance
stay outside the copy boundary. Copying does not send or update a report.

Missed flag is true only for a critical observation with report-documented unflagged status;
false for report-documented flagged status; unknown when not established. An exact source quote
is required for known status. A diagnosis in the impression or a documented call does not prove
a PACS flag. Critical comments remain even if already flagged. With no critical observations,
the full template uses No. The metadata is not a third comment group.

## Skills and boundaries

`qa-skills/framework/` and `qa-skills/clinical-content/` are separately versioned artifacts.
Nine modules and referenced guidance are selected through the registry, not dynamically from
patient text. The host checks package integrity before acceptance and captures exact instructions,
policy, model settings and versions for retries/recovery. Private candidates require valid ownership,
unique IDs, exact source anchors and appropriate critical basis before public assembly.
These checks do not prove clinical interpretation is correct.

No approved QA manual or critical catalog is supplied. Optional manual text is unvalidated guidance;
critical review is generic/provisional and cannot assert an unmet local mandatory requirement.
Clinical knowledge supports interpretation of report text; it cannot invent patient facts, inspect images,
decide a correct side in a contradiction or assert communication happened.

## Workflow and feedback

New pasted content changes the draft, marks previous results stale and disables all copy and feedback
controls. Restore returns the original submitted report. Review happens only on request. A running
review uses its original snapshot; reload resumes the current review ID. There is no report-history UI.

Thumbs up saves immediately. Thumbs down requires a reason, with optional detail/wording.
Feedback binds to the current immutable result or observation. It never edits the result, overrides
clinical policy or automatically trains the model.

## System boundaries

FastAPI, DBOS, Agents SDK, React and SQLite remain the stack. Vesta is the local tenant;
API authentication supports registered tenants without a caller-selected tenant field.
QA-Version 2026-09-15 supports richer section labels and group copy fields. Legacy receipts and
representable completed results remain readable; old-version creates require upgrade.

Default local persistence is `.qa-data-v0.6`. Finish older pending workflows with their original
application before reusing a database. Same-code recovery is tested; arbitrary cross-version replay
and exactly-once model billing are not claimed. Evidence UI, PACS/HL7/chat sending, report editing,
production data controls, approved clinical evaluation and MVP expansion remain later phases.
