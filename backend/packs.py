"""Pack references, workspace identity, and draft pack composition.

A pack reference names which instruction set a run composes. `published` is the verified
installed package and is the only reference live report QA may use. `draft:<workspace>` is a
tenant-scoped workspace overlaid on the published package; it can be composed and run, and is
stamped so it can never be mistaken for a live release.

Composition itself stays in `skill_runtime`. This module owns the reference, the workspace
record, and the overlay those two need.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Literal

PUBLISHED = "published"
WORKSPACE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$|^[a-z0-9]$")
STATUSES = ("open", "submitted", "published", "closed")
# Drafts saved outside any workspace, by the read-only editorial path. They never compose.
NO_WORKSPACE = ""


class PackError(ValueError):
    """An unusable pack reference or workspace state."""


@dataclass(frozen=True)
class PackRef:
    kind: Literal["published", "draft"]
    workspace_id: str = ""

    def __str__(self) -> str:
        return PUBLISHED if self.kind == "published" else f"draft:{self.workspace_id}"

    @property
    def is_draft(self) -> bool:
        return self.kind == "draft"

    def stamp(self, content_sha256: str) -> str:
        """The release id a run made against this reference carries."""
        return f"draft:{self.workspace_id}@{content_sha256}" if self.is_draft else ""


def parse(value: PackRef | str | None) -> PackRef:
    if value is None:
        return PackRef("published")
    if isinstance(value, PackRef):
        return value
    if value == PUBLISHED:
        return PackRef("published")
    if value.startswith("draft:"):
        workspace = value.removeprefix("draft:")
        if not WORKSPACE_ID.fullmatch(workspace):
            raise PackError("Invalid workspace identifier in pack reference")
        return PackRef("draft", workspace)
    raise PackError("Unknown pack reference")


def require_published(value: PackRef | str | None) -> PackRef:
    """Live report QA composes the published package and nothing else."""
    ref = parse(value)
    if ref.is_draft:
        raise PackError("Live report QA cannot run a draft pack")
    return ref


def overlay(conn, tenant: str, workspace_id: str, paths: dict[str, str]) -> dict[str, str]:
    """Draft text for this workspace, keyed by the package path it replaces.

    `paths` maps an editable document id to its package path. A draft for a document that is
    not editable content, or that is no longer in the package, is refused rather than dropped:
    silently ignoring it would compose a pack the reviewer did not write.
    """
    # SQLite takes the bare columns from the row holding MAX(revision) in each group.
    rows = conn.execute(
        "SELECT document_id, document, MAX(revision) AS revision FROM knowledge_drafts"
        " WHERE tenant_id=? AND workspace_id=? GROUP BY document_id",
        (tenant, workspace_id),
    ).fetchall()
    drafted = {}
    for row in rows:
        document_id = row["document_id"]
        if document_id not in paths:
            raise PackError(f"Workspace draft targets content that is not composable: {document_id}")
        drafted[paths[document_id]] = json.loads(row["document"])["content"]
    return drafted
