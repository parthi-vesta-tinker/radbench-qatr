"""Safe operational diagnostics. Never include report text, keys or exception messages."""

import logging
import traceback
from datetime import datetime, timezone
from pathlib import Path
from dbos import DBOS
from openai import (
    AsyncOpenAI,
    AuthenticationError,
    PermissionDeniedError,
    NotFoundError,
    RateLimitError,
    APIConnectionError,
    APITimeoutError,
)
from . import store
from .settings import runtime_config

log = logging.getLogger("qa.diagnostics")


def configure_logging():
    logger = logging.getLogger("qa")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def record_failure(event, exc, **context):
    frames = " > ".join(
        f"{Path(f.filename).name}:{f.lineno}:{f.name}"
        for f in traceback.extract_tb(exc.__traceback__)
    )
    log.error(
        "%s error_type=%s context=%s frames=%s",
        event,
        type(exc).__name__,
        context,
        frames,
    )


def config_problem(exc):
    if isinstance(exc, UnicodeError):
        return (
            "CONFIG_ENCODING_ERROR",
            "A configuration or skill file cannot be read as UTF-8. Restore the supplied UTF-8 files.",
        )
    if isinstance(exc, FileNotFoundError):
        return (
            "CONFIG_FILE_MISSING",
            "A configured file is missing. Check QA_POLICY_PATH and QA_SKILL_PACKAGE_DIR, or restore the complete extracted bundle.",
        )
    if isinstance(exc, PermissionError):
        return (
            "CONFIG_PERMISSION_DENIED",
            "The application cannot read a configured file. Check folder permissions.",
        )
    if isinstance(exc, ValueError) and str(exc) == "Package inventory mismatch":
        return (
            "SKILL_INVENTORY_MISMATCH",
            "The skill package inventory does not match. Use the updated Windows-compatible bundle; restore the complete package if files were changed.",
        )
    return (
        "SKILL_CONFIGURATION_INVALID",
        "The skill package or configuration is invalid. Check the backend diagnostic log and restore the pinned release or correct settings.",
    )


def component(status, message, **extra):
    return dict(status=status, message=message, **extra)


def status_report(app, tenant):
    components = {
        "api": component("ok", "API responds."),
        "database": component("unknown", "Not checked."),
        "dbos": component("unknown", "Not checked."),
        "skills": component("unknown", "Not checked."),
        "openai": component("unknown", "Not checked."),
    }
    try:
        with store.db() as conn:
            conn.execute("SELECT 1 FROM reviews LIMIT 1").fetchall()
        components["database"] = component("ok", "Application database is readable.")
    except Exception as exc:
        record_failure("database.status_failed", exc)
        components["database"] = component(
            "error",
            "Application database is unavailable. Check the data directory permissions and backend log.",
        )
    try:
        if not getattr(app.state, "dbos_ready", False):
            raise RuntimeError("DBOS not initialized")
        DBOS.get_workflow_status("qa:diagnostic:checkpoint-read")
        components["dbos"] = component(
            "ok",
            "DBOS initialized; checkpoint store responds. This is not a test review.",
        )
    except Exception as exc:
        record_failure("dbos.status_failed", exc)
        components["dbos"] = component(
            "error",
            "DBOS or its checkpoint store is unavailable. Check the backend log.",
        )
    try:
        config = runtime_config(tenant)
        components["skills"] = component(
            "ok",
            "Skill package integrity verified.",
            version=config["skill_content_version"],
        )
        components["openai"] = (
            component("not_required", "Demo mode; no OpenAI calls.")
            if config["mode"] == "demo"
            else component(
                "configured" if config["ready"] else "not_configured",
                "Key and model configured; connection and inference have not been tested."
                if config["ready"]
                else "Set OPENAI_API_KEY and OPENAI_MODEL, then restart.",
                model=config["model"],
            )
        )
    except Exception as exc:
        record_failure("configuration.status_failed", exc, tenant=tenant)
        code, message = config_problem(exc)
        components["skills"] = component("error", message, code=code)
        components["openai"] = component(
            "unknown", "Configuration failed; OpenAI readiness cannot be determined."
        )
    ready = all(
        v["status"] in ("ok", "configured", "not_required") for v in components.values()
    )
    return dict(
        status="ready" if ready else "not_ready",
        checked_at=datetime.now(timezone.utc).isoformat(),
        components=components,
        readiness_scope="Local prerequisites only; OpenAI inference is not verified.",
    )


async def check_openai(tenant):
    try:
        config = runtime_config(tenant)
    except Exception as exc:
        record_failure("openai.configuration_check_failed", exc, tenant=tenant)
        code, message = config_problem(exc)
        return component("error", message, code=code)
    try:
        if config["mode"] == "demo":
            return component("not_required", "Demo mode; no OpenAI calls.")
        if not config["ready"]:
            return component(
                "not_configured", "Set OPENAI_API_KEY and OPENAI_MODEL, then restart."
            )
        # Explicit metadata-only probe. No report, generation or token charge.
        async with AsyncOpenAI(max_retries=0, timeout=10.0) as client:
            await client.models.retrieve(config["model"])
        return component(
            "accessible",
            "OpenAI authentication and model metadata access succeeded. Inference has not been tested.",
            model=config["model"],
        )
    except Exception as exc:
        record_failure("openai.connection_check_failed", exc, tenant=tenant)
        for cls, code, message in (
            (
                AuthenticationError,
                "OPENAI_AUTHENTICATION_FAILED",
                "OpenAI rejected the API key. Set a valid key and restart.",
            ),
            (
                PermissionDeniedError,
                "OPENAI_PERMISSION_DENIED",
                "The key does not have permission for this request.",
            ),
            (
                NotFoundError,
                "OPENAI_MODEL_UNAVAILABLE",
                "The configured model is unavailable to this key.",
            ),
            (
                RateLimitError,
                "OPENAI_RATE_LIMITED",
                "OpenAI rejected the request due to quota or rate limits. Check account limits.",
            ),
            (
                APITimeoutError,
                "OPENAI_TIMEOUT",
                "OpenAI timed out. Check connectivity and proxy settings.",
            ),
            (
                APIConnectionError,
                "OPENAI_CONNECTION_FAILED",
                "Could not connect to OpenAI. Check internet access, proxy and TLS settings.",
            ),
        ):
            if isinstance(exc, cls):
                return component("error", message, code=code)
        return component(
            "error",
            "OpenAI check failed. Check the backend diagnostic log and retry.",
            code="OPENAI_CHECK_FAILED",
        )
