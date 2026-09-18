# Analytics and outcomes contract

Analytics aggregates the entire tenant-scoped database population matching the selected UTC period and source. It never treats the currently loaded history page as its denominator.

## Definitions

- **Review operations:** accepted, queued/running, completed, needs-input, and failed reviews; known model calls, tokens, and conservative cost fields remain nullable when unavailable.
- **Feedback:** latest applicable feedback counts and reasons. Feedback measures user response, not clinical correctness.
- **Acceptance:** latest applicable stakeholder outcome for each perspective, subject, and immutable result version. Report acceptance and QA-comment acceptance remain separate.
- **Clinical performance:** recall, precision, false-positive rate, false-alert share, and related values remain `null` until an independent adjudicated reference cohort exists. Missing evidence is never displayed as zero.

Source filters describe provenance such as live-provider or controlled fixture data. They do not represent Test/Production isolation.

## Stakeholder outcomes

Completed reviews support append-only outcome events with a perspective, subject, decision, required source/reason note, timestamp, and immutable result binding. The latest applicable event supplies the current view; earlier events remain readable. `unknown` can withdraw a prior decision without deleting history.

These are authenticated-tenant operator records. They are not verified radiologist/facility signatures, delivery receipts, clinical references, or release authorization. They do not change reports, QA results, feedback, content, or training.

Outcome POSTs require `reviews:read`, `feedback:write`, and an idempotency key. Reads require the documented feedback/review scopes. Tenant identity comes only from authentication. Event and receipt commit atomically; receipt replay returns the original result.

## Future clinical metrics

Enabling clinical performance requires a predeclared representative cohort, explicit unit of analysis, versioned reference standard, qualified independent adjudication, disagreement handling, positive and negative cases, immutable release provenance, and visible exclusions. Report-level detection and finding-level matching must be reported separately with numerator, denominator, coverage, sample size, and uncertainty.
