from typing import Literal
from datetime import datetime, timezone
from .contracts import ReviewList
import asyncio
from contextlib import asynccontextmanager, suppress
import logging
from typing import Annotated
import uuid
from fastapi import FastAPI, Header, Request, Depends, Query, Path as PathParam
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from dbos import DBOS
from agents import set_tracing_disabled
from . import store, presentation, reporting, knowledge, playground
from .access import AccessError, Principal, require, validate_access_config
from .contracts import (
    ReviewProblem,
    FeedbackInput,
    ReviewInput,
    ReviewReplacement,
    ReviewResource,
    FeedbackResource,
    FeedbackList,
    ReviewComments,
    APIErrorEnvelope,
    ConfigResource,
    FeedbackInbox,
    AnalyticsResource,
    REASONS,
)
from .settings import APP_VERSION, DATA, ROOT, runtime_config
from .workflow import dispatch, workflow_id
from .reviewer import SAMPLES
from .diagnostics import (
    configure_logging,
    record_failure,
    config_problem,
    status_report,
    check_openai,
)

configure_logging()

log = logging.getLogger("qa.api")


def reconcile():
    for tenant, rid in store.pending():
        try:
            doc = store.get(tenant, rid)
            generation = doc["input_version"]
            status = DBOS.get_workflow_status(workflow_id(tenant, rid, generation))
            if status is None:
                dispatch(tenant, rid)
            elif status.status in (
                "ERROR",
                "CANCELLED",
                "MAX_RECOVERY_ATTEMPTS_EXCEEDED",
            ):
                doc = store.get(tenant, rid)
                active = next(
                    (s["step_id"] for s in doc["steps"] if s["status"] == "running"),
                    "input_validation",
                )
                from .attempts import uncertain
                unknown = uncertain(tenant, rid, store.job(tenant, rid)[1])
                store.update(
                    tenant,
                    rid,
                    input_version=generation,
                    execution_status="failed",
                    step=active,
                    step_status="failed",
                    error=dict(
                        code="MODEL_OUTCOME_UNKNOWN" if unknown else "EXECUTION_STOPPED",
                        message="Durable execution stopped before completion. No automatic provider retry will occur.",
                        retryable=False,
                    ),
                )
        except Exception:
            log.error("outbox.reconcile_failed tenant=%s review=%s", tenant, rid)


async def reconciliation_loop():
    while True:
        await asyncio.sleep(1)
        try:
            await asyncio.to_thread(reconcile)
        except Exception:
            log.error("outbox.scan_failed; reconciliation will retry")


@asynccontextmanager
async def lifespan(app):
    log.info("startup.begin application_version=%s", APP_VERSION)
    try:
        validate_access_config()
        store.init()
    except Exception as exc:
        record_failure("startup.configuration_or_database_failed", exc)
        raise RuntimeError(
            "QA startup failed; inspect the diagnostic log above. Check tenant configuration, data folder permissions and incompatible pending workflows."
        ) from None
    set_tracing_disabled(True)
    try:
        DBOS(
            config=dict(
                name="vesta-report-qa",
                system_database_url="sqlite:///" + (DATA / "dbos.sqlite").as_posix(),
                application_version=APP_VERSION,
                run_admin_server=False,
                enable_otlp=False,
                log_level="WARNING",
            )
        )
        DBOS.launch()
    except Exception as exc:
        record_failure("startup.dbos_failed", exc)
        raise RuntimeError(
            "DBOS startup failed; inspect the diagnostic log above."
        ) from None
    app.state.dbos_ready = True
    log.info(
        "startup.ready api=ready dbos=initialized database=initialized; OpenAI not probed"
    )
    reconcile()
    worker = asyncio.create_task(reconciliation_loop())
    try:
        yield
    finally:
        worker.cancel()
        with suppress(asyncio.CancelledError):
            await worker
        app.state.dbos_ready = False
        DBOS.destroy(workflow_completion_timeout_sec=3)


def api_version(
    qa_version: Annotated[
        str, Header(alias="QA-Version")
    ] = presentation.API_VERSION,
):
    if qa_version != presentation.API_VERSION:
        raise AccessError(
            400,
            "UNSUPPORTED_API_VERSION",
            "Supported QA-Version: " + presentation.API_VERSION,
        )
    return qa_version


ERROR_RESPONSES = {
    status: {"model": APIErrorEnvelope}
    for status in (400, 401, 403, 404, 409, 422, 500, 503)
}
app = FastAPI(
    title="Vesta Report QA API",
    version="0.14.0",
    lifespan=lifespan,
    dependencies=[Depends(api_version)],
    responses=ERROR_RESPONSES,
)


