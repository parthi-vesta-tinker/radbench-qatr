# Feedback comment classification

**Status:** proposal under review. This document is not implementation authority and changes nothing until accepted.

Classify free-text feedback comments against two independent Jev Nouls, so the Feedback inbox can
be triaged by clinical topic alongside — not instead of — the reason the user picked.

Delivered in two iterations. **Iteration 1 changes nothing that a general user or the Analytics
page can see.** It adds a derived topic beside the user's own reason in the Studio inbox, and
nothing else. Iteration 2 decides, with evidence in hand, whether the required reason dropdown can
be retired in favour of a short free-text box.

## Source

Motivation:

Two separate things are worth knowing about a piece of feedback, and today only one of them is
captured.

The existing `reason` dropdown (`backend/contracts.py:58`, `frontend/src/Feedback.tsx:146-169`)
answers **"what did the QA system get wrong?"** — missed, unnecessary or incorrect observation,
wrong grouping, unclear wording. That is a judgment about our output, and the user is the right
person to make it.

Nothing captures **"what clinical topic is this comment about?"** — whether the person is writing
about an internal contradiction in the report, or about a critical finding. That is a reading of
their prose, it is not a judgment the user should be asked to make about their own sentence, and it
is exactly what a model can supply.

These are orthogonal axes, not competing labels for one thing. A comment can be
`missed_observation` *and* about a critical finding; `unclear_wording` *and* about an inconsistency.
Showing both side by side is more informative than either alone.

Prior analysis and the decision drill behind this document are in
[UI_ENHANCEMENT_RESEARCH.md](UI_ENHANCEMENT_RESEARCH.md) §10. The existing feedback contract is in
[API_DESIGN.md](API_DESIGN.md); durable-execution rules are in [DBOS_VALIDATION.md](DBOS_VALIDATION.md).

## Problem

1. **The inbox cannot be triaged by clinical topic.** An operator looking for every comment about a
   possible missed critical finding has no filter for it. `reason` does not answer the question:
   `missed_observation` covers a missed critical finding and a missed typo equally.
2. **One user reason cannot describe one comment.** The schema stores exactly one `reason`, so a
   comment that is about both an internal contradiction and a critical finding loses one of those
   at write time, unrecoverably.
3. **The form taxes the user** — the dropdown is the only required field on the feedback form and
   the one field the user has no stake in. *Iteration 2 problem; stated here so the sequencing is
   deliberate rather than forgotten.*

A `Choice` primitive does not solve (2). Its distribution sums to 1, so a 0.4 / 0.4 split means
"torn between two labels", not "both apply". Co-occurrence requires N independent Nouls.

## Requested Change

### The two Nouls

Two independent Jev Nouls, each carrying explicit true and false criteria. They are evaluated as a
**multilabel task: one `system_one` request carrying both questions**, not two requests.

| Noul | `true_criteria` | `false_criteria` |
|---|---|---|
| `clinical_inconsistency` | The comment says something in the report contradicts something else in the report, or contradicts itself. | The comment raises no contradiction within the report. |
| `critical_findings` | The comment is about a critical or urgent finding — that one was missed, wrongly raised, or mishandled. | The comment is not about a critical or urgent finding. |

Each Noul returns one probability. Both may be true. Both may be false; a comment matching neither
is **Other topic**, a first-class visible outcome and not an error state.

The criteria wording above is a **starting draft, not the specification**. It is the artifact the
alignment loop under Validation optimizes, and the accepted wording ships as a versioned classifier
pack. Do not hand-tune it in application code.

A Noul is a label on **the comment**, never a claim about the report. `clinical_inconsistency: 0.9`
means "this person is writing about an inconsistency", not "the report is inconsistent". No
classification output may be rendered as a statement about the report, feed analytics as a quality
measure, or become ground truth.

---

## Iteration 1 — derived topic beside the user reason

### What the general user sees

**Nothing changes.** The feedback form is untouched: the reason dropdown stays, stays required, and
keeps its six values. The explanation box stays optional at 2000 characters. No new field, no
label, no confirmation text, no correction prompt.

