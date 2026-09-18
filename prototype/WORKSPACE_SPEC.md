# Workspace contract

The current interface is a responsive Scope–Work–Studio workspace for report-text review.

## Layout and interaction

- **Scope:** a slim reports column with independent in-tab drafts, active work, recent results, and history access. Selection does not jump when another review finishes.
- **Work:** the report input appears above the review output. Accepted report text is immutable and read-only. Review report sits beside the minimum-input hint. Revise as new draft leaves the original resource unchanged.
- **Studio:** compact tools for New report, Review history, Feedbacks, Analytics, and Skills & knowledge. Tool navigation preserves the current report draft and mounted editor state.
- **Comments:** general comments and critical findings are visible together with copy actions beside their respective content. Full-template copy is available only when a nonempty result exists. There is no comments tab.
- **Responsive behavior:** the three regions stack on narrow screens without hiding actions or changing data semantics. Appearance supports light and dark themes.

Draft report text lives only in the current tab. Submitted resources persist in SQLite. A delete action supports one exact Undo. Once submission begins, the draft and deletion controls lock; an ambiguous HTTP response keeps the exact input and idempotency key available for retry. After reload, users inspect history before intentionally resubmitting.

## Review states

Accepted work shows the four actual phases: input validation, combined report review, output validation, and comment assembly. `needs_input` explains deterministic report-section problems. Failed or incomplete work never displays successful empty comments. `MODEL_OUTCOME_UNKNOWN` tells the operator that the external outcome could not be established and that the system did not retry.

Copy text is always server derived from the same immutable result displayed on screen. Editing a draft makes an older result stale; restoring the submitted text restores the matching display.

## Preserved tools

- Review history is tenant scoped and paginated.
- Feedbacks is a searchable/filterable inbox linked to the original review.
- Analytics uses the full matching tenant dataset and keeps operational, feedback, acceptance, and unmeasured clinical metrics distinct.
- Stakeholder outcomes are collapsed, append-only, result-bound operator records.
- Skills & knowledge shows verified installed content and tenant draft revisions; editing never activates a model change.
- Health is an on-demand timestamped snapshot. Provider metadata is checked only when explicitly requested and does not perform inference.

No control sends a report, edits a source report, triggers clinical escalation, or releases a content draft.
