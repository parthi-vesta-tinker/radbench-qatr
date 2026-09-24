# Workspace contract

The current interface is a responsive Scope–Work–Studio workspace for report-text review.

## Layout and interaction

- **Application bar:** the supplied Vesta logo, secondary Vesta brand label and primary Radiology Report Review title form the left identity group. Share, Settings, Health and appearance form a compact right icon group. Share and Settings are focusable `aria-disabled` provisions with coming-soon tooltips; no sharing or settings operation exists. Health opens a details popover from an icon with a status indicator and an accessible current-status label. Header actions stay grouped on a second row when narrow widths cannot accommodate the full title.
- **Panel artwork:** state-specific vectors follow the supplied visual references: an expanded right panel shows a rounded outline with an inset right bar; a collapsed right panel shows an inset left bar and left-pointing chevron. Left-panel controls mirror those shapes. Mobile drawer openers use the collapsed icon. Tooltips continue to explain expand/collapse state.
- **Feature notice:** a dismissible single-line “New: Collapsible panels” notice sits immediately below QA Studio when expanded. It has no Try it action. Dismissal is browser-local and keyed to this announcement so future notices can use a new key.

- **Scope:** a slim reports column with independent in-tab drafts, active work, recent results, and history access. Selection does not jump when another review finishes.
- **Work:** New review accepts pasted text without a scope badge or permanent instruction. Contextual feedback below the input reports pasted text, unreviewed changes and submission uncertainty. Review again replaces the same saved review and clears the previous output atomically. An edit stays in the same input; before submission the earlier output is marked stale and cannot be copied. Exact text restoration restores its matching output.
- **Typography:** system fonts, an 18px semibold application and work heading, 16px panel headings, 14px secondary sidebar headings, 13px tool labels and 15px report input. New drafts use the heading New review; the matching Studio action is also New review.
- **Studio:** compact tools for New review, Review history, Feedbacks, Analytics, Skills, and Playground. Tool navigation preserves the current report draft and mounted editor state.
- **Review panel:** review steps show real execution state; **Guidance: Next steps** lists the numbered actions for the current state. Guidance is advice, not tracked progress, and stores no per-step state.
- **Feedback:** thumbs down opens a modal dialog with two fields, the required reason and an optional note. Feedback binds to the result, not to an individual comment.
- **Review results:** the output panel is headed **Review Results**. PACS comments and critical findings are visible together with copy actions beside their respective content. Full-template copy is available only when a nonempty result exists. There is no comments tab.
- **Side panels:** Report reviews and QA Studio collapse independently into 60px rails. Expand/collapse controls live in their headers. The collapsed Report reviews rail retains Current review; the Studio rail retains all six tool icons in the same order. Every rail control has a visible hover/focus tooltip and an accessible name. Escape dismisses tooltips without moving focus. The entire Studio side panel, including guidance, collapses together.
- **Skills placement:** six equal Studio tiles in three rows: New review / Review history, Feedbacks / Analytics, Skills / Playground. The destination heading and Playground link also use Skills; reference content remains available inside it.
- **Responsive behavior:** above 1120px both panels default expanded and remember independent browser-local collapse preferences. At 651–1120px both default to rails, with at most one expanded. At 650px and below, Report reviews and QA Studio buttons open modal side drawers over full-width work. Escape, close, backdrop, or navigation dismisses the drawer; focus is trapped while open and returned to its opener on dismissal. Desktop preferences survive viewport changes. Appearance supports light and dark themes.
- **Preserved work:** collapsing panels does not remount editors or reset report input, selection, Skills edits or Playground state. When Studio is collapsed or a mobile drawer is closed, the center always retains the single review journey beside the Review button, with contextual feedback below the review title.

Draft report text lives only in the current tab. The latest submitted text and outcome persist in SQLite. History and the sidebar contain one entry per review, ordered by latest submission. No submitted-text revision history is maintained. Feedback belongs to the review and survives replacement. Only one unfinished review is kept per tab under Current review. New review returns to it without discarding text; there are no numbered draft entries, deletion or Undo controls. Once submission begins, the input locks; an ambiguous HTTP response keeps the exact input and idempotency key available for retry. After reload, users inspect history before intentionally resubmitting.

## Review states

The UI journey shows Input → Validate → AI review → Output. The backend retains input validation, combined report review, output validation and comment assembly; Output represents the last two. Ticks mark completed stages, a warning marks missing input, and a blocker marks failure. The Studio has no duplicate progress list. `needs_input` explains deterministic report-section problems. Failed or incomplete work never displays successful empty comments. `MODEL_OUTCOME_UNKNOWN` tells the operator that the external outcome could not be established and that the system did not retry.

Copy text is always server derived from the same immutable result displayed on screen. Editing a draft makes an older result stale; restoring the submitted text restores the matching display.

## Preserved tools

- Review history is tenant scoped and paginated.
- Feedbacks is a searchable/filterable inbox linked to the original review.
- Analytics shows saved comment counts by inconsistency, critical finding, clinical observation,
  and other issue first; submitted/completed/failed counts are secondary. One period control
  spans 1 hour through all time and includes all review sources. Feedback and unmeasured
  clinical metrics remain distinct in the API and are omitted from this compact screen.
- Stakeholder outcomes are removed; no outcome controls or acceptance analytics remain.
- Skills shows verified installed content and tenant draft revisions; editing never activates a model change.
- Playground runs the real review against curated samples or a pasted report, in isolation. It never becomes a review: no history, feedback, analytics, outcome or copy action, and its banner cannot be dismissed.
- Health is an on-demand timestamped snapshot. Provider metadata is checked only when explicitly requested and does not perform inference.

No control sends a report, edits a source report, triggers clinical escalation, or releases a content draft.

## Secondary workspace typography

Review history, Feedbacks, Analytics, Skills and Playground share 18px page titles,
16px section headings, 14px subsection headings and controls, and 13px supporting text.
Filters are grouped with consistent labels and spacing; mobile controls have 44px minimum
heights. History retains a table on desktop and labelled entries on phones, with every
column available. Skills source editors keep monospace text; Playground keeps its test
boundary and distinct notice. Analytics uses a monochrome four-metric findings row,
a smaller activity row, and one concise clinical-boundary sentence.

The four-stage journey is compact and shares one row with the Review button at desktop and mobile widths. One status message lives below the journey; no duplicate input hint or output status is shown. Copy actions omit the UI-only QA review prefix. Light/dark palettes are monochrome, with amber reserved for progress warning/blocker states.

Contextual review feedback sits directly below the New review/Report review title, above the paste field. The compact journey beside Review uses Input, Validate, AI review and Output. Show the feedback once only.

## Service health presentation

The popup pairs a concise summary with a prominent top-right refresh icon and its Last
checked timestamp. A bordered, keyboard-operable View all N checks disclosure reveals
consistent name/status rows for API backend, Database, DBOS, QA skills and OpenAI.
The OpenAI row has a tooltip-labelled check icon; only explicit activation probes the
connection. Its result updates the row status and summary. Refresh clears that result.
Routine descriptions and model-metadata/no-report disclaimers are omitted from the UI;
connection errors retain actionable messages and codes. Keep monochrome styling,
light/dark appearance, narrow-screen fit, Escape/outside-click dismissal and focus return.

Copy buttons share one size and align with the right edge of their headings. Display comments without numbering; copied groups use PACS comments and omit numbering and the UI-only QA review title. Successful copying adds no contextual message; clipboard failure retains a manual-copy fallback.
