# UX state blueprint

Version 0.2 · Design for review; no interactive application

## Stable structure

Left: slim Scope with Current report. Center: one report textarea above the result/comments and feedback; a separate required Yes/No flag and compact Review action share its footer row. Right: compact Studio with QA Review and Feedback controls, five review steps and contextual next step. Preserve selected neutral-light style and readable body text. No modal requirement for routine feedback, no comments tab, fleet or history. The Studio Feedback control opens/focuses the same form as thumbs-down; it is not another result tab. An empty/not-completed result has no enabled feedback action. Apply UX_DESIGN_SYSTEM.md.

## State specifications

| State | Input area | Center result area | Progress and next step |
|---|---|---|---|
| Empty | Blank report; both radios unselected; helper identifies minimum requirements. | “Your QA review will appear here.” No template or copy. | All five steps pending. Paste report and select flag. |
| Missing flag | Preserve report; inline “Select Yes or No for the radiologist's critical-finding flag.” | No result from this request. | No clinical checks start. |
| Missing section | Preserve text and flag; name findings/impression missing or ambiguous. | “More information needed” plus specific repair request. No partial comments. | Input validation needs_input; subsequent steps skipped. |
| Running | Preserve submitted snapshot; prevent repeated submissions. | “Review in progress” plus current step. No copyable partial output. | Actual step states only; do not simulate progress in live mode. |
| No observations | Reviewed text and flag remain visible. | “No actionable observations” / “In the supplied report.” Feedback visible. No template or copy. | All steps completed; no comment communication required by this review. |
| General only | Submitted input shown. | Full standard template; general comments, missed flag No, critical comments “None.” One Copy QA review control. | Completed. Paste comments for radiologist review. |
| Critical only | Submitted flag remains explicit. | Full template; general “None.”, derived missed flag, critical comments. | Completed. Share review through established workflow; no automatic communication completion. |
| Mixed | Submitted input shown. | General section first, missed flag, then critical comments, following exact user template. | Completed with five steps. |
| Failed | Input retained. | Safe failure explanation; no successful result/template/copy. Explicit retry action. | Failed step and skipped downstream work; do not relabel as no observations. |
| Disconnected | Preserve active review identity. | Last known information with “Connection lost; review status is unknown.” | Reconnect/read existing resource; no automatic duplicate job. |
| Edited draft | Any text or flag change marks a draft. | Old result marked “For previous input”; copying disabled. | Restore reviewed input (both fields) or request new review. |

Buttons and radios need visible keyboard focus and explicit accessible labels. Do not use color alone for critical review or selected flags. On small screens stack areas; place current execution state near results. Runtime behavior and responsive layout still require prototype testing.

## Feedback form

Thumbs-down opens this compact form below the result without obscuring comments:

| Field | Control | Required |
|---|---|---|
| What was wrong? | Single-select reason: missed, unnecessary, incorrect observation; wrong grouping; unclear wording; other | Yes |
| Tell us more | Short text area | No |
| Suggested wording | Short text area | No |
| Applies to | Defaults to whole review; optional observation or missed-flag field | Default sufficient |

Save feedback and Cancel are explicit. Disable/mark saving only during submission. On failure keep entries and show retryable error; on acknowledgement show “Feedback saved.” Cancel changes neither the original result nor stored feedback. Thumbs-up does not open the form. No-observation results support missed-observation feedback with whole-result target.

The submitted reason may stand alone, including Other. Never turn suggested wording into an edited comment in the prototype. No hidden required explanation field in the API.

## Copy behavior

Primary result action: Copy QA review. It copies the complete read-only template exactly, without application labels, execution/provenance metadata, feedback, next-step instructions or paste destination. Announce success after the clipboard operation succeeds. On failure present selectable exact text. No modal confirmation is needed for copying.

All standard headings remain on an observations result, with None. for a group with no observations. A no-observation result suppresses the entire template rather than displaying an empty document. The input flag is not copied as a separate input field; the calculated missed-flag line is part of the user's standard output.

## Next bounded design review

Review the updated completed-state reference and these states. The browser slice is now implemented under the user’s build authorization; use IMPLEMENTATION_STATUS.md for observed evidence. Validate missing-section input, all truth-table combinations, no-observation feedback, clipboard failure and a flag-only edit. The QA manual can arrive later; fixture screens must not claim actual policy-backed review.
