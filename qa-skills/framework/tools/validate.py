"""Validate draft artifacts and preview composition sizes; no model or application execution."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath

FRAMEWORK = Path(__file__).resolve().parents[1]
STAGES = ("language_review", "consistency_review", "critical_finding_review")
SEMVER = re.compile(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)$")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode()


def require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(root: Path, lock_path: Path) -> dict:
    root = root.resolve()

    def path(relative: str) -> Path:
        pure = PurePosixPath(relative)
        require(bool(relative) and not pure.is_absolute(), "Invalid relative path")
        require(str(pure) == relative and ".." not in pure.parts, "Noncanonical path")
        require(not any(c in relative for c in ("\\", ":", "\0")), "Unsafe path")
        target = root.joinpath(*pure.parts)
        require(target.is_file(), "Required package file missing")
        require(root in target.resolve().parents, "Path escapes package")
        require(not any(p.is_symlink() for p in (target, *target.parents) if p != root),
                "Symlink not allowed")
        return target

    manifest = json.loads(path("MANIFEST.json").read_text(encoding="utf-8"))
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    framework = json.loads((FRAMEWORK / "version.json").read_text(encoding="utf-8"))
    schema = (FRAMEWORK / "stage-output.schema.json").read_bytes()
    require(digest(schema) == framework["stage_schema_sha256"], "Framework schema drift")
    json.loads(schema)
    rows = manifest["files"]
    names = [entry["path"] for entry in rows]
    require(names == sorted(set(names)), "Inventory not unique/sorted")
    actual = sorted(p.relative_to(root).as_posix() for p in root.rglob("*")
                    if p.is_file() and p.name != "MANIFEST.json"
                    and "__pycache__" not in p.parts and p.suffix != ".pyc")
    require(actual == names, "Package inventory mismatch")
    for entry in rows:
        require(set(entry) == {"path", "sha256"}, "Invalid inventory row")
        require(digest(path(entry["path"]).read_bytes()) == entry["sha256"],
                "Package file digest mismatch")
    content_digest = digest(canonical(rows))
    require(content_digest == manifest["artifact_sha256"] == lock["content_sha256"],
            "Content release pin mismatch")
    registry = json.loads(path("registry.json").read_text(encoding="utf-8"))
    require(registry["framework_version"] == framework["version"] == lock["framework_version"],
            "Framework version mismatch")
    require(registry["content_version"] == lock["content_version"], "Content version mismatch")
    require(registry["package_id"] == lock["package_id"], "Package identity mismatch")
    require(registry["clinically_approved"] is False, "Draft cannot claim clinical approval")
    require(registry["status"] == "prototype_evaluation", "Unexpected integration claim")
    for name, expected in registry["qatr_source"]["git_blobs"].items():
        raw = path("references/" + name).read_bytes()
        require(hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == expected,
                "Pinned upstream reference changed")
    require(set(registry["stages"]) == set(STAGES), "Model stage mapping mismatch")
    skills, owners, evaluation_ids = {}, {}, set()
    suite_cases = 0
    for manifest_path in registry["skills"]:
        skill = json.loads(path(manifest_path).read_text(encoding="utf-8"))
        name = skill["name"]
        require(re.fullmatch(r"[a-z][a-z0-9-]{0,63}", name), "Invalid skill name")
        require(name not in skills, "Duplicate skill")
        require(SEMVER.fullmatch(skill["version"]) is not None, "Invalid skill version")
        require(
            registry["skill_versions"].get(name) == skill["version"],
            "Skill registry version mismatch",
        )
        require(skill["role"] in {"shared", "gate", "check", "synthesis", "verification"},
                "Unknown role")
        require(set(skill["stages"]) <= set(registry["supported_stages"]), "Unknown stage")
        md = path(skill["instruction"]).read_text(encoding="utf-8")
        front = md.split("---", 2)
        require(len(front) == 3 and not front[0], "Missing frontmatter")
        values = dict(line.split(":", 1) for line in front[1].strip().splitlines())
        require(values["name"].strip() == name, "Frontmatter name mismatch")
        require(json.loads(values["description"].strip()) == skill["description"],
                "Frontmatter description mismatch")
        require(path(skill["instruction"]).parent.name == name, "Skill directory mismatch")
        changelog = path(skill["changelog"])
        require(
            f"## {skill['version']}" in changelog.read_text(encoding="utf-8"),
            "Skill changelog lacks current version",
        )
        require(not skill["owns"] or skill["role"] == "check", "Non-check owns issues")
        for code in skill["owns"]:
            require(code not in owners, "Issue has multiple owners")
            owners[code] = name
        for reference in skill["references"]:
            require(reference["authority"] in {"review_guidance_not_policy", "source_wording", "draft_catalog", "proposed_matching_guidance"}, "Unknown authority")
            require(set(reference["load_stages"]) <= set(skill["stages"]), "Reference stage mismatch")
            require(digest(path(reference["path"]).read_bytes()) == reference["sha256"],
                    "Reference digest mismatch")
        suite = json.loads(path(skill["evaluation"]).read_text(encoding="utf-8"))
        require(suite["skill"] == name, "Evaluation suite skill mismatch")
        require(suite["skill_version"] == skill["version"], "Evaluation suite version mismatch")
        require(suite["status"] == "proposed_not_adjudicated", "Unexpected evaluation approval claim")
        require({case["partition"] for case in suite["cases"]} == {"development", "held_out"},
                "Evaluation suite needs development and held-out partitions")
        for case in suite["cases"]:
            require(case["id"] not in evaluation_ids, "Duplicate evaluation ID")
            evaluation_ids.add(case["id"])
            require(case["stage"] in skill["stages"], "Evaluation stage outside skill scope")
            require(case["expectation_status"] in {"proposed_not_adjudicated", "adjudicated"},
                    "Invalid expectation status")
            require(case["policy_binding"] == "none", "Unapproved policy-bound evaluation")
            require(bool(case["input"]["report_text"].strip()), "Blank evaluation report")
        suite_cases += len(suite["cases"])
        skills[name] = skill
    disk_skills = {p.parent.name for p in (root / "skills").glob("*/SKILL.md")}
    require(disk_skills == set(skills), "Undeclared/missing skill")
    compositions = {}
    for stage, ids in registry["stages"].items():
        require(len(ids) == len(set(ids)), "Duplicate stage module")
        chunks, refs = [], set()
        for name in ids:
            require(name in skills and stage in skills[name]["stages"], "Invalid stage skill")
            skill = skills[name]
            chunks.append(path(skill["instruction"]).read_text(encoding="utf-8"))
            for reference in skill["references"]:
                if stage in reference["load_stages"] and reference["path"] not in refs:
                    refs.add(reference["path"])
                    chunks.append(path(reference["path"]).read_text(encoding="utf-8"))
        require(any(skills[x]["role"] == "check" for x in ids), "Stage has no check")
        require(skills[ids[-1]]["role"] == "verification", "Stage lacks final verification")
        compositions[stage] = {"skills": len(ids), "references": len(refs),
                               "content_characters": len("\n\n".join(chunks))}
    require(set(registry["skill_versions"]) == set(skills), "Skill version registry mismatch")
    legacy_cases = json.loads(path("evaluation/cases.json").read_text(encoding="utf-8"))["cases"]
    require(len({x["id"] for x in legacy_cases}) == len(legacy_cases),
            "Duplicate cross-stage evaluation ID")
    return {"valid": True, "skills": len(skills), "files": len(rows),
            "atomic_evaluation_cases": suite_cases,
            "cross_stage_regression_cases": len(legacy_cases),
            "content_sha256": content_digest,
            "composition_preview": compositions,
            "scope": "Artifact and evaluation-contract checks only; no clinical approval."}


if __name__ == "__main__":
    try:
        content = Path(sys.argv[1]) if len(sys.argv) > 1 else FRAMEWORK.parent / "clinical-content"
        lockfile = Path(sys.argv[2]) if len(sys.argv) > 2 else FRAMEWORK.parent / "lock.json"
        print(json.dumps(validate(content, lockfile), indent=2))
    except (ValueError, KeyError, TypeError, OSError, IndexError) as exc:
        print("Artifact validation failed: " + str(exc), file=sys.stderr)
        sys.exit(1)
