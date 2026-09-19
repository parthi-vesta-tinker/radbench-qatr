"""QA Studio playground: run the real review against curated samples, in isolation.

The playground exists so people can learn what report QA does and re-run a fixed corpus,
without any of it becoming a review. It composes the published pack, dispatches the same
combined request as live QA and applies the same validation, then writes only to
`playground_runs`. Nothing here reaches review history, feedback, analytics or outcomes.

Editing instructions is deliberately out of scope for this version.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from . import packs, skill_runtime, store
from .access import AccessError

# Model choices are server controlled. The picker exists so a future release can widen this
# list without a contract change; today exactly one model is offered.
MODELS = ("gpt-6-astra",)

CATEGORIES = (
    dict(
        id="critical_finding",
        title="Critical findings",
        description="Reports containing a critical observation, with and without a documented designation.",
    ),
    dict(
        id="inconsistency",
        title="Findings and impression inconsistency",
        description="Reports where the impression does not follow from the findings.",
    ),
)

# Each category leads with a sample the canned demo path can serve, so the playground is
# usable with no provider configured, followed by richer cases read from the verified
# installed package. Case text stays hash-pinned and is never duplicated here.
SAMPLES = (
    dict(id="critical-documented", category="critical_finding", case=None, demo="critical_documented"),
    dict(id="critical-flagged", category="critical_finding", case="W13", demo=None),
    dict(id="critical-uncertain", category="critical_finding", case="W12", demo=None),
    dict(id="laterality-swap", category="inconsistency", case=None, demo="discrepancy"),
    dict(id="impression-contradiction", category="inconsistency", case="W17", demo=None),
    dict(id="technique-conflict", category="inconsistency", case="W06", demo=None),
)

MAX_REPORT = 40000


class PlaygroundRunInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sample_id: str | None = Field(default=None, max_length=80)
    report_text: str | None = Field(default=None, max_length=MAX_REPORT)
    model: str = Field(max_length=80)

    @field_validator("model")
    @classmethod
    def known_model(cls, value):
        if value not in MODELS:
            raise ValueError("Select a supported playground model.")
        return value


class PlaygroundStep(BaseModel):
    step: str
    status: Literal["queued", "running", "completed", "failed", "needs_input"]
    elapsed_ms: int | None = None


class PlaygroundSample(BaseModel):
    sample_id: str
    category: str
    title: str
    report_text: str
    demo_supported: bool


class PlaygroundCategory(BaseModel):
    id: str
    title: str
    description: str


class PlaygroundCatalog(BaseModel):
    object: Literal["qa_playground_catalog"] = "qa_playground_catalog"
    mode: Literal["demo", "openai"]
    ready: bool
    models: list[str]
    live_model: str | None
    pack_version: str
    pack_release: str
    skills: list[str]
    categories: list[PlaygroundCategory]
    samples: list[PlaygroundSample]
    boundary: str


class PlaygroundRun(BaseModel):
    object: Literal["qa_playground_run"] = "qa_playground_run"
    run_id: str
    release_id: str
    pack_ref: str
    source: Literal["sample", "pasted"]
    sample_id: str | None
    report_text: str
    model: str
    mode: str
    status: Literal["queued", "running", "completed", "needs_input", "failed"]
    created_at: str
    completed_at: str | None
    steps: list[PlaygroundStep]
    result: dict | None
    error: dict | None


BOUNDARY = (
    "Playground output is not a clinical review. It is never stored as a review, never enters "
    "review history, feedback, analytics or stakeholder outcomes, and has no copy actions."
)


def case_reports() -> dict[str, dict]:
    """Report text from the verified installed package, checked against its manifest."""
    root = skill_runtime.package_root() / "clinical-content"
    inventory = {
        row["path"]: row["sha256"]
        for row in json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))["files"]
    }
    import hashlib

    raw = (root / "evaluation/cases.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != inventory["evaluation/cases.json"]:
        raise ValueError("Installed evaluation corpus does not match the package manifest")
    return {case["id"]: case for case in json.loads(raw)["cases"]}


def demo_reports() -> dict[str, dict]:
    from .reviewer import SAMPLES as DEMO

    return {row["id"]: row for row in DEMO}


def samples() -> list[PlaygroundSample]:
    from .reviewer import normalized

    cases, demo = case_reports(), demo_reports()
    # Demo support is computed from the text the canned path actually matches, never declared.
    # A mapping could drift; this cannot claim support the demo path does not provide.
    servable = {normalized(row["report_text"]) for row in demo.values()}
    values = []
    for entry in SAMPLES:
        if entry["case"]:
            case = cases[entry["case"]]
            title, text = case["title"], case["input"]["report_text"]
        else:
            row = demo[entry["demo"]]
            title, text = row["label"], row["report_text"]
        values.append(
            PlaygroundSample(
                sample_id=entry["id"],
                category=entry["category"],
                title=title,
                report_text=text,
                demo_supported=normalized(text) in servable,
            )
        )
    return values


def catalog(tenant: str) -> PlaygroundCatalog:
    from .settings import runtime_config

    try:
        config = runtime_config(tenant)
    except (ValueError, OSError, KeyError) as exc:
        raise AccessError(
            503,
            "PLAYGROUND_UNAVAILABLE",
            "Installed skills or backend configuration could not be verified.",
        ) from exc
    snapshot = config["skill_snapshot"]
    mode = config["mode"]
    ready = mode == "demo" or bool(os.environ.get("OPENAI_API_KEY"))
    return PlaygroundCatalog(
        mode=mode,
        ready=ready,
        models=list(MODELS),
        live_model=config["model"],
        pack_version=snapshot["content_version"],
        pack_release=snapshot["release_id"],
        skills=sorted(config["skill_versions"]),
        categories=[PlaygroundCategory(**row) for row in CATEGORIES],
        samples=samples(),
        boundary=BOUNDARY,
    )


def resolve(payload: PlaygroundRunInput) -> tuple[str, str, str | None]:
    """A run reads one curated sample or one pasted report, never both and never neither."""
    if bool(payload.sample_id) == bool(payload.report_text and payload.report_text.strip()):
        raise AccessError(
            422,
            "PLAYGROUND_INPUT_INVALID",
            "Provide either a sample to run or your own report text.",
        )
    if payload.sample_id:
        found = next((s for s in samples() if s.sample_id == payload.sample_id), None)
        if found is None:
            raise AccessError(404, "PLAYGROUND_SAMPLE_NOT_FOUND", "Unknown playground sample.")
        return "sample", found.report_text, found.sample_id
    return "pasted", payload.report_text, None


def config_for(tenant: str, model: str) -> dict:
    """Live configuration, composing the published pack, with the playground model applied.

    The playground never resolves a draft pack and never edits the live configuration: this
    is a copy with the chosen model and a private attempt table.
    """
    from .settings import runtime_config

    config = dict(runtime_config(tenant))
    packs.require_published(config["skill_snapshot"]["pack_ref"])
    if config["mode"] == "openai":
        config["model"] = model
        config["ready"] = bool(os.environ.get("OPENAI_API_KEY"))
    config["attempt_table"] = "playground_attempts"
    config["playground"] = True
    return config


def to_model(row: dict) -> PlaygroundRun:
    steps = [
        PlaygroundStep(step=item["step"], status=item["status"], elapsed_ms=item.get("elapsed_ms"))
        for item in row["steps"]
    ]
    return PlaygroundRun(**{**row, "steps": steps})


def create_run(tenant: str, payload: PlaygroundRunInput, key: str, version: str):
    from .contracts import ReviewInput, ReviewProblem
    from .workflow import dispatch_playground

    operation = "POST /api/v1/playground/runs"
    data = payload.model_dump()
    with store.db() as conn:
        saved = store.replay_in(conn, tenant, operation, key, data, version)
        if saved:
            return saved, False
    source, report_text, sample_id = resolve(payload)
    try:
        config = config_for(tenant, payload.model)
    except (ValueError, OSError, KeyError) as exc:
        raise AccessError(
            503,
            "PLAYGROUND_UNAVAILABLE",
            "Installed skills or backend configuration could not be verified.",
        ) from exc
    if not config["ready"]:
        raise AccessError(
            503,
            "MODEL_NOT_CONFIGURED",
            "Configure OPENAI_API_KEY before running the playground against a model.",
        )
    ReviewInput.model_validate({"report_text": report_text})
    if config["mode"] == "openai":
        from .combined import input_bound

        try:
            input_bound(config, report_text)
        except ReviewProblem as exc:
            raise AccessError(422, exc.code, exc.message) from None
    snapshot = config["skill_snapshot"]
    run_id = store.new_id("pg")
    row = dict(
        run_id=run_id, pack_ref=snapshot["pack_ref"], release_id=snapshot["release_id"],
        source=source, sample_id=sample_id, report_text=report_text,
        model=config["model"] or "demo", mode=config["mode"], status="queued",
        created_at=store.now(), completed_at=None, steps=store.playground_steps(),
        result=None, error=None,
    )
    with store.db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        saved = store.replay_in(conn, tenant, operation, key, data, version)
        if saved:
            return saved, False
        # The row is built here rather than read back: this transaction is still open, so a
        # second connection would not see the insert.
        conn.execute(
            "INSERT INTO playground_runs(tenant_id,id,pack_ref,release_id,source,sample_id,"
            "report_text,model,mode,created_at,status,steps)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,'queued',?)",
            (tenant, run_id, row["pack_ref"], row["release_id"], source, sample_id,
             report_text, row["model"], row["mode"], row["created_at"],
             store.canonical(row["steps"])),
        )
        saved = store.receipt(202, to_model(row).model_dump())
        store.remember(conn, tenant, operation, key, data, version, saved)
    payload_body = {"report_text": report_text}
    try:
        dispatch_playground(tenant, run_id, payload_body, config)
    except Exception:
        from .diagnostics import record_failure

        store.update_playground(
            tenant, run_id, status="failed",
            error=dict(code="PLAYGROUND_DISPATCH_FAILED",
                       message="The playground run could not be started. Run it again.",
                       retryable=True),
        )
        record_failure("playground.dispatch_failed", RuntimeError("enqueue failed"), tenant=tenant)
    return saved, True


def read_run(tenant: str, run_id: str) -> PlaygroundRun:
    row = store.playground_run(tenant, run_id)
    if row is None:
        raise AccessError(404, "PLAYGROUND_RUN_NOT_FOUND", "Playground run not found.")
    return to_model(row)
