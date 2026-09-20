# Feedback inbox triage order

**Status:** proposal under review. This document is not implementation authority and changes nothing until accepted.

Let the Feedback inbox be ordered by how uncertain the classifier was, and export that ordering for
the alignment loop, so adjudication effort lands on the comments that would most improve the
classifier instead of on whatever arrived most recently.

**Depends on** [FEEDBACK_CLASSIFICATION_SPEC.md](FEEDBACK_CLASSIFICATION_SPEC.md) iteration 1. There
is nothing to order by until classification probabilities exist. Do not schedule this first.

## Source

Motivation:

The classification proposal stores a probability per Noul per feedback comment and shows a band on
the inbox row. Nothing consumes those probabilities for prioritisation. The inbox is fixed at
newest-first (`backend/reporting.py:46-50`, `ORDER BY f.rowid DESC`), which is the right default for
"what just came in" and the wrong one for "what should I look at to make this better."

That matters because the classification proposal's validation plan runs rounds of human
adjudication through `jev-align`, whose whole acquisition strategy is *label the ambiguous rows
plus a random audit sample*. Today an operator would have to page through the inbox by hand to find
those rows, and there is no way to get them out of the application at all.

## Problem

1. **The useful rows are scattered.** A comment the classifier scored 0.51 / 0.49 — the one whose
   label is a coin-flip and whose adjudication would most change the criteria — sits wherever it
   happens to fall in arrival order, indistinguishable at a glance from forty confident rows.
2. **There is no export.** The alignment loop needs a CSV of comment text. The only route today is
   paging the API by hand and reassembling it.
3. **Newest-first cannot be turned off.** The ordering is literal in the query and the cursor
   scheme depends on it.

## Requested Change

### The sort control

One more control in the existing filter row, beside Rating / Reason / Topic / Source:

```
Sort  [ Newest first        ▾ ]      ← default, unchanged behaviour
      [ Most uncertain first  ]
```

**Newest first stays the default.** An operator opening the inbox to see what arrived should not
have the order changed under them.

Under *Most uncertain first*, rows are ordered by the classifier's ambiguity, descending:

```
ambiguity(p) = 1 - 2 * |p - 0.5|
row ambiguity = max(ambiguity(p)) over the pack's labels
```

This is the same measure the classification proposal uses to decide the `unclear` band, and the
same one `jev-align` uses to select an annotation batch. One definition, three consumers.

Unclassified rows — no explanation text, classifier unreachable, retries exhausted — have no
ambiguity. They sort **last**, and their count is disclosed rather than hidden:

```
Sort: Most uncertain first     38 ordered by uncertainty · 6 unclassified, at the end
```

### The export

A script, not a UI button:

```sh
uv run python scripts/export_feedback_alignment.py --tenant vesta --limit 200 \
  --out prototype/examples/feedback-alignment-2026-09.csv
```

It writes one row per feedback entry with columns `feedback_id`, `comment`, and the stored
probability per label, ordered exactly as *Most uncertain first* orders the inbox. That file is the
input to a `jeva optimize` round.

Must-haves for the export:

- **Tenant-scoped, like every other read.** The tenant comes from an argument resolved against the
  store, never a free-text label in the output path.
- **Comment text only.** No report text, no QA comment, no review ID. Same egress rule as the
  classifier itself: what leaves is what the user typed.
- **It writes a file and stops.** No provider call, no upload, no network.
- **The written path is reported on stdout**, so the operator knows what to hand to `jeva`.

### What this does not do

**It adds no way to correct a label.** Sorting by uncertainty puts the most-informative rows in
front of an operator who, in iteration 1, has no control to act on them with — they can read the
row and they can export it. That is deliberate (the correction affordance is deferred in the
classification proposal) and it does cap this feature's value: the sort is the human-readable half
of the export, not a triage workflow.

Say so in review rather than discovering it later. The follow-up that unlocks it is an operator
adjudication action on the row, which belongs in its own proposal.

## Implementation Notes

### Relevant area

- `backend/reporting.py:13-67` — `feedback_inbox`, its filters, ordering and cursor
- `backend/main.py:551-572` — the inbox endpoint and its query params
- `backend/contracts.py:382-403` — `FeedbackInboxItem` / `FeedbackInbox`
- `frontend/src/FeedbackInbox.tsx:38-46` — the filter form; `:11-30` — filter state and paging
- `scripts/export_feedback_alignment.py` — new

### Current behavior

- `ORDER BY f.rowid DESC LIMIT ?`, one extra row fetched to compute `next_cursor`.
- The cursor is a feedback id; `starting_after` resolves it to a `rowid` and appends `f.rowid<?`.
- `FeedbackInbox.tsx` already dedupes across pages by `feedback.id`
  (`new Map([...old, ...page.items]...)`), so a row seen twice is harmless today.

### Add / modify

**Newest classifier version per feedback**, since classification is append-only:

