> Current implementation: application **0.12.0**, bundle **1.16**, foundation **F2**. [Decisions and verification](prototype/FOUNDATION_CHANGELOG.md) supersede older baseline statements below. Fresh schema 3 and API 2026-09-17 are implemented; F2 imports the pinned qatr references and tenant-bound snapshots; single-call execution and session-spend enforcement remain F3 work. Use the new default `.qa-data-foundation-v2`, or explicitly select an empty `QA_DATA_DIR`; application and DBOS files must start fresh together. No old data is migrated or deleted.

## F2 tenant content configuration

The default local Vesta binding is `vesta-qatr-0.3.0` for prototype evaluation.
Other tenants default to `generic-0.3.0` with no Vesta catalog or manual inheritance.
Set `QA_TENANTS_FILE` to a backend-owned JSON file to choose explicitly:

```json
{"vesta":{"skill_release":"vesta-qatr-0.3.0"},"example":{"skill_release":"generic-0.3.0"}}
```

These are immutable release profiles over content package 0.3.0. Unknown releases fail closed.
Restart after changing server configuration. New reviews capture the configured release;
accepted reviews retain their exact snapshot. Browser drafts are never activated by saving.
Use an empty `QA_DATA_DIR` for both application and DBOS files at this version cutover.
The default is `.qa-data-foundation-v2`; existing folders are not deleted.
No paid tests were authorized for this phase. Runtime still uses three calls until F3;
the planned durable $1 session ledger is not implemented in F2.


# Next-build testing boundary — 2026-09-17

[FOUNDATION_PLAN.md](prototype/FOUNDATION_PLAN.md) sections 6–9 govern the replacement.
Commands below run current 0.10.0, not the future single-call path. Old test counts do not prove
new behavior. Implementation will select fresh app/DBOS stores together, preferably a new directory.
Preserve secrets and the independent spend ledger; a reset tool requires exact-path preview,
worker checks and confirmation. No new reset command is claimed to exist.

Test one-call crash boundaries, unknown provider outcomes, fresh-data feature parity, tenant
isolation, concurrency budgets and generated schema drift with controlled outputs first.
Live reports, diagnostics and evaluations need explicit permission and share the $1 session cap.
Historical $2 allowances below are not new authority.

# Skills Studio update 1.14

Open **QA Studio → Skills & knowledge**. Inspect a skill, shared reference, or configured local
manual. Its purpose, version and actual model usage are shown. Compare with installed opens
read-only source beside the editor. Enter a change summary, Save draft, and Export saved draft.
Saved revisions persist in the same QA_DATA_DIR. Use revision restores earlier text as a new proposal.
Switching Studio tools preserves unsaved edits; changing documents or reloading source warns first.

Saving does not activate the change. It remains a tenant-specific editorial proposal for the
existing evaluated skill-package release process. See prototype/SKILLS_STUDIO_SPEC.md.
No OpenAI key is needed to inspect/edit the catalog; no provider call is made by this tool.

Local mode permits editing. API-key deployments must explicitly grant skills:read and skills:write;
existing review/feedback keys do not gain access. Host validation and framework contracts remain
code-managed. Finish pending work and stop the old app before upgrading; reuse the same absolute
QA_DATA_DIR to retain saved reports, outcomes and draft revisions. Do not copy open databases.

Verification: 73 Python tests and 19 DOM interaction tests passed. Browser navigation was blocked
by ERR_BLOCKED_BY_CLIENT, so please review desktop/narrow layouts and keyboard behavior locally.
No skill contents or runtime prompt versions were changed by this feature release.

# Studio analytics update 1.13

This bundle includes the built light-default UI, a dedicated Feedbacks inbox, database-wide
Analytics and a collapsed Stakeholder outcomes log on completed reviews. Startup commands below
are unchanged. No environment switch or canned-example selector has been added.

