# Feedback comment classification

**Status:** proposal under review. This document is not implementation authority and changes nothing until accepted.

Classify free-text feedback comments against two independent Jev Nouls so the Feedback inbox can be triaged by topic, without asking the person writing the comment to classify anything.

## Source

Motivation:

Today a down-vote cannot be saved without picking one of six reasons from a dropdown
(`backend/contracts.py:63-65`, `frontend/src/Feedback.tsx:146-169`). The taxonomy is ours, not the
user's: someone who wants to say "the impression contradicts the findings" has to first decide
whether that is an *incorrect observation*, a *wrong grouping*, or *other*. The cost lands on every
down-vote, and the payoff is a single label whose accuracy nobody has measured.

This proposal moves the classification from the person to the model, keeps human words and model
labels in separate fields, and — unlike the current dropdown — allows a comment to carry more than
one topic at once.

Prior analysis and the decision drill behind this document are recorded in
[UI_ENHANCEMENT_RESEARCH.md](UI_ENHANCEMENT_RESEARCH.md) §10. The existing feedback contract is in
[API_DESIGN.md](API_DESIGN.md); durable-execution rules are in [DBOS_VALIDATION.md](DBOS_VALIDATION.md).

## Problem

Three separate failures, all downstream of forcing the user to classify:

1. **The form taxes the user.** A required six-option dropdown stands between a person and saying
   what is wrong. It is the only required field on the form and it is the one field the user has no
   stake in.
2. **One label cannot describe one comment.** "The impression says no pneumothorax but the findings
   describe one, and nobody flagged it" is both an internal inconsistency *and* a critical-finding
   concern. The current schema stores exactly one `reason`, so one of those is discarded at write
   time and never recoverable.
3. **The labels are unvalidated.** `reporting.analytics` aggregates `reason` counts and the inbox
   filters on them, but no one has checked whether users pick the reason a reviewer would pick.

A `Choice` primitive does not solve (2). Its distribution sums to 1, so a 0.4 / 0.4 split means
"torn between two labels", not "both apply". Co-occurrence requires N independent Nouls.

## Requested Change

### The two Nouls

Two independent questions, each returning one probability, evaluated in parallel:

| Noul | Question put to the classifier |
|---|---|
| `clinical_inconsistency` | Does this comment say something in the report contradicts something else in the report, or contradicts itself? |
| `critical_findings` | Is this comment about a critical or urgent finding — that one was missed, wrongly raised, or mishandled? |

Both may be true. Both may be false; a comment matching neither is **Other topic**, a first-class
visible outcome and not an error state.

A Noul is a label on **the comment**, never a claim about the report. `clinical_inconsistency: 0.9`
means "this person is writing about an inconsistency", not "the report is inconsistent". No
classification output may be rendered as a statement about the report, feed analytics as a quality
measure, or become ground truth.

### What the general user sees

**Nothing about the classification.** No label at submit time, none in the saved-feedback history,
no "we filed this under X", no correction prompt. The processing is invisible to the person giving
feedback. This is a contract-level decision, not a CSS one: the inferred labels are not part of
`FeedbackResource`, so the per-report history endpoint the general user reads cannot carry them.

What the general user *does* see is the subtraction:

```
before                                   after
─────────────────────────────────        ─────────────────────────────────
What was wrong?  [Required]              What should we improve?
[ Select a reason            ▾ ]         [                              ]
Tell us more  Optional                   [                              ]
[                              ]                              248 / 300
[                              ]
[ Save ]  [ Cancel ]                     [ Save ]  [ Cancel ]
```

One field instead of two, nothing required but the text, a visible character budget.

Consequence to accept deliberately: **there is no ongoing human signal on label quality.** The only
correction path is an operator overriding a label in the inbox, and that is out of scope here. If
the classifier drifts, nothing in this design detects it. Validation (below) is therefore a
one-time gate, and a periodic re-validation belongs in the backlog.

### What the inbox shows

Per row, above the existing note:

```
Topic: Clinical inconsistency · Critical findings          likely · likely
Topic: Critical findings                                   likely
Topic: —                                        unclear on both topics
(blank while unclassified)
```

