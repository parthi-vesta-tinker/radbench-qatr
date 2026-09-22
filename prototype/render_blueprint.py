"""Build a standalone reading edition from the current documentation set."""

from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

SECTIONS = [
    ("FOUNDATION_PLAN.md", "plan", "Foundation plan"),
    ("FOUNDATION_CHANGELOG.md", "changes", "Implemented decisions"),
    ("IMPLEMENTATION_STATUS.md", "status", "Implementation status"),
    ("API_DESIGN.md", "api", "API contract"),
    ("DBOS_VALIDATION.md", "dbos", "DBOS and recovery"),
    ("WORKSPACE_SPEC.md", "workspace", "Workspace"),
    ("ANALYTICS_SPEC.md", "analytics", "Analytics"),
    ("SKILLS_STUDIO_SPEC.md", "skills", "Skills Studio"),
    ("ACCEPTANCE.md", "acceptance", "Acceptance gates"),
    ("BACKLOG.md", "backlog", "Backlog"),
]


def inline(value: str) -> str:
    value = html.escape(value)
    value = re.sub(r"`([^`]+)`", r"<code>\1</code>", value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(
        r"\[([^]]+)]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', value
    )
    return value


def render(markdown: str, prefix: str) -> str:
    lines = markdown.splitlines()
    output: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if line.startswith("```"):
            block: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].startswith("```"):
                block.append(lines[index])
                index += 1
            index += 1
            output.append("<pre><code>" + html.escape("\n".join(block)) + "</code></pre>")
            continue
        heading = re.match(r"(#+) (.*)", line)
        if heading:
            level = min(len(heading.group(1)) + 1, 6)
            slug = prefix + "-" + re.sub(
                r"[^a-z0-9]+", "-", heading.group(2).lower()
            ).strip("-")
            output.append(
                f'<h{level} id="{slug}">{inline(heading.group(2))}</h{level}>'
            )
            index += 1
            continue
        if line.startswith("|"):
            rows: list[list[str]] = []
            while index < len(lines) and lines[index].startswith("|"):
                cells = lines[index].strip().strip("|").split("|")
                if not all(
                    re.fullmatch(r"\s*:?-+:?\s*", cell) for cell in cells
                ):
                    rows.append(cells)
                index += 1
            output.append(
                "<div class=table-wrap><table><thead><tr>"
                + "".join("<th>" + inline(cell.strip()) + "</th>" for cell in rows[0])
                + "</tr></thead><tbody>"
            )
            for row in rows[1:]:
                output.append(
                    "<tr>"
                    + "".join("<td>" + inline(cell.strip()) + "</td>" for cell in row)
                    + "</tr>"
                )
            output.append("</tbody></table></div>")
            continue
        if re.match(r"^(- |\d+\. )", line):
            ordered = bool(re.match(r"^\d+\.", line))
            tag = "ol" if ordered else "ul"
            output.append(f"<{tag}>")
            while index < len(lines) and re.match(r"^(- |\d+\. )", lines[index]):
                output.append(
                    "<li>"
                    + inline(re.sub(r"^(- |\d+\. )", "", lines[index]))
                    + "</li>"
                )
                index += 1
            output.append(f"</{tag}>")
            continue
        paragraph = [line]
        index += 1
        while (
            index < len(lines)
            and lines[index].strip()
            and not re.match(r"^(#|```|\||- |\d+\. )", lines[index])
        ):
            paragraph.append(lines[index])
            index += 1
        output.append("<p>" + inline(" ".join(paragraph)) + "</p>")
    return "\n".join(output)


css = """*{box-sizing:border-box}body{margin:0;background:#f5f6f8;color:#20242b;font:16px/1.65 system-ui,-apple-system,sans-serif}header{padding:44px max(5vw,24px);background:#20242b;color:#fff}header p{max-width:850px;color:#d5d7dc}nav{position:sticky;top:0;display:flex;gap:18px;flex-wrap:wrap;padding:14px max(5vw,24px);background:#fff;border-bottom:1px solid #dde2e8}a{color:#245bb2}main{max-width:1120px;margin:auto;background:#fff;padding:20px 46px 50px}h2{font-size:29px;border-top:2px solid #dde2e8;padding-top:22px;margin-top:42px}h3{font-size:21px;margin-top:30px}table{border-collapse:collapse;width:100%;font-size:14px}td,th{text-align:left;vertical-align:top;padding:11px;border-bottom:1px solid #dde2e8}th{background:#f0f2f5}.table-wrap{overflow:auto}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f6f8;padding:16px;border-left:3px solid #737d8c}code{font-family:ui-monospace,monospace}footer{text-align:center;color:#59616d;padding:28px}@media(max-width:700px){main{padding:12px 18px}nav{position:static}}@media print{nav{position:static}body{background:#fff}main{padding:0}}"""

nav = "".join(f'<a href="#{key}">{label}</a>' for _, key, label in SECTIONS)
body = "".join(
    f'<section id="{key}">{render((ROOT / name).read_text(encoding="utf-8"), key)}</section>'
    for name, key, _ in SECTIONS
)
page = f"""<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>Vesta Report QA — current documentation</title><style>{css}</style></head><body><header><strong>Vesta / Report QA</strong><h1>Current foundation documentation</h1><p>Application 0.14.0 · bundle 1.20 · schema 7 · F1–F3 implemented · F4/F5 pending. This edition contains only active contracts and evidence.</p></header><nav>{nav}</nav><main>{body}</main><footer>Generated from the active prototype documentation. Archived design history is intentionally excluded.</footer></body></html>"""
(ROOT / "BLUEPRINT.html").write_text(page, encoding="utf-8")
print("Built prototype/BLUEPRINT.html from current documentation")