To retain completed history, stop the previous app and use the same absolute QA_DATA_DIR after
extracting the new bundle into a separate folder. The new outcomes table is created additively;
existing reports and feedback are not rewritten. Do not copy live/open databases. Clinical skill
content and DBOS workflow identities are unchanged from 1.12; package version is now 0.9.0.

Local acceptance checklist (use only authorized/de-identified report data):

1. Reopen a completed live-AI review; verify the two comment groups and all copy actions are unchanged.
2. Save feedback. Open QA Studio → Feedbacks; search the note, change rating/reason filters,
   and reopen the original report. Unsaved report drafts should remain intact.
3. On the completed report, expand Stakeholder outcomes. Record a QA decision about the report
   with a source/reason note. Separately record a decision about QA comments if appropriate.
4. Open Analytics and select a period containing that report's submission date. Its latest
   recorded decision should appear for the relevant perspective and subject. Unrecorded stakeholder
   responses remain separate. Change period/source and refresh; counts must not depend on history pages.
5. Record a revised decision and then Unknown to withdraw it. History retains every entry, while
   Analytics counts only the latest decision for each perspective/subject/result.
6. Confirm critical recall/precision/FPR/false-alert share display Not measured, not 0%.
   No independently adjudicated reference cohort is connected yet.
7. Check desktop/narrow layouts, light/dark contrast and keyboard operation locally. Browser-rendered
   verification was blocked here; the supplied DOM tests do not establish visual correctness.

Source filters are provenance, not Test/Production separation. Older technical fixtures are
excluded by default. The new pages make no OpenAI call. Outcome notes are operator-recorded claims,
not verified stakeholder signatures. Keep notes concise and avoid unnecessary patient identifiers.
Ambiguous outcome retries retain the exact operation only while the view remains mounted; after
navigation/reload, inspect outcome history before recording the same decision again.

See [Analytics specification](prototype/ANALYTICS_SPEC.md) and
[implementation evidence](prototype/IMPLEMENTATION_STATUS.md). Earlier release notes follow.

# Skill evaluation update 1.12

The application UI is unchanged from workspace release 1.11. The default data directory is now
`.qa-data-v0.6`; finish pending work using its original release before changing code versions.

Inspect a no-call evaluation plan and run technical checks:

```sh
uv run python scripts/evaluate_skills.py --skill qa-critical-match --partition development
uv run pytest -q tests/test_skill_evaluation.py
python qa-skills/framework/tools/validate.py
```

The first command makes no provider calls unless `--execute` is added. See
`qa-skills/clinical-content/evaluation/METHOD.md` before any live or clinical evaluation.

# Workspace update 1.11

Read [prototype/WORKSPACE_SPEC.md](prototype/WORKSPACE_SPEC.md) and the
[backlog](prototype/BACKLOG.md). Test/Prod separation is deferred; this release has no environment toggle.

Start the real OpenAI application with the existing launcher below. No canned-example picker is shown.
Set `QA_REVIEW_CONCURRENCY=2` (or another integer 1–32) before startup to bound DBOS parent reviews.
The change requires a restart. Drafts remain in memory in the tab; submitted reports persist.
Finish pending reviews with the old release before upgrading. Use a new extracted folder and retain
an explicit absolute QA_DATA_DIR to preserve completed history. Neither Test nor Prod data migration
is performed by this release.

The header contains Health and a light/dark appearance button. Health is a timestamped snapshot;
click Refresh status to recheck. OpenAI connection checking is explicit and metadata-only.

Developer checks: `npm --prefix frontend run test:dom`, `npm --prefix frontend run build`,
`uv run pytest -q`. See the implementation status for browser validation limitations.

---

# Run Vesta Report QA locally

This release integrates the separate clinical skill package into the browser application.
Release archives may include the built frontend. Git source downloads exclude generated files;
the launcher builds a missing UI automatically. Install Node.js 22 LTS and reopen PowerShell so
`node` and `npm` are on PATH.

## Upgrade to workspace bundle 1.11

Your successful local Windows test of 1.9.1 is recorded as user-reported acceptance of that
release. This refinement is a new build and needs your local acceptance.

