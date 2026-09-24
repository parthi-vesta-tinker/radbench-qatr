# Analytics contract

Analytics aggregates the entire tenant-scoped database population matching the selected UTC period and source. It never treats the currently loaded history page as its denominator.

The Analytics screen has one period control: rolling 1, 6, 12 and 24 hours; 7 and 30 days;
or all time. It includes all saved review sources so controlled/demo reviews are visible.
The API retains its optional source parameter for existing clients. Changing the period
reloads all counts from the full matching tenant dataset.

## Definitions

- **Review operations:** accepted, queued/running, completed, needs-input, and failed reviews; known model calls, tokens, and conservative cost fields remain nullable when unavailable.
- **Review findings:** counts of saved comments on completed latest-state reviews. Each comment
  belongs to exactly one display category: critical comments are **Critical findings**;
  internal-consistency checks are **Inconsistencies**; clinical-question and recommendation
  checks are **Clinical observations**; remaining checks are **Other issues**. If an older or
  demo result lacks private check identity, a noncritical discrepancy counts as an
  inconsistency and a noncritical suggestion as another issue. These are comment counts,
  so a report can contribute to multiple categories. They do not assert clinical accuracy.
- **Feedback:** latest applicable feedback counts and reasons. Feedback measures user response, not clinical correctness.
- **Clinical performance:** recall, precision, false-positive rate, false-alert share, and related values remain `null` until an independent adjudicated reference cohort exists. Missing evidence is never displayed as zero.

The screen prioritizes findings, with submitted/completed/failed review counts secondary.
Feedback and unmeasured clinical-performance detail remain available through the API but
do not occupy the simplified screen. Source filters describe provenance such as
live-provider or controlled fixture data; they do not represent Test/Production isolation.


## Future clinical metrics

Enabling clinical performance requires a predeclared representative cohort, explicit unit of analysis, versioned reference standard, qualified independent adjudication, disagreement handling, positive and negative cases, immutable release provenance, and visible exclusions. Report-level detection and finding-level matching must be reported separately with numerator, denominator, coverage, sample size, and uncertainty.

## Latest-state reviews (0.14.0)

Review totals count saved review IDs once, using latest submitted text/status/time. A failure
replaced by a completed review counts as completed, not an additional failure. Feedback events
remain review-scoped and continue contributing to feedback totals. These are latest-state
operational counts, not historical execution-attempt reliability metrics.

Stakeholder outcomes and acceptance measures were removed on 2026-09-22 by user decision.
Analytics exposes review totals, finding-category counts, feedback totals and explicitly
unmeasured clinical metrics. Dormant legacy outcome rows are not queried.
