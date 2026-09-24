# Local setup and verification

These instructions apply to application **0.15.0**, foundation **F3**, API **2026-09-22**, and schema **8**.

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

Create local configuration once:

```sh
copy .env.example .env
```

Run canned demo behavior without a provider call:

```sh
npm run demo
```

The launcher builds the frontend when it is missing or stale, starts the combined local app, and uses `RUN_MODE=demo`. It does not prompt for or call OpenAI. `.env.example` uses a fresh `.qa-data-local` folder so it does not reuse an older database. Set optional `QA_LOCAL_OPERATOR_NAME` there to display a local submitter in Review History.

Use schema-8 storage. To isolate a run, point `QA_DATA_DIR` at a new empty directory; the application and DBOS database inside it must move together. Older or mismatched stores fail closed and are never automatically migrated or deleted.

## Live provider session

```sh
npm run live
```

`npm run live` selects Live core review and requires `OPENAI_API_KEY` in the ignored
`.env` or process environment. It does not prompt. JEV is optional and requires
`TYPESAFE_API_KEY` when enabled. Access defaults to local; `ACCESS_MODE` controls it.
Shell environment variables take precedence over `.env`.

Top-right Settings controls run mode, core model and optional features. `RUN_MODE=demo|live`,
`OPENAI_MODEL` and `QA_JEV_ENABLED` supply initial defaults. Saved per-tenant settings in
`QA_DATA_DIR/settings/` take precedence. Explicit `--run-mode`, `--model` and `--jev`
launcher flags update saved choices at startup; subsequent UI changes apply to new runs
without restarting. `CORE_REVIEW_MODELS` controls the model allowlist. Access mode is
server-only, independent of run mode, and requires a restart to change.

For optional JEV classification of completed reviews with critical comments in demo mode,
run `uv run python scripts/run_local.py --run-mode demo --jev`. JEV uses the draft research rubric,
keeps suggestions separate from report QA, and never calls the provider for a review
without critical comments. See `evals/classification/README.md` for the local evaluation
workflow. A key shared in chat should be rotated after testing.

`frontend/dist` is generated and never committed, so a pull that changes the UI leaves the previous
bundle on disk. The launcher compares the build against the frontend sources and rebuilds when they
are newer, so a pull is enough; it never serves a stale UI. Starting uvicorn directly skips that
check — run `npm --prefix frontend run build` yourself in that case. The static mount is resolved
once at import, so a rebuilt UI needs the server restarted, and the browser may need a hard reload.

There is no spend ledger, session authorization or cost ceiling; they were removed on 2026-09-18 by explicit user decision. Provider cost is managed in the OpenAI account. Live reviews incur ordinary provider charges.

A review is admitted on configuration readiness and context size alone. A request whose composed instructions, report and bounded output exceed the context allowance is rejected before dispatch with `REVIEW_CONTEXT_TOO_LARGE`; instructions and report text are never clipped to make one fit.

A valid live review makes one provider call. Invalid input makes zero. There is no automatic repair request. After a claimed request with no durable response, the review fails as `MODEL_OUTCOME_UNKNOWN` and is never retried automatically. Submitting a new review is a new explicit operation.

## Public sharing through Tailscale Funnel

For an intentionally public, unauthenticated shared workspace, stop the backend with Ctrl+C
and restart it from the project root:

```sh
ACCESS_MODE=public uv run python scripts/run_local.py
```

The launcher honours the existing model configuration and builds stale frontend assets.
Keep Funnel forwarding to the same local port as before (8000 for the combined app, or
the Vite port when using the separate dev server). `frontend/vite.config.ts` also permits
`homarchy.velociraptor-pauling.ts.net` for Vite development access.

Public mode permits remote and proxy-forwarded clients without credentials. Every visitor
shares the Vesta tenant, including its saved reports, feedback, analytics, Studio drafts,
and review/playground actions. Live model calls use the server's configured provider account.
Tenant selection remains server controlled; request tenant overrides are rejected.