- Inferred labels carry a `Topic:` prefix and a distinct visual class, so a model label is never
  mistaken for a human's own word. Legacy rows keep rendering their human `reason` exactly as
  today, unprefixed and unstyled.
- Bands, not numbers, on the row. The probability is available on demand behind a disclosure.
- Blank until classified. No spinner, no "pending" chip; an unclassified row simply carries no
  topic line.

A **Topic** filter joins Rating / Reason / Source in `frontend/src/FeedbackInbox.tsx`, applied
server-side. The filter excludes `unclear` rows but **discloses how many it excluded**:

```
Topic: Critical findings ▾     12 shown · 4 unclear, not shown · 3 unclassified
```

### Bands and threshold

Bands are derived at **read time** from the stored probability, never baked into the stored record,
so the threshold can be retuned without reclassifying:

| Band | Range |
|---|---|
| likely | p ≥ 0.70 *(to confirm)* |
| unclear | 0.30 ≤ p < 0.70 *(to confirm)* |
| unlikely | p < 0.30 *(to confirm)* |

The thresholds ship in the API response, not hardcoded in the frontend, and the inbox states the
active threshold in a footnote. **The numbers above are placeholders.** They must be set from the
validation run, not from intuition.

### What the classifier receives

The user's typed text and nothing else. No report text, no QA comment, no rating, no review ID, no
tenant identifier. This keeps the feature off the report-egress path entirely — the report never
leaves the application because of this feature.

The typed text is untrusted input being sent to a provider. The blast radius is bounded by the
output shape: two probabilities. A prompt-injection attempt in a feedback comment can move a
probability; it cannot produce free text, call a tool, or reach a report.

### Scope boundaries for v1

- **Inbox triage only.** No Analytics aggregation of topics. `reporting.analytics` is untouched.
- **New down-votes only.** Existing rows are never backfilled. Their human reasons stay, and become
  the validation set.
- **No correction affordance**, for anyone. Deferred, with the drift consequence stated above.

### Required change to an existing surface

Because new feedback carries no human `reason`, the Analytics section *"What do users want
improved?"* (`frontend/src/AnalyticsView.tsx:94-101`) will show a reason breakdown that silently
decays into a growing `other` bucket — `reporting.analytics` maps a null reason to `"other"`
(`backend/reporting.py:118`). Left alone this turns a real metric into a misleading one.

Must-have: the reason breakdown is relabelled to say what it covers and how many entries it does
not, e.g. `Reasons (feedback saved before <cutover date>) · 41 of 96 entries`. Unlabelled entries
are counted and shown, not folded into `other`.

## Implementation Notes

### Relevant area

Frontend:
- `frontend/src/Feedback.tsx:146-169` — the reason `<select>` to remove
- `frontend/src/Feedback.tsx:62-98` — `save()`, and its `rating === "down" && !reason` guard
- `frontend/src/Feedback.tsx:200-212` — saved-feedback history; **must stay free of topic output**
- `frontend/src/FeedbackInbox.tsx:40-45` — filter row; `:50-60` — the row renderer
- `frontend/src/feedbackLabels.ts` — human reason labels; topic labels go in a **separate** map

Backend:
- `backend/contracts.py:52-68` — `FeedbackInput`; `:364-403` — feedback resources and inbox items
- `backend/presentation.py:100-108` — `feedback()`, the public projection
- `backend/main.py:443-521` — feedback write and per-report read; `:551-572` — the inbox endpoint
- `backend/reporting.py:13-67` — `feedback_inbox` query and filters
- `backend/workflow.py` — queue, step and workflow identity conventions
- `backend/diagnostics.py:76-141` — `status_report` components and the readiness rule
- `backend/schema.sql` — `feedback` table and the `schema_version=6` check

### Current behavior

- `rating="down"` without a `reason` is rejected by a model validator.
- `explanation` is optional, `max_length=2000`.
- One `FeedbackResource` projection serves both the per-report history and the inbox.
- Health components are a fixed dict of five; readiness requires every one in
  `("ok", "configured", "not_required")`.
