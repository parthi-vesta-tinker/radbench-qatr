# Local setup and verification

These instructions apply to application **0.13.0**, foundation **F3**, API **2026-09-18**, and schema **4**.

## Prerequisites

- Python 3.11 or newer
- `uv`
- Node.js 22 LTS and npm
- local Chromium only when running Playwright

Install locked dependencies and build the frontend:

```sh
uv sync --locked
npm --prefix frontend ci
npm --prefix frontend run build
```

The launcher also builds `frontend/dist` when it is missing.

## Controlled local use

Run canned demo behavior without a provider call:

```sh
QA_MODE=demo uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Use fresh schema-4 storage. The default is `.qa-data-foundation-v3`. To isolate a run, point `QA_DATA_DIR` at a new empty directory; the application and DBOS database inside it must move together. Older or mismatched stores fail closed and are not migrated or deleted.

## Live provider session

```sh
uv run python scripts/run_local.py --model gpt-5.6-sol
```

The launcher prompts for `OPENAI_API_KEY` without storing it. Rotate any key exposed in chat before use.

`frontend/dist` is generated and never committed, so a pull that changes the UI leaves the previous
bundle on disk. The launcher compares the build against the frontend sources and rebuilds when they
are newer, so a pull is enough; it never serves a stale UI. Starting uvicorn directly skips that
check — run `npm --prefix frontend run build` yourself in that case. The static mount is resolved
once at import, so a rebuilt UI needs the server restarted, and the browser may need a hard reload.

There is no spend ledger, session authorization or cost ceiling; they were removed on 2026-09-18 by explicit user decision. Provider cost is managed in the OpenAI account. Live reviews incur ordinary provider charges.

A review is admitted on configuration readiness and context size alone. A request whose composed instructions, report and bounded output exceed the context allowance is rejected before dispatch with `REVIEW_CONTEXT_TOO_LARGE`; instructions and report text are never clipped to make one fit.

A valid live review makes one provider call. Invalid input makes zero. There is no automatic repair request. After a claimed request with no durable response, the review fails as `MODEL_OUTCOME_UNKNOWN` and is never retried automatically. Submitting a new review is a new explicit operation.

## Tenant content

The local Vesta tenant defaults to release `vesta-qatr-0.3.0`. Other tenants default to `generic-0.3.0`. A backend-owned configuration file can bind explicit releases:

```json
{"vesta":{"skill_release":"vesta-qatr-0.3.0"},"example":{"skill_release":"generic-0.3.0"}}
```

Set its path with `QA_TENANTS_FILE` before startup. Studio drafts never activate installed content.

## Verification

Run the checks relevant to a change:

```sh
uv run pytest -q
npm --prefix frontend run test:dom
npm --prefix frontend run build
npm --prefix frontend run test:browser
uv run python qa-skills/framework/tools/validate.py
uv run python scripts/export_openapi.py --check
uv run python scripts/export_contracts.py --check
uv run python scripts/check_docs.py
```

Rebuild the current reading edition and source manifest after documentation or artifact changes:

```sh
uv run python prototype/render_blueprint.py
uv run python scripts/package_project.py --manifest-only
uv run python verify_bundle.py
```

`scripts/evaluate_skills.py` is a no-call plan/fixture tool. Use `scripts/evaluate.py` against an already running API for any live evaluation. Keep provider evaluation results separate from controlled tests and from qualified clinical review.

## Expected local behavior

- Open `http://127.0.0.1:8000`.
- New reports use the four real phases: input validation, combined report review, output validation, and comment assembly.
- Completed output has independent general and critical copy groups plus full-template copy when observations exist.
- Review history, feedback, analytics, stakeholder outcomes, and Skills Studio remain tenant scoped.
- The health panel performs a provider metadata check only when explicitly requested; startup does not make an inference call.

Current executed evidence and limitations are recorded in [prototype/IMPLEMENTATION_STATUS.md](prototype/IMPLEMENTATION_STATUS.md).