Finish running reviews in the previous release, stop the old server, then extract this
bundle into a new folder. To retain history, set QA_DATA_DIR to the **absolute path** of
your existing data directory before starting. Keep both reviews.sqlite and dbos.sqlite;
do not move/copy open databases. The current default is .qa-data-v0.6 under the project folder.
A different empty data folder starts with no history; no records are deleted by upgrading.
Do not copy old code, skills or virtual environments over this release.

```powershell
$env:QA_DATA_DIR = "C:\path\to\previous-project\.qa-data-v0.5"
uv sync --locked
uv run python scripts/run_local.py --model gpt-6-astra
```

Use Review history in QA Studio to search report text/ID and filter by status,
result or feedback. Open a row to restore the original report and review. New report preserves other drafts and opens or reuses an empty draft. Accepted input is read-only. Feedback is
visible under Saved feedback below QA comments, including after reload or reopening history.

Inline labels such as `CT chest. Findings: ... Impression: ...` and uppercase labels
without colons are accepted. Unlabeled prose still needs identifiable sections.

## Windows startup and diagnostics

Extract this release into a **new folder**, open PowerShell in `vesta-qa-ux-project`,
and use the startup commands below. Do not open `frontend/dist/index.html` directly.
Keep the terminal running; it prints startup, API error and workflow failure diagnostics.
Do not copy an old virtual environment or old skill package over this release.

The prior bundle had a Windows skill-inventory separator bug and locale-dependent text
reads. Both are fixed. Configuration errors now retain their error code, HTTP status
and request ID instead of being described as a network outage.

Expand **Health** in the top-right header to inspect the API, application database,
DBOS checkpoint store, QA skill integrity and OpenAI configuration. **Refresh status**
rechecks them and retries configuration. These are on-demand snapshots, not monitoring.
**Check OpenAI connection** verifies authentication and model metadata access. It sends
no report and runs no inference; a successful check does not guarantee a review will succeed.
The button is disabled in demo mode or when configuration is incomplete.

- `GET /api/v1/health`: process liveness only; HTTP 200 is not review readiness.
- `GET /api/v1/status`: component results; inspect `status` (`ready` / `not_ready`).
  HTTP 200 means the diagnostic request succeeded, even when a component failed.
- `POST /api/v1/diagnostics/openai`: explicit metadata-only provider check.
  Both diagnostic endpoints require the existing `reviews:read` access in token mode.

If even `/api/v1/health` will not open, inspect the startup terminal: the server may have
failed to start or another process may own port 8000. Try `--port 8001`, then open the
printed URL. An `INVALID_API_RESPONSE` indicates a non-JSON response (often a wrong
server/proxy or an older backend). A skill error requires restoring the complete package,
not editing the checksums. Configuration changes require restarting the backend.

