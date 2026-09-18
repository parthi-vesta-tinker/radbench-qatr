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


@DBOS.workflow(name="qa.review.f3.v1", max_recovery_attempts=5)
def run_review(tenant, rid, payload, config):
    active = "input_validation"
    try:
        state(
            tenant, rid, step=active, step_status="running", execution_status="running"
        )
        validate(payload)
        state(tenant, rid, step=active, step_status="completed")
        test_checkpoint(rid, "after_input_validation")
        active = 'combined_review'
        state(tenant, rid, step=active, step_status='running')
        if config['mode'] == 'demo':
            outputs = {stage: demo_stage(stage, payload) for stage in
                       ('language_review', 'consistency_review', 'critical_finding_review')}
            raw = None
            metrics = dict(provider='demo', model_calls=0)
        else:
            response = DBOS.start_workflow(openai_combined, tenant, rid, payload, config).get_result()
            raw, metrics = response['raw'], response['metrics']
        state(tenant, rid, step=active, step_status='completed', metrics=metrics)
        test_checkpoint(rid, 'after_combined_review')
        active = 'output_validation'
        state(tenant, rid, step=active, step_status='running')
        if raw is not None:
            from .combined import validate_combined
            outputs = validate_combined(raw, payload['report_text'], config['skill_snapshot'])
        state(tenant, rid, step=active, step_status='completed')
        test_checkpoint(rid, 'after_output_validation')
        active = "comment_assembly"
        state(tenant, rid, step=active, step_status="running")
        result = format_result(outputs, payload["report_text"])
        state(
            tenant,
            rid,
            step=active,
            step_status="completed",
            execution_status="completed",
            result=result,
        )
        test_checkpoint(rid, 'after_final_commit')
        return result
    except Exception as exc:
        from . import spend
        from .diagnostics import record_failure
        try:
            spend.release_unclaimed(tenant, config)
        except Exception as ledger_exc:
            # A missing/unavailable ledger cannot turn a failed review into stuck work.
            record_failure('spend.release_deferred', ledger_exc, tenant=tenant, review_id=rid)
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
        state(
            tenant,
            rid,
            metrics=metrics,
            step=active,
            step_status="needs_input" if is_input else "failed",
            execution_status="needs_input" if is_input else "failed",
            error=error,
        )
        return None


def workflow_id(tenant, rid):
    return f"qa:f3:{tenant}:{rid}"


def dispatch(tenant, rid):
    args = store.job(tenant, rid)
    if args:
        with SetWorkflowID(workflow_id(tenant, rid)):
            return review_queue.enqueue(run_review, tenant, rid, *args)
