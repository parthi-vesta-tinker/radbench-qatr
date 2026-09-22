# Analytics contract

Analytics aggregates the entire tenant-scoped database population matching the selected UTC period and source. It never treats the currently loaded history page as its denominator.

## Definitions

- **Review operations:** accepted, queued/running, completed, needs-input, and failed reviews; known model calls, tokens, and conservative cost fields remain nullable when unavailable.
- **Feedback:** latest applicable feedback counts and reasons. Feedback measures user response, not clinical correctness.
- **Clinical performance:** recall, precision, false-positive rate, false-alert share, and related values remain `null` until an independent adjudicated reference cohort exists. Missing evidence is never displayed as zero.

Source filters describe provenance such as live-provider or controlled fixture data. They do not represent Test/Production isolation.


## Future clinical metrics

Enabling clinical performance requires a predeclared representative cohort, explicit unit of analysis, versioned reference standard, qualified independent adjudication, disagreement handling, positive and negative cases, immutable release provenance, and visible exclusions. Report-level detection and finding-level matching must be reported separately with numerator, denominator, coverage, sample size, and uncertainty.

## Latest-state reviews (0.14.0)

Review totals count saved review IDs once, using latest submitted text/status/time. A failure
replaced by a completed review counts as completed, not an additional failure. Feedback events
remain review-scoped and continue contributing to feedback totals. These are latest-state
operational counts, not historical execution-attempt reliability metrics.

Stakeholder outcomes and acceptance measures were removed on 2026-09-22 by user decision. Analytics exposes review totals, feedback totals and explicitly unmeasured clinical metrics only. Dormant legacy outcome rows are not queried.