- `feedback.schema_version` is pinned by `CHECK(schema_version=6)`.

### Add / modify

**Contract** (additive; relaxing a required field does not break existing clients):
- Drop the `rating="down" → reason required` validator. `reason` stays in the schema and keeps
  accepting the six existing values, so a client that still sends one still works.
- `explanation` keeps `max_length=2000` in the contract. The 300-character budget is a form
  constraint, enforced in the UI and by the classifier's own input bound — not a contract change
  that would reject already-valid clients.
- Classification is **not** added to `FeedbackResource`. It surfaces in exactly two places:
  - `GET /api/v1/feedback` — a sibling field on each inbox item, next to the existing
    `report_preview`, `source` and `target_comment`, plus the active thresholds and the
    `unclear` / `unclassified` counts for the current filter.
  - `GET /api/v1/reviews/{review_id}/feedback/{feedback_id}/classification` — the full record:
    both probabilities, classifier version, classified-at, attempt count.
- New list params on `GET /api/v1/feedback`: `topic` (`clinical_inconsistency` |
  `critical_findings` | `other`) and `classified` (`true` | `false`).
- Regenerate `prototype/openapi.json` and `frontend/src/generated-api.ts` with
  `scripts/export_openapi.py` / `scripts/export_contracts.py`. Do not hand-edit them.
- `QA-Version` stays `2026-09-18` *(to confirm)* — every change above is additive or a relaxation.
  If review disagrees, the bump must be decided before implementation, not during.

**Storage** — new table, append-only, one row per `(feedback_id, classifier_version)`:

```sql
CREATE TABLE feedback_classifications (
 tenant_id TEXT NOT NULL, feedback_id TEXT NOT NULL, classifier_version TEXT NOT NULL,
 document TEXT NOT NULL CHECK(json_valid(document)), classified_at TEXT NOT NULL,
 PRIMARY KEY(tenant_id,feedback_id,classifier_version),
 FOREIGN KEY(tenant_id,feedback_id) REFERENCES feedback(tenant_id,id)
);
CREATE TRIGGER feedback_classification_immutable BEFORE UPDATE ON feedback_classifications
BEGIN SELECT RAISE(ABORT,'Feedback classification is immutable'); END;
```

`document` holds `{clinical_inconsistency: <float>, critical_findings: <float>}` — probabilities
only. Bands are never stored. Reclassification under a new `classifier_version` appends a row; the
read path takes the newest version. Nothing is ever updated or deleted.

This bumps the application schema to **7**. Per `AGENTS.md`, schema cutovers use a fresh store and
never migrate — see the sequencing note under Validation, which depends on this.

**Durable execution** — a new workflow, following the existing identity conventions in
`backend/workflow.py`:

- queue `qa-feedback-classify-f3-v1`, concurrency **1**, env `QA_CLASSIFY_CONCURRENCY`, validated
  `1..32` like its siblings. Its own queue so classification can never consume live review
  concurrency.
- workflow `qa.feedback.classify.f3.v1`, `max_recovery_attempts=5`
- deterministic id `qa:fc:{tenant}:{feedback_id}:{classifier_version}`
- **Enqueued after the feedback write commits, never inside it.** `store.save_feedback` and its
  idempotency receipt must not gain a dependency on the classifier. If the classifier is down,
  unreachable, or unconfigured, feedback still saves with a 201 and the row is simply unclassified.
- Bounded retry with backoff on transient provider failure; on exhaustion the workflow completes
  and the row stays unclassified. It does not fail loudly, does not block, and is not retried
  automatically thereafter.
- Add the new identities to the `AGENTS.md` identity line, and a process-recovery test alongside
  `tests/test_f3_recovery.py` per `DBOS_VALIDATION.md`.

**Health** — a sixth component, `classifier`, mirroring `openai`: reports configured /
not_configured from settings and is **never auto-probed**. Add `classifier: "Feedback classifier"`
to the `LABELS` map in `frontend/src/SystemStatus.tsx:9`.

