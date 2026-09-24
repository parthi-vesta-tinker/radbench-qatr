# Vesta Report QA

Application **0.15.0** · bundle **1.21** · foundation **F3** · API **2026-09-22** · schema **8**.

Vesta Report QA is a local FastAPI, DBOS, OpenAI Agents SDK, React, and SQLite prototype. A user pastes report text, runs one durable combined review request, reads two copy-ready comment groups, and records feedback or stakeholder outcomes. It also includes tenant-scoped analytics and a Skills Studio draft editor.

Start with [START_HERE.md](START_HERE.md). Use [LOCAL_TESTING.md](LOCAL_TESTING.md) for setup and test commands. Current implementation decisions and evidence live in [prototype/FOUNDATION_CHANGELOG.md](prototype/FOUNDATION_CHANGELOG.md) and [prototype/IMPLEMENTATION_STATUS.md](prototype/IMPLEMENTATION_STATUS.md).

## Run locally

Install Python 3.11+, `uv`, and Node.js 22 LTS, then:

```sh
uv sync --locked
copy .env.example .env
npm run demo
```

`npm run demo` builds the browser app when needed, starts FastAPI and DBOS, and runs controlled local examples without an OpenAI API key. Open the address printed in the terminal, normally `http://127.0.0.1:8000`.

For a real provider review, run:

```sh
npm run live
```

It builds the browser app when needed and uses both `OPENAI_API_KEY` and `TYPESAFE_API_KEY` from `.env` without prompting. This command uses local access for its process. Set the optional `QA_LOCAL_OPERATOR_NAME` in `.env` when you want Review History to show who submitted local reviews. See [the live provider session instructions](LOCAL_TESTING.md#live-provider-session). Controlled tests and demo mode make no paid provider call.

## Current architecture

- `backend/`: tenant-aware API, SQLite resources, DBOS workflows, presentation, analytics, outcomes, and knowledge drafts.
- `frontend/`: React/TypeScript workspace and browser tests.
- `qa-skills/framework/`: active skill schema and validator.
- `qa-skills/clinical-content/`: pinned clinical instructions, qatr references, manifests, and evaluation fixtures.
- `prototype/`: current specifications, generated OpenAPI, implementation evidence, and synthetic examples.
- `tests/`: backend, workflow, recovery, contract, and controlled-provider tests.
- `design-history/`: superseded documents and visual artifacts. Nothing in this directory is implementation authority.

The active runtime uses one tool-free structured provider request per admitted review. Invalid input makes zero calls. An ambiguous claimed provider attempt is never retried automatically. A request that exceeds the context allowance is rejected before dispatch rather than clipped.

## Boundaries

The prototype reviews report text only. It does not interpret images, edit or deliver reports, send external messages, activate Studio drafts, or establish clinical correctness. Installed clinical content remains provisional until independently reviewed and evaluated. API idempotency protects accepted operations but cannot promise exactly-once provider billing after every external failure mode.