def error(request, status, code, message, retryable=False, field_errors=None):
    kind = (
        "authentication_error"
        if status == 401
        else "permission_error"
        if status == 403
        else "idempotency_error"
        if status == 409 and code == "IDEMPOTENCY_CONFLICT"
        else "api_error"
        if status >= 500
        else "invalid_request_error"
    )
    detail = dict(
        type=kind,
        code=code,
        message=message,
        retryable=retryable,
        request_id=request.state.request_id,
    )
    if field_errors:
        detail.update(field_errors=field_errors, param=field_errors[0]["field"])
    log.warning(
        "request.error request_id=%s status=%s code=%s",
        request.state.request_id,
        status,
        code,
    )
    headers = {"Retry-After": "1"} if retryable else {}
    if status == 401:
        headers["WWW-Authenticate"] = "Bearer"
    return JSONResponse(status_code=status, content={"error": detail}, headers=headers)


@app.middleware("http")
async def request_context(request, call_next):
    request.state.request_id = "req_" + uuid.uuid4().hex
    try:
        response = await call_next(request)
    except Exception as exc:
        record_failure("request.failed", exc, request_id=request.state.request_id)
        response = error(
            request, 500, "INTERNAL_ERROR", "The request could not be completed.", True
        )
    if request.url.path.startswith("/api/"):
        response.headers["Request-Id"] = request.state.request_id
        response.headers["QA-Version"] = request.headers.get(
            "QA-Version", presentation.API_VERSION
        )
        response.headers["Cache-Control"] = "no-store"
        log.info(
            "request.complete request_id=%s tenant=%s method=%s status=%s",
            request.state.request_id,
            getattr(request.state, "tenant_id", "unauthenticated"),
            request.method,
            response.status_code,
        )
    return response


@app.exception_handler(AccessError)
async def access_failure(request, exc):
    return error(request, exc.status, exc.code, exc.message)


@app.exception_handler(store.ReviewConflict)
def review_conflict(request: Request, exc):
    return error(request, 409, "REVIEW_CONFLICT", str(exc))


@app.exception_handler(store.IdempotencyConflict)
async def conflict(request, exc):
    return error(
        request,
        409,
        "IDEMPOTENCY_CONFLICT",
        "This key was already used for different parameters or an API version in this tenant and operation.",
    )


@app.exception_handler(RequestValidationError)
async def invalid(request, exc):
    # Do not echo raw report text, bearer keys or idempotency header values.
    fields = [
        dict(field=".".join(map(str, e["loc"])), message=e["msg"]) for e in exc.errors()
    ]
    return error(
        request,
        422,
        "INVALID_INPUT",
        "Please correct the indicated fields.",
        field_errors=fields,
    )


@app.exception_handler(HTTPException)
async def http_error(request, exc):
    return error(
        request,
        exc.status_code,
        "HTTP_ERROR",
        "Requested resource or operation is unavailable.",
    )


Key = Annotated[
    str, Header(alias="Idempotency-Key", min_length=1, max_length=255, pattern=r"^\S+$")
]
Read = Annotated[Principal, Depends(require("reviews:read"))]
Write = Annotated[Principal, Depends(require("reviews:write"))]
FeedbackRead = Annotated[Principal, Depends(require("feedback:read"))]
FeedbackWrite = Annotated[Principal, Depends(require("feedback:write"))]
Version = Annotated[str, Depends(api_version)]
SkillsRead = Annotated[Principal, Depends(require("skills:read"))]
SkillsWrite = Annotated[Principal, Depends(require("skills:write"))]


def respond(receipt, replayed=False):
    return Response(
        status_code=receipt["status"],
        content=store.canonical(receipt["body"]),
        media_type="application/json",
        headers=receipt["headers"] | {"Idempotency-Replayed": str(replayed).lower()},
    )


@app.get("/api/v1/config", response_model=ConfigResource)
def config(request: Request, p: Read, version: Version):
    try:
        c = runtime_config(p.tenant_id)
    except (ValueError, OSError, KeyError) as exc:
        record_failure(
            "configuration.invalid", exc, request_id=request.state.request_id
        )
        code, message = config_problem(exc)
        return error(
            request,
            503,
            code,
            message,
        )
    return {k: v for k, v in c.items() if k != "policy_text"} | dict(
        tenant_id=p.tenant_id,
        api_version=version,
        samples=SAMPLES if c["mode"] == "demo" else [],
    )


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "version": APP_VERSION}


