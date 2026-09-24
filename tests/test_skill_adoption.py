"""Skill integration invariants. Synthetic candidate payloads are not model evaluation."""

import copy
import json
import shutil
import uuid
import pytest
from backend import store, presentation, skill_runtime
from backend.contracts import ReviewInput, ReviewProblem, parse_sections, section_index
from backend.settings import runtime_config
from test_api import post, finish

RICH = "History:\nCough.\nTechnique:\nTwo views.\nComparison:\nPrior study.\nFindings\nLungs are clear.\nImpression\nNo acute abnormality.\nAddendum:\nClinical history corrected to fever."


def candidate():
    return dict(
        stage="language_review",
        input_problem=None,
        designation=None,
        observations=[
            dict(
                candidate_id="c1",
                check_id="qa-terminology-errors",
                issue_code="TYPO",
                finding_type="suggestion",
                comment="History: please correct the spelling.",
                anchors=[dict(section_id="history-1", quote="Cough.")],
                basis="Synthetic grounding test.",
                critical_basis=None,
                requirement_ref=None,
            )
        ],
    )


def test_rich_sections_and_no_silent_merging():
    assert parse_sections(RICH)["impression"] == "No acute abnormality."
    ix = section_index(RICH)
    assert [s["kind"] for s in ix] == [
        "history",
        "technique",
        "comparison",
        "findings",
        "impression",
        "addendum",
    ]
    assert (
        RICH[ix[-1]["start"] : ix[-1]["end"]].strip()
        == "Clinical history corrected to fever."
    )
    with pytest.raises(ReviewProblem):
        parse_sections(RICH + "\nFindings: A second study. Impression: Second study.")
    with pytest.raises(ReviewProblem):
        parse_sections("Findings:\n\nImpression: No acute abnormality.")


def test_composition_integrity_and_stage_ownership(tmp_path):
    snapshot = skill_runtime.load_snapshot()
    assert "qa-critical-match" not in snapshot["owners"]["language_review"]
    assert "qa-internal-consistency" in snapshot["owners"]["consistency_review"]
    root = tmp_path / "package"
    shutil.copytree(skill_runtime.ROOT, root)
    (root / "clinical-content/references/critical-boundaries.md").write_text("drift")
    with pytest.raises(ValueError):
        skill_runtime.load_snapshot(root)


def test_private_grounding_and_rich_public_projection():
    snap = skill_runtime.load_snapshot()
    data = candidate()
    # Use the exact declared issue code, independently check location and scope.
    data["observations"][0]["issue_code"] = snap["owners"]["language_review"][
        "qa-terminology-errors"
    ][0]
    public, private = skill_runtime.adapt(
        skill_runtime.SkillStageOutput(**data), "language_review", RICH, snap
    )
    assert public["observations"][0]["report_section"] == "history"
    a = private[0]["grounded_anchors"][0]
    assert RICH[a["start"] : a["end"]] == "Cough."
    for mutate in ("quote", "owner", "policy", "critical", "duplicate"):
        bad = copy.deepcopy(data)
        c = bad["observations"][0]
        if mutate == "quote":
            c["anchors"][0]["quote"] = "Fabricated quote"
        if mutate == "owner":
            c["check_id"] = "qa-critical-match"
        if mutate == "policy":
            c["requirement_ref"] = {"policy_id": "invented", "rule_id": "invented"}
        if mutate == "critical":
            c["critical_basis"] = {
                "assessment": "generic_provisional",
                "assertion_support": "explicit_diagnosis",
                "policy_id": None,
                "rule_id": None,
            }
        if mutate == "duplicate":
            bad["observations"].append(copy.deepcopy(c))
        with pytest.raises(ReviewProblem):
            skill_runtime.adapt(
                skill_runtime.SkillStageOutput(**bad), "language_review", RICH, snap
            )


def test_acceptance_pins_bytes_and_replay_bypasses_changed_loader(client, monkeypatch):
    key = uuid.uuid4().hex
    a = post(client, key=key)
    d = finish(client, a)
    cfg = store.job("vesta", d["id"])[1]
    assert cfg["stage_instructions"]["language_review"]
    before = json.dumps(cfg, sort_keys=True)
    monkeypatch.setattr(
        skill_runtime,
        "load_snapshot",
        lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("drift")),
    )
    assert post(client, key=key).content == a.content
    failure = post(client)
    assert (
        failure.status_code == 503
        and failure.json()["error"]["code"] == "SKILL_CONFIGURATION_INVALID"
    )
    assert json.dumps(store.job("vesta", d["id"])[1], sort_keys=True) == before
    assert "stage_instructions" not in json.dumps(d)
    assert 'skill_snapshot"' not in json.dumps(d)


def test_single_api_version_rejects_old_projection(client):
    for version in ("2026-09-14", "2026-09-15"):
        response = client.get("/api/v1/config", headers={"QA-Version": version})
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "UNSUPPORTED_API_VERSION"
    from backend.main import api_version
    assert api_version() == presentation.API_VERSION
    record = store.get("vesta", finish(client, post(client))["id"])
    record["result"]["general_comments"][0]["report_section"] = "history"
    assert presentation.review(record)["result"]["general_comments"][0]["report_section"] == "history"


def test_two_copy_groups_match_result_and_hide_internal_mapping(client):
    d = finish(client, post(client))
    r = d["result"]
    assert (
        "PACS comments:" in r["general_copy_text"]
        and "Critical Findings" not in r["general_copy_text"]
    )
    assert (
        "PACS comments" not in r["critical_copy_text"]
        and "Cannot determine" in r["critical_copy_text"]
    )
    assert "_candidate_mapping" not in r
    clean = finish(client, post(client, sample="clean"))["result"]
    assert (
        clean["general_copy_text"]
        == clean["critical_copy_text"]
        == clean["copy_text"]
        == ""
    )


def test_context_limit_rejects_before_acceptance_without_consuming_key(
    client, monkeypatch, tmp_path
):
    monkeypatch.setenv("QA_MODE", "openai")
    monkeypatch.setenv("OPENAI_MODEL", "controlled-no-network")
    monkeypatch.setenv("OPENAI_API_KEY", "controlled-no-network")
    policy = tmp_path / "guidance.md"
    policy.write_text("Guidance. " * 9500)
    monkeypatch.setenv("QA_POLICY_PATH", str(policy))
    key = uuid.uuid4().hex
    r = post(client, key=key)
    assert (
        r.status_code == 422 and r.json()["error"]["code"] == "REVIEW_CONTEXT_TOO_LARGE"
    )
    assert (
        store.replay(
            "vesta",
            store.CREATE_REVIEW,
            key,
            {
                "report_text": __import__(
                    "backend.reviewer", fromlist=["SAMPLES"]
                ).SAMPLES[0]["report_text"]
            },
            presentation.API_VERSION,
        )
        is None
    )
    assert post(client, text="x" * 40001).status_code == 422


def test_addendum_prose_does_not_create_a_second_impression():
    text='Findings: Small left effusion.\nImpression: Small right effusion.\nAddendum: Correction to the Impression: left effusion, not right.'
    assert parse_sections(text)['impression']=='Small right effusion.'
    assert [s['kind'] for s in section_index(text)]==['findings','impression','addendum']
    assert parse_sections('Findings: Lungs clear. Impression: No acute disease.')['impression']=='No acute disease.'