Windows troubleshooting commands (while the backend runs in another terminal):

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/status | ConvertTo-Json -Depth 8
```

Local-mode examples above use the loopback-only launcher. In token mode provide the
configured bearer token (tenant is derived from the credential). Backend diagnostic errors include exception
type and stack locations but omit exception payloads, report text and credentials.
To save logs locally in PowerShell, append `2>&1 | Tee-Object -FilePath qa-local.log`
to the launcher command. Never publish keys or patient reports with support logs.

## Start with real AI

Extract the bundle, open PowerShell in `vesta-qa-ux-project`, then run:

```sh
uv sync --locked
uv run python scripts/run_local.py --model gpt-6-astra
```

Enter your OpenAI API key at the hidden terminal prompt. The launcher does not save it.
On the first source-checkout run, it automatically executes the equivalent of
`npm --prefix frontend ci` followed by `npm --prefix frontend run build`. Do not run the build
step alone before dependencies are installed.
Open **http://127.0.0.1:8000**. Stop the server with **Ctrl+C**.
For GPT-5.6 Sol use `--model gpt-5.6-sol`. Model access depends on your account.
The app never substitutes a demo response after a model failure.

Automated developer fixtures remain separate from live AI verification; the launcher runs real OpenAI only.

## What to try

1. Paste one current report containing Findings and Impression (or Conclusion).
2. Click **Review report**. Studio shows the five actual execution steps.
3. Read the comments directly below the report. Use **Copy general**, **Copy critical**, or **Copy all comments**.
4. Use thumbs down, select a reason, and save feedback. Additional text is optional.
5. Select **New report** even while another review runs. Use the left report list to return to a draft or review. Use the trash icon to delete a draft and Undo to restore it.

A clean result displays **No actionable observations** with feedback but no copy buttons.
The missed-flag section is hidden and omitted from current UI clipboard exports. Critical comments remain available.
History, indication, technique, comparison and addenda can be included in the same field.
No extra form is needed. Missing required sections or unresolved multiple-report ambiguity requests clearer input.

## Configuration

The launcher uses live AI and defaults to GPT-6 Astra.
Alternatively copy `.env.example` to `.env` and edit it locally. Never commit the key.

| Setting | Default / meaning |
|---|---|
| `QA_DATA_DIR` | `.qa-data-v0.6`; reports, results, feedback and DBOS checkpoints persist here |
| `QA_REASONING_EFFORT` | `medium`; accepts low, medium or high |
| `QA_MAX_OUTPUT_TOKENS` | `6000` per stage, including reasoning; incomplete results fail visibly |
| `QA_POLICY_PATH` | Optional UTF-8 unvalidated guidance; no approved manual/catalog is bundled |
| `QA_AUTH_MODE` | `local`; Vesta only, loopback access |
| `QA_SKILL_PACKAGE_DIR` | Optional development override for the whole pinned `qa-skills` package |

Local interactive reviews incur normal provider charges. The earlier $2 limit applies to the assistant's recorded verification runs, not an account-wide spending cap implemented by this launcher.
Use synthetic or de-identified reports for prototype testing. There is no image interpretation, report editing, external sending, or clinical release decision.

## Troubleshooting

- **`uv` not found:** install uv from [the official uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).
- **Port occupied:** add `--port 8001`, then open the printed address.
- **UI build fails:** verify `node --version` and `npm --version`, then run `npm --prefix frontend ci`
  followed by `npm --prefix frontend run build`. Use Node 22 LTS. Paste the first `npm ERR!` block
  when requesting help; the launcher will retry the build on its next run.
- **Model unavailable/authentication error:** confirm the model and key in your account, stop, and restart. Failed reviews never become empty successful reviews.
- **Skill configuration invalid:** restore the pinned package and lock together. Existing accepted workflows retain captured instructions.
- **Upgrading older data:** use the fresh default directory. If you deliberately reuse older data, finish pending reviews with the previous application first. Completed records remain readable; arbitrary cross-version DBOS replay is not supported.

## Developer verification

```sh
uv run pytest -q
npm --prefix frontend ci
npm --prefix frontend run build
cd frontend
npx playwright install chromium
npm run test:browser
```

Browser tests use isolated demo data. SDK tests use explicitly controlled model payloads.
Real provider results are documented separately in `prototype/IMPLEMENTATION_STATUS.md`.
For API clients, pin `QA-Version: 2026-09-15`; `/docs` exposes the current schema.

## Optional bounded model diagnostics

Use synthetic or de-identified inputs only. Start with development cases, keep the held-out
partition untouched until the skill change is frozen, and have a qualified reviewer adjudicate
results. The runner uses the same stage instructions and structured model output as the app:

```sh
uv run python scripts/evaluate_skills.py --skill qa-critical-match --partition development --max-cases 3 --max-total-tokens 20000 --execute --output .qa-data/evaluation/critical.json
uv run python scripts/score_skill_evaluations.py .qa-data/evaluation/critical.json --output .qa-data/evaluation/critical-scored.json
```

Automatic scores cover contract and narrow hygiene checks only. They do not establish clinical
accuracy, a release decision, policy compliance or a model spending cap.