@app.get("/api/v1/status")
def operational_status(request: Request, p: Read):
    return status_report(request.app, p.tenant_id)


@app.post("/api/v1/diagnostics/openai")
async def openai_connection(p: Read):
    return await check_openai(p.tenant_id)


@app.post(
    "/api/v1/reviews",
    status_code=202,
    response_model=ReviewResource,
    response_model_exclude_unset=True,
)
def create_review(
    request: Request,
    payload: ReviewInput,
    idempotency_key: Key,
    p: Write,
    version: Version,
):
    return accept_review(request, payload, idempotency_key, p, version)


@app.put("/api/v1/reviews/{review_id}", status_code=202, response_model=ReviewResource, response_model_exclude_unset=True)
def replace_review(request: Request, review_id: str, payload: ReviewReplacement, idempotency_key: Key, p: Write, version: Version):
    return accept_review(request, payload, idempotency_key, p, version, review_id)


def accept_review(request, payload, idempotency_key, p, version, replace_id=None):
    operation = f"PUT /api/v1/reviews/{replace_id}" if replace_id else store.CREATE_REVIEW
    # Replay precedes mutable provider readiness. A previously accepted request remains accepted.
    saved = store.replay(
        p.tenant_id, operation, idempotency_key, payload.model_dump(), version
    )
    if saved:
        return respond(saved, True)
    try:
        cfg = runtime_config(p.tenant_id)
    except (ValueError, OSError, KeyError) as exc:
        record_failure(
            "configuration.invalid", exc, request_id=request.state.request_id
        )
        code, message = config_problem(exc)
        return error(
            request,
            503,
            code,
            message,
        )
    if not cfg["ready"]:
        return error(
            request,
            503,
            "MODEL_NOT_CONFIGURED",
            "Configure OPENAI_API_KEY and OPENAI_MODEL before reviewing.",
        )
    if cfg['mode'] == 'openai':
        from .combined import input_bound
        try:
            input_bound(cfg, payload.report_text)
        except ReviewProblem as exc:
            return error(request, 422, exc.code, exc.message)
    try:
        saved, created = store.reserve(
            p.tenant_id, idempotency_key, payload, cfg, version, replace_id, p.actor_name
        )
    except KeyError:
        return error(request, 404, "REVIEW_NOT_FOUND", "Review not found.")
    except store.ReviewConflict as exc:
        return error(request, 409, "REVIEW_CONFLICT", str(exc))
    if created:
        try:
            dispatch(p.tenant_id, saved["body"]["id"])
        except Exception:
            log.error(
                "outbox.dispatch_deferred request_id=%s tenant=%s",
                request.state.request_id,
                p.tenant_id,
            )
    # The committed resource/outbox/receipt are the acceptance boundary even if dispatch is deferred.
    return respond(saved, not created)


@app.get("/api/v1/reviews", response_model=ReviewList)
def list_reviews(
    request: Request,
    p: Read,
    version: Version,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    starting_after: str | None = None,
    q: Annotated[str, Query(max_length=200)] = "",
    status: Literal["queued", "running", "completed", "needs_input", "failed"]
    | None = None,
    outcome: Literal["observations", "no_observations"] | None = None,
    critical: bool | None = None,
    comment_type: Literal["any", "general", "critical"] | None = None,
    has_feedback: bool | None = None,
    submitted_after: datetime | None = None,
    submitted_before: datetime | None = None,
):
    can_read_feedback = "feedback:read" in p.scopes
    if has_feedback is not None and not can_read_feedback:
        return error(
            request,
            403,
            "INSUFFICIENT_SCOPE",
            "Feedback filtering requires feedback:read.",
        )
    if any(value is not None and value.tzinfo is None for value in (submitted_after, submitted_before)):
        return error(
            request, 422, "INVALID_SUBMISSION_TIME", "Submission time filters must include a timezone."
        )
    after_value = submitted_after.astimezone(timezone.utc).isoformat() if submitted_after else None
    before_value = submitted_before.astimezone(timezone.utc).isoformat() if submitted_before else None
    if after_value and before_value and after_value >= before_value:
        return error(
            request, 422, "INVALID_SUBMISSION_RANGE", "submitted_after must be before submitted_before."
        )
    try:
        items, more = store.list_reviews(
            p.tenant_id,
            limit,
            starting_after,
            q.strip(),
            status,
            outcome,
            critical,
            comment_type,
            has_feedback,
            can_read_feedback,
            after_value,
            before_value,
        )
    except store.InvalidCursor:
        return error(
            request,
            400,
            "INVALID_CURSOR",
            "Cursor does not belong to this review collection.",
        )
    return dict(
        object="list",
        items=items,
        has_more=more,
        next_cursor=items[-1]["id"] if more else None,
        url="/api/v1/reviews",
    )


