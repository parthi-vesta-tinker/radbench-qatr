"""Check the current documentation inventory, links, and archive boundary."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_ROOT = {
    "AGENTS.md",
    "CLAUDE.md",
    "LOCAL_TESTING.md",
    "README.md",
    "START_HERE.md",
}
ACTIVE_PROTOTYPE = {
    "ACCEPTANCE.md",
    "ANALYTICS_SPEC.md",
    "API_DESIGN.md",
    "BACKLOG.md",
    "DBOS_VALIDATION.md",
    "FEEDBACK_CLASSIFICATION_SPEC.md",
    "FOUNDATION_CHANGELOG.md",
    "FOUNDATION_PLAN.md",
    "IMPLEMENTATION_STATUS.md",
    "PLAYGROUND_UX_SPEC.md",
    "README.md",
    "SKILL_PACK_SPEC.md",
    "SKILLS_STUDIO_SPEC.md",
    "UI_ENHANCEMENT_RESEARCH.md",
    "WORKSPACE_SPEC.md",
}
LINK = re.compile(r"(?<!!)\[[^]]+]\(([^)]+)\)")


def fail(message: str) -> None:
    raise SystemExit("Documentation check failed: " + message)


root_docs = {path.name for path in ROOT.glob("*.md")}
if root_docs != ACTIVE_ROOT:
    fail(f"root Markdown inventory differs: {sorted(root_docs ^ ACTIVE_ROOT)}")

prototype_docs = {path.name for path in (ROOT / "prototype").glob("*.md")}
if prototype_docs != ACTIVE_PROTOTYPE:
    fail(f"prototype Markdown inventory differs: {sorted(prototype_docs ^ ACTIVE_PROTOTYPE)}")

active = [
    *(ROOT / name for name in sorted(ACTIVE_ROOT)),
    *((ROOT / "prototype" / name) for name in sorted(ACTIVE_PROTOTYPE)),
]
for source in active:
    text = source.read_text(encoding="utf-8")
    for raw_target in LINK.findall(text):
        target = raw_target.split(maxsplit=1)[0].strip("<>")
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        relative = unquote(target.split("#", 1)[0])
        resolved = (source.parent / relative).resolve()
        archive = ROOT / "design-history"
        if resolved == archive or archive in resolved.parents:
            fail(
                f"active document links into archive: {source.relative_to(ROOT)} -> {target}"
            )
        if not resolved.exists():
            fail(f"broken link: {source.relative_to(ROOT)} -> {target}")

print(
    f"PASS: {len(active)} active Markdown files; inventory, local links, and archive boundary are valid"
)
