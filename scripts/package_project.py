"""Create a reproducible source/artifact bundle without dependencies or runtime data."""

import hashlib
import argparse
import json
import os
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {
    ".git",
    ".qa-secrets",
    ".venv",
    "node_modules",
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".qa-data",
    ".qa-data-v0.3",
    ".qa-browser-test-data-v0.3",
    ".qa-browser-test-data",
    "test-results",
    "playwright-report",
}


def files():
    for parent, directories, names in os.walk(ROOT):
        directories[:] = sorted(d for d in directories if d not in SKIP_DIRS and not d.startswith(".qa-"))
        for name in sorted(names):
            path = Path(parent) / name
            if path == ROOT / "MANIFEST.json" or path.is_symlink():
                continue
            if name.startswith(".env") and name != ".env.example":
                continue
            if name.endswith(
                (
                    ".pyc",
                    ".tsbuildinfo",
                    ".log",
                    ".sqlite",
                    ".sqlite-wal",
                    ".sqlite-shm",
                    ".db",
                    ".db-wal",
                    ".db-shm",
                )
            ):
                continue
            yield path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest-only", action="store_true")
    args = parser.parse_args()
    shipped = sorted(files())
    manifest = {
        **json.loads((ROOT / "RELEASE.json").read_text(encoding="utf-8")),
        "files": [
            {
                "path": p.relative_to(ROOT).as_posix(),
                "bytes": p.stat().st_size,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            }
            for p in shipped
        ],
    }
    (ROOT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    if args.manifest_only:
        print(f"Updated manifest for {len(shipped)} files, bundle {manifest['bundle_version']}")
        return
    output = ROOT.parent / f"Vesta-QA-UX-Project-v{manifest['bundle_version']}.zip"
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in [*shipped, ROOT / "MANIFEST.json"]:
            info = zipfile.ZipInfo(
                (Path(ROOT.name) / path.relative_to(ROOT)).as_posix(),
                date_time=(*map(int, manifest["created"].split("-")), 0, 0, 0),
            )
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    print(
        f"Packaged {len(shipped) + 1} files: {output} ({output.stat().st_size:,} bytes)"
    )


if __name__ == "__main__":
    main()
