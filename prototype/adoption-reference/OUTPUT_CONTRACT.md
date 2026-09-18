> Next-build authority (2026-09-17): [clean-start foundation plan](../FOUNDATION_PLAN.md). Original examples are historical, not current clipboard fixtures. Do not restore the missed-flag line; current Workspace/refinement and foundation govern.

> Original adoption proposal retained as a reference. For implemented behavior and verification, see ../IMPLEMENTATION_STATUS.md.

# Two-group output and copy contract

Proposed adoption behavior; the existing application has not implemented group copy yet.

## Public result

Retain general_comments and critical_comments arrays, outcome, missed_flag,
critical_flag_status, critical_flag_quote and copy_text. Add general_copy_text and
critical_copy_text to the new API projection; both are server-derived strings, empty when
their corresponding group is empty. Each visible Copy button copies its exact server field.
Do not assemble a competing template in React or ask the model to write the template.

Add a deliberate new report_section vocabulary in that projection:
history, indication, technique, comparison, findings, impression, addendum, other, multiple.
Retain both as a compatibility label for exactly Findings + Impression; use multiple for
other cross-section combinations. Candidate source anchors retain the actual section IDs and
original labels internally. Never substitute findings for a comment about Technique.

The public observation still has observation_id, finding_type, report_section and comment.
Internal source anchors, skill ownership, basis and requirement metadata are not leaked by
generic dictionary serialization. Feedback binds to the immutable public observation ID.

## Full-copy example — synthetic, not model output

```text
QA review:

General Comments:
1. Findings describe a 10 mm nodule; Impression gives 14 mm. Please reconcile the measurement.

Critical Findings missed flag: Cannot determine

Critical Findings comments:
1. Impression reports suspected pulmonary embolism. Please confirm critical designation and the applicable communication pathway.
```

## General-only clipboard from that same result

```text
QA review:

General Comments:
1. Findings describe a 10 mm nodule; Impression gives 14 mm. Please reconcile the measurement.
```

## Critical-only clipboard from that same result

```text
QA review:

Critical Findings missed flag: Cannot determine

Critical Findings comments:
1. Impression reports suspected pulmonary embolism. Please confirm critical designation and the applicable communication pathway.
```

The missed-flag line is critical-review metadata. It is not a third comment group and is not
included when copying general comments alone. Preserve its earlier position in full copy.
When there are multiple critical observations, a report-level flag does not prove individual
communication or handling. Do not suppress any retained critical observation because flagged.

## Empty and failed states

| State | Display and copy |
|---|---|
| Both groups contain comments | Two group-copy buttons plus full copy |
| Only general comments | Critical group says None.; critical copy disabled; full copy retains the approved empty-group template |
| Only critical comments | General group says None.; general copy disabled; full copy retains the approved empty-group template |
| Both empty after completed review | Existing no-action message and feedback; no template and no copy actions |
| Running, needs_input or failed | No new copyable result |
| Input edited after review | Old result visibly stale; all copy/feedback disabled until restore or successful new review |
| Clipboard permission/API failure | Keep result; announce failure and allow native text selection; never announce successful copy |

No timestamps, citations, textbook reasoning, internal categories or workflow logs are added
to clipboard content. Exact headings remain controlled by product presentation, not skills.

## Guidance versus comments

Comments tell the radiologist what needs attention. Studio tells QA what to do with those
comments. For critical observations without a supplied operational policy, Studio asks QA to
copy for radiologist assessment and follow the applicable pathway. It does not invent a
facility, phone number, deadline or PACS field. Known policy exceptions affect guidance where
applicable; they never imply that a call occurred or silently erase clinical observations.

If many comments exist, show every independently actionable item in a compact list; allow
scrolling/expansion without omitting any item from full copy. Do not add a findings cap solely
to make the UI shorter. Skill and evidence details stay outside the default copy surface.
