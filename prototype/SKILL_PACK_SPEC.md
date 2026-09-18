> Design proposal, not implemented. This document describes a target organization for report QA
> skills and a playground. It changes no current behavior. Application **0.13.0**, bundle **1.17**,
> foundation **F3** remain as described in [FOUNDATION_CHANGELOG.md](FOUNDATION_CHANGELOG.md).

# Skill pack and playground specification

Status: **proposal for review** · 18 September 2026 · supersedes nothing until accepted

## 1. Why this exists

Today a radiologist cannot answer two simple questions without an engineer:

1. *What exactly is the AI being told to do?*
2. *If I change this sentence, what changes in the comments?*

This specification reorganizes report QA skills so both questions are answerable in the browser,
and so that answering them cannot affect live report QA.

Audience: radiologists and non-specialist reviewers (read, edit, test), and engineers (publish).

## 2. Decisions taken

These were confirmed before drafting and are not reopened here.

| Decision | Choice |
|---|---|
| Skill definition format | Agent Skills format — `SKILL.md` folders with frontmatter |
| Portability | Format only. The pack stays app-specific; it is not loaded by other agent runtimes |
| Playground isolation | Same application, separate mode, separate data |
| Publish authority | Engineer-only. Clinicians propose; they never publish |
| Test corpus | Paste-your-own **and** a curated example set stored with the pack |
| Output contract / ownership rules | Move out of Python into a visible skill file, editable like any other skill |
| 43-rule critical catalog | Frozen. Byte-pinned to qatr upstream, readable, not editable |

## 3. What makes the current process hard

Evidence from the installed implementation, not opinion.

### 3.1 The prompt is split across two places, one of which is invisible

The nine `SKILL.md` files hold roughly 20 KB of clinical instruction. A further ~1.8 KB of
model-facing rules — the check-ownership map, the output contract, the `critical_basis` rules,
the authority labels — is assembled in Python at request time:

- `backend/content.py:60` `combined_instructions()` — ~820 characters
- `backend/combined.py:19` `task()` — ~990 characters

None of it appears in Skills & knowledge. A reviewer editing a skill is editing part of the
prompt and cannot see the rest.

### 3.2 One sentence costs eight to eleven coordinated edits

`qa-skills/framework/tools/validate.py` cross-checks every artifact, so changing one sentence
requires all of:

1. `skills/<name>/SKILL.md`
2. `skills/<name>/skill.json` — version bump; frontmatter `description` must byte-match
3. `skills/<name>/CHANGELOG.md` — must contain `## <new version>`
4. `registry.json` → `skill_versions` must agree
5. the evaluation suite — `suite.skill_version` must agree
6. `scripts/build_skill_evaluations.py` — because suites are generated, hand edits are overwritten
7. `scripts/release_skill_package.py` → regenerates `MANIFEST.json` and `lock.json`
8. `qa-skills/framework/tools/validate.py` must pass
9. If `content_version` moves: `backend/skill_runtime.py:98`, `backend/content.py:7-8`,
   `backend/settings.py:49` are hardcoded to `0.3.0` and must be edited too

Clinical content and Python are welded together. Content cannot version without a code change.

### 3.3 There are only two disk states, and one of them is production

`runtime_config()` calls `load_snapshot()` on every review request (`backend/main.py:341`) and
re-verifies every file hash. Therefore:

- edit a file **and** regenerate manifest/lock → live on the next review, with no gate
- edit a file **without** regenerating → every review fails closed with `KNOWLEDGE_SOURCE_UNAVAILABLE`

There is no third state. Skills Studio avoids both by keeping drafts in `knowledge_drafts` and
never composing them (`backend/knowledge.py`), which is safe but means **a draft can never be run**.

### 3.4 Structure that no longer matches execution

`registry.json` still groups skills into `language_review` / `consistency_review` /
`critical_finding_review`, and `skill_runtime.adapt()` still projects per stage — but F3 issues a
single combined call. Reviewers reason about a three-stage model that no longer describes
execution. Separately, `qa-input-adequacy` is presented as a skill but is a deterministic host
gate that is never sent to the model.

### 3.5 Two inconsistencies to close

- The Studio permits saving drafts of `critical-rules.json` and the pinned source wording.
  `backend/knowledge.py` treats `catalog` and `policy_source` documents as editable exactly like
  skills, and `can_edit` is one global flag with no per-kind check. This contradicts "frozen".
