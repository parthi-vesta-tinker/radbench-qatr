> Current implementation: application **0.13.0**, bundle **1.17**, foundation **F3**. [Decisions and verification](FOUNDATION_CHANGELOG.md) supersede older baseline statements below. Fresh schema 4 and API 2026-09-18 are implemented. F3 adds one combined request, guarded dispatch and durable response checkpoints. F4/F5 remain separate gates.

# Foundation compatibility — 2026-09-17

[FOUNDATION_PLAN.md](FOUNDATION_PLAN.md) preserves this feature and its denominators. Reconnect
feedback inbox, outcomes and whole-database aggregates to fresh records. Use actual review/attempt
calls/tokens/cost, not fabricated per-skill allocations. Unknown cost is not zero; keep conservative
reservations. Empty stores have zero operational counts and unmeasured clinical metrics. Feedback
and acceptance remain distinct from clinical truth; advanced trends/adjudication stay deferred.

# QA Studio analytics — release 1.13

## Product decision

The next high-value capabilities are a cross-report feedback inbox and a business-question-led
Analytics page. They reuse QA Studio, preserve the report paste/review/copy flow and do not add
new required fields to report intake. Facility is used for the user's facility/facilitator perspective.

The existing application SQLite database is the source of operational metrics. No live business
measurements are invented, no sample reports are inserted into user workspaces, and no external
source is treated as connected. Legacy fixtures are excluded by default and remain explicitly labeled.

## Questions and definitions

| Business question | Implemented measure | Grain and denominator | Limit |
|---|---|---|---|
| Are reports acceptable? | Report accepted/rejected/review-requested/unknown/not-recorded, separately for QA, radiologist, facility | Latest operator-recorded outcome per completed report/result and perspective; acceptance = accepted / (accepted + rejected) | Not clinical correctness or verified stakeholder identity |
| Are QA comments useful to stakeholders? | The same independent outcome breakdown for QA comments | Separate subject from report; accepting comments does not imply accepting a report | Not automatically inferred from thumbs up |
| Are critical findings missed? | Critical recall readiness, formula TP/(TP+FN) | Intended report-level classification against an independent reference standard | Not measured until an adjudicated cohort is connected |
| Are critical alerts excessive? | Precision TP/(TP+FP), false-positive rate FP/(FP+TN), false-alert share FP/(TP+FP) | These denominators are explicitly different | No rate is estimated from complaints or rejected comments |
| Where does workflow stop? | Queued/running/completed/input-needed/failed totals | All reports submitted within the selected rolling UTC period | Snapshot, not throughput SLA or live monitoring |
| What do users want improved? | Feedback counts and reasons, with a searchable inbox | Feedback entries received within the period; also distinct report count | Multiple entries per report; not a prevalence estimate |

No composite "report quality score" is invented. AI comment prevalence is not report accuracy,
and completed-without-comments is not a clinical quality certification. Coverage (recorded,
unknown and not recorded) must be visible beside acceptance percentages.

## Research and measurement rationale

FDA's statistical guidance distinguishes accuracy against a reference standard from agreement
against another imperfect assessment. It also warns about evaluating only disagreements and calls
for representative sampling and uncertainty reporting. This informs our decision to keep unadjudicated
feedback separate from precision/recall; it does not classify this prototype as a diagnostic device
or establish regulatory compliance.

Source: [FDA — Statistical Guidance on Reporting Results from Studies Evaluating Diagnostic Tests](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/statistical-guidance-reporting-results-studies-evaluating-diagnostic-tests-guidance-industry-and-fda), accessed 16 September 2026.

The report-only QA scope additionally means an image finding absent from the report cannot be counted
as a report-text detection miss. Such feedback belongs to upstream report-quality assessment. The
independent reviewer must specify what constitutes a report-supported critical finding, including
negation, historical/resolved statements and uncertain assertions.

## Implemented UX

