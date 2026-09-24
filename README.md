# Vesta Report QA

Application **0.15.0** · bundle **1.21** · foundation **F3** · API **2026-09-22** · schema **8**.

Vesta Report QA is a local FastAPI, DBOS, OpenAI Agents SDK, React, and SQLite prototype. A user pastes report text, runs one durable combined review request, reads two copy-ready comment groups, and records feedback. It also includes tenant-scoped analytics and a Skills Studio draft editor.

Start with [START_HERE.md](START_HERE.md). Use [LOCAL_TESTING.md](LOCAL_TESTING.md) for setup and test commands. Current implementation decisions and evidence live in [prototype/FOUNDATION_CHANGELOG.md](prototype/FOUNDATION_CHANGELOG.md) and [prototype/IMPLEMENTATION_STATUS.md](prototype/IMPLEMENTATION_STATUS.md).

## Starter guide

Install Python 3.11+, `uv`, and Node.js 22 LTS. From the repository root, install the locked Python dependencies:

```sh
uv sync --locked
```

If `.env` does not exist, create it from the example (`cp .env.example .env` on Linux/macOS or `Copy-Item .env.example .env` in PowerShell). Keep any existing `.env`; it is ignored by Git. Choose a run mode:

| Mode | Command | Provider use |
| --- | --- | --- |
| Demo | `npm run demo` | Controlled local examples; no OpenAI request. Leave `QA_JEV_ENABLED=false` for provider-free demo use. |
| Live | `npm run live` | Real OpenAI report review. JEV classifies a finding only after the review produces a critical comment. |

For **live mode**, put both keys in the repository-root `.env` file. OpenAI reviews the
report; TypeSafe JEV classifies critical findings from the completed review.

```dotenv
OPENAI_API_KEY=your_openai_key
TYPESAFE_API_KEY=your_typesafe_key
```

`npm run live` reads these values without prompting and exits with a named missing-key message if either is absent. It uses local access for that process, even if `.env` specifies another access mode. Existing shell environment variables take precedence over `.env`. The launcher checks that keys are present; provider acceptance is checked when a real review or classification runs. Never commit `.env`.

Both commands build the browser app when needed and print its address, normally `http://127.0.0.1:8000`. If that port is occupied, use `npm run live -- --port 8900` (or `npm run demo -- --port 8900`); npm passes the argument after the first `--` to the launcher. Stop with Ctrl+C. You can set `QA_LOCAL_OPERATOR_NAME` in `.env` to show a local submitter in Review History. See [local testing and storage upgrade instructions](LOCAL_TESTING.md) for more detail.

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
