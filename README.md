> Current implementation: application **0.13.0**, bundle **1.17**, foundation **F3**. [Decisions and verification](prototype/FOUNDATION_CHANGELOG.md) supersede older baseline statements below. Fresh schema 4 and API 2026-09-18 are implemented. F3 adds one combined request, guarded dispatch, durable response checkpoints and per-session spend admission. F4/F5 remain separate gates.

F3 startup requires a separately authorized test session and fresh `.qa-data-foundation-v3` storage. See [current startup and budget instructions](LOCAL_TESTING.md#f3-start-a-separately-authorized-test-session). Earlier release commands below are historical.


# Next build: clean-start, API-first foundations

The [revised foundation plan](prototype/FOUNDATION_PLAN.md) governs the next build: fresh app/DBOS
databases, one model request, qatr's three references/43-entry catalog, and preserved history,
feedback, outcomes, analytics and tenant drafts. See [implementation gates](prototype/IMPLEMENTATION_PLAN.md).
This documentation revision does not change application 0.10.0, reset data or run paid tests.
Current startup and baseline evidence follow below.

> **Current release 1.14 / application 0.10.0:** [Workspace specification](prototype/WORKSPACE_SPEC.md) and [Analytics specification](prototype/ANALYTICS_SPEC.md) govern the current UX: feedback inbox, tenant-wide analytics and stakeholder outcomes. Nine independently versioned clinical skills now include 54 proposed development/held-out evaluation cases. [Backlog](prototype/BACKLOG.md) records deferred Test/Production isolation and adjudicated clinical metrics. Earlier release-specific text below is historical where it conflicts. See [Skills Studio specification](prototype/SKILLS_STUDIO_SPEC.md) for the new content review and draft editor.

# Current release: Skills Studio bundle 1.14

Use [LOCAL_TESTING.md](LOCAL_TESTING.md) for startup and upgrading while retaining history.
Read [prototype/ANALYTICS_SPEC.md](prototype/ANALYTICS_SPEC.md) for current Studio UX/API decisions.
The built UI is included. Earlier release notes below are historical where they conflict.

# Vesta Report QA — skill-enabled local prototype

Bundle **v1.14** · implementation **0.10.0** · 16 September 2026.

Paste one report, request structured QA, copy general and critical comments independently, and save feedback. FastAPI + DBOS + OpenAI Agents SDK, React/TypeScript, local SQLite.

QA Studio includes **Skills & knowledge** to inspect installed instructions, edit saved drafts,
compare content, restore earlier revisions and export proposals. Saved drafts do not activate
model changes; the versioned release process remains explicit. It also includes a searchable
feedback inbox and tenant-wide analytics. Record stakeholder
decisions without changing clinical output. Clinical performance rates stay unmeasured until an
independent reference cohort is available; acceptance and thumbs down are not accuracy labels.

Start with [LOCAL_TESTING.md](LOCAL_TESTING.md). The launcher builds a missing UI automatically:

```sh
uv sync --locked
uv run python scripts/run_local.py --model gpt-6-astra
```

The terminal prompts for your key without saving it. Open **http://127.0.0.1:8000**.
Use `--model gpt-5.6-sol` for Sol. The launcher runs real OpenAI only.

## Project map

- `qa-skills/framework/`: independently versioned package contract, private schema and integrity validator.
- `qa-skills/clinical-content/evaluation/suites/`: per-skill diagnostic cases; proposed, not clinically adjudicated.
- `scripts/evaluate_skills.py` and `scripts/score_skill_evaluations.py`: bounded no-call-by-default runner and diagnostic scorer.
- `qa-skills/clinical-content/`: nine clinical SKILL.md modules, references, registry and synthetic evaluation cases.
- `qa-skills/lock.json`: pinned framework/content release. Clinical content is provisional, not an approved manual.
- `backend/skill_runtime.py`: host loader, stage composition, private candidates and grounded public adaptation.
- `backend/`: tenant-aware API, durable workflows, captured configuration, persistence and presentation.
- `frontend/`: familiar Scope–Work–Studio interface, direct comments, three copy actions and feedback.
- `prototype/`: blueprint, adoption specification, API design and verification record.
- `framework/`: broader UX framework for later phases; `design-history/` preserves prior design work.
- `tests/`, `frontend/tests/`: controlled technical tests, distinct from real model evaluation.

Every accepted review captures its report, model settings, policy and exact stage instruction bytes before dispatch.
API idempotency prevents duplicate accepted operations; it does not guarantee exactly-once provider billing.
New API clients pin **QA-Version: 2026-09-15**. Legacy receipts replay unchanged; old clients need the new version to create reviews or read richer section labels.

See [prototype/IMPLEMENTATION_STATUS.md](prototype/IMPLEMENTATION_STATUS.md) for actual results and limits.
This release does not alter the qatr origin repository. No PACS/HL7/chat delivery, image interpretation, clinical approval or automatic learning is included.
