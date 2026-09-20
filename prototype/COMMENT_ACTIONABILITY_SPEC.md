# QA comment actionability

**Status:** proposal under review. This document is not implementation authority and changes nothing until accepted.

Rate each drafted QA comment on an ordered actionability rubric with a Jev Score, so the Studio can
show which skill versions produce comments a radiologist can act on — and which produce comments
that name a problem without saying what to change.

Independent of the feedback-classification proposals. It can ship before, after, or instead of them.

## Source

Motivation:

The prototype measures whether reviews *complete* (`reporting.analytics` counts queued, running,
completed, failed) and whether stakeholders *accept* them. It measures nothing about whether the
comments themselves are any good.

The only quality signal today is feedback, and feedback is sparse, voluntary, and negative-biased:
`unclear_wording` and `wrong_grouping` exist as reasons precisely because comment quality varies,
but a comment nobody complained about is not thereby a good comment — it is an unmeasured one.

Meanwhile the whole Skills Studio exists to let someone draft, compose and publish a new skill pack.
There is no way to tell whether a new pack's comments read better than the old pack's. A pack is
released on integrity checks and evaluation fixtures, not on any measure of the prose it produces.

This proposal supplies that measure, and confines it to the operator's side of the application.

## Problem

1. **Comment quality is invisible.** Nothing distinguishes *"The impression is inconsistent with the
   findings"* from *"The impression states there is no pneumothorax; the findings describe a small
   apical pneumothorax. Reconcile the impression with the findings."* The second is actionable; the
   first makes a radiologist go hunting.
2. **Pack releases fly blind on prose.** `scripts/evaluate_skills.py` checks fixtures. Nothing
   compares the readability or actionability of what two pack versions produce.
3. **Feedback cannot fill the gap.** It arrives on a small minority of reviews, only when someone
   is annoyed enough to click, and it rates the review — not each comment in it.

## Requested Change

### The rubric

One Jev `Score` question per drafted comment, over three ordered levels:

| Level | Name | Criteria |
|---|---|---|
| 0 | Not actionable | Names a problem but not what to change. The reader must locate the issue themselves. |
| 1 | Partly actionable | Names what to change, but not where in the report, or not what it should become. |
| 2 | Actionable | Identifies the specific report text and the change needed. |

Three levels, not ten. Every additional level is another boundary two human adjudicators can
disagree about, and the rubric is only as good as the agreement behind it.

`Score` returns a fractional score, a per-level distribution and a confidence. **Below a confidence
floor the comment is `Unrated`, not level 0.** An uncertain rating rendered as a bad rating is the
single most likely way for this feature to mislead someone.

The rubric wording is a starting draft and the artifact the alignment loop optimizes. It ships as a
versioned, hashed scorer pack, governed the way `qa-skills/` packs are, and is never hand-tuned in
application code.

### What this rates, and what it does not

It rates **our own prose**. Level 0 means *this sentence is hard to act on*. It is not a claim that
the comment is clinically wrong, that the finding is unimportant, or that the report is at fault.
The surface states this in place, alongside the existing pattern of
*"Feedback is not a clinical verdict and does not change results or train the model."*

Hard boundaries, all load-bearing:

- **The radiologist never sees a score.** `frontend/src/ReviewOutput.tsx` is untouched. No badge,
  no ordering change, no colour, nothing.
- **No comment is ever hidden, reordered, rewritten or suppressed** by its score. `AGENTS.md`
  requires read-only structured comments and forbids automatic report or comment editing.
- **Nothing is written into the result.** `review_results` and `observations` carry immutability
  triggers, and scores live in their own table.
- **No Analytics aggregation.** Same discipline as the classification proposal: a derived signal
  earns a place in a metric by being validated first, and `AnalyticsView.tsx` is already the most
  crowded screen in the product.
- **The review never waits for it.** Scoring runs after a review completes, in its own workflow. A
  scorer that is down, unconfigured or failing has no effect on QA at all.

### The egress decision — read before accepting

This is the one place this proposal differs materially from the feedback classifier, and it needs a
deliberate answer rather than a footnote.

The feedback classifier sees only what a user typed. **This scorer sees QA comment text, which is
derived from the report and routinely quotes it** — a comment that says *"the impression states
'no pneumothorax'"* carries report content by design.

So accepting this proposal means report-derived clinical text reaches **a second provider**
(TypeSafe/Jev) in addition to the one that already performs the review (OpenAI). That is a new
egress path, not an extension of an existing one.

Three ways to answer it, in the order I would defend them:

1. **Accept it explicitly**, behind a feature flag that is off by default and a per-tenant opt-in,
   with the provider named in `/api/v1/status` and in the Studio surface. The report already leaves
   the application for the review itself, so the question is whether a second recipient is
   acceptable — an organisational answer, not a technical one.