```sql
LEFT JOIN (
  SELECT tenant_id, feedback_id, document,
         row_number() OVER (
           PARTITION BY tenant_id, feedback_id
           ORDER BY classified_at DESC, classifier_version DESC
         ) AS recency
  FROM feedback_classifications
) c ON c.tenant_id = f.tenant_id AND c.feedback_id = f.id AND c.recency = 1
```

**Ambiguity**, one expression built from the pack's label list:

```sql
max(1 - 2*abs(json_extract(c.document,'$.clinical_inconsistency') - 0.5),
    1 - 2*abs(json_extract(c.document,'$.critical_findings')      - 0.5))
```

**A trap that must be guarded.** SQLite's scalar `max()` returns `NULL` if *any* argument is `NULL`
(verified on 3.45.1: `select max(0.9, NULL)` → `NULL`). If a future classifier pack adds a third
label and this expression is not updated, every `json_extract` for the missing key returns `NULL`,
every row's ambiguity becomes `NULL`, and the entire inbox silently sorts as "unclassified" — no
error, no empty result, just a quietly useless feature. Build the expression from the pack's label
list at query time, and add a test that fails when the SQL's labels and the pack's labels diverge.

**Ordering and cursor.** `ORDER BY ambiguity DESC NULLS LAST, f.rowid DESC`, with `f.rowid` as the
deterministic tiebreak. `NULLS LAST` requires SQLite ≥ 3.30; the environment has 3.45.1.

The cursor stays an opaque feedback id. Resolving it now reads both the row's ambiguity and its
rowid, and the page predicate becomes a row-value comparison, which SQLite supports:

```sql
(coalesce(ambiguity, -1), f.rowid) < (?, ?)
```

`coalesce(..., -1)` keeps unclassified rows in a single ordered tail rather than making the
comparison undefined. Reject a cursor whose sort order does not match the requested one, with the
existing `INVALID_CURSOR` error, rather than silently paging from the wrong position.

**Pagination honesty.** Ambiguity can change mid-scan when a row is reclassified under a new
classifier version. A row may then be seen twice — already handled by the client's dedupe — or
skipped, which is not. This is acceptable for a triage view and must be stated in the endpoint
description rather than papered over; the export script is the route that needs a complete set, and
it reads one page-free snapshot inside a single transaction.

**API.** New `sort` param on `GET /api/v1/feedback`: `recent` (default) | `uncertain`. The response
carries the applied sort and the unclassified count for the current filter. Additive; `QA-Version`
unchanged. Regenerate `openapi.json` and `generated-api.ts` with the existing scripts.

**Export script.** Reads through `store.db()` in one transaction, reuses the same ordering
expression as `feedback_inbox` — imported, not retyped, so the two cannot drift.

### Document changes this proposal carries

- `prototype/API_DESIGN.md` — the `sort` param and the pagination caveat.
- `prototype/README.md` — move to "Read by task" on acceptance.
- No `AGENTS.md` change. No schema change. No workflow change.

## Acceptance Criteria

- With no `sort` param, the inbox returns rows in exactly the order it returns them today.
- `sort=uncertain` returns rows ordered by descending ambiguity, with a row at p=0.50 ahead of a row
  at p=0.62, which is ahead of a row at p=0.95.
- Two rows with equal ambiguity return in a stable, repeatable order across repeated requests.
- Unclassified rows appear after every classified row, and the response states how many there are.
- Paging to the end under `sort=uncertain` returns every matching row exactly once, given no
  reclassification during the scan.
- A cursor issued under one sort order is rejected with `INVALID_CURSOR` when replayed under the
  other.
- A test fails if the ambiguity SQL's label list and the classifier pack's label list differ.
- `sort=uncertain` composes with the existing rating, reason, topic and source filters.
- The export script writes a CSV whose row order matches `sort=uncertain`, containing comment text
  and probabilities and no report text, review ID or QA comment.
- The export script makes no network call.
- `uv run pytest` passes.
- `npm --prefix frontend run build` and `npx playwright test` pass.
- `uv run python scripts/check_docs.py` passes.
- `prototype/openapi.json` and `frontend/src/generated-api.ts` are regenerated, not hand-edited.

## Verification Prompt

With classification enabled and at least a dozen classified feedback entries, open QA Studio →
Feedbacks. Confirm the list is newest-first and that a **Sort** control now sits beside the existing
filters. Switch it to *Most uncertain first*. The top row should be one whose topic bands read
`unclear`; expand its probability disclosure and confirm the value is near 0.5. Scroll to the
bottom: any entries with no explanation text appear last, and the count line states how many are
unclassified. Now apply the Topic filter as well and confirm the ordering survives the filter. Press
*Load more* twice and confirm no row appears twice and none is skipped. Finally run
`uv run python scripts/export_feedback_alignment.py --tenant vesta --limit 20 --out /tmp/a.csv`,
open the CSV, and confirm its first row is the same comment that was at the top of the sorted inbox
and that no column contains report text.