The classification is absent from `FeedbackResource`, so
`GET /api/v1/reviews/{review_id}/feedback` — the endpoint the report page reads — structurally
cannot carry it, and the *Saved feedback* list beneath a report renders no topic. This is enforced
in the contract, not the stylesheet.

Comments with no explanation text are not classified at all. There is nothing to read.

### What the Analytics page sees

**Nothing changes.** `reporting.analytics` and its reason breakdown are untouched and keep counting
user-provided reasons. Because the dropdown stays required, every new down-vote still carries one,
so the breakdown neither decays nor develops a null bucket.

No topic aggregation anywhere. A derived label must earn a place in a metric by being measured
first, and iteration 1 is what measures it.

### What the Studio inbox shows

Two labelled fields per row, side by side — the user's own word on the left, the derived topic on
the right:

```
▼ Needs improvement                                    14 Mar 2026, 09:12

  User reason                     Topic  (derived)
  Missed observation              Clinical inconsistency · likely
                                  Critical findings · likely

  "the impression says no pneumothorax but the findings describe one
   and it was never flagged"
```

```
  User reason                     Topic  (derived)
  Unclear wording                 Other topic
                                  unclear on both topics

  User reason                     Topic  (derived)
  Wrong grouping                  —
                                  (no explanation text to classify)
```

- The derived column is visually distinct from the user column and carries the word `derived` in
  its heading, so a model label is never mistaken for a human's own word.
- Bands, not numbers, on the row. The probability sits behind a disclosure.
- Blank until classified. No spinner, no "pending" chip — an unclassified row shows `—`.
- On narrow viewports the two fields stack, user reason first.

A **Topic** filter joins Rating / Reason / Source in `frontend/src/FeedbackInbox.tsx`, applied
server-side, and composes with the existing Reason filter. It excludes `unclear` rows but
**discloses how many it excluded**:

```
Topic: Critical findings ▾    12 shown · 4 unclear, not shown · 3 unclassified
```

**Do not build an "agreement" or "they differ" indicator.** The two columns measure different
things, so disagreement between them is not an error signal and a differs-filter would be noise.

### Bands and threshold

Bands are derived at **read time** from the stored probability, never baked into the stored record,
so the threshold can be retuned without reclassifying.

Use the standard ambiguity measure rather than hand-picked cut points:

```
ambiguity(p) = 1 - 2 * |p - 0.5|        # 1.0 at p=0.5, 0.0 at p=0 or p=1
```

| Band | Condition |
|---|---|
| unclear | `ambiguity(p) >= 0.8`, i.e. `0.4 <= p <= 0.6` |
| likely | `p > 0.6` |
| unlikely | `p < 0.4` |

`0.8` is `jev-align`'s default capture threshold, so the rows the inbox marks `unclear` are exactly
the rows its alignment loop would select for labelling. One number governs both, which is the point:
tuning the band retunes what gets queued for review.

Thresholds ship in the API response, not hardcoded in the frontend, and the inbox states the active
threshold in a footnote. The value is confirmed by the validation run below, not assumed.

### What the classifier receives

The user's explanation text and nothing else. No report text, no QA comment, no rating, no user
reason, no review ID, no tenant identifier. The report never leaves the application because of this
feature.

Withholding the user's reason from the classifier is deliberate: it keeps the derived column an
independent reading of the prose rather than an echo of the dropdown, which is the only thing that
makes the two columns worth showing together.

The typed text is untrusted input sent to a provider. The blast radius is bounded by the output
shape — two probabilities. An injection attempt in a feedback comment can move a probability; it
cannot produce free text, call a tool, or reach a report.

### Validation

**Correction to an earlier draft of this document:** it proposed grading the Nouls against existing
`reason` values — treating `missed_observation` and `incorrect_observation` as bounding
`clinical_inconsistency`. That is unsound. `missed_observation` says QA missed something; it does
not say whether the missed thing was a contradiction or a critical finding. Only the text does. The
reason field is a weak prior, not a label, and cannot grade this classifier.

