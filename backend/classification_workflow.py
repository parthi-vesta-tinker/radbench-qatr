"""Independent durable JEV workflow; report QA and Playground are unchanged."""

from dbos import DBOS, Queue, SetWorkflowID

from . import classification_store as records
from .classification import ClassificationProblem, validate_response
from .jev import dispatch_once, parsed_response

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


def dispatch(tenant, rid):
    if not records.job(tenant, rid):
        return None
    with SetWorkflowID(f"qa:classification:v1:{tenant}:{rid}"):
        return classification_queue.enqueue(run, tenant, rid)