@app.get(
    "/api/v1/reviews/{review_id}",
    response_model=ReviewResource,
    response_model_exclude_unset=True,
)
def get_review(request: Request, review_id: str, p: Read, version: Version):
    doc = store.get(p.tenant_id, review_id)
    if doc is None:
        return error(request, 404, "REVIEW_NOT_FOUND", "Review not found.")
    return presentation.review(doc, version)


@app.get("/api/v1/reviews/{review_id}/comments", response_model=ReviewComments)
def get_comments(request: Request, review_id: str, p: Read, version: Version):
    doc = store.get(p.tenant_id, review_id)
    if doc is None:
        return error(request, 404, "REVIEW_NOT_FOUND", "Review not found.")
    return presentation.comments(doc)


@app.post(
    "/api/v1/reviews/{review_id}/feedback",
    status_code=201,
    response_model=FeedbackResource,
)
def add_feedback(
    request: Request,
    review_id: str,
    payload: FeedbackInput,
    idempotency_key: Key,
    p: FeedbackWrite,
    version: Version,
):
    doc = store.get(p.tenant_id, review_id)
    if doc is None:
        return error(request, 404, "REVIEW_NOT_FOUND", "Review not found.")
    saved = store.replay(
        p.tenant_id,
        store.feedback_scope(review_id),
        idempotency_key,
        payload.model_dump(),
        version,
    )
    if saved:
        return respond(saved, True)
    result = doc["result"]
    if not result or doc["execution_status"] != "completed":
        return error(
            request, 422, "RESULT_NOT_COMPLETE", "Feedback requires a completed result."
        )
    ids = {
        x["observation_id"]
        for x in result["general_comments"] + result["critical_comments"]
    }
    if payload.target == "observation" and payload.observation_id not in ids:
        return error(
            request,
            422,
            "OBSERVATION_NOT_FOUND",
            "The observation does not belong to this result.",
        )
    saved, created = store.save_feedback(
        p.tenant_id, review_id, idempotency_key, payload, version
    )
    return respond(saved, not created)


@app.get("/api/v1/reviews/{review_id}/feedback", response_model=FeedbackList)
def get_feedback(
    request: Request,
    review_id: str,
    p: FeedbackRead,
    version: Version,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    starting_after: str | None = None,
):
    if store.get(p.tenant_id, review_id) is None:
        return error(request, 404, "REVIEW_NOT_FOUND", "Review not found.")
    try:
        items, more = store.feedback(p.tenant_id, review_id, limit, starting_after)
    except store.InvalidCursor:
        return error(
            request,
            400,
            "INVALID_CURSOR",
            "Cursor does not belong to this feedback collection.",
        )
    return dict(
        object="list",
        items=[presentation.feedback(x, version) for x in items],
        has_more=more,
        next_cursor=items[-1]["feedback_id"] if more else None,
        url=f"/api/v1/reviews/{review_id}/feedback",
    )


@app.get("/api/v1/feedback", response_model=FeedbackInbox)
def list_feedback_inbox(
    request: Request,
    p: FeedbackRead,
    report_access: Read,
    version: Version,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    starting_after: str | None = None,
    q: Annotated[str, Query(max_length=200)] = "",
    rating: Literal["up", "down"] | None = None,
    reason: REASONS | None = None,
    source: Literal["openai", "demo", "all"] = "openai",
):
    try:
        items, more = reporting.feedback_inbox(
            p.tenant_id, version, limit, starting_after, q.strip(), rating, reason, source
        )
    except store.InvalidCursor:
        return error(request, 400, "INVALID_CURSOR", "Cursor does not belong to this feedback collection.")
    return dict(object="list", items=items, has_more=more,
                next_cursor=items[-1]["feedback"]["id"] if more else None,
                url="/api/v1/feedback")


@app.get("/api/v1/analytics", response_model=AnalyticsResource)
def get_analytics(
    p: Read,
    period: Literal["7d", "30d", "all"] = "7d",
    source: Literal["openai", "demo", "all"] = "openai",
):
    return reporting.analytics(p.tenant_id, period, source, "feedback:read" in p.scopes)


