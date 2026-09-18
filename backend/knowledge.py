"""Installed instruction catalog and tenant-scoped editorial drafts.

Drafts are data, never imported, executed, or selected by the review runtime.
"""
import difflib
import hashlib
import json
import os
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from . import store, skill_runtime
from .access import AccessError, tenants


class DraftInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=0)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    package_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    content: str = Field(min_length=1, max_length=100000)
    change_note: str = Field(min_length=1, max_length=1000)

    @field_validator("content", "change_note")
    @classmethod
    def meaningful(cls, value):
        if not value.strip() or "\x00" in value:
            raise ValueError("Provide non-blank text without null characters.")
        return value


class Draft(BaseModel):
    draft_id: str
    document_id: str
    revision: int
    content: str
    content_sha256: str
    source_sha256: str
    package_sha256: str
    change_note: str
    created_at: str
    status: Literal["draft_not_active"] = "draft_not_active"


class Document(BaseModel):
    document_id: str
    title: str
    kind: Literal["skill", "reference", "guidance", "catalog", "policy_source"]
    description: str
    source_path: str | None
    version: str
    source_sha256: str
    stages: list[str]
    used_by: list[str]
    runtime_use: Literal["model_instruction", "host_reference", "not_configured"]
    latest_revision: int = 0
    has_changes: bool = False
    source_changed: bool = False


class Catalog(BaseModel):
    object: Literal["qa_knowledge_catalog"] = "qa_knowledge_catalog"
    package_version: str
    package_sha256: str
    can_edit: bool
    items: list[Document]


class Detail(BaseModel):
    document: Document
    package_sha256: str
    installed_content: str
    draft: Draft | None
    saved_diff: str
    recent_revisions: list[Draft]
    history_truncated: bool


class DraftExport(BaseModel):
    object: Literal["qa_knowledge_draft_export"] = "qa_knowledge_draft_export"
    format_version: Literal[1] = 1
    tenant_id: str
    draft: Draft
    activation: str


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def installed(tenant):
    root = Path(os.environ.get("QA_SKILL_PACKAGE_DIR", str(skill_runtime.ROOT)))
    from .content import binding
    snapshot = skill_runtime.load_snapshot(root, release_id=binding(tenant, tenants()[tenant]))
    content_root = (root / "clinical-content").resolve()
    inventory = json.loads((content_root / "MANIFEST.json").read_text(encoding="utf-8"))["files"]
    hashes = {row["path"]: row["sha256"] for row in inventory}

    def read(relative):
        path = (content_root / relative).resolve()
        if not path.is_relative_to(content_root) or relative not in hashes:
            raise ValueError("Invalid catalog path")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != hashes[relative]:
            raise ValueError("Installed content changed during catalog capture")
        return raw.decode("utf-8")

    registry = json.loads(read("registry.json"))
    docs = {}
    for filename in registry["skills"]:
        skill = json.loads(read(filename))
        name = skill["name"]
        stages = [stage for stage, names in registry["stages"].items() if name in names]
        key = "skill_" + name
        docs[key] = dict(document_id=key, title=name, kind="skill", description=skill["description"],
                         source_path=skill["instruction"], version=skill["version"],
                         content=read(skill["instruction"]), stages=stages, used_by=[name],
                         runtime_use="model_instruction" if stages else "host_reference")
        for ref in skill["references"]:
            if ref["path"] not in snapshot["reference_hashes"]:
                continue
            key = "reference_" + Path(ref["path"]).stem
            if key not in docs:
                docs[key] = dict(document_id=key, title=Path(ref["path"]).stem.replace("-", " ").capitalize(),
                                 kind={"draft_catalog": "catalog", "source_wording": "policy_source"}.get(ref["authority"], "reference"), description="Supporting source or proposed guidance; clinical approval is not established.",
                                 source_path=ref["path"], version=registry["content_version"], content=read(ref["path"]),
                                 stages=[], used_by=[], runtime_use="model_instruction")
            docs[key]["used_by"].append(name)
            docs[key]["stages"] = sorted(set(docs[key]["stages"]) | (set(ref["load_stages"]) & set(stages)))
    entry = tenants()[tenant]
    policy_path = entry.get("policy_path", os.environ.get("QA_POLICY_PATH", "") if tenant == "vesta" else "").strip()
    policy = Path(policy_path).read_text(encoding="utf-8") if policy_path else ""
    if len(policy) > 100000:
        raise ValueError("Supplied guidance exceeds the supported size")
    docs["guidance_tenant"] = dict(document_id="guidance_tenant", title="QA manual / local guidance", kind="guidance",
        description="Tenant-specific manual supplied through backend configuration. It remains unvalidated guidance.",
        source_path=None, version="Configured guidance" if policy else "Not configured", content=policy,
        stages=list(registry["stages"]) if policy else [], used_by=[],
        runtime_use="model_instruction" if policy else "not_configured")
    for doc in docs.values():
        doc["source_sha256"] = digest(doc["content"])
    return snapshot, docs


