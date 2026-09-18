# Vesta Report QA — runnable prototype

Project bundle **v1.6** · prototype contract **v0.2** · implementation **0.1.0** · 14 September 2026

A local browser workspace for pasting one radiology report, requesting structured QA, copying concise comments and saving feedback. Python/FastAPI, DBOS, OpenAI Agents SDK, React/TypeScript/Vite and two local SQLite databases.

Start with [START_HERE.md](START_HERE.md). Read [prototype/BLUEPRINT.md](prototype/BLUEPRINT.md) for the product contract and [prototype/IMPLEMENTATION_STATUS.md](prototype/IMPLEMENTATION_STATUS.md) for observed test results and limitations. Open [prototype/BLUEPRINT.html](prototype/BLUEPRINT.html) for a standalone reading edition.

## Run

Requirements: Python 3.11+ with `uv`, Node 20.19+ or 22.12+ with npm. Commands run from this directory.

```sh
uv sync --locked
npm --prefix frontend ci
npm --prefix frontend run build
uv run python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**. Default mode is a clearly labeled synthetic demo: choose “Try an example,” explicitly select the radiologist flag, then Review report. Five supplied reports exercise the complete browser/API/DBOS path. Other pasted reports fail explicitly in demo mode.

For real model review, copy `.env.example` to `.env`, set `QA_MODE=openai`, `OPENAI_API_KEY` and `OPENAI_MODEL` to a model available to your account, and restart. Optional `QA_POLICY_PATH` loads a UTF-8 manual/instructions file. The manual and critical vocabulary have not been supplied. Live mode is provisional, and no real model evaluation is claimed in this bundle. There is no silent demo fallback.

Use synthetic/de-identified material in this local prototype. There is no authentication or production data lifecycle. Inputs, outputs, model checkpoints and feedback persist under `.qa-data/`; API keys are read from the environment and are not stored with review resources. Keep the server bound to loopback.

## Verify

```sh
uv run pytest -q
npm --prefix frontend run build
npm --prefix frontend exec playwright install chromium
npm --prefix frontend run test:browser
python verify_bundle.py
```

The browser tests start their own API process and use an isolated synthetic database. Python tests include actual process termination and restart. `verify_bundle.py` verifies delivered files and historical framework fixtures; it is not a substitute for runtime tests.

## Orientation

- `backend/`: small API, contracts, storage, review adapters and durable workflow modules.
- `frontend/`: the running Scope–Work–Studio interface; no hidden production integrations.
- `tests/`: API/SDK and process-recovery checks. `frontend/tests/`: browser interactions.
- `prototype/`: current contract, roadmap, design rules, acceptance criteria, implementation records and screenshots.
- `framework/`: earlier broader UX framework and reference HTML; future design resources.
- `design-history/`: superseded handoffs and visual iterations, retained as history.
- `AGENTS.md` and `CLAUDE.md`: continuation instructions for coding agents.

The user authorized this prototype implementation. Detailed MVP design and broader autonomy/integration work remain subsequent decisions.