- `scripts/evaluate_skills.py --execute` raises `SystemExit` (line 32) but is still referenced as a
  working command in `qa-skills/clinical-content/evaluation/METHOD.md`.

## 4. Target model — four nouns

| Noun | Definition | Who owns it |
|---|---|---|
| **Skill** | One folder, one `SKILL.md`. Everything a human needs is in that file. | Clinical reviewer |
| **Pack** | One `PACK.md` naming a single version and the ordered skills that are on. | Clinical reviewer proposes; engineer publishes |
| **Workspace** | A named, tenant-scoped draft of a whole pack. Runs, but never serves live QA. | Clinical reviewer |
| **Run** | A report plus a pack reference, producing comments. Live or playground. | — |

Three verbs, one screen each: **review**, **edit**, **test**.

## 5. Pack layout

```
qa-skills/pack/
  PACK.md                       # one version; ordered list of skills that are on
  skills/
    _review-contract/SKILL.md   # the output contract, moved out of Python (§7)
    clinical-report-qa/SKILL.md
    qa-terminology-errors/SKILL.md
    ...
  references/                   # FROZEN, byte-pinned to qatr upstream
  examples/
    <example-id>.md             # curated test reports with expectations (§8)
```

### 5.1 `SKILL.md` frontmatter

The Agent Skills shape — YAML frontmatter, markdown body — carrying everything `skill.json`
carried today. Arbitrary frontmatter keys are permitted by the format, so nothing is lost.

```yaml
---
name: qa-terminology-errors
description: Find actionable spelling, dictation and single-span terminology defects.
version: 0.2.0
role: check                     # shared | check | synthesis | verification | host-gate
owns: [TERM]                    # issue codes this skill may emit
references:                     # optional; frozen files this skill needs loaded
  - references/rich-report-context.md
---
```

Rules:

