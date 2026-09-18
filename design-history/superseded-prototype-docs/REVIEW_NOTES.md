> Current implementation: application **0.13.0**, bundle **1.17**, foundation **F3**. [Decisions and verification](FOUNDATION_CHANGELOG.md) supersede older baseline statements below. Fresh schema 4 and API 2026-09-18 are implemented. F3 adds one combined request, guarded dispatch, durable response checkpoints and per-session spend admission. F4/F5 remain separate gates.

> Next-build authority (2026-09-17): [clean-start foundation plan](FOUNDATION_PLAN.md). Historical migration and three-stage decisions are superseded for the next cutover; report-only input and no external actions remain.

# Decisions and consistency review

Report-only decisions retained in contract v0.4 · Bundle v1.8

The latest user instruction removes the critical-finding Yes/No selection entirely and derives review information from report text. This overrides all earlier instructions requiring an explicit operator flag. Earlier documents and the radio-based generated concept are retained only under design-history/prototype-contract-v0.2.

| Area | Revision |
|---|---|
| UI | Removed radios, flag hint, validation, state and restore behavior. Compact Review remains beneath input. |
| API | report_text is the only input; removed flag field is rejected. Hash binds report text only. |
| Critical review | Model extracts explicit report designation with a verbatim quote; ambiguous/absent designation is unknown. |
| Copy output | Same heading/group structure. Unknown missed flag renders Cannot determine instead of fabricating Yes/No. |
| Feedback | Existing result/observation/field feedback remains; no new required input. |
| Recovery | Tenant context and v3 workflow identity; completed v0.3 records migrate into Vesta; pending older workflows block upgrade without changing their records. |
| Tests | Replaced old flag truth table with report-only and documented/unknown designation cases. Added controlled SDK grounding failure coverage. |
| Evidence | Exact flag quote is internal validation data only; evidence UI remains deferred. |
| Clinical quality | Fixture assertions and controlled SDK output are explicitly separated from real provider/domain evaluation. |

Known designation still describes what the report says, not independently verified PACS activity. Report missing a flag statement does not prove a radiologist failed to flag a finding. Critical observations remain prominent in all designation states. The UI explanation is excluded from the clipboard template.

The current brief lives in the center as radiologist-facing comments. Studio provides operational status and next steps. It does not duplicate comments or become an evidence pane. Existing broader framework concepts remain future resources rather than current scope.

API_REVIEW.md records the subsequent tenant-aware API review. Stable POST receipts, scoped authorization, versioned presentation, consistent errors and pagination were added without introducing a tenant/flag selector in the browser.
