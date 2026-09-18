"""Regenerate immutable skill-package inventory and lock metadata."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "qa-skills/clinical-content"


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode()


def main() -> None:
    files = sorted(
        path for path in CONTENT.rglob("*")
        if path.is_file() and path.name != "MANIFEST.json"
        and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )
    rows = [
        {"path": path.relative_to(CONTENT).as_posix(), "sha256": digest(path.read_bytes())}
        for path in files
    ]
    release_hash = digest(canonical(rows))
    registry = json.loads((CONTENT / "registry.json").read_text(encoding="utf-8"))
    manifest = {
        "package_id": registry["package_id"],
        "artifact_sha256": release_hash,
        "files": rows,
    }
    lock = {
        "package_id": registry["package_id"],
        "content_version": registry["content_version"],
        "framework_version": registry["framework_version"],
        "content_sha256": release_hash,
    }
    (CONTENT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (ROOT / "qa-skills/lock.json").write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    print(f"Released {len(rows)} skill artifacts at {release_hash}")


if __name__ == "__main__":
    main()