- `version` is derived from content hash at publish, not hand-maintained. It is displayed, not edited.
- `role: host-gate` marks a skill that is **never sent to the model** (today's `qa-input-adequacy`).
  The UI labels it distinctly and disables the editor body.
- Frontmatter is parsed as YAML. The current validator's `dict(line.split(":", 1))` parse and its
  JSON-quoted `description` requirement are replaced.

### 5.2 `PACK.md`

One human-readable file replacing `registry.json`:

```markdown
---
pack_id: vesta-web-report-qa
version: 0.4.0
status: prototype_evaluation
clinically_approved: false
skills:                         # order is the order composed into the prompt
  - _review-contract
  - clinical-report-qa
  - qa-terminology-errors
  - ...
---

# What this pack does
Plain-language summary a radiologist can read in one minute.
```

### 5.3 Migration map — what disappears

| Today | Tomorrow |
|---|---|
| `skill.json` ×9 | frontmatter keys in `SKILL.md` |
| `registry.json` | `PACK.md` |
| `registry.json` → `stages` | removed; one combined call, order from `PACK.md` |
| `registry.json` → `skill_versions` | derived from content hash |
| `MANIFEST.json`, `lock.json` | build outputs of publish; never hand-edited, still verified at load |
| 9 × `CHANGELOG.md` | one pack changelog, composed from workspace change notes at publish |
| `evaluation/suites/*.json` (generated) | `examples/*.md`, authored as data |
| `scripts/build_skill_evaluations.py` | retired |
| prompt text in `content.py` / `combined.py` | `skills/_review-contract/SKILL.md` |
| hardcoded `0.3.0` in three Python files | removed; pack version is data |

Nothing is deleted from `qa-skills/clinical-content` until a published pack passes its gate.

## 6. The three modes

One application. One deployment. A hard wall between live and playground.

### 6.1 Skills (live) — read-only

- The published pack, its version, and every skill in plain text.
- **The exact composed prompt** the model receives, shown in full. This is the transparency fix
  for §3.1: what you review is what is sent.
- The 43-rule catalog rendered as a searchable table of 43 rows, not a 41 KB JSON blob.
  Read-only, with its qatr provenance (repo, commit, blob hash) visible.
- No editing controls in this mode at all.

### 6.2 Playground — edit and test

- Create or pick a **workspace**. A workspace is a draft of the whole pack, not a per-document draft.
- Edit any skill's text in one box, with a change note. Same editor ergonomics as today.
- Test, two ways, both available:
  - **Paste your own** — paste a report, run once, see the result.
  - **Curated set** — run the pack's saved examples in one action.
- Results render as **current pack vs workspace pack, side by side, per comment**:
  `kept` / `new` / `dropped` / `changed`. This diff is the review artifact a radiologist signs
  off on. A prose diff of the skill text is secondary and stays available for engineers.
- Every playground run is stamped `release_id = "draft:<workspace>@<pack-hash>"` and is
  structurally incapable of being mistaken for a live review.

### 6.3 Proposals — submit and publish

- A clinician submits a workspace with a summary. It becomes read-only pending review.
- An engineer publishes (§9). Clinicians never touch the filesystem and never publish.

## 7. The review contract becomes a skill

`combined_instructions()` and `task()` move into `skills/_review-contract/SKILL.md`, editable
like any other skill, as decided.

The safety boundary is drawn at a different place than the file:

- **Editable prose** — what the model is *told* to return: the ownership map, the shape of
  `critical_basis`, the untrusted-report rule, the coverage requirement.
- **Code, not editable** — what is *enforced* on what comes back: the `CombinedOutput` Pydantic
  schema, anchor grounding in `skill_runtime.adapt()`, ownership validation, duplicate detection.

If the prose and the validator diverge, runs fail closed and visibly — in the playground, before
publish, never in live QA. The ownership map should be **generated into the prompt from the pack's
`owns:` declarations** rather than typed by hand, so a skill edit cannot silently desynchronize it.

`_review-contract` is marked `critical: true` in frontmatter. Editing it is permitted, but the
publish gate requires a clean run of the full curated set, not a partial one.

## 8. Curated examples as data

One file per example, authored by clinicians, replacing the code-generated suites:

```yaml
---
id: TERM-01
title: Dictation error changes meaning
partition: development          # development | held_out
expect:
  comments: [{ skill: qa-terminology-errors, issue_code: TERM, quote: "silhoutte" }]
  forbidden_issue_codes: [CRIT]
---

Findings:
...
```

An expectation is a **proposed** hypothesis, never adjudicated truth — that framing from
`evaluation/METHOD.md` is preserved verbatim. `held_out` examples are hidden in the playground UI
and run only at the publish gate, so drafts cannot be tuned against them.

Adding an example is the single highest-value contribution a radiologist can make. Today it
requires editing Python; here it is a form.

## 9. Publish — one engineer action

A publish takes a workspace and performs, in order:

1. Compose the draft pack and verify frontmatter, unique issue-code ownership, and that every
   `owns:` code is reachable.
2. Write skill files to disk and regenerate `MANIFEST.json` + `lock.json`.
3. Run package validation (today's `validate.py`, adapted to the new layout).
4. Run the **full** curated set, development and held-out, and record results.
5. Bump the pack version and compose the pack changelog from workspace change notes.
6. Refuse on any failure, leaving disk untouched.

This is the same integrity that exists today. What changes is that it stops being a manual
nine-step human procedure and stops being the *editing* interface.

## 10. Data model

Additive. No change to existing review tables, views, triggers or immutability guarantees.

```sql
CREATE TABLE skill_workspaces (
  tenant_id TEXT NOT NULL REFERENCES tenants(id), id TEXT NOT NULL,
  name TEXT NOT NULL, created_at TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('open','submitted','published','closed')),
  PRIMARY KEY(tenant_id,id)
);
-- existing knowledge_drafts gains a workspace_id, keeping its revision semantics
CREATE TABLE playground_runs (
  tenant_id TEXT NOT NULL, workspace_id TEXT NOT NULL, id TEXT NOT NULL,
  pack_ref TEXT NOT NULL,           -- always 'draft:<workspace>@<hash>'
  source TEXT NOT NULL CHECK(source IN ('pasted','example')),
  example_id TEXT, report_text TEXT NOT NULL,
  created_at TEXT NOT NULL, result TEXT CHECK(result IS NULL OR json_valid(result)),
  PRIMARY KEY(tenant_id,id)
);
```

Isolation rules, enforced in code and asserted in tests:

- Playground runs are written **only** to `playground_runs`. They never enter `review_records`,
  `review_results` or `observations`.
- Analytics, feedback inbox and stakeholder outcomes read live tables only and must be tested to
  exclude playground data.
- Copy-to-clipboard is disabled or watermarked in the playground, so a playground comment cannot
  be pasted into a real report.
- Accepted live reviews keep their immutable snapshot. A workspace can never alter a past result.

### 10.1 The one enabling backend change

`load_snapshot()` currently resolves a pack from a directory only (`QA_SKILL_PACKAGE_DIR`). It
takes a **pack reference** instead:

- `published` → today's behaviour: read disk, verify hashes, fail closed. Live QA uses only this.
- `draft:<workspace>` → the published pack overlaid with that workspace's draft rows, stamped with
  a draft `release_id`.

Everything else in this document is UI and data on top of that one change.

## 11. API

| Endpoint | Scope | Purpose |
|---|---|---|
| `GET /api/v1/pack` | `skills:read` | Published pack, skills, composed prompt, catalog table |
| `GET/POST /api/v1/workspaces` | `skills:read` / `skills:write` | List, create a workspace |
| `PUT /api/v1/workspaces/{id}/skills/{name}` | `skills:write` | Save a skill draft (keeps today's revision + hash conflict semantics) |
| `POST /api/v1/workspaces/{id}/runs` | `skills:write` | Run pasted report or curated set against the draft pack |
| `GET /api/v1/workspaces/{id}/diff` | `skills:read` | Output diff, current vs draft |
| `POST /api/v1/workspaces/{id}/submit` | `skills:write` | Submit a proposal |
| publish | not an API | Engineer-only script (§9) |

Idempotency keys, `QA-Version` pinning and tenant-from-credential rules are unchanged. A new
`skills:run` scope is worth considering so a reviewer can edit without being able to spend.

## 12. Spend

Playground runs make real model calls and therefore need budget, but must not compete with live QA:

- A playground workspace draws on its **own** authorized spend session, separate from the session
  live reviews draw on. Exhausting the playground budget must never block report QA.
- Reservation, admission and the conservative accounting in `backend/spend.py` are reused as-is.
- Running the full curated set is the expensive action. It is one explicit button with a visible
  estimated cost and a confirmation, never automatic on save.

## 13. What must not be simplified away

Keep in code, out of the editor:

- The strict output schema and **anchor grounding** — every quote must resolve verbatim and
  uniquely within its section. This is what prevents fabricated findings.
- Ownership validation: a check cannot emit another check's issue code.
- Spend admission before dispatch.
- Immutable snapshots on accepted reviews.
- Fail-closed on package corruption.
- The frozen qatr byte pins in `content.py:validate_catalog()`.

The goal is fewer human steps, not fewer guardrails. Today the guardrails and the paperwork are
tangled; this separates them.

## 14. Sequencing

| Phase | Delivers | Risk |
|---|---|---|
| P1 | Pack reference in `load_snapshot()`; remove hardcoded `0.3.0`; workspaces table | Low; no user-visible change |
| P2 | Playground: paste-your-own, run, output diff | Medium; first draft composition path |
| P3 | Format migration: frontmatter, `PACK.md`, manifest/lock as build outputs | Medium; one-time conversion, validator rewrite |
| P4 | `_review-contract` moved out of Python; ownership map generated from `owns:` | Medium; prompt changes, needs live comparison |
| P5 | Curated examples as data; publish gate; proposals | Low |
| P6 | Catalog table view; block catalog/source drafts; retire dead eval path | Low; closes §3.5 |

P1 and P2 together are the smallest thing that makes editing testable. P3–P4 are what make the
skill readable by a non-specialist. They are separable.

## 15. Out of scope

- Separate Test/Production deployments (ENV-01 in [BACKLOG.md](BACKLOG.md)) — this uses one
  deployment with separate data, by decision.
- Portability of the pack to other agent runtimes. `AGENTS.md:47` stands: these are not
  coding-agent skills. Only the file shape is borrowed.
- Editing the critical catalog or the pinned source wording.
- Clinical approval of any content. Nothing here makes provisional content approved.
- Adding or removing skills from a pack in a workspace. A new issue code touches ownership
  validation and public comment grouping, so it is deferred to a second version and called out
  explicitly rather than assumed.
- Replaying historical reports against a draft pack. The test corpus is paste-your-own plus the
  curated set, by decision.

## 16. Open questions

1. Does a clinician need `skills:write` to run the playground, or should a separate `skills:run`
   scope gate spending?
2. Should a workspace pin the published pack version it forked from, and refuse to submit when
   live has moved on — or rebase like today's `source_changed` warning?
3. How many curated examples is a credible publish gate? 54 exist today, all synthetic.
4. Who is the named approver on a proposal, and is one enough?
5. Should the composed-prompt view be visible to every `skills:read` holder, or engineers only?
