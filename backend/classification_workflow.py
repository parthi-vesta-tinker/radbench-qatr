"""Versioned classification execution; v1 remains registered for accepted jobs."""

import threading

from dbos import DBOS, Queue, SetWorkflowID

from . import classification_store as records
from .classification import ClassificationProblem, validate_response
from .jev import dispatch_once, parsed_response

classification_ready = threading.Event()

classification_queue = Queue("qa-finding-classifications-v1", concurrency=2)


@DBOS.step(name="qa.finding.state.v1")
def state(tenant, rid, **values):
    records.update(tenant, rid, **values)


@DBOS.step(name="qa.finding.input.v1")
def load_input(tenant, rid):
    job = records.job(tenant, rid)
    if not job:
        raise ClassificationProblem("CLASSIFICATION_NOT_FOUND", "Classification job is unavailable.")
    input_data, config = job
    if not input_data["finding_text"].strip():
        raise ClassificationProblem("CLASSIFICATION_INVALID_INPUT", "Critical finding text is empty.")
    return job


@DBOS.step(name="qa.finding.jev.v1")
def provider(tenant, rid, input_data, config):
    return dispatch_once(tenant, rid, input_data, config)


@DBOS.step(name="qa.finding.validate.v1")
def validate(checkpoint, config):
    return validate_response(parsed_response(checkpoint), config, checkpoint.get("duration_ms"))


@DBOS.workflow(name="qa.finding.classify.v1", max_recovery_attempts=5)
def run(tenant, rid):
    active = "input_validation"
    try:
        state(tenant, rid, step=active, step_status="running", status="running")
        input_data, config = load_input(tenant, rid)
        state(tenant, rid, step=active, step_status="completed")
        active = "jev_classification"
        state(tenant, rid, step=active, step_status="running")
        checkpoint = provider(tenant, rid, input_data, config)
        state(tenant, rid, step=active, step_status="completed")
        active = "output_validation"
        state(tenant, rid, step=active, step_status="running")
        result = validate(checkpoint, config)
        state(tenant, rid, step=active, step_status="completed")
        active = "result_assembly"
        state(tenant, rid, step=active, step_status="running")
        state(tenant, rid, step=active, step_status="completed", status="completed", result=result)
        return result
    except ClassificationProblem as exc:
        state(tenant, rid, step=active, step_status="failed", status="failed",
              error=dict(code=exc.code, message=exc.message, retryable=exc.retryable))
        return None
    except Exception:
        # DBOS may recover local failures. Do not turn a competing claim into a
        # terminal result while the owner might still be executing.
        raise


@DBOS.step(name="qa.finding.execute.v2")
def execute_classification(tenant, rid):
    existing = records.get(tenant, rid)
    if not existing:
        raise ClassificationProblem("CLASSIFICATION_NOT_FOUND", "Classification job is unavailable.")
    if existing["execution_status"] in ("completed", "failed"):
        return existing.get("result")
    phases = [dict(step_id=step, status="pending", started_at=None, completed_at=None) for step in records.STEPS]
    active = 0

    def start(index):
        phases[index].update(status="running", started_at=records.store.now())

    def finish(index):
        phases[index].update(status="completed", completed_at=records.store.now())

    try:
        start(active)
        input_data, config = records.job(tenant, rid)
        if not input_data["finding_text"].strip():
            raise ClassificationProblem("CLASSIFICATION_INVALID_INPUT", "Critical finding text is empty.")
        finish(active)
        active = 1
        start(active)
        records.update(tenant, rid, status="running", phases=phases)
        from .jev import dispatch_retrying
        checkpoint = dispatch_retrying(tenant, rid, input_data, config)
        finish(active)
        active = 2
        start(active)
        result = validate_response(parsed_response(checkpoint), config, checkpoint.get("duration_ms"))
        finish(active)
        active = 3
        start(active)
        finish(active)
        records.update(tenant, rid, status="completed", result=result, phases=phases)
        from .workflow import boundary_hook
        boundary_hook(rid, "jev_after_final_commit")
        return result
    except ClassificationProblem as exc:
        phases[active].update(status="failed", completed_at=records.store.now())
        records.update(tenant, rid, status="failed", phases=phases,
                       error=dict(code=exc.code, message=exc.message, retryable=exc.retryable))
        return None


@DBOS.workflow(name="qa.finding.classify.v2", max_recovery_attempts=5)
def run_v2(tenant, rid):
    return execute_classification(tenant, rid)


def dispatch(tenant, rid):
    job = records.job(tenant, rid)
    if not job:
        return None
    version = "v2" if job[1].get("workflow_version") == "qa.finding.classify.v2" else "v1"
    with SetWorkflowID(f"qa:classification:{version}:{tenant}:{rid}"):
        return classification_queue.enqueue(run_v2 if version == "v2" else run, tenant, rid)


def dispatch_automatic(tenant=None, review_id=None):
    """Immediate best-effort enqueue; the durable source query is also the fallback outbox."""
    import logging
    from .classification import snapshot
    from .contracts import ClassificationInput
    for owner, source, version, observation in records.pending_automatic(tenant, review_id):
        try:
            accepted = records.store.job(owner, source)[1]
            config = accepted.get("jev_config_at_acceptance") or snapshot(owner, accepted=True)
            payload = ClassificationInput(review_id=source, input_version=version, observation_id=observation)
            saved, created = records.reserve(owner, "", payload, config, automatic=True)
            if created:
                dispatch(owner, saved["body"]["id"])
        except ClassificationProblem:
            continue  # The source may have been replaced since discovery.
        except Exception:
            logging.getLogger("qa.api").error("classification.auto_dispatch_deferred tenant=%s review=%s", owner, source)
