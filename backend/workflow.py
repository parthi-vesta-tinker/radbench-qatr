import os
import time
from pathlib import Path
from dbos import DBOS, SetWorkflowID, Queue
from . import store
from .contracts import ReviewInput, ReviewProblem, parse_sections, assemble
from .reviewer import demo_stage, openai_combined


REVIEW_CONCURRENCY = int(os.environ.get("QA_REVIEW_CONCURRENCY", "2"))
if not 1 <= REVIEW_CONCURRENCY <= 32:
    raise ValueError("QA_REVIEW_CONCURRENCY must be between 1 and 32")
review_queue = Queue("qa-reviews-f3-v1", concurrency=REVIEW_CONCURRENCY)


@DBOS.step(name="qa.resource.state.f3.v1")
def state(tenant, rid, **values):
    store.update(tenant, rid, **values)


@DBOS.step(name="qa.validate.f3.v1")
def validate(payload):
    ReviewInput.model_validate(payload)
    return parse_sections(payload["report_text"])


@DBOS.step(name="qa.assemble.f3.v1")
def format_result(outputs, report_text):
    return assemble(outputs, report_text)


@DBOS.step(name="qa.test.checkpoint.f3.v1")
def test_checkpoint(rid, point):
    boundary_hook(rid, point)


def boundary_hook(rid, point):
    # Isolated process-recovery tests only. No client can set these hooks.
    directory = os.environ.get("QA_TEST_HOOK_DIR")
    if not directory:
        return
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    with (root / "executions.log").open("a") as log:
        log.write(f"{rid} {point}\n")
    if os.environ.get("QA_TEST_PAUSE_AT") == point:
        (root / "paused").write_text(rid)
        time.sleep(120)
    if os.environ.get("QA_TEST_FAIL_AT") == point:
        raise RuntimeError("Injected isolated test failure")


def execute(tenant, rid, payload, config, sink, checkpoint):
    """The four real phases, shared by live review and the playground.

    Both callers run the same validation, the same combined request and the same output
    validation. Only where state is written differs, so a playground run exercises the
    live path rather than a copy of it that can drift.
    """
    active = "input_validation"
    try:
        sink(tenant, rid, step=active, step_status="running", execution_status="running")
        validate(payload)
        sink(tenant, rid, step=active, step_status="completed")
        checkpoint(rid, "after_input_validation")
        active = 'combined_review'
        sink(tenant, rid, step=active, step_status='running')
        if config['mode'] == 'demo':
            outputs = {stage: demo_stage(stage, payload) for stage in
                       ('language_review', 'consistency_review', 'critical_finding_review')}
            raw = None
            metrics = dict(provider='demo', model_calls=0)
        else:
            response = DBOS.start_workflow(openai_combined, tenant, rid, payload, config).get_result()
            raw, metrics = response['raw'], response['metrics']
        sink(tenant, rid, step=active, step_status='completed', metrics=metrics)
        checkpoint(rid, 'after_combined_review')
        active = 'output_validation'
        sink(tenant, rid, step=active, step_status='running')
        if raw is not None:
            from .combined import validate_combined
            outputs = validate_combined(raw, payload['report_text'], config['skill_snapshot'])
        sink(tenant, rid, step=active, step_status='completed')
        checkpoint(rid, 'after_output_validation')
        active = "comment_assembly"
        sink(tenant, rid, step=active, step_status="running")
        result = format_result(outputs, payload["report_text"])
        sink(
            tenant,
            rid,
            step=active,
            step_status="completed",
            execution_status="completed",
            result=result,
        )
        checkpoint(rid, 'after_final_commit')
        return result
    except Exception as exc:
        from .diagnostics import record_failure
        record_failure("review.failed", exc, tenant=tenant, review_id=rid, stage=active)
        is_input = isinstance(exc, ReviewProblem) and exc.needs_input
        if isinstance(exc, ReviewProblem):
            error = dict(code=exc.code, message=exc.message, retryable=exc.retryable)
        else:
            error = dict(
                code="REVIEW_FAILED",
                message="The review could not finish. Check backend/model configuration or retry the report.",
                retryable=True,
            )
        metrics = None
        if active == 'combined_review' and config['mode'] == 'openai':
            try:
                from .attempts import failure_metrics
                metrics = failure_metrics(tenant, rid, config)
            except Exception as metric_exc:
                record_failure('attempt.metrics_unavailable', metric_exc, tenant=tenant, review_id=rid)
        sink(
            tenant,
            rid,
            metrics=metrics,
            step=active,
            step_status="needs_input" if is_input else "failed",
            execution_status="needs_input" if is_input else "failed",
            error=error,
        )
        return None


@DBOS.workflow(name="qa.review.f3.v1", max_recovery_attempts=5)
def run_review(tenant, rid, payload, config):
    return execute(tenant, rid, payload, config, state, test_checkpoint)


def workflow_id(tenant, rid):
    return f"qa:f3:{tenant}:{rid}"


def dispatch(tenant, rid):
    args = store.job(tenant, rid)
    if args:
        with SetWorkflowID(workflow_id(tenant, rid)):
            return review_queue.enqueue(run_review, tenant, rid, *args)


PLAYGROUND_CONCURRENCY = int(os.environ.get("QA_PLAYGROUND_CONCURRENCY", "2"))
if not 1 <= PLAYGROUND_CONCURRENCY <= 32:
    raise ValueError("QA_PLAYGROUND_CONCURRENCY must be between 1 and 32")
# A separate queue so a playground run can never starve live report QA of its concurrency.
playground_queue = Queue("qa-playground-f3-v1", concurrency=PLAYGROUND_CONCURRENCY)


@DBOS.step(name="qa.playground.state.f3.v1")
def playground_state(tenant, run_id, *, execution_status=None, metrics=None, **values):
    # Playground logs are phases and timings. Provider metrics are deliberately not stored.
    store.update_playground(tenant, run_id, status=execution_status, **values)


@DBOS.step(name="qa.playground.checkpoint.f3.v1")
def playground_checkpoint(run_id, point):
    return None


@DBOS.workflow(name="qa.playground.f3.v1", max_recovery_attempts=5)
def run_playground(tenant, run_id, payload, config):
    return execute(tenant, run_id, payload, config, playground_state, playground_checkpoint)


def playground_workflow_id(tenant, run_id):
    return f"qa:pg:{tenant}:{run_id}"


def dispatch_playground(tenant, run_id, payload, config):
    with SetWorkflowID(playground_workflow_id(tenant, run_id)):
        return playground_queue.enqueue(run_playground, tenant, run_id, payload, config)
