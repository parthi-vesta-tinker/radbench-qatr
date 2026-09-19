"""Pack references, derived pack identity, and workspace draft composition.

No provider call and no clinical claim: these are controlled storage and composition contracts.
"""
import sqlite3
import uuid

import pytest

from backend import content, knowledge, packs, skill_runtime, store, workspaces
from backend.access import AccessError
from backend.settings import runtime_config

SKILL = "skill_qa-critical-match"
FROZEN = "reference_critical-rules"


@pytest.fixture
def pack_db(monkeypatch, tmp_path):
    monkeypatch.setattr(store, "DATA", tmp_path / "data")
    store.init()
    return tmp_path


def draft_into(tenant, workspace, document_id=SKILL, text="Workspace proposal for the playground."):
    _, docs = knowledge.sources(tenant)
    doc = docs[document_id]
    payload = knowledge.DraftInput(
        expected_revision=0,
        source_sha256=doc["source_sha256"],
        package_sha256=knowledge.sources(tenant)[0]["content_sha256"],
        content=doc["content"] + "\n" + text + "\n",
        change_note="Controlled composition test.",
    )
    return knowledge.save(tenant, document_id, payload, uuid.uuid4().hex, "2026-09-18", workspace)


def make_workspace(tenant="vesta", name="Terminology tightening"):
    receipt, created = workspaces.create(tenant, workspaces.WorkspaceInput(name=name), uuid.uuid4().hex, "2026-09-18")
    assert created and receipt["status"] == 201
    return receipt["body"]["workspace_id"]


def test_pack_reference_parses_and_stamps():
    assert str(packs.parse(None)) == str(packs.parse("published")) == "published"
    ref = packs.parse("draft:terminology-abc123")
    assert ref.is_draft and ref.workspace_id == "terminology-abc123"
    assert str(ref) == "draft:terminology-abc123"
    assert ref.stamp("a" * 64) == "draft:terminology-abc123@" + "a" * 64
    assert packs.parse("published").stamp("a" * 64) == ""
    for bad in ("draft:", "draft:Not Valid", "draft:-leading", "drafts:x", "", "published "):
        with pytest.raises(packs.PackError):
            packs.parse(bad)


def test_live_review_refuses_a_draft_pack():
    assert packs.require_published("published").kind == "published"
    with pytest.raises(packs.PackError):
        packs.require_published("draft:anything")
    # Live QA composes the published pack and stamps it with a release, never a draft.
    config = runtime_config("vesta")
    assert config["skill_snapshot"]["pack_ref"] == "published"
    assert config["skill_release"] == content.binding("vesta", {})
    assert not config["skill_release"].startswith("draft:")


def test_pack_version_comes_from_the_pack_not_the_code():
    version = skill_runtime.installed_version()
    assert content.binding("vesta", {}) == content.release_id(content.VESTA_PROFILE, version)
    assert content.binding("other", {}) == content.release_id(content.GENERIC_PROFILE, version)
    assert runtime_config("vesta")["prompt_version"] == f"qa-skills-{version}-combined-1"
    # A configured pin is honoured only when the installed pack actually carries that version.
    assert content.profile("vesta", {"skill_release": f"vesta-qatr-{version}"}) == ("vesta-qatr", version)
    with pytest.raises(ValueError):
        content.binding("vesta", {"skill_release": "vesta-qatr-0.0.1"})


def test_workspace_draft_composes_and_is_stamped(pack_db):
    workspace = make_workspace()
    published = skill_runtime.load_snapshot(profile=content.VESTA_PROFILE)
    draft_into("vesta", workspace)
    snapshot = workspaces.compose("vesta", workspace)
    assert snapshot["release_id"] == f"draft:{workspace}@{snapshot['pack_sha256']}"
    assert snapshot["pack_ref"] == f"draft:{workspace}"
    assert snapshot["forked_from"] == published["release_id"]
    assert "Workspace proposal for the playground." in snapshot["combined_content"]
    assert "Workspace proposal for the playground." not in published["combined_content"]
    assert snapshot["pack_sha256"] != published["pack_sha256"]
    # Composing a draft leaves the published pack and live configuration untouched.
    assert skill_runtime.load_snapshot(profile=content.VESTA_PROFILE)["pack_sha256"] == published["pack_sha256"]
    assert runtime_config("vesta")["skill_snapshot"]["pack_ref"] == "published"


