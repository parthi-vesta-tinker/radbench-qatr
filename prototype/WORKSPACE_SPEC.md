# Workspace contract

The current interface is a responsive Scope–Work–Studio workspace for report-text review.

## Layout and interaction

- **Application bar:** the supplied Vesta logo, secondary Vesta brand label and primary Radiology Report Review title form the left identity group. Share, Settings, Health and appearance form a compact right icon group. Share remains a coming-soon provision. Settings opens a modal for Demo/Live run mode, approved core model choices and Playground, Skills and JEV feature switches. Access mode is shown read-only and defaults to local. Health opens a details popover from an icon with a status indicator and an accessible current-status label. Header actions stay grouped on a second row when narrow widths cannot accommodate the full title.
- **Panel artwork:** state-specific vectors follow the supplied visual references: an expanded right panel shows a rounded outline with an inset right bar; a collapsed right panel shows an inset left bar and left-pointing chevron. Left-panel controls mirror those shapes. Mobile drawer openers use the collapsed icon. Tooltips continue to explain expand/collapse state.
- **Feature notice:** a dismissible single-line “New: Collapsible panels” notice sits immediately below QA Studio when expanded. It has no Try it action. Dismissal is browser-local and keyed to this announcement so future notices can use a new key.

- **Scope:** a slim reports column with independent in-tab drafts, active work, recent results, and history access. Selection does not jump when another review finishes.
- **Work:** New review accepts pasted text without a scope badge or permanent instruction. Contextual feedback below the journey reports pasted text, unreviewed changes and submission uncertainty at the corresponding stage. Review again replaces the same saved review and clears the previous output atomically. An edit stays in the same input; before submission the earlier output is marked stale and cannot be copied. Exact text restoration restores its matching output.
- **Typography:** system fonts, an 18px semibold application and work heading, 16px panel headings, 14px secondary sidebar headings, 13px tool labels and 15px report input. New drafts use the heading New review; the matching action at the top of the reports rail is also New review.
- **Studio:** compact tools for Review history, Feedbacks, Analytics, Classification (when enabled), Skills, and Playground. Tool navigation preserves the current report draft and mounted editor state.
- **Review panel:** review steps show real execution state. **Post-review Guidance** provides advice only after a completed, current review; it stores no per-step progress. See the post-review guidance contract below.
- **Feedback:** each PACS comment and critical finding has always-visible thumbs up/down. Whole-review thumbs remain for overall usefulness, omissions and empty results. One shared dialog shows the selected comment, requires a reason for down feedback, and accepts optional explanation and suggested wording (including for Other). Suggested wording never edits the result or copy text. Feedback is disabled for edited or disconnected results. See comment feedback below.
- **Review results:** the output panel is headed **Review Results**. PACS comments and critical findings are visible together with copy actions beside their respective content. Full-template copy is available only when a nonempty result exists. There is no comments tab.
- **Side panels:** Report reviews and QA Studio collapse independently into 60px rails. Expand/collapse controls live in their headers. The collapsed Report reviews rail retains New review and Current review; the Studio rail retains its enabled tool icons in the same order. Every rail control has a visible hover/focus tooltip and an accessible name. Escape dismisses tooltips without moving focus. The entire Studio side panel, including guidance, collapses together.
- **Skills placement:** equal Studio tiles in two columns: Review history, Feedbacks, Analytics, Classification (when enabled), Skills, and Playground. The destination heading and Playground link also use Skills; reference content remains available inside it.
- **Responsive behavior:** above 1120px both panels default expanded and remember independent browser-local collapse preferences. At 651–1120px both default to rails, with at most one expanded. At 650px and below, Report reviews and QA Studio buttons open modal side drawers over full-width work. Escape, close, backdrop, or navigation dismisses the drawer; focus is trapped while open and returned to its opener on dismissal. Desktop preferences survive viewport changes. Appearance supports light and dark themes.
- **Preserved work:** collapsing panels does not remount editors or reset report input, selection, Skills edits or Playground state. When Studio is collapsed or a mobile drawer is closed, the center always retains the single review journey beside the Review button, with contextual feedback beneath its relevant stage.

Draft report text lives only in the current tab. The latest submitted text and outcome persist in SQLite. History and the sidebar contain one entry per review, ordered by latest submission. No submitted-text revision history is maintained. Feedback belongs to the review and survives replacement. Only one unfinished review is kept per tab under Current review. New review returns to it without discarding text; there are no numbered draft entries, deletion or Undo controls. Once submission begins, the input locks; an ambiguous HTTP response keeps the exact input and idempotency key available for retry. After reload, users inspect history before intentionally resubmitting.

## Review states

The UI journey shows Input → Validate → AI review → Results → Classification (when enabled). The backend retains input validation, combined report review, output validation and comment assembly; Results represents the last two. Ticks mark completed stages, a warning marks missing input, and a blocker marks failure. The Studio has no duplicate progress list. `needs_input` explains deterministic report-section problems. Failed or incomplete work never displays successful empty comments. `MODEL_OUTCOME_UNKNOWN` tells the operator that the external outcome could not be established and that the system did not retry.

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
- Playground runs the real review against curated samples or a pasted report, in isolation. It never becomes a review: no history, feedback, analytics, outcome or copy action, and retains a separate Playground title and Run test review action.
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

