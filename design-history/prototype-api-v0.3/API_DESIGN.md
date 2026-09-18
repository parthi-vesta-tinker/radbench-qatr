# Prototype API contract

Contract v0.3 · Implementation 0.2.0 · Report-only input

FastAPI exposes a small JSON resource API for both browser and agent clients. DBOS handles durable execution behind it. OpenAPI is available at /openapi.json and /docs; a snapshot is included in openapi.json.

| Operation | Endpoint | Behavior |
|---|---|---|
| Create | POST /api/v1/reviews | Required Idempotency-Key; report_text only; 202 and stable review ID/Location after acceptance. |
| Read | GET /api/v1/reviews/{review_id} | Immutable input, provenance, step states and terminal result/error. |
| Feedback | POST /api/v1/reviews/{review_id}/feedback | Save against completed result with independent idempotency key; 201. |
| Read feedback | GET /api/v1/reviews/{review_id}/feedback | Retrieve saved feedback for this result. |
| Configuration | GET /api/v1/config | Mode, readiness, policy version/status and demo-only samples. No API key returned. |
| Health | GET /api/v1/health | Process health and workflow version. |

## Request

```json
{"report_text":"Findings:\nLeft pleural effusion.\n\nImpression:\nRight pleural effusion."}
```

report_text is the only required and accepted field, with a non-whitespace limit of 40,000 characters. The former radiologist_critical_flag field is removed and rejected as an extra field. This is an intentional prototype contract change, not backward compatibility within a production API.

Input_version identifies the snapshot within the review; input_hash is deterministic over the exact report_text request. Source provenance records manual_paste, source_version, unknown authorship/signature, null upstream_qa and workflow/prompt/model/policy versions. Policy text is persisted for recovery but not exposed in configuration/resources.

## States and results

Execution statuses: queued, running, completed, needs_input, failed. Five steps: input_validation, language_review, consistency_review, critical_finding_review, comment_assembly. Step statuses: pending, running, completed, needs_input, failed, skipped. Network disconnection is a client state, not an execution result.

Result is null until completed. Result fields: result_version, outcome (observations/no_observations), critical_finding_detected, critical_flag_status, critical_flag_quote, missed_flag, general_comments, critical_comments and copy_text. Observation fields: observation_id, finding_type, report_section and comment.

critical_flag_status is documented_flagged, documented_not_flagged or unknown. Known states require a non-empty exact quote present in the input. Unknown requires null quote. The model performs the interpretation; source substring validation is not semantic validation. These internal grounding fields do not introduce an evidence viewer.

missed_flag is true only for detected critical comments plus documented_not_flagged; false for no critical comments or documented_flagged; null for critical comments with unknown designation. UI/copy render null as Cannot determine. Never map null to No with a truthiness shortcut. The known flag describes report documentation and does not independently verify PACS state.

Critical comments remain regardless of documented flag. For observations, copy_text follows the complete standard template, with None. for an empty group. For no_observations, copy_text is empty and no flag/template is rendered. Assembly is deterministic; no second model call rewrites the clipboard content.

## Feedback and failures

Feedback payload: result_version, rating (up/down), target (result/observation/missed_flag), optional observation_id, reason, explanation and suggested_comment. Down requires a known reason; other text is optional for every reason. Reject non-existing observations and mismatched result versions. Persist feedback independently without changing results.

| Condition | Behavior |
|---|---|
| Missing/blank/oversized report or extra input field | 422, no accepted workflow. |
| Unidentifiable/empty/ambiguous findings or impression | needs_input resource, downstream steps skipped. |
| Unsupported demo report | Explicit failed review; no fabricated observations or empty success. |
| Same idempotency key with changed report | 409; no cross-input result reuse. |
| Missing OpenAI configuration | 503 MODEL_NOT_CONFIGURED; no demo fallback. |
| Acceptance uncertain | 503; retry same request/key. |
| Malformed model output or unsupported flag quote | failed resource; no copyable result. |
| Unknown review | 404. |

Safe error envelope: code, message, retryable, optional field_errors. No raw provider error/report input is echoed in validation errors.

## Run example

```sh
curl -X POST http://127.0.0.1:8000/api/v1/reviews \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: report-only-example-1' \
  -d '{"report_text":"Findings:\nLeft pleural effusion.\n\nImpression:\nRight pleural effusion."}'
```

Poll the returned review ID. A client retry reuses its key; an intentional new review uses a new key. The UI/API do not promise exactly-once external provider invocation.

## Upgrade boundary

Default storage is .qa-data-v0.3. If QA_DATA_DIR points at records containing the removed operator flag, startup asks for a fresh directory and preserves the old records. No destructive migration or cross-workflow-version recovery is attempted. Workflow names, application version and browser current-review namespace are updated.
