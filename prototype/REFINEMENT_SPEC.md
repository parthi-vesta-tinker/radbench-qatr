> Current implementation: application **0.13.0**, bundle **1.17**, foundation **F3**. [Decisions and verification](FOUNDATION_CHANGELOG.md) supersede older baseline statements below. Fresh schema 4 and API 2026-09-18 are implemented. F3 adds one combined request, guarded dispatch, durable response checkpoints and per-session spend admission. F4/F5 remain separate gates.

> Next-build authority (2026-09-17): [clean-start foundation plan](FOUNDATION_PLAN.md). Preserve comment/copy and history/feedback UX. Historical legacy-receipt migration requirements do not apply at cutover; do not restore missed-flag UI.

> **Current release 1.14 / application 0.10.0:** [Workspace specification](WORKSPACE_SPEC.md) and [Analytics specification](ANALYTICS_SPEC.md) govern current behavior. DBOS workflow identities and clinical skills are unchanged from 1.12. [Backlog](BACKLOG.md) records deferred Test/Production isolation and clinical metric adjudication. Earlier release-specific text below is historical where it conflicts. See [Skills Studio specification](SKILLS_STUDIO_SPEC.md) for the new content review and draft editor.

# Prototype refinement — implementation 0.6.0 / bundle 1.10

This amendment supersedes conflicting baseline UI requirements below.

- QA comments are the primary output, with General comments and Critical findings groups.
  Copy all comments shares the same right edge as Copy general and Copy critical.
  Professional sentence-case labels replace the redundant QA-review subheading.
- A static, accessible five-segment indicator summarizes queued/running/completed/error states.
  No observation-count completion sentence. Review steps and QA comments share a grid row;
  mobile stacks secondary content. No animation dependencies were added.
- Missed-flag display, explanatory note and feedback target are deferred. All current UI copy
  actions omit the missed-flag section. Critical observations remain visible and copyable.
  Internal assessment and legacy API fields are retained for compatibility and future use.
- Recognize inline Findings:/Impression:/Conclusion: after report preamble, plus uppercase
  FINDINGS/IMPRESSION/CONCLUSION labels without colons. Preserve exact raw text and offsets.
  Avoid known prose references and addendum corrections. Missing/duplicate/ambiguous sections
  still request clearer input. This is deterministic parsing, not AI-invented section content.
- Review history is tenant-scoped persistent SQLite data, not browser storage. Search text or
  review ID; filter status, comments/no comments, critical comments and feedback presence.
  Newest-first pages have 20 entries with Load more. Open retrieves the full original input,
  result and steps. Navigation retains the current draft; replacement asks before discarding it.
- Feedback remains append-only and idempotent, linked to review, input hash, result version
  and optional observation. Saved feedback displays rating, reason, timestamp, explanation
  and suggested wording; supports pagination and recovery from loading errors. It does not
  edit clinical results, become ground truth or trigger learning. Edit/delete/triage are later.
- GET /api/v1/reviews adds bounded summaries and filters q/status/outcome/critical/has_feedback,
  limit (1–100), starting_after. Summary projections never contain private candidates/config.
  Feedback counts are null without feedback:read; feedback filtering requires that scope.
  Existing tenant, review-read and cursor checks apply. Search is local SQLite substring search;
  large-scale search indexing, retention policy and production PHI controls remain MVP work.
- API 2026-09-15 gains additive result fields comments_copy_text and critical_comments_copy_text
  for the current UI. general_copy_text remains. Legacy copy_text/critical_copy_text and saved
  POST receipts are unchanged. Existing results receive new copy projections without rerunning AI.
- Parser code changes advance APP_VERSION to prototype-0.6-refinement-1. Finish prior pending
  workflows using the previous release before upgrading. Completed schema-2 records remain
  readable in the same data directory. No cross-version recovery is claimed.
- Clinical SKILL.md content and framework pins remain 0.1.1; no model instructions were changed.
  qatr origin is unchanged. This release improves workflow and presentation, not clinical efficacy.
