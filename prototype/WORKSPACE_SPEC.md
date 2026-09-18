> Current implementation: application **0.12.0**, bundle **1.16**, foundation **F2**. [Decisions and verification](FOUNDATION_CHANGELOG.md) supersede older baseline statements below. Fresh schema 3 and API 2026-09-17 are implemented; F2 imports the pinned qatr references and tenant-bound snapshots; single-call execution and session-spend enforcement remain F3 work.

# Foundation compatibility — 2026-09-17

[FOUNDATION_PLAN.md](FOUNDATION_PLAN.md) changes execution/storage, not the product. Preserve
accepted reviews, independent drafts, Undo, history restore, immutable input and stale-copy checks.
Replace three clinical-stage progress rows with real validation/combined-review/output-validation/
assembly phases. Skills represent check coverage, not independently timed agents. After reset,
stale browser review IDs show not-found/reset; never auto-resubmit their report text.

# Workspace release 1.14 / implementation 0.10.0

This specification supersedes conflicting prototype UI and navigation instructions. The broader
framework remains a future design reference. Public review semantics are unchanged. Clinical skills
are independently versioned at 0.2.0; their UX output contract remains the same.

## Implemented interaction contract

- Left: Reports, with drafts, active reviews and recent results. The bounded recent list contains
  the latest 20 reviews. Active polling separately requests up to 100 running and 100 queued reviews;
  use Review history for larger collections. Selection never changes because another review finishes.
- Center: one paste field above QA comments. Accepted reports are immutable and read-only.
  New report is available during submission, queueing and review. It preserves other drafts and
  reuses an existing empty draft. Revise as new draft leaves the original review untouched.
- Drafts are memory-only in the current tab. Browser reload/close warns when draft text exists.
  Submitted records persist in the application database. Session storage holds only the selected
  accepted review ID; local storage holds only the appearance preference. Neither stores report text.
- Every ordinary draft has a labeled trash icon. Delete removes that draft immediately; Undo restores
  its exact text and selects it. The most recent deletion can be undone until dismissed or replaced
  by another deletion. Deleting the last draft leaves an empty usable draft if no reports exist.
- Once submission starts, input and deletion are locked. A timeout or 5xx retains the input and
  idempotency key for Retry submission. This avoids abandoning potentially accepted work. New report
  is still available. A definitive 4xx rejection unlocks the draft. Pending retries do not survive
  reload in this prototype; consult history before intentionally submitting the same report again.
- Right: QA Studio, with New report, Review history, Feedbacks and Analytics tiles at the top,
  followed by a compact full-width Skills & knowledge tool. It opens the installed-content catalog
  and tenant-scoped draft editor; see SKILLS_STUDIO_SPEC.md. Editing never activates a model change.
  These are workspace tools. Review report and Revise as new draft stay beside the input;
  group/full-copy buttons stay beside the corresponding comments. No comments tab is introduced.
- Review steps and comments share the same grid row. On narrow screens tools and content stack.
  General comments and Critical findings retain their server-derived, independent clipboard content.
  Missed-flag UI/copy remains deferred. No automatic sending, corrections or release is introduced.
- Feedbacks opens a dedicated searchable entry inbox, with rating, reason and source filters,
  pagination and links to the original review. It defaults to Needs improvement / Live AI reviews.
- Analytics queries the entire matching tenant database, not the loaded history page. It separates
  report acceptance, QA-comment acceptance, critical-metric readiness, operations and feedback.
  Periods are rolling UTC windows; source is provenance, never Test/Production environment.
- Completed reviews have a collapsed Stakeholder outcomes log below feedback. Its append-only,
  result-bound decisions distinguish QA, radiologist and facility perspectives and report versus
  QA-comment acceptance. These are operator-recorded claims, not verified signatures or ground truth.
  See [Analytics specification](ANALYTICS_SPEC.md) for metric definitions and limitations.
- Header: Health and light/dark theme. Health opens by click, double-click or keyboard; Escape closes.
  Service detail shows existing API/database/DBOS/skills/OpenAI checks and the timestamp. Status is an
  on-demand snapshot, not live monitoring. OpenAI metadata is checked only on explicit request;
  successful local checks do not establish inference readiness. Theme persists without animations.

## Execution and API

DBOS queue `qa-reviews-v1` admits parent reviews with QA_REVIEW_CONCURRENCY (default 2, range 1–32).
The limit applies across tenants using this application's queue. It bounds parent reviews, not
provider token spend or the SDK's internal requests. Accepted work waiting for admission remains
queued. Child model workflows run through the existing durable path, outside the parent queue,
which avoids a parent waiting on a child blocked by the same queue limit.

Existing API 2026-09-15, tenant boundaries, receipt replay, outbox reconciliation and storage schema 2
remain. APP_VERSION is prototype-0.8-skill-eval-1; parent/child workflow names are v5/v4 so newly
composed skill bytes cannot be confused with older pending workflow code. Release 1.13 adds an
outcomes table and read-only query routes, without changing those workflow identities or skill bytes.
Finish pending reviews under the previous release before upgrading. Same-version
restart is covered by the recovery suite; cross-version replay and exactly-once billing are not claimed.

## Explicitly deferred

Test/Production isolation and environment switching are BACKLOG ENV-01. No Test/Prod selector,
QA-Mode header, mode-based request routing, environment database migration or deployment is included.
Both future environments must run real AI. Test never means canned examples. New application review
uses the configured OpenAI provider; historical technical fixtures remain recognizable as fixtures.
No new canned-example selector or report generator is included in the UI.

## Verification boundaries

See IMPLEMENTATION_STATUS.md for executed tests. DOM tests exercise React and interaction state with
explicit API doubles; they are not a browser layout test or AI evaluation. Existing backend controlled
fixtures and model doubles test technical contracts only. No paid provider calls or new clinical
accuracy claims are part of this workspace release.