Feedbacks opens a newest-first entry list, defaulted to Needs improvement and Live AI reviews.
Users can search notes/suggested wording/IDs, filter rating/reason/source, load more, inspect the
original targeted comment and open the associated report. Suggested wording remains feedback;
it never replaces the copy-ready QA output. Target comments are attached only to matching result
versions. Changing filters resets pagination, and late requests cannot overwrite a newer filter.

Analytics opens four business areas: stakeholder acceptance, critical-finding measurement readiness,
review operations, and feedback patterns. Controls select last 7 days, last 30 days or all time and
live AI, legacy fixtures or all sources. It queries the entire matching tenant population, not the
20 rows currently loaded in history. It contains no decorative chart or added visualization library.

The collapsed Stakeholder outcomes section appears after feedback on completed reports. Users
select perspective, subject, decision and a required source/reason note. No default acceptance is
assumed. Unknown can withdraw an earlier decision while retaining its audit history. Inputs lock
after ambiguous submission failure; retry reuses the original payload and idempotency key.

Outcome records are explicitly **operator-recorded**, not authenticated radiologist/facility
signatures. The note records a source claim, not independently verified evidence. This log does not
send communications, authorize release, verify delivery, change a report, or train the model.
The current input has no reliable facility/radiologist identity fields, so these are perspective-level
aggregates, not comparisons or rankings of individual people or facilities. Outcome retry state is
view-local; after navigation/reload, inspect persisted history before recording the decision again.

## API and storage

- `GET /api/v1/feedback`: newest-first, `limit` 1–100, `starting_after`, `q` up to 200 characters,
  optional `rating`/`reason`, `source=openai|demo|all`. Requires both feedback:read and reviews:read.
- `GET /api/v1/analytics`: `period=7d|30d|all`, `source=openai|demo|all`. Requires reviews:read;
  feedback and acceptance are null without feedback:read, not misleading zero counts.
- `POST /api/v1/reviews/{id}/outcomes`: result_version, stakeholder, subject, decision, source_note.
  Requires feedback:write + reviews:read and an Idempotency-Key. Event and receipt commit atomically.
- `GET /api/v1/reviews/{id}/outcomes`: bounded, newest-first immutable event history; same-tenant,
  same-report cursors. Requires feedback:read + reviews:read.
- New `outcomes` table is an additive schema-2 extension with tenant/review foreign keys and an
  index for report lookup. No existing rows or receipts are rewritten. Clinical output is untouched.
- Latest outcome uses insertion order, matching result version, and separate subject/perspective.
  Earlier decisions remain readable; replay of an old key does not restore an old decision.
- Analytics queries share a SQLite read snapshot. Review/acceptance cohorts use report submission
  time; feedback uses feedback submission time. Windows include the start and exclude checked_at.
- Workflow APP_VERSION, DBOS identities, skill bytes and `.qa-data-v0.6` remain unchanged because
  this feature does not change durable review execution. Package version advances to 0.9.0.

## Deferred clinical evaluation connection

The readiness cards deliberately return null, never 0%, for clinical performance. Enabling them
requires a reviewed protocol and independent reference cohort—not just more UI.

1. Select a representative cohort including unflagged/no-comment reports; predeclare unit,
   inclusion/exclusion, critical standard/version, adjudicator qualification and disagreement process.
2. Preserve immutable report and model/skill/policy provenance; avoid pooling model releases silently.
3. Adjudicate reference-positive/reference-negative/indeterminate outcomes independently of QA output.
   Count TP/FP/FN/TN only for eligible completed results; show failures/indeterminate exclusions separately.
4. Show numerator/denominator, coverage, sample size and confidence intervals. A selected complaint
   cohort must not be generalized as real-world recall. A zero denominator remains not measurable.
5. Distinguish report-level detection from finding-level detection and matching. A flagged report may
   still contain an additional missed critical finding; report-level recall does not answer that question.

No arbitrary quality targets, provider cost estimates, automated skill updates, doctor ranking,
PACS/HL7/chat ingestion, Test/Production separation or production readiness claims are included.
