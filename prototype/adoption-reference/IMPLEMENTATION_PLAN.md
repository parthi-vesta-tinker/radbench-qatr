> Next-build authority (2026-09-17): [clean-start foundation plan](../FOUNDATION_PLAN.md). Historical adoption handoff only: do not implement its three-call or legacy-migration instructions; follow F1–F5.

> Original adoption proposal retained as a reference. For implemented behavior and verification, see ../IMPLEMENTATION_STATUS.md.

# Web-app implementation handoff

This is a planned change map, not implemented application code. Do not modify qatr origin.
Start with WEB_APP_SKILL_ADOPTION.md and the content package's SOURCE.md. The app's existing
AGENTS.md, BLUEPRINT.md and API/DBOS documents remain baseline records; update them explicitly
when implementing this adoption rather than claiming the draft is already live.

## B. Load skills and understand rich input

1. Add a small backend/skill_runtime/ loader/composer. Vendor the independently versioned
   clinical-content release under qa-skills/ (or use an explicit local development path).
   Validate inventory, registry, manifests, ownership, schemas and reference hashes before
   admitting reviews. Do not install the package as a coding-agent skill.
2. Replace BASE/TASKS construction in reviewer.py with stage-specific composition. Keep the
   three stage invocations and existing Agents SDK/DBOSRunner boundary. Include drafting and
   final verification in each stage, not extra agent calls.
3. Extend parse_sections in contracts.py to produce an exact-offset section index alongside
   the complete raw report. Recognize optional sections and common heading forms; retain
   minimum Findings + Impression. Supply section IDs to the model. Detect repeated top-level
   report blocks rather than silently treating them as one study. Request clarification when
   identity or section interpretation is ambiguous; no model-based parser call in this phase.
4. Update settings.py and store.reserve to capture the verified composition snapshot before
   acceptance, with tenant policy/model bindings and digests. Do not expose policy paths/text
   or the new private snapshot via provenance's public allowlist.
5. Deliberately version workflow names/application code and drain or reject incompatible
   pending work. Keep old completed resources intact. Verify recovery of the exact accepted
   snapshot after content files change; this is distinct from arbitrary code-version recovery.

## C. Ground results and provide two copy actions

1. Introduce private stage-candidate schemas and validation. Derive source offsets from exact
   quotes and section IDs. Reject ungrounded or wrong-owner candidates before final assembly.
   Keep model interpretation failures distinct from malformed JSON and missing input.
2. Adapt candidates into existing public observations with app-owned IDs; preserve separate
   general/critical arrays. Record the private candidate-to-result mapping for feedback.
3. Add the new QA-Version projection for richer section labels and group-copy fields. Preserve
   legacy GET rendering/receipts. At adoption cutover, require the new version for new skill
   executions; old-version create requests return a documented upgrade-required error before
   acceptance, except valid existing idempotency receipts still replay their original response.
   Reading new rich results also requires a projection that can represent their section labels;
   return an explicit upgrade-required error for incompatible older projections. Do not implement
   two concurrent clinical engines merely for this prototype.
4. Have the bundled browser explicitly request that new version. Update frontend types, then
   add group-copy buttons to ReviewOutput.tsx. Reuse current clipboard feedback and stale-state
   rules. Keep the full-copy button, center-panel placement, two sections and Studio layout.
5. Derive Studio guidance from the final accepted critical array and applicable policy context.
   A generic clinical concern should not be presented as a proven catalog violation or missed
   call. Do not claim deterministic validation can establish clinical criticality.

## Focused offline verification

| Risk | Verification |
|---|---|
| Silent missing/drifted skill or policy | Loader failure before acceptance; no success fallback |
| Accidental inclusion of every reference | Inspect composition for each stage against registry; eval files absent |
| Optional rich sections ignored/mislabelled | Same raw input retained; section IDs/offsets and public labels correct |
| Repeated/ambiguous section headings | Safe needs_input response, not merged studies |
| Meaning lost in duplicate detection | Preserve distinct actions sharing a sentence; reject wrong ownership mechanically |
| Unsupported critical routing | Direct validator checks ownership/basis shape; live eval tests clinical route correctness |
| New sections leak into old API contract | Old create rejected before acceptance after cutover; historical GET and receipts unchanged |
| Copy diverges from visible result | Browser tests compare each clipboard field with displayed group; no metadata leakage |
| Long report/response truncation | Boundary inputs, budget admission and explicit failure; no silently capped candidates |
| Retry/recovery changes clinical context | Accepted skill/policy bytes survive restart; idempotent POST returns original receipt |
| Feedback becomes a new instruction | Persist against result only; do not feed it into the next patient review |

Synthetic candidate objects can exercise local validators/formatters. Label them as local test
inputs. They are not AI outcomes. Existing controlled SDK tests establish only the boundaries
they actually exercise; never present them as real Astra clinical evaluation.

## D. Evaluate actual clinical outputs

Use clinical-content/evaluation/cases.json plus independently selected hold-out cases. Every
case is a synthetic report with proposed expectations; domain review is still required.
First compare existing BASE/TASKS with the new content under the same Astra model/settings,
input, policy mode and output budget. Evaluate reasoning settings separately afterward.

Measure issue-level precision/recall, missed critical candidates, general-to-critical route
errors, certainty inflation, unsupported patient/policy assertions, source fidelity, duplicate
burden and radiologist edits/time needed before copying. Count failed, truncated and unreviewed
cases explicitly. Include no-action cases and rich reports whose critical assertion is early,
middle or late. No invented numerical clinical acceptance threshold is supplied here.

Use genuine authorized API requests, preserve available usage on all attempts, and check the
existing spending ledger before starting. Do not reuse qatr's unrelated budget allowance or
reset a ledger. The previous web-app $2 ceiling is not a new $2 allowance. No paid calls are
part of authoring this deliverable. Record and resolve observed failures before adoption.

## E. Adopt and maintain

Pin the reviewed content release and framework compatibility in the app; publish a changelog
and actual validation record. Keep policy approval separate from instruction/package review.
Update the app's blueprint, API schema, screenshots, AGENTS.md and bundle manifest together.
Promote feedback-derived changes through content review and evals, not automatic learning.
Clinical performance, human UX acceptance and production readiness remain separate judgments.
