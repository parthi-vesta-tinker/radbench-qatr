"""One-request TypeSafe JEV adapter with an application-owned response checkpoint."""

import json
import os
import time

import httpx

from .classification import ClassificationProblem, MAX_RESPONSE, request_body
from . import classification_store as records

URL = "https://api.typesafe.ai/v1/systemone"


def make_client(timeout):
    return httpx.Client(timeout=timeout, follow_redirects=False)


def _status_problem(status):
    if status in (401, 422):
        return ClassificationProblem("JEV_REQUEST_FAILED", "JEV rejected its configuration or request.")
    if status in (429, 529):
        return ClassificationProblem("JEV_BUSY", "JEV is busy. You may start a new request later.", retryable=True)
    return ClassificationProblem("JEV_PROVIDER_FAILED", "JEV could not classify this finding.", retryable=True)


def dispatch_once(tenant, rid, input_data, config):
    previous = records.attempt(tenant, rid)
    if previous:
        if previous["outcome"] == "claimed":
            records.mark_unknown(tenant, rid)
            raise ClassificationProblem("MODEL_OUTCOME_UNKNOWN", "The previous JEV outcome could not be recovered.")
        if previous["outcome"] == "unknown":
            raise ClassificationProblem("MODEL_OUTCOME_UNKNOWN", "The previous JEV outcome could not be recovered.")
        return previous
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        raise ClassificationProblem("JEV_NOT_CONFIGURED", "JEV credentials are unavailable.")
    if not records.claim(tenant, rid):
        # The deterministic DBOS workflow owns one provider call. A competing execution
        # cannot dispatch and must not overwrite the active owner's state.
        raise RuntimeError("JEV attempt already claimed by another execution")
    started = time.monotonic()
    try:
        timeout = httpx.Timeout(connect=5.0, read=25.0, write=10.0, pool=5.0)
        with make_client(timeout) as client:
            with client.stream("POST", URL, headers={"Authorization": "Bearer " + key,
                       "Content-Type": "application/json"}, json=request_body(input_data, config)) as response:
                status = response.status_code
                chunks, size = [], 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > MAX_RESPONSE:
                        chunks = None
                        break
                    chunks.append(chunk)
                body = b"".join(chunks).decode("utf-8", errors="replace") if chunks is not None else None
        duration = int((time.monotonic() - started) * 1000)
        records.checkpoint(tenant, rid, status, body, duration)
    except Exception as exc:
        # A request may have reached the vendor. No automatic second dispatch.
        records.mark_unknown(tenant, rid)
        raise ClassificationProblem("MODEL_OUTCOME_UNKNOWN", "The JEV outcome could not be recovered.") from exc
    return records.attempt(tenant, rid)


def parsed_response(checkpoint):
    if checkpoint["outcome"] == "unknown":
        raise ClassificationProblem("MODEL_OUTCOME_UNKNOWN", "The JEV outcome could not be recovered.")
    if checkpoint["outcome"] == "known_failure":
        if checkpoint["http_status"] in range(200, 300):
            raise ClassificationProblem("JEV_INVALID_OUTPUT", "JEV response exceeded the allowed size.")
        raise _status_problem(checkpoint["http_status"])
    if checkpoint["outcome"] != "response":
        raise ClassificationProblem("MODEL_OUTCOME_UNKNOWN", "The JEV outcome could not be recovered.")
    try:
        raw = json.loads(checkpoint["response_body"])
    except (TypeError, ValueError):
        raise ClassificationProblem("JEV_INVALID_OUTPUT", "JEV returned malformed JSON.") from None
    return raw