@app.get("/api/v1/knowledge", response_model=knowledge.Catalog)
def knowledge_catalog(p: SkillsRead):
    return knowledge.catalog(p.tenant_id, "skills:write" in p.scopes)


@app.get("/api/v1/knowledge/{document_id}", response_model=knowledge.Detail)
def knowledge_detail(document_id: str, p: SkillsRead):
    return knowledge.detail(p.tenant_id, document_id)


@app.post("/api/v1/knowledge/{document_id}/drafts", response_model=knowledge.Draft, status_code=201)
def save_knowledge_draft(document_id: str, payload: knowledge.DraftInput, p: SkillsWrite,
                         read_access: SkillsRead, idempotency_key: Key, version: Version):
    saved, created = knowledge.save(p.tenant_id, document_id, payload, idempotency_key, version)
    return respond(saved, not created)


@app.get("/api/v1/knowledge/{document_id}/drafts/{revision}/export", response_model=knowledge.DraftExport)
def export_knowledge_draft(document_id: str, revision: Annotated[int, PathParam(ge=1)], p: SkillsRead):
    return knowledge.export_draft(p.tenant_id, document_id, revision)


@app.get("/api/v1/playground", response_model=playground.PlaygroundCatalog)
def playground_catalog(p: SkillsRead):
    return playground.catalog(p.tenant_id)


@app.post("/api/v1/playground/runs", response_model=playground.PlaygroundRun, status_code=202)
def create_playground_run(payload: playground.PlaygroundRunInput, p: SkillsWrite, read_access: SkillsRead,
                          idempotency_key: Key, version: Version):
    saved, created = playground.create_run(p.tenant_id, payload, idempotency_key, version)
    return respond(saved, not created)


@app.get("/api/v1/playground/runs/{run_id}", response_model=playground.PlaygroundRun)
def read_playground_run(run_id: str, p: SkillsRead):
    return playground.read_run(p.tenant_id, run_id)


class BuiltUI(StaticFiles):
    """Serve the built UI with cache headers that match how Vite names its output.

    index.html names the content-hashed bundles, so a cached copy pins the browser to
    a build that no longer exists: the server updates and the page does not. It must be
    revalidated every load. The hashed assets beside it can never change under a given
    name, so they are cached indefinitely.
    """

    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        if response.status_code < 400:
            immutable = path.startswith("assets/") and not path.endswith(".html")
            response.headers["Cache-Control"] = (
                "public, max-age=31536000, immutable" if immutable else "no-cache"
            )
        return response


DIST = ROOT / "frontend/dist"
if DIST.exists():
    app.mount("/", BuiltUI(directory=DIST, html=True), name="ui")

# Publish authorization requirements in the live OpenAPI document as well as prose.
for route in app.routes:
    path = getattr(route, "path", "")
    if not path.startswith("/api/v1/") or path.endswith("/health"):
        continue
    methods = getattr(route, "methods", set())
    family = "feedback" if "/feedback" in path else "reviews"
    scope = (
        "reviews:read"
        if path == "/api/v1/diagnostics/openai"
        else family + (":write" if "POST" in methods else ":read")
    )
    route.openapi_extra = {"x-required-scope": scope}
    route.description = f"Required scope in api_key mode: {scope}."
    if path == "/api/v1/feedback":
        route.openapi_extra = {"x-required-scopes": ["feedback:read", "reviews:read"]}
        route.description = "Requires feedback:read and reviews:read. Newest-first tenant feedback with bounded report context."
    if path.startswith("/api/v1/knowledge"):
        rights = ["skills:read", "skills:write"] if "POST" in methods else ["skills:read"]
        route.openapi_extra = {"x-required-scopes": rights}
        route.description = "Requires " + " and ".join(rights) + ". Draft editing only; installed model instructions remain unchanged."
    if path.startswith("/api/v1/playground"):
        rights = ["skills:read", "skills:write"] if "POST" in methods else ["skills:read"]
        route.openapi_extra = {"x-required-scopes": rights}
        route.description = ("Requires " + " and ".join(rights) + ". Isolated test runs against the "
                             "published pack. Playground output is never a review and never enters "
                             "review history, feedback, analytics or outcomes.")
    route.description += (
        " Scope requirements apply in api_key mode. Local mode permits Vesta-only loopback access."
        " Explicit public mode permits unauthenticated remote access to the shared Vesta tenant"
        " with all scopes."
    )