Trap to avoid: `status_report` computes readiness as *every* component in
`("ok", "configured", "not_required")`. A naive `classifier: not_configured` turns the health pill
amber for every existing deployment that never asked for this feature. When the feature is disabled
or the mode is demo, the component must report `not_required`.

**Settings** — the classifier's endpoint and credential are separate from `OPENAI_API_KEY`. A
feature flag defaulting to **off** governs the whole path: off means no new component state, no
enqueue, no form change.

### Validation gate

Before any of the above is built, run the two Nouls offline over the existing human-labelled
feedback and compare. Rows whose human reason is `missed_observation` or `incorrect_observation`
bound the `clinical_inconsistency` question; rows about flagged findings bound `critical_findings`.
The comparison sets the band thresholds and establishes whether the two questions are separable at
all. If they are not, this proposal does not proceed.

**Sequencing matters and is load-bearing:** the schema-7 cutover discards the current store, and
with it the human-labelled rows this gate depends on. Export the validation set to a fixture under
`prototype/examples/` while the schema-6 store still exists. Run the gate. Only then cut over.

### Document changes this proposal carries

- `AGENTS.md` — repeal **"Down feedback requires a reason."** under Product boundary; update the
  header `schema **6**` and the DBOS storage line; add the new queue and workflow identities.
- `prototype/API_DESIGN.md` — the new sub-resource and list params.
- `prototype/ANALYTICS_SPEC.md` — the relabelled reason breakdown.
- `prototype/DBOS_VALIDATION.md` — the new workflow and its recovery obligation.
- `prototype/IMPLEMENTATION_STATUS.md` — schema 7, tests actually run.
- `prototype/README.md` — move this document from "Proposals under review" to "Read by task" on
  acceptance.

## Acceptance Criteria

- A down-vote saves with free text and no reason selected; the request returns 201.
- The reason `<select>` is absent from the feedback form. The textarea is required and capped at
  300 characters with a visible counter.
- A feedback comment about both an internal contradiction and a missed critical finding is stored
  with two independent probabilities, both above the `likely` threshold.
- `GET /api/v1/reviews/{id}/feedback` contains no classification field for any entry, before or
  after classification. The saved-feedback history under a report renders no topic.
- An inbox row shows `Topic:` with a distinct class and band words, never a bare probability; the
  probability is reachable behind a disclosure.
- A comment matching neither Noul renders as **Other topic**, not as an error or a blank.
- Filtering by topic states the number of `unclear` and `unclassified` rows it excluded.
- With the classifier endpoint unreachable, feedback still saves with 201 and the row appears in
  the inbox with no topic line. No error is shown to the person giving feedback.
- With the feature flag off, `/api/v1/status` reports `classifier: not_required` and overall
  readiness is unchanged from today.
- Killing the process mid-classification and restarting produces exactly one classification row for
  that `(feedback_id, classifier_version)`.
- A second `UPDATE` against `feedback_classifications` raises
  `Feedback classification is immutable`.
- The Analytics reason breakdown names the period it covers and counts unlabelled entries
  separately from `other`.
- `uv run pytest` passes, including the new recovery test.
- `npm --prefix frontend run build` and `npx playwright test` pass.
- `uv run python scripts/check_docs.py` passes.
- `prototype/openapi.json` and `frontend/src/generated-api.ts` are regenerated, not hand-edited.

## Verification Prompt

Start the app in demo mode with the classifier configured. Open a completed report, click thumbs
down, and confirm there is no reason dropdown — just one text box with a character counter. Type
"the impression says no pneumothorax but the findings describe one and it was never flagged" and
save. You should land back on the report with "Feedback saved." and **no mention of any topic**;
expand *Saved feedback* beneath the QA comments and confirm the new entry shows the text and no
topic line. Now open QA Studio → Feedbacks. The same entry carries
`Topic: Clinical inconsistency · Critical findings` with both bands reading `likely`. Set the Topic
filter to *Critical findings* and confirm the row count line states how many unclear and
unclassified entries were excluded. Finally, stop the classifier endpoint, save a second down-vote,
and confirm it still saves and appears in the inbox with no topic line and no error anywhere.
