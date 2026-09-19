> Design proposal, no interface implemented. This document describes the interaction model for
> the playground proposed in [SKILL_PACK_SPEC.md](SKILL_PACK_SPEC.md). Its P1 foundation — pack
> references, draft composition, workspace fork pinning and the schema-5 tables — landed on
> 19 September 2026; see [FOUNDATION_CHANGELOG.md](FOUNDATION_CHANGELOG.md). Every screen, route
> and control described here is still unbuilt. Application **0.13.0**, bundle **1.18**,
> foundation **F3**, schema **5**.

# Playground UX interaction model

Status: **proposal for review** · 19 September 2026 · companion to [SKILL_PACK_SPEC.md](SKILL_PACK_SPEC.md) §6
Interaction decisions taken 19 September 2026 are recorded in §10.

[SKILL_PACK_SPEC.md](SKILL_PACK_SPEC.md) decides *what* the playground is: a workspace draft of a
whole pack that runs, never serves live QA, and is published only by an engineer. It does not
decide how a radiologist moves through it. This document does, at the level needed to implement
P2 and accept it.

Everything here inherits [WORKSPACE_SPEC.md](WORKSPACE_SPEC.md) and
[SKILLS_STUDIO_SPEC.md](SKILLS_STUDIO_SPEC.md). Where this document is silent, those contracts hold.

## 1. The one sentence

A reviewer edits skill text, runs a report, and sees **what changed in the comments** — never in
the same place, and never in the same visual register, as a real review.

## 2. Placement in Scope–Work–Studio

The established layout is preserved. The Studio tool list gains **one** entry, not three.

| Mode (§6) | Where it lives | Change |
|---|---|---|
| Skills (live, read-only) | Existing **Skills & knowledge** tool | Gains the composed prompt and the 43-row catalog table; loses its editor |
| Playground (edit and test) | New **Playground** Studio tool | New |
| Proposals (submit) | A list inside Playground, not a tool | New |

Rationale: Studio tools stay compact per [AGENTS.md](../AGENTS.md). Proposals are a state of a
workspace, not a separate place, so they belong to the workspace surface that produced them.

Consequence for today's code: the editor in `frontend/src/SkillsKnowledge.tsx` moves into the
Playground and becomes workspace-scoped. Skills & knowledge becomes what its name already claims —
a reading surface. Draft revision semantics, conflict handling and export are not redesigned; they
move.

Playground occupies the Work region like every other Studio tool. Scope keeps showing **reports**.
A workspace is never a row in the reports column.

The composed prompt shown in Skills & knowledge is visible to **every `skills:read` holder**, by
decision. A clinician editing half a prompt must be able to read the whole of it; that is the
§3.1 transparency fix and the reason this feature exists. This concerns the *published pack's*
composition. It does not relax `backend/presentation.py`: a review record's captured instruction
snapshot stays out of public projection, and confirming that boundary in code is P1 work.

## 3. The spine: Edit → Run → Compare

One workspace header, three panes, in that reading order. The header is persistent; the panes are
not modal and do not replace each other.

```
┌ Playground ─────────────────────────────────────────────────────────────┐
│ Workspace: Terminology tightening ▾   Open · forked from pack 0.4.0      │
│ DRAFT — playground output, not a clinical review                         │
├───────────────┬─────────────────────────────────────────────────────────┤
│ Skills        │  Edit        <skill text, change note, save>            │
│ (draft badges)│  Run         <paste-your-own | curated set>             │
│               │  Compare     <current pack vs workspace, per comment>   │
└───────────────┴─────────────────────────────────────────────────────────┘
```

- **Skills list** — same ergonomics as today's `knowledge-list`: title, kind, version, and a draft
  badge per skill. A `role: host-gate` skill is listed, labeled, and has a disabled body. Frozen
  references and the catalog appear read-only with no draft affordance at all (closing §3.5).
- **Edit** — today's editor: plain Markdown, compare-with-installed, required change summary,
  saved revisions, restore, export. Unchanged behavior, new parent.
- **Run** — the test surface (§4).
- **Compare** — the output diff (§5). Empty until a run completes.

Switching panes never discards unsaved text. Switching workspaces or Studio tools follows today's
rule: warn before discarding, preserve mounted state.

### 3.1 A run needs a hash, so a run needs a save

Every playground run is stamped `draft:<workspace>@<pack-hash>`. Unsaved editor text has no hash.

Therefore **Run is disabled while the editor is dirty**, and the primary action reads
**Save and run**: one click, save first, then dispatch, with the change note prompt inline. A run
never silently tests text the reviewer has not committed to a revision, and the diff can always
name the exact revision it tested.

## 4. Run

Two sources, both always available, as decided.

### 4.1 Paste your own

A single report field with the same minimum-input hint and the same deterministic input gate as
live review. It is a distinct field, in a distinct region, and it never pre-fills from the Scope
column. Copying a live report into it is a deliberate paste.

### 4.2 Curated set

