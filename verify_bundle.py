"""Verify the current source bundle and active skill package. Python stdlib only."""
import hashlib
import json
from pathlib import Path
import runpy

root = Path(__file__).resolve().parent
manifest = json.loads((root / 'MANIFEST.json').read_text(encoding="utf-8"))
for entry in manifest['files']:
    path = root / entry['path']
    assert path.is_file(), f"Missing: {entry['path']}"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256'], f"Changed: {entry['path']}"
runpy.run_path(str(root / 'qa-skills' / 'framework' / 'tools' / 'validate.py'), run_name='__main__')
print(f"PASS: {len(manifest['files'])} current source file hashes. Artifact verification only. See prototype/IMPLEMENTATION_STATUS.md for separately executed runtime tests.")