`ACCESS_MODE` defaults to `local`, which accepts loopback clients only. `api_key` retains
its existing credential and scope checks. To return to local-only access, stop the backend
and restart with `ACCESS_MODE=local`. This changes access only; it does not reset storage.
Do not disable forwarded-header handling to make remote clients appear local.

## Playground

QA Studio's **Playground** runs the real review against curated synthetic samples, in isolation.
Its output never becomes a review: no history, feedback, analytics, outcome or copy action.

Two of the six samples are served by the canned demo path, so the playground is usable with no
provider key at all:

| Category | Sample | Needs a provider? |
|---|---|---|
| Critical findings | Critical · documented flag | No — runs in demo |
| Critical findings | Flagged critical comments remain visible | Yes |
| Critical findings | Rich report with uncertain critical concern | Yes |
| Findings and impression inconsistency | Laterality discrepancy | No — runs in demo |
| Findings and impression inconsistency | Recommendation contradiction in rich report | Yes |
| Findings and impression inconsistency | Rich report technique conflict | Yes |

In demo mode the remaining samples are disabled and say why. Pasting your own report also needs a
configured provider, because the demo path only recognises its own fixed reports.

The playground model list is server controlled and currently offers `gpt-6-astra` only. It is
independent of the live review model: when the two differ, the screen says so, because a
playground result then does not predict live output. A model your OpenAI account cannot serve
fails at dispatch like any other provider error, and is never retried automatically.

Playground runs use a separate DBOS queue, so they cannot consume live review concurrency. Set
`QA_PLAYGROUND_CONCURRENCY` to change it; the default is 2.

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
- Review history, feedback, analytics, classification, and Skills Studio remain tenant scoped.
- The health panel performs a provider metadata check only when explicitly requested; startup does not make an inference call.

Current executed evidence and limitations are recorded in [prototype/IMPLEMENTATION_STATUS.md](prototype/IMPLEMENTATION_STATUS.md).

## Upgrade existing schema-6 storage

Stop the application and finish pending live/playground work with the previous build.
Then run (substitute the actual QA_DATA_DIR):

```sh
.venv/bin/python scripts/upgrade_review_storage.py --data-dir .qa-data-foundation-v5
.venv/bin/python scripts/upgrade_classification_storage.py --data-dir .qa-data-foundation-v5
npm --prefix frontend run build
```

Each upgrade writes a timestamped SQLite backup, preserves existing review rows and feedback,
and checks foreign keys before committing schema 7 then 8. Both refuse pending work and other
schema versions. For a schema-7 store, run only `upgrade_classification_storage.py`.
Restart the application normally and refresh the browser. Existing separate reviews
are not guessed or merged. Future Review again submissions replace the selected review.
API clients must use QA-Version 2026-09-22 and the generated replacement/feedback contracts.

### Recover history from another schema-7 folder

If a changed `QA_DATA_DIR` makes older reviews disappear, first locate the previous
folder. Do not replace the current folder with the old one: that would hide newer work.
For an explicit import of finished reviews, stop all applications using either folder,
ensure neither store has queued/running reviews or Playground runs, then run:

```sh
.venv/bin/python scripts/restore_review_history.py --source .qa-data-foundation-v5 --destination .qa-data-local --applications-stopped
```

The command backs up each folder's application and DBOS SQLite databases into a dated
`history-backup-*` subfolder. It imports terminal reviews, their captured configurations,
results, observations, feedback, dormant outcomes, provider checkpoints and review-related
idempotency receipts in one transaction. Identical records are skipped; conflicts abort
and roll back. Destination tenant bindings remain unchanged; unknown tenants are refused.
Column order differences from an explicit schema-7 upgrade are supported.

DBOS workflows, Studio drafts and Playground records are not imported. The source folder
remains intact. Keep the backups and the original folder. Restart using the same destination
`QA_DATA_DIR`; if the API key was entered interactively, enter it again at the launcher’s
hidden prompt. Verify Review history, Load more reviews, and reopening an older review.
