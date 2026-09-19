"""Tenant skill workspaces: a named draft of a whole pack that runs but never serves live QA.

A workspace pins the published pack it forked from. When live moves past that pin the workspace
is out of date: its stored diffs no longer describe what publishing would produce, so it cannot
be submitted until it is explicitly rebased.
"""

from __future__ import annotations

import re
import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from . import knowledge, packs, skill_runtime, store
from .access import AccessError, tenants
from .content import profile

NAME = re.compile(r"^[\w][\w .'()/-]{0,79}$")


class WorkspaceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=80)

    @field_validator("name")
    @classmethod
    def meaningful(cls, value):
        if not value.strip() or not NAME.fullmatch(value.strip()):
            raise ValueError("Provide a short workspace name.")
        return value.strip()


class Workspace(BaseModel):
    object: Literal["qa_skill_workspace"] = "qa_skill_workspace"
    workspace_id: str
    name: str
    status: Literal["open", "submitted", "published", "closed"]
    created_at: str
    forked_release: str
    forked_content_sha256: str
    submitted_at: str | None = None
    summary: str | None = None
    out_of_date: bool = False
    drafted_documents: int = 0


def identifier(name: str) -> str:
    """A readable, bounded workspace id derived from the name plus a short unique suffix."""
    stem = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "workspace"
    return f"{stem}-{uuid.uuid4().hex[:8]}"


def published_pack(tenant: str) -> dict:
    """The verified published snapshot this tenant's workspaces fork from."""
    return knowledge.sources(tenant)[0]


def row_to_model(row, current_sha256: str, drafted: int) -> Workspace:
    return Workspace(
        workspace_id=row["id"],
        name=row["name"],
        status=row["status"],
        created_at=row["created_at"],
        forked_release=row["forked_release"],
        forked_content_sha256=row["forked_content_sha256"],
        submitted_at=row["submitted_at"],
        summary=row["summary"],
        out_of_date=row["forked_content_sha256"] != current_sha256,
        drafted_documents=drafted,
    )


def counts(conn, tenant: str) -> dict[str, int]:
    rows = conn.execute(
        "SELECT workspace_id, COUNT(DISTINCT document_id) AS n FROM knowledge_drafts"
        " WHERE tenant_id=? AND workspace_id<>'' GROUP BY workspace_id",
        (tenant,),
    ).fetchall()
    return {row["workspace_id"]: row["n"] for row in rows}


def listing(tenant: str) -> list[Workspace]:
    snapshot = published_pack(tenant)
    with store.db() as conn:
        conn.execute("BEGIN")
        drafted = counts(conn, tenant)
        rows = conn.execute(
            "SELECT * FROM skill_workspaces WHERE tenant_id=? ORDER BY created_at DESC, id",
            (tenant,),
        ).fetchall()
    return [row_to_model(row, snapshot["content_sha256"], drafted.get(row["id"], 0)) for row in rows]


def record(conn, tenant: str, workspace_id: str):
    row = conn.execute(
        "SELECT * FROM skill_workspaces WHERE tenant_id=? AND id=?", (tenant, workspace_id)
    ).fetchone()
    if row is None:
        raise AccessError(404, "WORKSPACE_NOT_FOUND", "Skill workspace not found.")
    return row


def get(tenant: str, workspace_id: str) -> Workspace:
    snapshot = published_pack(tenant)
    with store.db() as conn:
        conn.execute("BEGIN")
        row = record(conn, tenant, workspace_id)
        drafted = counts(conn, tenant).get(workspace_id, 0)
    return row_to_model(row, snapshot["content_sha256"], drafted)


def create(tenant: str, payload: WorkspaceInput, key: str, version: str):
    operation = "POST /api/v1/workspaces"
    data = payload.model_dump()
    with store.db() as conn:
        saved = store.replay_in(conn, tenant, operation, key, data, version)
        if saved:
            return saved, False
    snapshot = published_pack(tenant)
    with store.db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        saved = store.replay_in(conn, tenant, operation, key, data, version)
        if saved:
            return saved, False
        workspace_id = identifier(payload.name)
        created = store.now()
        conn.execute(
            "INSERT INTO skill_workspaces(tenant_id,id,name,created_at,status,forked_release,forked_content_sha256)"
            " VALUES(?,?,?,?,'open',?,?)",
            (tenant, workspace_id, payload.name, created, snapshot["release_id"], snapshot["content_sha256"]),
        )
        value = Workspace(
            workspace_id=workspace_id, name=payload.name, status="open", created_at=created,
            forked_release=snapshot["release_id"], forked_content_sha256=snapshot["content_sha256"],
        )
        saved = store.receipt(201, value.model_dump())
        store.remember(conn, tenant, operation, key, data, version, saved)
        return saved, True


def editable_paths(docs: dict) -> dict[str, str]:
    """Document ids that may be drafted into a pack, mapped to the package path they replace.

    Frozen references, the pinned source wording and tenant guidance are excluded: they are not
    skill instructions, so a workspace cannot compose them.
    """
    return {
        key: doc["source_path"]
        for key, doc in docs.items()
        if doc["kind"] == "skill" and doc["source_path"]
    }


def compose(tenant: str, workspace_id: str) -> dict:
    """Compose this workspace's draft pack. Never reachable from live report QA."""
    snapshot, docs = knowledge.sources(tenant)
    with store.db() as conn:
        conn.execute("BEGIN")
        row = record(conn, tenant, workspace_id)
        overlay = packs.overlay(conn, tenant, workspace_id, editable_paths(docs))
    if not overlay:
        raise AccessError(
            409,
            "WORKSPACE_UNCHANGED",
            "This workspace matches the published pack. Edit a skill before running.",
        )
    if row["forked_content_sha256"] != snapshot["content_sha256"]:
        raise AccessError(
            409,
            "WORKSPACE_OUT_OF_DATE",
            "The published pack moved since this workspace was created. Rebase the workspace before running.",
        )
    name = profile(tenant, tenants()[tenant])[0]
    return skill_runtime.load_snapshot(
        profile=name, pack=packs.PackRef("draft", workspace_id), overlay=overlay
    )


def rebase(tenant: str, workspace_id: str) -> Workspace:
    """Re-point a workspace at the current published pack, keeping every saved revision.

    Saved revisions and past runs are kept: every run carries the pack hash it was composed
    against, so a run made before the rebase identifies itself as a superseded composition
    rather than needing to be deleted. A submitted workspace returns to open, because the gate
    would otherwise run against a pack the reviewer never saw.
    """
    snapshot = published_pack(tenant)
    with store.db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = record(conn, tenant, workspace_id)
        if row["status"] in ("published", "closed"):
            raise AccessError(409, "WORKSPACE_CLOSED", "This workspace is no longer editable.")
        conn.execute(
            "UPDATE skill_workspaces SET forked_release=?, forked_content_sha256=?, status='open',"
            " submitted_at=NULL, summary=NULL WHERE tenant_id=? AND id=?",
            (snapshot["release_id"], snapshot["content_sha256"], tenant, workspace_id),
        )
        drafted = counts(conn, tenant).get(workspace_id, 0)
        row = record(conn, tenant, workspace_id)
    return row_to_model(row, snapshot["content_sha256"], drafted)