The journey is compact and shares one row with the Review button at desktop and mobile widths. One status message lives below the journey; a persistent error callout points to its Input, Validate, AI review, Results or Classification stage. Skill or provider configuration failures before review admission point to AI review and retain Retry connection. Error callouts show only the readable message, without request codes, IDs or a technical-details disclosure. The message remains readable on narrow screens and is announced as an alert for errors. No duplicate input hint or output status is shown. Copy actions omit the UI-only QA review prefix. Light/dark palettes are monochrome, with amber reserved for progress warning/blocker states.

The compact journey beside Review uses Input, Validate, AI review, Results and optional Classification. Show contextual feedback once, beneath the journey and associated with the relevant stage.

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


## Playground sample browser

The Playground uses a two-column sample browser and report preview on desktop, stacked
on narrow screens. Sample reports and Paste report are explicit source controls; switching
preserves the selected sample and pasted text independently. The first available sample
is previewed on load. Samples are grouped by use case, searchable by title or report text,
and filterable by category. Selected rows have a visible indicator and pressed state.
Short display titles do not change installed sample content.

Model selection and Run test review sit below the report. Availability labels appear only
in demo mode. Configuration details are collapsed. At the user's explicit request on
24 September 2026, remove the disclaimer banner and repeated clinical/copy restrictions
from this surface. This supersedes earlier banner requirements. Isolation, absence of
copy/feedback actions, server-controlled models, and the four execution phases are unchanged.
Source and model selection stay locked while a run is starting or executing.


## Classification tool

QA Studio exposes **Classification** when the feature is enabled. Its workspace is
scoped to the selected review and latest submitted input version, never the globally
latest run. A new or edited report shows “Review this report to see classification.”
After a completed review with no critical findings, the tool says “No critical findings
were reported. Classification is not applicable.” Other unavailable classifications
show “No classification available.” A small indicator covers loading; actual failures remain visible in Run details.

The compact **Classification Overview** defaults to up to two finding summaries, each
showing the finding group in medium-weight text and a compact Priority label/value. Its neutral heading is clickable when more content
is available, with a chevron indicating expansion. Expanding reveals the finding group,
Report certainty, Communication priority, inputs and feedback for each finding. The current
classification contract has no subtype field; omit subtype until a governed contract supplies it. Inputs used is collapsed by
default and distinguishes report excerpts plus the QA comment from comment-only
fallback on saved legacy runs. New runs show section-labeled target excerpts, full
submitted report context and the QA comment as secondary interpretation in the saved
state disclosure. The introductory JEV sentence and repeated expanded input are removed.
The Classification workspace includes all five fields, raw and available calibrated
probabilities, provider confidence, margin, review flags, saved questions/criteria,
exact JEV state and run details. Feedback remains separate from immutable predictions. A single **Something wrong?** button
opens Accept and Reject / correct choices. Accept saves acceptance. Reject / correct opens
editable labels and a required reason: changed labels save an `edit`, unchanged labels save
a `reject`. Save errors preserve the form and retry receipt. Cancel makes no request.
The overview and shared result card omit the communication-priority verification sentence
and the “Model suggestion · Uncalibrated · Review all labels” sentence at the user's request;
calibration and rubric details remain available in the full analysis.

The journey's Classification stage reflects the existing asynchronous DBOS workflow.
Results remain completed and usable while classification runs or fails. Missing
classifications are never marked successful. A completed
review with zero critical comments marks Classification as not applicable using a
neutral minus-in-circle icon, with hover and screen-reader explanation. Opening the
tool only reads saved data; it never dispatches a provider request. Changing review,
replacing submitted text or beginning new work clears unrelated classifications;
late fetches cannot attach to a different review or input version.


The Classification page has a **Back to report** action above its title. It restores
the selected report workspace without changing review ID, input version, report text
or any unfinished Current review. It does not navigate to a different draft.

## Post-review guidance

Both Studio overview sections use a shared accessible disclosure with a neutral heading
background and expand/collapse chevron only when more content exists. They start collapsed
for each selected review/input version. Collapsing keeps feedback edits mounted; switching
reviews or replacing input resets the sections. Loading/unavailable sections without additional
content have no chevron. Expanding/collapsing does not dispatch provider requests.

The Studio section is titled **Post-review Guidance**. Its heading has a subtle neutral
background, compact padding, and softly rounded corners using theme-aware colors. Before a review,
while queued or running, and after needs-input or failed work, show only the neutral
placeholder “Guidance appears after review.” Do not render
numbered steps, input instructions, running updates, or error recovery here. The
existing journey and contextual review feedback own those messages.

