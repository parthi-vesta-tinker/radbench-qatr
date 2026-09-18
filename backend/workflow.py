import os
import time
from pathlib import Path
from dbos import DBOS, SetWorkflowID, Queue
from . import store
from .contracts import ReviewInput, ReviewProblem, parse_sections, assemble
from .reviewer import demo_stage, openai_stage


REVIEW_CONCURRENCY = int(os.environ.get("QA_REVIEW_CONCURRENCY", "2"))
if not 1 <= REVIEW_CONCURRENCY <= 32:
    raise ValueError("QA_REVIEW_CONCURRENCY must be between 1 and 32")
review_queue = Queue("qa-reviews-v1", concurrency=REVIEW_CONCURRENCY)


@DBOS.step(name="qa.resource.state.v5")
def state(tenant, rid, **values):
    store.update(tenant, rid, **values)


@DBOS.step(name="qa.validate.v5")
def validate(payload):
    ReviewInput.model_validate(payload)
    return parse_sections(payload["report_text"])


@DBOS.step(name="qa.assemble.v5")
def format_result(outputs, report_text):
    return assemble(outputs, report_text)


@DBOS.step(name="qa.test.checkpoint.v5")
def test_checkpoint(rid, point):
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


@DBOS.workflow(name="qa.review.v5", max_recovery_attempts=5)
def run_review(tenant, rid, payload, config):
    active = "input_validation"
    try:
        state(
            tenant, rid, step=active, step_status="running", execution_status="running"
        )
        sections = validate(payload)
        state(tenant, rid, step=active, step_status="completed")
        test_checkpoint(rid, "after_input_validation")
        outputs = {}
        for active in [
            "language_review",
            "consistency_review",
            "critical_finding_review",
        ]:
            state(tenant, rid, step=active, step_status="running")
            test_checkpoint(rid, "before_" + active)
            outputs[active] = (
                demo_stage(active, payload)
                if config["mode"] == "demo"
                else DBOS.start_workflow(
                    openai_stage, active, payload, sections, config
                ).get_result()
            )
            state(
                tenant,
                rid,
                step=active,
                step_status="completed",
                metrics=outputs[active]["metrics"],
            )
            test_checkpoint(rid, "after_" + active)
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
        state(
            tenant,
            rid,
            step=active,
            step_status="needs_input" if is_input else "failed",
            execution_status="needs_input" if is_input else "failed",
            error=error,
        )
        return None


def workflow_id(tenant, rid):
    return f"qa:{tenant}:{rid}"


def dispatch(tenant, rid):
    args = store.job(tenant, rid)
    if args:
        with SetWorkflowID(workflow_id(tenant, rid)):
            return review_queue.enqueue(run_review, tenant, rid, *args)