Real validation needs the comment text hand-adjudicated against the two Noul questions. Rather than
building that loop, use [`jev-align`](https://github.com/sutro-sh/jev-align), an Apache-2.0 CLI
that implements exactly it for multilabel Jev functions:

- Export feedback comment text to CSV and run `jeva optimize` as a multilabel task with the two
  labels above.
- It selects the most ambiguous rows plus a random audit sample each round, so adjudication effort
  lands where it changes the answer instead of on easy cases.
- The adjudicator labels each row and may attach a free-text rationale. GEPA then proposes new
  `true_criteria` / `false_criteria` wording from those rationales; a human accepts or rejects every
  proposal and a higher training score never auto-accepts.
- It reports per-label precision, recall, F1 and support against a 20% held-out split, which is the
  measurement this document previously called for without supplying any machinery for.

This replaces the ad-hoc two-rater procedure in the earlier draft. Inter-rater disagreement is still
worth recording: if two readers cannot agree whether a comment is about a critical finding, the
criteria are badly worded and get rewritten before the model sees them again — which is what the
tool's accept/reject gate is for.

**Adopt it as a design-time tool, not a runtime dependency.** See the Tooling note under
Implementation Notes.

The schema-7 cutover below discards the current store. Export the existing comment *text* to a
fixture under `prototype/examples/` before cutting over, so the adjudication set survives.

Unlike the one-shot gate in the earlier draft, iteration 1 keeps producing material: every
classified row is a candidate for re-adjudication, so drift is detectable by re-sampling rather
than invisible.

---

## Iteration 2 — retire the dropdown (not in scope here)

Gated on iteration 1's validation result. If the derived topic proves reliable, iteration 2
replaces the required dropdown with a single 300-character text box:

```
before                                   after
─────────────────────────────────        ─────────────────────────────────
What was wrong?  [Required]              What should we improve?
[ Select a reason            ▾ ]         [                              ]
Tell us more  Optional                   [                              ]
[                              ]                              248 / 300
[ Save ]  [ Cancel ]                     [ Save ]  [ Cancel ]
```

Everything that made the first draft of this proposal large belongs to iteration 2 and is listed
here so it is not rediscovered as a surprise:

- Repealing **"Down feedback requires a reason"** in `AGENTS.md` under Product boundary.
- Relaxing the `rating="down" → reason required` validator in `backend/contracts.py:63-65`.
- Relabelling the Analytics reason breakdown, which starts decaying the moment new feedback stops
  carrying user reasons — `backend/reporting.py:118` maps a null reason to `"other"`, so an
  untreated breakdown turns into a growing `other` bucket that looks like a finding and is not.
- Deciding whether derived topics may enter Analytics at all, and under what caveat.
- The correction affordance: once the user no longer supplies a reason, the only human signal on
  label quality is an operator override in the inbox, or periodic re-adjudication.

## Implementation Notes

Scope below is **iteration 1 only**.

### Tooling: jev-align at design time only

[`jev-align`](https://github.com/sutro-sh/jev-align) (Apache-2.0, Sutro; not affiliated with
TypeSafe) is the right tool for authoring and optimizing the two Nouls' criteria, and the wrong
thing to run inside this application. Three concrete reasons, all verified against the source at
`49753df`:

1. **Its runtime call is synchronous and its own AGENTS.md says so.** `AIFunction.__call__` reaches
   `TypeSafeJevEvaluator.evaluate_many`, which is `asyncio.run(...)`. This application's provider
   calls are async DBOS workflows (`backend/reviewer.py:170`), so an `asyncio.run` inside one raises
   `RuntimeError: asyncio.run() cannot be called from a running event loop` — the hazard `AGENTS.md`
   already names under Runtime and persistence. An `asyncio.to_thread` hop would work (the pattern
   exists at `backend/main.py:87`) but puts the provider call outside DBOS's step accounting.
2. **It depends on `gepa[full]`.** The optimizer belongs on a workstation, not in the served
   application's dependency tree.
3. **Its `Capture` writes JSONL to local disk** from a background thread with no durability
   guarantee, containing the user's feedback text. That is a second persistence story beside SQLite
   and DBOS, and it would need its own retention answer.

Adopt it this way instead:

- **Design time.** Run `jeva optimize` on exported feedback text to author, adjudicate and optimize
  the criteria.
- **Artifact.** Commit the accepted `instructions` and per-label `true_criteria` / `false_criteria`
  as a versioned, hashed classifier pack, governed the way `qa-skills/` packs already are — pinned
  version, changelog, evaluation record. The wording is content, not code.
- **Runtime.** The DBOS step calls `AsyncTypeSafeClient.system_one` directly with the packed
  criteria, as one multilabel request carrying both Nouls. Runtime dependency is `typesafe-sdk`
  alone.
- **Feeding the loop back.** Do not install `Capture`. The `feedback_classifications` table already
  records every probability durably; an export script selects the ambiguous and audit rows from it
  for the next `jeva` round. Same active-learning cycle, one persistence story.

### Relevant area

Frontend:
- `frontend/src/FeedbackInbox.tsx:40-45` — filter row; `:50-60` — the row renderer to split into
  two labelled fields
- `frontend/src/Feedback.tsx` — **unchanged**
- `frontend/src/AnalyticsView.tsx` — **unchanged**
- `frontend/src/feedbackLabels.ts` — human reason labels; topic labels go in a **separate** map
- `frontend/src/style.css` — two-field row, stacking under the existing `max-width:650px` breakpoint

Backend:
- `backend/contracts.py:364-403` — feedback resources and inbox items
- `backend/presentation.py:100-108` — `feedback()`, the public projection, **unchanged**
- `backend/main.py:551-572` — the inbox endpoint
- `backend/reporting.py:13-67` — `feedback_inbox` query and filters
  (`analytics`, `:69-127` — **unchanged**)
- `backend/workflow.py` — queue, step and workflow identity conventions
- `backend/diagnostics.py:76-141` — `status_report` components and the readiness rule
- `backend/schema.sql` — the `schema_version=6` check

### Current behavior

- `rating="down"` without a `reason` is rejected by a model validator. **Keep.**
- `explanation` is optional, `max_length=2000`. **Keep.**
- One `FeedbackResource` projection serves both the per-report history and the inbox.
- Health components are a fixed dict of five; readiness requires every one in
  `("ok", "configured", "not_required")`.
- `feedback.schema_version` is pinned by `CHECK(schema_version=6)`.

### Add / modify

**Contract** — purely additive. `FeedbackInput` and `FeedbackResource` are untouched, so no
existing client, stored document or receipt changes shape.

- Classification surfaces in exactly two places:
  - `GET /api/v1/feedback` — a sibling field on each inbox item, next to the existing
    `report_preview`, `source` and `target_comment`, plus the active thresholds and the
    `unclear` / `unclassified` counts for the current filter.
  - `GET /api/v1/reviews/{review_id}/feedback/{feedback_id}/classification` — the full record:
    both probabilities, classifier version, classified-at, attempt count.
- New list params on `GET /api/v1/feedback`: `topic` (`clinical_inconsistency` |
  `critical_findings` | `other`) and `classified` (`true` | `false`).
- Regenerate `prototype/openapi.json` and `frontend/src/generated-api.ts` with
  `scripts/export_openapi.py` / `scripts/export_contracts.py`. Do not hand-edit them.
- `QA-Version` stays `2026-09-18` *(to confirm)* — every change is additive. If review disagrees,
  the bump is decided before implementation, not during.

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
never migrate — hence the pre-cutover text export under Validation.

**Durable execution** — a new workflow, following the existing identity conventions in
`backend/workflow.py`:

- queue `qa-feedback-classify-f3-v1`, concurrency **1**, env `QA_CLASSIFY_CONCURRENCY`, validated
  `1..32` like its siblings. Its own queue, so classification can never consume live review
  concurrency.
- workflow `qa.feedback.classify.f3.v1`, `max_recovery_attempts=5`
- deterministic id `qa:fc:{tenant}:{feedback_id}:{classifier_version}`
- **Enqueued after the feedback write commits, never inside it.** `store.save_feedback` and its
  idempotency receipt must not gain a dependency on the classifier. If the classifier is down,
  unreachable or unconfigured, feedback still saves with a 201 and the row stays unclassified.
- Enqueued only for a down-vote that carries explanation text.
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
enqueue, no inbox column.

### Document changes iteration 1 carries

- `AGENTS.md` — header `schema **6**` → **7**; the DBOS storage line; the new queue and workflow
  identities. **The Product boundary line "Down feedback requires a reason" is unchanged.**
- `prototype/API_DESIGN.md` — the new sub-resource and list params.
- `prototype/DBOS_VALIDATION.md` — the new workflow and its recovery obligation.
- `prototype/IMPLEMENTATION_STATUS.md` — schema 7, tests actually run.
- `prototype/ANALYTICS_SPEC.md` — **unchanged in iteration 1.**
- `prototype/README.md` — move this document from "Proposals under review" to "Read by task" on
  acceptance.

## Acceptance Criteria

- The feedback form is byte-identical to today: reason dropdown present and required, explanation
  optional at 2000 characters.
- `GET /api/v1/reviews/{id}/feedback` contains no classification field for any entry, before or
  after classification. The saved-feedback history under a report renders no topic.
- The Analytics reason breakdown returns the same counts before and after this change for the same
  underlying feedback.
- An inbox row shows two labelled fields, `User reason` and `Topic (derived)`, visually distinct,
  with the derived one marked as derived.
- A comment about both an internal contradiction and a missed critical finding shows both topics as
  `likely`, alongside whatever single reason the user picked.
- Classifying one comment issues exactly one provider request carrying both Nouls, not two.
- The criteria wording in use is read from the versioned classifier pack, not literal in Python.
- Bands are shown as words; the probability is reachable only behind a disclosure.
- A comment matching neither Noul renders as **Other topic**, not as an error or a blank.
- A down-vote with no explanation text is never enqueued and renders `—` in the derived column.
- Filtering by topic states the number of `unclear` and `unclassified` rows it excluded, and
  composes with the existing Reason filter.
- No agreement, match or "differs" indicator exists anywhere in the UI or API.
- With the classifier endpoint unreachable, feedback still saves with 201 and appears in the inbox
  with an empty derived column. No error is shown to the person giving feedback.
- With the feature flag off, `/api/v1/status` reports `classifier: not_required` and overall
  readiness is unchanged from today.
- Killing the process mid-classification and restarting produces exactly one classification row for
  that `(feedback_id, classifier_version)`.
- A second `UPDATE` against `feedback_classifications` raises
  `Feedback classification is immutable`.
- `uv run pytest` passes, including the new recovery test.
- `npm --prefix frontend run build` and `npx playwright test` pass.
- `uv run python scripts/check_docs.py` passes.
- `prototype/openapi.json` and `frontend/src/generated-api.ts` are regenerated, not hand-edited.

## Verification Prompt

Start the app in demo mode with the classifier configured. Open a completed report and click thumbs
down. Confirm the form is exactly as it is today — a required reason dropdown and an optional
explanation box. Pick *Missed observation*, type "the impression says no pneumothorax but the
findings describe one and it was never flagged", and save. Back on the report, expand *Saved
feedback* and confirm the entry shows the reason and the text and **no topic of any kind**. Open
Analytics and confirm *What do users want improved?* counts your new entry under Missed
observation, exactly as before. Now open QA Studio → Feedbacks: the same entry shows `User reason:
Missed observation` on the left and `Topic (derived): Clinical inconsistency · likely, Critical
findings · likely` on the right, with the derived side marked as derived. Set the Topic filter to
*Critical findings* and confirm the count line states how many unclear and unclassified entries
were excluded. Finally, stop the classifier endpoint and save a second down-vote: it still saves,
still appears in Analytics, and appears in the inbox with the user reason filled and the derived
column empty — with no error shown anywhere on the report page.
