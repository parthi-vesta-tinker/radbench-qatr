import hashlib
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("QA_DATA_DIR", str(ROOT / ".qa-data-foundation-v2"))).resolve()
APP_VERSION = "foundation-f2-0.12.0"


def runtime_config(tenant_id="vesta") -> dict:
    from .access import tenants

    entry = tenants()[tenant_id]
    mode = os.environ.get("QA_MODE", "openai")
    if mode not in ("demo", "openai"):
        raise ValueError("QA_MODE must be demo or openai")
    model = entry.get("model", os.environ.get("OPENAI_MODEL", "")).strip()
    path = entry.get(
        "policy_path",
        os.environ.get("QA_POLICY_PATH", "") if tenant_id == "vesta" else "",
    ).strip()
    policy = Path(path).read_text(encoding="utf-8") if path else ""
    if len(policy) > 100000:
        raise ValueError(
            "Policy text exceeds the prototype limit of 100,000 characters."
        )
    from .skill_runtime import load_snapshot, instructions, SkillStageOutput

    from .content import binding, combined_instructions
    snapshot = load_snapshot(release_id=binding(tenant_id, entry))
    tasks = {
        stage: instructions(
            snapshot,
            stage,
            policy,
            hashlib.sha256(policy.encode()).hexdigest() if policy else None,
        )
        for stage in snapshot["stages"]
    }
    max_output = int(os.environ.get("QA_MAX_OUTPUT_TOKENS", "6000"))
    effort = os.environ.get("QA_REASONING_EFFORT", "medium")
    if not 1000 <= max_output <= 16000 or effort not in ("low", "medium", "high"):
        raise ValueError("Invalid model output limit or reasoning effort")
    return dict(
        mode=mode,
        model=model or None,
        prompt_version="qa-skills-0.3.0-host-4",
        skill_release=snapshot["release_id"],
        combined_instructions=combined_instructions(snapshot, policy),
        skill_snapshot=snapshot,
        stage_schema_sha256=hashlib.sha256(
            str(SkillStageOutput.model_json_schema()).encode()
        ).hexdigest(),
        stage_instructions=tasks,
        skill_content_version=snapshot["content_version"],
        skill_versions=snapshot["skill_versions"],
        skill_content_sha256=snapshot["content_sha256"],
        skill_snapshot_sha256=snapshot["snapshot_sha256"],
        model_max_output_tokens=max_output,
        model_reasoning_effort=effort,
        workflow_version=APP_VERSION,
        policy_text=policy,
        policy_status="supplied_unvalidated" if policy else "provisional_no_manual",
        policy_version=hashlib.sha256(policy.encode()).hexdigest() if policy else None,
        ready=mode == "demo" or bool(model and os.environ.get("OPENAI_API_KEY")),
    )