One action runs the pack's `partition: development` examples. Progress is a single bounded counter
with a **Stop** action; stopping keeps completed results and marks the rest `not run`.

`held_out` examples are **absent from the UI**, not greyed out — a disabled row still leaks its id
and title. The surface shows one line: *"N held-out examples are reserved for the publish gate."*

### 4.3 What a run actually dispatches

A comparison needs two outputs. The run dispatches the **draft pack**, and reuses the published
pack's result for the same report text and published pack hash when one is already stored;
otherwise it dispatches the published pack too. The UI states which of the two it did, because it
is the difference between one provider call and two.

Caching is keyed on (report text, published pack hash), so a stale reuse is not expressible: a
published pack that has moved has a different hash and misses the cache.

An unmodified workspace is refused before dispatch with *"This workspace matches the published
pack. Edit a skill before running."* — not run, not diffed.

### 4.4 Progress

Progress names the four real phases, as [AGENTS.md](../AGENTS.md) requires: input validation,
combined report review, output validation, comment assembly. With two dispatches, two lanes are
shown, labeled **Published pack** and **Workspace**, each with those four phases. No invented
phase, no spinner standing in for a phase.

### 4.5 Failure is the product

The playground's value is that a bad edit fails here instead of in live QA, so failures are
rendered as findings, not as toasts.

| Outcome | Surface |
|---|---|
| `REVIEW_CONTEXT_TOO_LARGE` | Rejected before dispatch, naming composed-pack size vs allowance, with the skills ordered by contribution |
| Output schema rejection | Names the field and the draft rule that asked for it |
| Anchor grounding failure | Shows the quote the model returned and that it does not resolve verbatim in the report |
| Ownership violation | Names the emitting skill, the issue code, and the skill that owns it |
| Duplicate detection | Shows both comments |
| Model refusal / incomplete | Stated plainly; no repair call, matching live behavior |
| `MODEL_OUTCOME_UNKNOWN` | Stated as unknown, never auto-retried. **Run again** is an explicit new run with a new key, labeled as a new run |

A divergence between edited prose and the code-enforced validator (§7 of the pack spec) is the
expected case here, and reads as *"the workspace asks for something the contract rejects"* with
both sides shown. It is never presented as a system error.

## 5. Compare — the review artifact

Per comment, published pack on the left, workspace on the right, grouped by the two visible
result groups so the diff reads like the thing it will become.

| Status | Meaning | Treatment |
|---|---|---|
| `kept` | Same comment, same wording | Collapsed by default |
| `changed` | Same finding, different wording | Expanded, inline word-level diff |
| `new` | Only the workspace produced it | Expanded |
| `dropped` | Only the published pack produced it | Expanded |

- A counts line leads: *"12 kept · 3 changed · 2 new · 1 dropped."* Status is carried by a text
  label as well as color.
- Each row states the owning skill and issue code, so a reviewer can jump back to the skill that
  caused the change. That jump is the loop this whole feature exists to close.
- Filter by status. `kept` is filterable away in one click.
- Across a curated-set run, the same four statuses aggregate per example, and an example whose
  expectations moved from met to unmet is sorted first. An expectation remains a **proposed
  hypothesis, never adjudicated truth**; the UI says so where results are shown, not only in a
  method document.
- The prose diff of the skill text stays available, one level down, labeled for engineers.

On narrow screens the two sides stack as labeled pairs. No status, count, or side is hidden.

### 5.1 When live moves on

A workspace pins the published pack version it forked from, by decision. A diff computed against a
pack that has since been republished does not describe what publish will produce, so it is not
presented as if it does.

- The workspace header carries the fork: *"forked from pack 0.4.0"*.
- When live moves past that version, the header reads **Out of date**, every stored diff in the
  workspace is marked **stale** with the version it was computed against, and **Submit is refused**.
- **Rebase** is an explicit action. It re-points the workspace at the current published pack,
  preserves every saved skill revision, and records itself in the workspace change notes. Past
  runs are kept, not deleted: each carries the pack hash it was composed against, so a run from
  before the rebase identifies itself as a superseded composition and is shown as one.
- Rebase never silently merges. Where a skill's published text changed under a saved draft, the
  reviewer gets today's compare-with-installed view on that skill and reconciles it, which is the
  existing `source_changed` reconciliation at pack granularity.
- A rebase does not re-run anything. The workspace returns to Open with no diff until the reviewer
  runs again — a diff always names the pack pair that produced it.
- A workspace that goes out of date **after** submission is returned to Open with a stated reason.
  The engineer's gate would run against a pack the reviewer never saw, so the submission no longer
  means what it meant when it was made.

## 6. The wall, as the user experiences it

Isolation is asserted in code and tests ([SKILL_PACK_SPEC.md](SKILL_PACK_SPEC.md) §10). These are
the affordances that make it visible, so that no one has to remember which mode they are in.

