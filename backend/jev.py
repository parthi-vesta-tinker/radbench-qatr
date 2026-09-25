"""One-request TypeSafe JEV adapter with an application-owned response checkpoint."""

import json
import math
import os
import time

import httpx

from .classification import ClassificationProblem, MAX_RESPONSE, request_body
from . import classification_store as records

URL = "https://api.typesafe.ai/v1/systemone"


def make_client(timeout):
    return httpx.Client(timeout=timeout, follow_redirects=False)


def _status_problem(status):
    if status in (400, 401, 403, 404, 422):
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


# V2 tolerates duplicate inference after a transport failure or expired lease.
# The durable counter bounds this policy across process restarts, not just one loop.
def transient_status(status):
    return status in (408, 429) or status is not None and 500 <= status <= 599


def retry_delay(response, count):
    from datetime import datetime, timezone
    from email.utils import parsedate_to_datetime
    import random
    delay = min(2.0, .25 * 2 ** (count - 1)) + random.uniform(0, .1)
    header = response.headers.get("retry-after") if response is not None else None
    if header:
        try:
            requested = float(header)
        except ValueError:
            try:
                requested = (parsedate_to_datetime(header) - datetime.now(timezone.utc)).total_seconds()
            except (ValueError, TypeError, OverflowError):
                requested = 0
        if not math.isfinite(requested):
            return None
        if requested > 30:
            return None  # Leave an explicit failure; never retry before the server permits.
        delay = max(delay, requested)
    return delay


def dispatch_retrying(tenant, rid, input_data, config):
    body = request_body(input_data, config)
    from .classification import validate_context_size
    validate_context_size(body)
    while True:
        previous = records.attempt(tenant, rid)
        metadata = json.loads(previous["claim_id"]) if previous else {"count": 0}
        if previous:
            if previous["outcome"] == "response":
                return previous
            if previous["outcome"] == "known_failure" and (
                not transient_status(previous["http_status"]) or not metadata.get("retry_allowed", True)
            ):
                return previous
            remaining = metadata.get("not_before", 0) - time.time()
            if remaining > 0:
                time.sleep(min(remaining, 1))
                continue
            if metadata["count"] >= records.MAX_JEV_ATTEMPTS or not metadata.get("retry_allowed", True):
                if previous["outcome"] == "known_failure":
                    return previous
                raise ClassificationProblem("JEV_RETRIES_EXHAUSTED",
                    "Classification could not complete after three attempts. You may start a new request.", retryable=True)
        key = os.environ.get("TYPESAFE_API_KEY")
        if not key:
            raise ClassificationProblem("JEV_NOT_CONFIGURED", "JEV credentials are unavailable.")
        token = records.acquire_retry_attempt(tenant, rid, previous)
        if token is None:
            continue
        from .workflow import boundary_hook
        boundary_hook(rid, "jev_after_claim")
        count = json.loads(token)["count"]
        started = time.monotonic()
        status, response_body, response, transport_error = None, None, None, False
        try:
            timeout = httpx.Timeout(connect=5.0, read=25.0, write=10.0, pool=5.0)
            with make_client(timeout) as client:
                with client.stream("POST", URL, headers={"Authorization": "Bearer " + key,
                        "Content-Type": "application/json"}, json=body) as response:
                    status = response.status_code
                    chunks, size = [], 0
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > MAX_RESPONSE:
                            chunks = None
                            break
                        if time.monotonic() - started > 45:
                            raise httpx.ReadTimeout("Classification response deadline exceeded")
                        chunks.append(chunk)
                    response_body = b"".join(chunks).decode("utf-8", errors="replace") if chunks is not None else None
        except httpx.DecodingError:
            # A malformed encoded response is invalid output, not a repair request.
            response_body = None
        except httpx.TransportError:
            # A known permanent HTTP rejection stays terminal even if its body
            # cannot be read; uncertain success/transient outcomes may retry.
            transport_error = status is None or 200 <= status < 300 or transient_status(status)
        boundary_hook(rid, "jev_after_response")
        delay = retry_delay(response, count) if transport_error or transient_status(status) else 0
        # Checkpoint persistence failures propagate to DBOS recovery. They are not
        # mistaken for HTTP failures and cannot reset the durable attempt budget.
        records.checkpoint_retry_attempt(tenant, rid, token, status=status, body=response_body,
            duration_ms=int((time.monotonic() - started) * 1000), transport_error=transport_error,
            retry_at=time.time() + (delay or 0) if count < records.MAX_JEV_ATTEMPTS else 0,
            retry_allowed=delay is not None,
            retry_pending=(transport_error or transient_status(status)) and delay is not None and count < records.MAX_JEV_ATTEMPTS)
        boundary_hook(rid, "jev_after_checkpoint")
