# Prototype API design brief

Version 0.2 · Input/output semantics reflect confirmed decisions; API mechanics implemented and tested locally; product/API review remains available

## 1. Aim and resources

The browser and another agent use the same small API. FastAPI owns the public resource contract; DBOS owns durable execution behind that boundary. Do not expose SDK objects or DBOS internal statuses as the public schema. Implemented transport: JSON over HTTP and short polling.

| Operation | Endpoint | Behavior |
|---|---|---|
| Create review | POST /api/v1/reviews | Accept report_text and an explicit boolean radiologist_critical_flag; return 202 with stable review ID and Location after durable acceptance. |
| Read review | GET /api/v1/reviews/{review_id} | Return submitted input identity, execution/step states, terminal result or actionable error/needs-input details. |
| Submit feedback | POST /api/v1/reviews/{review_id}/feedback | Validate result/target binding; return 201 after saving. |
| Read feedback | GET /api/v1/reviews/{review_id}/feedback | Inspect saved feedback; no review-history UI or dashboard required. |

No review-list/fleet endpoint in this prototype. The active review ID supports reconnect only. Initial service is local; shared/live deployment and access/retention policies require later design.

## 2. Input and provenance

```json
{
  "report_text": "Findings:\nLeft pleural effusion.\n\nImpression:\nRight pleural effusion.",
  "radiologist_critical_flag": false
}
```

Both fields required. The flag must be a strict boolean; missing, null, empty string and implicit defaults are invalid. False is a valid deliberate answer, not missing input. Implemented report limit: 40,000 characters total, non-whitespace. Do not silently truncate or rewrite text. No modality restriction or patient identity is required.

The client does not submit separate findings/impression fields. Input validation identifies these sections from the report and asks for replacement/clarification if either is missing, empty or ambiguous. Internal parsing preserves its association with the exact raw input; evidence UI remains deferred.

Store input_version and input_hash over the exact report_text plus explicit flag using deterministic serialization. A flag-only change is a new input. Preserve field names and boolean types in the hash representation. Author/signature remain unknown; the flag is operator-supplied, not verified PACS provenance.

Record workflow/prompt/model/policy versions with the review. Source provenance also records manual_paste, source_version, unknown authorship/signature and null upstream_qa. A missing Vesta manual is explicit; no run can claim policy-backed review without the corresponding material/version. UX fixtures are labeled synthetic.

## 3. State and result contract

Execution: queued, running, completed, needs_input, failed. Steps: input_validation, language_review, consistency_review, critical_finding_review, comment_assembly. Step states: pending, running, completed, needs_input, failed, skipped. Client disconnection is independent of execution state.

Result is null outside completed. A completed result includes result_version, outcome, critical_finding_detected, missed_flag, general_comments, critical_comments and copy_text. Observation records include application-assigned observation_id, finding_type, report_section and concise comment. critical_finding_detected must equal whether critical_comments contains at least one observation. Do not allow an identified critical finding to lose its comment during assembly.

Derive missed_flag = critical_finding_detected AND NOT input.radiologist_critical_flag. It is a result field, not an additional clinical observation. General and critical comments remain present regardless of the flag when there is an observation to communicate.

For completed reviews, outcome is observations if either group has content, otherwise no_observations. For no_observations, copy_text is empty and no user-facing missed-flag/template is rendered. Never use an empty result for a failed/partial review.

Illustrative completed non-critical result fragment:

```json
{
  "result_version": 1,
  "outcome": "observations",
  "critical_finding_detected": false,
  "missed_flag": false,
  "general_comments": [
    {
      "observation_id": "obs-1",
      "finding_type": "discrepancy",
      "report_section": "both",
      "comment": "Findings state left pleural effusion; impression states right. Please reconcile laterality."
    }
  ],
  "critical_comments": [],
  "copy_text": "QA review:\n\nGeneral Comments:\n1. Findings state left pleural effusion; impression states right. Please reconcile laterality.\n\nCritical Findings missed flag: No\n\nCritical Findings comments:\nNone."
}
```

The application derives copy_text from the validated structured result using the user's exact heading order. No second model call rewrites the clipboard payload. UI formatting can add visual hierarchy but copy must retain exact words/order. The proposed empty-group marker is “None.” only when another group contains observations.

## 4. Feedback contract

A completed result is eligible for feedback, including no_observations. Proposed payload: result_version, rating (up/down), target (result, observation, missed_flag), optional observation_id, reason, optional explanation and suggested_comment. Default target is result. An observation target requires an existing observation ID. The missed_flag target refers to the calculated field, not an invented observation.

For down, require one known reason. Explanation and suggested_comment are optional for every reason. For up, no reason/explanation is required. Bind input/model/policy provenance on the server via the referenced result. Reject mismatched result versions/observation IDs. Feedback never overwrites copy_text. Preserve the same result when reopening/cancelling the form.

## 5. Validation and errors

| Condition | Proposed response |
|---|---|
| Empty report, missing flag, non-boolean flag or oversized text | 422 with field-specific errors; no workflow accepted. |
| Accepted report lacks identifiable findings/impression | GET returns resource with needs_input and an error code/message; downstream steps skipped. |
| Arbitrary embedded flag metadata | Not parsed in this prototype; the separate explicit operator flag is used. |
| Unknown review | 404 with stable error code. |
| Same idempotency key with changed text or flag | 409; never return a different input's result. |
| Invalid feedback target/version or missing down reason | 422; no feedback saved. |
| Workflow not durably accepted | 503; retry with the same key. |
| Accepted execution later fails | GET returns 200 for the resource with execution_status failed and a safe error. |

Error envelope: code, message, retryable and optional field_errors. No raw provider errors, stack traces or full reports in error messages. A needs_input outcome requests corrective input; it is not a completed clinical result. Distinguish an ordinary missing input from a model/provider failure.

## 6. Idempotency and recovery

Propose required Idempotency-Key for review and feedback creation. Same key and payload returns the original resource; changed payload conflicts. Persist mappings for the stored lifetime. Flag changes count as changed payload. New intentional reviews use a new key/snapshot, including retries after needs_input. No visible history feature is required to preserve these backend associations.

Resolve durable acceptance and workflow/resource identity atomically or through a proven recovery design before returning acceptance. Test the crash gap explicitly. A new intentional retry of a terminal failed review creates a new linked review; DBOS recovery of an interrupted execution keeps its existing identity. Do not promise exactly-once external model invocation.

## 7. Phase 3 contract validation

Create OpenAPI and browser/cURL examples during implementation. Cover strict true/false/missing flag, single-field parsing, missing sections, all four truth-table combinations, exact copy text, no template on no observations, stale results after text/flag edits, optional feedback explanation, invalid feedback targets, duplicates and reconnect. The corresponding API and browser tests are implemented; see IMPLEMENTATION_STATUS.md. OpenAPI is available at /openapi.json and interactive API docs at /docs. A generated schema snapshot is included at prototype/openapi.json.

## 8. Running API example

```sh
curl -X POST http://127.0.0.1:8000/api/v1/reviews \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: example-discrepancy-1' \
  -d '{"report_text":"Findings:\nLeft pleural effusion.\n\nImpression:\nRight pleural effusion.","radiologist_critical_flag":false}'
```

Use the returned review_id with GET /api/v1/reviews/{review_id}. Do not reuse the example key for changed input. GET /api/v1/config reports demo/openai mode, readiness and policy status; GET /api/v1/health reports process health. No API key is returned.
