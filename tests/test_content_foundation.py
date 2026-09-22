"""F2 source, isolation and attribution contracts; no clinical or paid evaluation."""
import copy
import hashlib
import json
import uuid

import pytest

from backend import content, knowledge, skill_runtime, store
from backend.contracts import ReviewInput, ReviewProblem
from backend.settings import runtime_config


def test_exact_upstream_inventory_and_complete_composition():
    snap = skill_runtime.load_snapshot(profile=content.VESTA_PROFILE)
    root = skill_runtime.ROOT / "clinical-content/references"
    raw = {name: (root / name).read_bytes() for name in content.SOURCE_FILES}
    catalog = content.validate_catalog(raw)
    assert len(catalog["rules"]) == 43
    prompt = content.combined_instructions(snap)
    for name, data in raw.items():
        assert prompt.count(data.decode()) == 1
        assert snap["reference_hashes"]["references/" + name] == hashlib.sha256(data).hexdigest()
    assert prompt.count("name: qa-final-verification\n") == 1
    assert "name: qa-input-adequacy\n" not in prompt
    assert "SOURCE.md" not in prompt and "## 0.3.0" not in prompt
    generic = skill_runtime.load_snapshot()
    assert generic["catalog"] is None
    assert "VESTA-CR-043" not in content.combined_instructions(generic)
    assert generic["snapshot_sha256"] != snap["snapshot_sha256"]
    broken = dict(raw)
    broken["critical-rules.json"] = raw["critical-rules.json"].replace(b"Tension Pneumothorax", b"Pneumothorax")
    with pytest.raises(ValueError, match="Pinned"):
        content.validate_catalog(broken)


def test_catalog_attribution_and_exception_anchors():
    snap = skill_runtime.load_snapshot(profile=content.VESTA_PROFILE)
    report = "Findings: Known unchanged pulmonary embolism.\nImpression: Pulmonary embolism."
    rule = snap["catalog"]["rules"][25]
    assert rule["source_label"] == "Pulmonary Embolism"
    candidate = dict(candidate_id="one", check_id="qa-critical-match", issue_code="CRIT",
        finding_type="suggestion", comment="Please review the reported pulmonary embolism.",
        anchors=[dict(section_id="findings-1", quote="Known unchanged pulmonary embolism.")],
        basis="Synthetic attribution contract fixture, not a clinical conclusion.", requirement_ref=None,
        critical_basis=dict(assessment="catalog_match", assertion_support="explicit_diagnosis",
            policy_id=snap["catalog"]["catalog_id"], rule_id=rule["id"], source_quote=rule["source_label"],
            exception_anchors=[dict(section_id="findings-1", quote="Known unchanged")]))
    def adapt(c, snapshot=snap):
        return skill_runtime.adapt(skill_runtime.SkillStageOutput(stage="critical_finding_review",
            input_problem=None, observations=[c], designation=dict(status="unknown", anchor=None)),
            "critical_finding_review", report, snapshot)
    public, private = adapt(candidate)
    assert private[0]["critical_basis"]["rule_id"] == "VESTA-CR-026"
    assert "critical_basis" not in public["observations"][0]
    for change in [dict(rule_id="VESTA-CR-999"), dict(source_quote="Acute Pulmonary Embolism"),
                   dict(policy_id="other"), dict(exception_anchors=[dict(section_id="findings-1", quote="Doctor decided no call")])]:
        bad = copy.deepcopy(candidate); bad["critical_basis"].update(change)
        with pytest.raises(ReviewProblem): adapt(bad)
    with pytest.raises(ReviewProblem): adapt(candidate, skill_runtime.load_snapshot())
    bad = copy.deepcopy(candidate); bad["check_id"] = "qa-terminology-errors"
    with pytest.raises(ReviewProblem): adapt(bad)


def test_tenant_binding_draft_isolation_and_captured_release(client, monkeypatch, tmp_path):
    tenants = tmp_path / "tenants.json"
    vesta_release, generic_release = content.binding("vesta", {}), content.binding("other", {})
    tenants.write_text(json.dumps({"vesta": {"skill_release":vesta_release},
                                  "other": {"skill_release":content.GENERIC_PROFILE}}))
    monkeypatch.setenv("QA_TENANTS_FILE", str(tenants))
    monkeypatch.setattr(store, "DATA", tmp_path / "db")
    store.init()
    cfg = runtime_config("vesta")
    other = runtime_config("other")
    assert "VESTA-CR-043" in cfg["combined_instructions"]
    assert "VESTA-CR-043" not in other["combined_instructions"]
    key = "reference_critical-rules"
    detail = knowledge.detail("vesta", key)
    assert detail.document.kind == "catalog"
    payload = knowledge.DraftInput(expected_revision=0, source_sha256=detail.document.source_sha256,
        package_sha256=detail.package_sha256, content="DRAFT MUST NEVER ENTER PROMPT", change_note="Test isolation")
    knowledge.save("vesta", key, payload, uuid.uuid4().hex, "2026-09-22")
    assert runtime_config("vesta") == cfg
    with pytest.raises(Exception) as exc: knowledge.detail("other", key)
    assert exc.value.code == "KNOWLEDGE_NOT_FOUND"
    receipt, _ = store.reserve("vesta", uuid.uuid4().hex,
        ReviewInput(report_text="Findings: Clear lungs.\nImpression: No acute disease."), cfg)
    rid = receipt["body"]["id"]
    tenants.write_text(json.dumps({"vesta":{"skill_release":content.GENERIC_PROFILE},"other":{}}))
    assert runtime_config("vesta")["skill_release"] == generic_release
    assert store.job("vesta", rid)[1] == dict(cfg, input_version=1)
    with store.db() as conn:
        assert conn.execute("SELECT active_release FROM tenants WHERE id='vesta'").fetchone()[0] == vesta_release


def test_complete_request_context_bounds():
    snap = skill_runtime.load_snapshot(profile=content.VESTA_PROFILE)
    prompt = content.combined_instructions(snap)
    assert content.check_request_bound(prompt, "Report", output_tokens=6000) > 60000
    with pytest.raises(ReviewProblem) as exc:
        content.check_request_bound(prompt, "Report", output_tokens=6000, context_limit=20000)
    assert exc.value.code == "REVIEW_CONTEXT_TOO_LARGE"
    with pytest.raises(ValueError): content.binding("other", {"skill_release":"unknown"})
    with pytest.raises(ValueError): content.binding("other", {"skill_release":"generic-9.9.9"})
    assert content.binding("other", {}) == content.release_id(
        content.GENERIC_PROFILE, skill_runtime.installed_version())


def test_catalog_fixture_relationships_and_qualifier_guidance():
    snap = skill_runtime.load_snapshot(profile=content.VESTA_PROFILE)
    cases = json.loads((skill_runtime.ROOT / "clinical-content/evaluation/catalog-cases.json").read_text())
    assert cases["status"] == "proposed_not_adjudicated"
    assert {c["partition"] for c in cases["cases"]} == {"development", "held_out"}
    rules = {r["id"]: r["source_label"] for r in snap["catalog"]["rules"]}
    for case in cases["cases"]:
        assert rules[case["source_rule"]] == case["source_label"]
    prompt = content.combined_instructions(snap)
    assert 'A keyword does not reveal the doctor' in prompt
    assert 'Entries written **without** a qualifier must not be narrowed by one.' in prompt