- A persistent, **non-dismissible** banner on every playground surface: the workspace name, the
  `draft:<workspace>@<hash>` stamp, and *"not a clinical review"*. It is not a colored border
  alone — it carries text and an icon.
- **Copy is absent**, not disabled-with-a-tooltip: no comment copy, no full-template copy. The one
  way text leaves the playground is **Export run** (JSON, stamped with the draft release id),
  which is not a paste-ready comment.
- No feedback control, no stakeholder outcome, no accept, no "revise as new draft" into live.
- Playground runs never appear in the reports column, review history, the feedback inbox, or
  analytics. There is no navigation path from a playground result to a live review surface.
- The inverse holds: a live review offers no path into a workspace. Reproducing a live report in
  the playground is a paste.

## 7. Proposals

A workspace has one visible status: **Open · Submitted · Published · Closed**.

- **Submit** requires a summary and at least one completed run in the workspace. Submitting makes
  every skill body read-only; the diff and run history stay readable.
- **Submit is refused while the workspace is out of date** (§5.1).
- A submitted workspace shows what an engineer will run at the gate — the **full** curated set,
  development and held-out — as a stated expectation, not as a button. That gate is a **regression**
  gate: it asserts that an edit changed nothing it should not have. It is not clinical validation,
  and the UI says so where the gate is described. Clinical adjudication stays in F5 per
  [BACKLOG.md](BACKLOG.md).
- There is **no approver step**, by decision, and no approve control anywhere in the UI. A
  submitted workspace waits for an engineer. Whether a named clinical approver is required is
  deliberately deferred (§11), so the submit surface must not imply one exists.
- There is **no publish control in the browser for any role**. It is structurally absent, not
  permission-disabled, matching today's "the browser has no publish button".
- Reopening a submitted workspace is an explicit action that clears the submission and is recorded
  in the workspace's change notes.

## 8. Permissions

| Scope | Can |
|---|---|
| `skills:read` | Read Skills & knowledge, open workspaces, read diffs and run history |
| `skills:write` | Everything above, plus edit, save, run, submit |

Read-only users see the Playground tool and its content with edit, run and submit absent.

There is **no `skills:run` scope**. Its only surviving rationale was a read-and-run approver who is
not the author — spend authorization, the other rationale, was removed on 18 September 2026 — and
the approver question is deferred (§11). A scope with no user is not added on speculation. If an
approver role is later introduced, `skills:run` is introduced with it, and the split is
additive: `skills:write` implies running, so existing credentials do not change meaning.

## 9. Acceptance criteria for P2

Testable, and phrased so a failing one blocks the phase.

1. A playground run appears in no live surface: reports column, history, feedback inbox, analytics,
   outcomes. Asserted by test against the store, not by inspection.
2. No playground surface exposes a copy-to-clipboard control for comment text.
3. Run is unavailable while the editor is dirty; **Save and run** produces a run whose stamp names
   the revision it saved.
4. An unmodified workspace cannot dispatch.
5. Progress shows the four real phases per lane, and two lanes when both packs are dispatched.
6. Each failure class in §4.5 renders its named surface, verified with controlled fixtures — no
   provider call needed.
7. `held_out` example ids and titles appear in no playground response payload.
8. The draft banner is present on every playground route and cannot be dismissed.
9. Narrow-viewport diff stacks without hiding a status or a count.
10. Switching Studio tools preserves unsaved workspace edits; switching workspace warns first.
11. A workspace whose forked pack version is no longer published reads **Out of date**, marks stored
    diffs stale, and refuses submit. Rebase preserves every saved revision and clears the diffs.
12. No approve control and no `skills:run` scope exist in the shipped surface or the generated
    contract.

## 10. Decisions taken

Confirmed 19 September 2026. They are not reopened here.

| Question | Decision |
|---|---|
| Does Skills & knowledge lose its editor? | Yes. Editing lives in a workspace, where it can be run (§2) |
| Published-pack result cached or re-dispatched? | Cached on (report text, published pack hash) (§4.3) |
| Copy absent or watermarked? | Absent. Export a stamped run instead (§6) |
| Curated-set run cancellable mid-flight? | Yes; completed results kept, rest marked `not run` (§4.2) |
| Workspace behavior when live moves on | Pin the forked version, mark diffs stale, refuse submit, explicit rebase that keeps saved revisions and past runs (§5.1) |
| What the publish gate asserts | Regression across the full curated set, not clinical validation (§7) |
| Composed-prompt visibility | Every `skills:read` holder (§2) |
| Separate `skills:run` scope? | No. Deferred with the approver question (§8) |

## 11. Still open

One question, deferred by decision rather than undecided by omission:

**Who is the named approver on a proposal, and is one enough?**
([SKILL_PACK_SPEC.md](SKILL_PACK_SPEC.md) §16.4.) P5 delivers proposals with no approval step. The
cost is a submit surface that may be built twice, so it is built to accommodate one: a submitted
workspace is a read-only record with a status field, not a two-state toggle, and adding an approval
transition later must not require re-modelling it.