Collapsed guidance shows the first two steps; clicking the heading reveals the complete
list when longer. Numbered advice requires `execution_status=completed`, a non-null result, matching
current report text, and confirmed status. An edited report or disconnected status
suppresses all previous steps and shows “Next steps are available only for a completed
review matching the current report with confirmed status.” Restoring exact submitted
text restores matching guidance once status is confirmed. Completed work without a
result must never fall through to successful empty guidance.

Completed critical results prioritize reading critical findings, confirming designation,
and following the applicable communication pathway before copying comments and rating
the review. Other observations advise reading and copying comments, then rating the
review. Completed empty results state that there are no QA comments to copy and offer
feedback if something was missed; they do not introduce copy controls or templates.

`PostReviewGuidance` owns presentation and `derivePostReviewGuidance` owns pure content
derivation. Studio composes this section alongside the independent finding classification
component. No additional request, persisted step state, or provider call is introduced.

### Planned extensions (not implemented)

- Compose separate guidance modules for review findings, per-critical-finding classification,
  and configured support workflow/radiologist preferences. Use stable action identities and
  finding associations when these modules are introduced; presentation remains independent.
- Bind classification inputs to the selected review, input version, and observation. Only
  current completed classifications may enrich advice. Pending, failed, unavailable, rejected,
  or indeterminate suggestions must not erase critical findings or delay basic review guidance.
  Keep human feedback distinct from immutable model predictions and define its precedence
  before using it to select recommendations.
- Define tenant-scoped support workflow configuration and radiologist preference ownership,
  defaults, precedence, and versioning before adding persistence or settings. Preferences may
  customize wording, ordering, and relevant actions but cannot hide critical observations or
  override applicable clinical policy. Do not infer radiologist identity from report text.
- Classification suggestions are not approved clinical policy. Unknown designation remains
  unknown without an exact report quote. Advice never establishes that communication,
  acknowledgement, report editing, delivery, or stakeholder outcomes occurred, and does not
  execute these actions. Clinical content changes require the existing governed release process.


### Compact Studio interaction and history projection

When guidance has more than two steps, its collapsed preview shows two steps and a
clickable remaining-step count on the third line. That cue and the heading chevron
open the same disclosure. Classification Overview previews group and priority, with
an explicit More details action; expanding reveals all five labels (including
certainty, polarity and temporal status), inputs and the feedback entry point.
Typography uses existing neutral tokens and medium-weight values, not bold category
headlines. Journey connector halves meet at shared column boundaries so Results to
Classification remains connected even when the final column is wider.

Review History adds a Classification column containing only paired finding-group
and communication-priority labels for each current critical observation's latest
completed attempt. Other classification fields remain in Classification. A newer
pending/failed attempt suppresses previous labels; replaced review versions never
appear. Existing saved classification records provide this read-only projection.

### Reports rail navigation

New review sits below the Report reviews heading, above the independently scrolling
list; it remains a labeled button in the mobile drawer and a plus icon with an
accessible name and tooltip when the desktop rail is collapsed. It is not duplicated
in QA Studio. The existing one-unfinished-review behavior is unchanged.

Current review returns to unfinished work and is selected only while that draft is
shown. A selected saved report highlights its own row instead. Recent is the sole
submitted-review section: queued and running reviews appear first, newest first,
with Queued or Reviewing labels and a neutral spinner. They remain independently
fetched so older pending work is not lost behind the newest 20 terminal reviews.
On completion, reports return to latest-submission ordering. Each review appears
once; no Active heading or additional draft entries are introduced.


## Comment feedback

Comment controls submit `target=observation`, the observation ID and the displayed
`expected_input_version`; whole-review controls submit `target=result` with the displayed
version. A thumbs-up saves immediately and confirms beside that comment. A thumbs-down
opens one shared dialog with the original comment as context. Cancel sends nothing.
One shared history loader serves the review; do not fetch history per comment.
Failed saves keep the form and reuse the same idempotency key for the same payload.

The server checks version and completion atomically with saving. Observation IDs may be
reused after replacement, so an observation ID alone is insufficient. Missing or mismatched
versions on comment feedback conflict; an existing idempotency receipt replays before
mutable completion/version checks. Whole-review API submissions without a version remain
supported. Saved feedback survives review replacement and includes its original quoted
comment and submitted version when available; historical records may lack these fields.
Do not show old feedback as a rating of a replacement comment just because its ID matches.

Suggested wording is optional, limited to 2,000 characters, displayed in saved feedback and
the feedback inbox, and never used to overwrite comments or establish clinical ground truth.
Classification-label feedback remains a separate interaction and resource. API feedback
aggregates expose `by_target` counts for whole-review, observation and legacy flag feedback;
these are feedback events, not adjudicated accuracy or unique reviewer votes.

### Classification analysis visibility

Settings includes a separate Classification analysis switch (Full screen), off by
default for new and existing settings that lack the field. It controls the QA Studio
Classification tool and Full analysis link. CF classification continues to control
processing, progress and the compact Classification Overview independently. Enabling
analysis reveals the full-screen view only when CF classification is also enabled.
Disabling analysis while viewing it returns to the report and preserves its draft.