2. **Restrict it to demo and legacy-fixture sources**, where no real report is involved. This makes
   the feature a pack-development tool only, which is most of its value, at no egress cost.
3. **Reject the proposal.** There is no version of comment-actionability scoring that does not send
   the comment.

Recommend (2) for the first release and (1) only on an explicit decision recorded in
`FOUNDATION_CHANGELOG.md`. Option 2 delivers the pack-comparison payoff — the reason this proposal
exists — without adding an egress path at all.

### The Studio surface

A new Studio view, **Comment quality**, beside Review history / Feedbacks / Analytics / Skills /
Playground. Not a section inside Analytics.

Per review:

```
Report: "CT chest without contrast. Findings: …"        v3 · vesta-qatr-0.3.0

  General comments
  ● Actionable        "The impression states there is no pneumothorax; the
                       findings describe a small apical pneumothorax.
                       Reconcile the impression with the findings."
  ◐ Partly actionable "Consider clarifying the comparison study reference."
  ○ Unrated           "Terminology is inconsistent."      low confidence

  Critical findings
  ● Actionable        "…"
```

Per pack version, the aggregate that justifies the feature:

```
  Pack                  Comments   Actionable   Partly   Not   Unrated
  vesta-qatr-0.3.0           412        68%       24%     5%       3%
  vesta-qatr-0.2.0           377        51%       31%    14%       4%
```

The aggregate is **advisory**. It informs a pack release conversation; it does not gate one, and it
is not clinical evidence. `AGENTS.md` already forbids presenting unreviewed guidance as approved
clinical policy.

### Validation

Same discipline the classification proposal arrived at, and the same trap avoided.

The existing `unclear_wording` and `wrong_grouping` feedback reasons are **a sampling prior, not
labels.** They say a human was unhappy with a review; they do not say which comment, at which
rubric level. Using them as ground truth would repeat exactly the orthogonality error corrected in
`FEEDBACK_CLASSIFICATION_SPEC.md`. Use them to decide *which comments to adjudicate first*, and
nothing else.

Validate by hand-adjudicating comment text against the three levels, through `jev-align`'s score
task (`jeva optimize --score-level ...`): it selects the most uncertain comments plus a random
audit sample, takes a rationale per label, proposes rubric rewrites through GEPA under a human
accept/reject gate, and reports mean absolute error and rounded accuracy against a held-out split.

Record inter-rater agreement. If two readers cannot agree whether a comment is level 1 or level 2,
the boundary is badly worded and gets rewritten before the model sees it again. Three levels exist
to make that agreement achievable.

## Implementation Notes

### Relevant area

- `backend/workflow.py` — queue, step and workflow identity conventions; `execute` at `:56-120`
- `backend/main.py:83-90` — the reconciliation loop, the dispatch point for scoring
- `backend/schema.sql` — `observations`, `review_results` and their immutability triggers
- `backend/diagnostics.py:76-141` — health components and the readiness rule
- `backend/presentation.py:36-99` — `review()`, the public projection; **must stay unchanged**
- `frontend/src/App.tsx:14,70-72` — the view union and the Studio nav
- `frontend/src/ReviewOutput.tsx` — **unchanged**
- `frontend/src/AnalyticsView.tsx` — **unchanged**
- `frontend/src/CommentQuality.tsx` — new

### Add / modify

**Storage** — append-only, one row per comment per scorer version:

```sql
CREATE TABLE comment_scores (
 tenant_id TEXT NOT NULL, review_id TEXT NOT NULL, result_version INTEGER NOT NULL,
 observation_id TEXT NOT NULL, scorer_version TEXT NOT NULL,
 document TEXT NOT NULL CHECK(json_valid(document)), scored_at TEXT NOT NULL,
 PRIMARY KEY(tenant_id,review_id,result_version,observation_id,scorer_version),
 FOREIGN KEY(tenant_id,review_id,result_version,observation_id)
   REFERENCES observations(tenant_id,review_id,result_version,id)
);
CREATE TRIGGER comment_score_immutable BEFORE UPDATE ON comment_scores
BEGIN SELECT RAISE(ABORT,'Comment score is immutable'); END;
```

`document` holds `{score: <float>, level_probabilities: {<level>: <float>}, confidence: <float>}`.
The rendered level and the `Unrated` decision are derived at read time from the confidence floor, so
the floor can be retuned without rescoring. Schema bumps to the next version; per `AGENTS.md`,
cutovers use a fresh store and never migrate.

**Durable execution:**

- queue `qa-comment-score-f3-v1`, concurrency **1**, env `QA_COMMENT_SCORE_CONCURRENCY`, validated
  `1..32` like its siblings. Its own queue so scoring can never consume live review concurrency.
