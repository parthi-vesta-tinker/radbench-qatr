# Prototype API design brief

Version 0.1 · Proposed contract for G3 review · Not implemented

## 1. Design aim

A human browser client and a coding agent should use the same small API. FastAPI owns request validation and resource semantics; DBOS owns durable execution behind that boundary. Do not expose DBOS internal statuses or serialized SDK objects as the public contract.

Initial proposal: JSON over HTTP with short polling. No WebSockets, callback registration, multi-tenant platform or generic agent API is necessary. Endpoint names and limits below are proposals to validate, not frozen production interfaces.

## 2. Resources and operations

| Operation | Proposed endpoint | Expected behavior |
|---|---|---|
| Create review | POST /api/v1/reviews | Accept findings/impression; return 202, stable review ID, status URL and Location header after durable acceptance. |
| Read review | GET /api/v1/reviews/{review_id} | Return input snapshot identity, execution/step states, terminal outcome/result when available. |
| Submit feedback | POST /api/v1/reviews/{review_id}/feedback | Validate result/observation binding; return 201 after saving. |
| Read feedback | GET /api/v1/reviews/{review_id}/feedback | Retrieve saved feedback for inspection; no analytics dashboard required. |

No list/fleet endpoint is needed initially. The browser retains the active review ID to reconnect; an input hash is an integrity check, not an authorization mechanism. Authentication and data-retention design belong to the later MVP, before any shared/live patient-data deployment. Initial service is a local prototype.

## 3. Proposed data contract

| Object | Required concepts |
|---|---|
| Review request | findings, impression; no patient identity required |
| Input snapshot | input_version, exact submitted fields, input_hash; manual_paste source; author/signature unknown |
| Review | review_id, created_at, input snapshot identity, execution_status, ordered steps, result or null, error or null |
| Step | stable step_id, execution_status, start/end times when known, attempt count where reliable |
| Result | result_version, outcome, critical_review observations, non_critical observations, exact plain-text exports |
| Observation | observation_id, finding_type, report_section, concise comment; critical group explicitly requires radiologist confirmation |
| Provenance | workflow_version, prompt_version(s), configured model identifier, provider/mode and actual usage where returned |
| Feedback | feedback_id, review_id, result_version, rating, optional observation_id, reason/explanation for thumbs-down, optional suggested_comment, created_at |

Keep result observation arrays and copy exports derived from the same validated result. No independent second generation for clipboard text. Empty groups export an empty string and have no copy control. Observation IDs are assigned/validated by the application rather than relied on as model-generated identifiers.

Execution states: queued, running, completed, needs_input, failed. Step states: pending, running, completed, needs_input, failed, skipped. A failed step can leave downstream steps skipped. A transient browser disconnection is a client connection state, not a server execution failure.

Outcome is null outside completed. For completed it is no_observations only if both groups are empty; otherwise observations. Only a completed result is eligible for feedback in this prototype; operational failures use retry/error UI rather than the result feedback form.

Illustrative request:

```json
{
  "findings": "Left pleural effusion.",
  "impression": "Right pleural effusion."
}
```

Illustrative completed result fragment, excluding resource-level provenance:

```json
{
  "result_version": 1,
  "outcome": "observations",
  "critical_review": [],
  "non_critical": [
    {
      "observation_id": "obs-1",
      "finding_type": "discrepancy",
      "report_section": "both",
      "comment": "Findings state left pleural effusion; impression states right. Please reconcile laterality."
    }
  ],
  "exports": {
    "critical_review": "",
    "non_critical": "NON-CRITICAL OBSERVATIONS\n1. Findings state left pleural effusion; impression states right. Please reconcile laterality.",
    "all": "NON-CRITICAL OBSERVATIONS\n1. Findings state left pleural effusion; impression states right. Please reconcile laterality."
  }
}
```

## 4. Validation and error semantics

Proposed initial input limit: 20,000 characters per field, both required and non-whitespace. Validate without silently rewriting or truncating the submitted report. Reassess this limit against example reports at G1/G3.

| Condition | Proposed response |
|---|---|
| Malformed/invalid field | 422 with field-specific errors |
| Unknown review | 404 with stable error code |
| Same idempotency key, different input | 409; never return another report's result |
| Invalid feedback observation/version | 422; no feedback persisted |
| Workflow not durably accepted | 503; client can safely retry with the same key |
| Accepted review later fails | GET remains 200 for the resource, with execution_status failed and a safe actionable error |

Use one error envelope: code, message, retryable and optional field_errors. Do not return full report text, credentials, raw provider exceptions or internal stack traces in errors.

## 5. Duplicates and retries

Require an Idempotency-Key on review creation and feedback creation in the first controlled client. Same key plus same payload returns the original resource; a changed payload conflicts. Scope keys by operation and persist the mapping for the prototype's stored lifetime. A new intentional review uses a new key and a new immutable snapshot, even if the text is identical.

Before acknowledging creation, resolve how acceptance, review identity and DBOS workflow identity persist together. Avoid a crash gap where a database row exists but no recoverable workflow was created. If acceptance is uncertain, retry the same request/key; do not create an unrelated second job.

A human-requested retry of a terminal failed review creates a new review linked to the previous attempt. Recovery of an interrupted DBOS execution retains the same review identity. Keep these two actions distinct.

## 6. Contract validation tasks

Validate with a browser client and a simple HTTP/cURL client. Exercise unknown IDs, invalid input, all output groups, no observations, queued/running/failed states, duplicate submissions, feedback persistence, invalid feedback targets and reconnect. Confirm input edits cannot cause cross-report result or feedback binding. Generate OpenAPI and request examples during Phase 3; do not implement this draft implicitly.