def sources(tenant):
    try:
        return installed(tenant)
    except (OSError, ValueError, KeyError) as exc:
        raise AccessError(503, "KNOWLEDGE_SOURCE_UNAVAILABLE", "Installed skills or guidance could not be verified. Check service health and backend configuration.") from exc


def head(conn, tenant, key):
    row = conn.execute("SELECT document FROM knowledge_drafts WHERE tenant_id=? AND document_id=? ORDER BY revision DESC LIMIT 1", (tenant, key)).fetchone()
    return json.loads(row[0]) if row else None


def summary(doc, draft, package_hash):
    return Document(**{key: value for key, value in doc.items() if key != "content"},
                    latest_revision=draft["revision"] if draft else 0,
                    has_changes=bool(draft and draft["content_sha256"] != doc["source_sha256"]),
                    source_changed=bool(draft and (draft["source_sha256"] != doc["source_sha256"] or draft["package_sha256"] != package_hash)))


def catalog(tenant, can_edit):
    snapshot, docs = sources(tenant)
    with store.db() as conn:
        conn.execute("BEGIN")
        items = [summary(doc, head(conn, tenant, key), snapshot["content_sha256"]) for key, doc in docs.items()]
    return Catalog(package_version=snapshot["content_version"], package_sha256=snapshot["content_sha256"], can_edit=can_edit, items=items)


def detail(tenant, key):
    snapshot, docs = sources(tenant)
    if key not in docs:
        raise AccessError(404, "KNOWLEDGE_NOT_FOUND", "Knowledge document not found.")
    doc = docs[key]
    with store.db() as conn:
        rows = conn.execute("SELECT document FROM knowledge_drafts WHERE tenant_id=? AND document_id=? ORDER BY revision DESC LIMIT 21", (tenant, key)).fetchall()
    history = [Draft.model_validate_json(row[0]) for row in rows[:20]]
    draft = history[0] if history else None
    diff = "".join(difflib.unified_diff(doc["content"].splitlines(keepends=True), draft.content.splitlines(keepends=True), fromfile="installed", tofile=f"draft-r{draft.revision}")) if draft else ""
    return Detail(document=summary(doc, draft.model_dump() if draft else None, snapshot["content_sha256"]),
                  package_sha256=snapshot["content_sha256"], installed_content=doc["content"],
                  draft=draft, saved_diff=diff, recent_revisions=history, history_truncated=len(rows)>20)


def save(tenant, document_id, payload, key, version):
    operation = f"POST /api/v1/knowledge/{document_id}/drafts"
    data = payload.model_dump()
    # Receipt lookup precedes source verification so accepted work can replay after package drift.
    with store.db() as conn:
        saved = store.replay_in(conn, tenant, operation, key, data, version)
        if saved:
            return saved, False
    snapshot, docs = sources(tenant)
    if document_id not in docs:
        raise AccessError(404, "KNOWLEDGE_NOT_FOUND", "Knowledge document not found.")
    source = docs[document_id]
    if payload.source_sha256 != source["source_sha256"] or payload.package_sha256 != snapshot["content_sha256"]:
        raise AccessError(409, "KNOWLEDGE_SOURCE_CHANGED", "Installed content changed. Reload the document and reconcile your edits before saving.")
    with store.db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        saved = store.replay_in(conn, tenant, operation, key, data, version)
        if saved:
            return saved, False
        previous = head(conn, tenant, document_id)
        revision = previous["revision"] if previous else 0
        if payload.expected_revision != revision:
            raise AccessError(409, "KNOWLEDGE_REVISION_CONFLICT", "A newer draft exists. Reload the document and reconcile your edits before saving.")
        doc = Draft(draft_id=store.new_id("kd"), document_id=document_id, revision=revision+1,
                    content=payload.content, content_sha256=digest(payload.content), source_sha256=source["source_sha256"],
                    package_sha256=snapshot["content_sha256"], change_note=payload.change_note.strip(), created_at=store.now())
        conn.execute("INSERT INTO knowledge_drafts VALUES(?,?,?,?,?)", (tenant, document_id, revision+1, doc.draft_id, store.canonical(doc.model_dump())))
        saved = store.receipt(201, doc.model_dump())
        store.remember(conn, tenant, operation, key, data, version, saved)
        return saved, True


def export_draft(tenant, key, revision):
    with store.db() as conn:
        row = conn.execute("SELECT document FROM knowledge_drafts WHERE tenant_id=? AND document_id=? AND revision=?", (tenant, key, revision)).fetchone()
    if row is None:
        raise AccessError(404, "DRAFT_NOT_FOUND", "Saved draft not found.")
    return {"object": "qa_knowledge_draft_export", "format_version": 1, "tenant_id": tenant,
            "draft": Draft.model_validate_json(row[0]).model_dump(),
            "activation": "Not active. Review and evaluate this proposal through the versioned skill-release process; never apply it to another tenant automatically."}