- workflow `qa.comment.score.f3.v1`, `max_recovery_attempts=5`
- deterministic id `qa:cs:{tenant}:{review_id}:{result_version}:{scorer_version}`
- **Dispatched by the existing reconciliation loop** when it observes a completed review whose
  comments have no row for the current scorer version — not from inside `workflow.execute`. The
  review path gains no branch, no dependency and no new failure mode, and the dispatch is naturally
  idempotent and recovers after a restart.
- One provider request per review carrying one `Score` question per comment, chunked at 20
  questions per request. A review with no comments is never enqueued.
- Bounded retry with backoff; on exhaustion the workflow completes and the comments stay unscored.
- Add the new identities to the `AGENTS.md` identity line, and a process-recovery test alongside
  `tests/test_f3_recovery.py` per `DBOS_VALIDATION.md`.

**API** — a new read-only Studio endpoint, `feedback:read`-equivalent scope to be decided in review:

- `GET /api/v1/reviews/{review_id}/comment-scores` — levels and confidences for the current result
  version.
- `GET /api/v1/comment-quality?period=&source=` — the per-pack aggregate, with `unrated` counted
  separately and never folded into a level.

Both additive. `QA-Version` unchanged *(to confirm)*. `presentation.review()` is untouched, so no
score can reach the review resource the radiologist's page reads — enforced in the projection, not
the stylesheet.

**Health** — a `comment_scorer` component mirroring `openai`: configured / not_configured from
settings, never auto-probed. Same trap as the classifier — `status_report` requires every component
in `("ok","configured","not_required")`, so when the flag is off or the mode is demo it must report
`not_required`, or every existing deployment's health pill turns amber. Add the label to
`frontend/src/SystemStatus.tsx:9`.

**Settings** — separate credential from `OPENAI_API_KEY`. Feature flag defaults to **off**; a
source restriction (see the egress decision) governs which reviews are eligible.

### Document changes this proposal carries

- `AGENTS.md` — schema version in the header; the DBOS storage line; the new queue and workflow
  identities. No Product boundary change: nothing here edits results or feeds ground truth.
- `prototype/API_DESIGN.md` — the two new endpoints.
- `prototype/DBOS_VALIDATION.md` — the new workflow and its recovery obligation.
- `prototype/WORKSPACE_SPEC.md` — the new Studio view in the navigation.
- `prototype/IMPLEMENTATION_STATUS.md` — schema version, tests actually run.
- `prototype/FOUNDATION_CHANGELOG.md` — the egress decision, with which option was chosen and why.
- `prototype/ANALYTICS_SPEC.md` — **unchanged.**

## Acceptance Criteria

- A completed review's comments each carry a level and a confidence in the Studio's Comment quality
  view.
- A comment scored below the confidence floor renders as `Unrated`, never as level 0.
- `GET /api/v1/reviews/{id}` contains no score field for any comment, and the report page renders
  no score, badge or ordering change. Diffing the review resource before and after scoring shows no
  change.
- Comment order in `ReviewOutput` is identical before and after scoring.
- The Analytics page is byte-identical before and after this change.
- The pack aggregate reports `unrated` as its own column, never folded into a level.
- With the scorer unconfigured, unreachable, or the flag off, reviews complete normally, no workflow
  is enqueued, and `/api/v1/status` reports `comment_scorer: not_required` with overall readiness
  unchanged from today.
- Submitting a review issues exactly the same number of provider requests as it does today.
- Killing the process mid-scoring and restarting produces exactly one row per
  `(review, result_version, observation, scorer_version)`.
- A second `UPDATE` against `comment_scores` raises `Comment score is immutable`.
- A review with no comments is never enqueued for scoring.
- A review from a source excluded by the egress restriction is never enqueued, verified by asserting
  no provider call is made for it.
- The rubric wording in use is read from the versioned scorer pack, not literal in Python.
- `uv run pytest` passes, including the new recovery test.
- `npm --prefix frontend run build` and `npx playwright test` pass.
- `uv run python scripts/check_docs.py` passes.
- `prototype/openapi.json` and `frontend/src/generated-api.ts` are regenerated, not hand-edited.

## Verification Prompt

With the scorer configured and the source restriction set to demo, submit a report in demo mode and
wait for it to complete. On the report page, confirm the QA comments look exactly as they do today —
no badges, no levels, no reordering, nothing new anywhere near them. Open QA Studio → **Comment
quality** and find that review: each comment now carries a level, and at least one low-confidence
comment reads `Unrated` rather than *Not actionable*. Check the per-pack table beneath it lists the
active pack with an `Unrated` column of its own. Now open the browser devtools network tab, reload
the report page, and confirm the review resource it fetches contains no score field. Finally, turn
the scorer's feature flag off, submit another report, and confirm it completes normally, appears in
Review history as usual, shows nothing in Comment quality, and that `/api/v1/status` reports the
scorer as `not_required` with the health pill unchanged.