def test_editorial_drafts_outside_a_workspace_never_compose(pack_db):
    workspace = make_workspace()
    draft_into("vesta", packs.NO_WORKSPACE)
    with pytest.raises(AccessError) as exc:
        workspaces.compose("vesta", workspace)
    assert exc.value.code == "WORKSPACE_UNCHANGED"
    assert knowledge.detail("vesta", SKILL).draft.revision == 1
    assert knowledge.detail("vesta", SKILL, workspace).draft is None


def test_unmodified_workspace_cannot_dispatch(pack_db):
    workspace = make_workspace()
    with pytest.raises(AccessError) as exc:
        workspaces.compose("vesta", workspace)
    assert exc.value.code == "WORKSPACE_UNCHANGED"
    with pytest.raises(packs.PackError):
        skill_runtime.load_snapshot(pack=f"draft:{workspace}", overlay={})


def test_frozen_content_cannot_be_drafted_into_a_pack(pack_db):
    workspace = make_workspace()
    draft_into("vesta", workspace, FROZEN, "MUST NEVER COMPOSE")
    with pytest.raises(packs.PackError):
        workspaces.compose("vesta", workspace)
    _, docs = knowledge.sources("vesta")
    assert FROZEN not in workspaces.editable_paths(docs)
    with pytest.raises(packs.PackError):
        skill_runtime.load_snapshot(
            pack=f"draft:{workspace}", overlay={"references/critical-rules.json": "{}"}
        )
    assert "MUST NEVER COMPOSE" not in runtime_config("vesta")["combined_instructions"]


def test_out_of_date_workspace_refuses_until_rebased(pack_db):
    workspace = make_workspace()
    draft_into("vesta", workspace)
    assert workspaces.get("vesta", workspace).out_of_date is False
    with store.db() as conn:
        conn.execute(
            "UPDATE skill_workspaces SET forked_content_sha256=? WHERE tenant_id='vesta' AND id=?",
            ("0" * 64, workspace),
        )
    assert workspaces.get("vesta", workspace).out_of_date is True
    with pytest.raises(AccessError) as exc:
        workspaces.compose("vesta", workspace)
    assert exc.value.code == "WORKSPACE_OUT_OF_DATE"
    rebased = workspaces.rebase("vesta", workspace)
    assert rebased.out_of_date is False and rebased.status == "open"
    # Rebase preserves every saved revision and composes again.
    assert knowledge.detail("vesta", SKILL, workspace).draft.revision == 1
    composed = workspaces.compose("vesta", workspace)
    assert composed["pack_ref"] == f"draft:{workspace}"
    assert composed["release_id"].startswith(f"draft:{workspace}@")


def test_workspaces_and_their_drafts_are_tenant_scoped(pack_db, monkeypatch, tmp_path):
    config = tmp_path / "tenants.json"
    config.write_text('{"vesta": {}, "other": {}}')
    monkeypatch.setenv("QA_TENANTS_FILE", str(config))
    store.init()
    workspace = make_workspace()
    draft_into("vesta", workspace)
    assert [w.workspace_id for w in workspaces.listing("vesta")] == [workspace]
    assert workspaces.listing("other") == []
    with pytest.raises(AccessError) as exc:
        workspaces.get("other", workspace)
    assert exc.value.code == "WORKSPACE_NOT_FOUND"


def test_draft_snapshots_are_never_reachable_from_a_live_review(pack_db):
    """A composed draft pack carries a stamp no live configuration can produce."""
    workspace = make_workspace()
    draft_into("vesta", workspace)
    stamp = workspaces.compose("vesta", workspace)["release_id"]
    assert stamp.startswith("draft:") and "@" in stamp
    live = runtime_config("vesta")
    assert live["skill_release"] != stamp
    assert not live["skill_release"].startswith("draft:")
    assert live["skill_snapshot"]["pack_ref"] == "published"
    with store.db() as conn:
        for table in ("review_records", "review_results", "observations", "playground_runs"):
            assert conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0
