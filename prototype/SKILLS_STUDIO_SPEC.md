> Current implementation: application **0.13.0**, bundle **1.17**, foundation **F3**. [Decisions and verification](FOUNDATION_CHANGELOG.md) supersede older baseline statements below. Fresh schema 4 and API 2026-09-18 are implemented. F3 adds one combined request, guarded dispatch and durable response checkpoints. F4/F5 remain separate gates.

F2 adds `catalog` and `policy_source` knowledge document kinds, full qatr source attribution,
server-controlled tenant release profiles, and immutable complete composition snapshots.
See [foundation changelog](FOUNDATION_CHANGELOG.md) for implemented boundaries and evidence.

# Foundation compatibility — 2026-09-17

[FOUNDATION_PLAN.md](FOUNDATION_PLAN.md) adds source/catalog/guidance document kinds and explicit
server-controlled tenant release binding. Preserve source view, tenant drafts, compare/save/export,
scopes and revision/hash checks. Drafts never alter runtime or accepted snapshots. Release the
three references/43 entries under a new lock, not silent edits to installed 0.2.0. Preserve missing
approval labels; import is not approval. Publishing/approval/rollback UI stays deferred in SK-01.

# Skills & knowledge — Studio tool, release 1.14

## User outcome

QA Studio gains a fifth tool, **Skills & knowledge**, below the four existing workflow tools.
It opens an editorial workspace in the center panel while retaining the report list, Studio
navigation, light-default styling and the current report draft. No new intake fields are required.

Users can inspect the actual installed instructions, understand which model stages use them,
prepare changes, compare with installed content, save revisions and export a proposal for release.
The tool is available even when no OpenAI key/model is configured. It performs no inference.

## Content boundaries

- The catalog comes from the verified installed package, including QA_SKILL_PACKAGE_DIR overrides.
  It currently includes nine skill documents and three referenced guidance documents.
- Model usage comes from actual stage composition, not merely a skill's declared stage labels.
  qa-input-adequacy is labeled **Host validation reference**: the deterministic input gate runs
  in code and does not send that SKILL.md to a model. Editing it alone cannot alter validation.
- Shared references show their consuming skills and stages in the API. The UI shows stage usage.
- QA manual / local guidance shows the effective tenant-specific configured text, when present.
  An unconfigured manual appears empty and allows a proposal for future configuration. The Vesta
  global manual is not inherited by another tenant. Server filesystem paths are never exposed.
- Framework schemas, host safety boundaries, stage ownership, runtime code, package manifests,
  evaluation answers and credentials are outside the editor. They remain separate code artifacts.
- Installed does not mean clinically approved. Existing provisional/manual authority is unchanged.

## Draft versus active

Saving creates an immutable **draft_not_active** revision in the application database, separate
from qa-skills/framework and qa-skills/clinical-content. It never writes to the installed files,
changes their lock hashes, modifies a review, or enters the prompt composition path.

Browser activation is not included. This is an editorial tool for a versioned clinical instruction
package. Applying a proposal uses the existing release process: qualified content review, affected
atomic-skill/reference versions and changelogs, evaluation updates, manifest/lock regeneration,
package validation and appropriate clinical/model evaluation, then an intentional package release.
An exported manual proposal remains unvalidated guidance even if later configured.

This preserves the existing immutable instruction snapshots used for accepted reviews and DBOS
recovery. Workflow names, APP_VERSION and default .qa-data-v0.6 do not change in this release.
No new permissions/approval UI is imposed on the ordinary paste–review–copy flow.

## Interaction contract

1. Filter All content / Skills / Knowledge base, or search by name and purpose.
2. Choose a document. Read its purpose, installed version and model stage usage.
3. Edit plain text/Markdown in a lightweight textarea. No HTML execution or third-party editor.
4. Compare with installed opens a side-by-side view, stacked on narrow screens. The installed
   text stays read-only. Source/version/hash details are available in a collapsed section.
5. Enter a required change summary and Save draft. A clear status identifies saved versus unsaved
   content and confirms that installed instructions remain active.
6. Saved revisions lists the latest 20 records. Use revision copies earlier content into the editor;
   saving it creates a new revision and retains history. Older records remain exportable through API.
7. Export saved draft downloads JSON with exact content, hashes, document identity, tenant,
   revision, timestamp and change note. Unsaved text is never silently substituted in an export.

Navigating between Studio tools preserves the mounted editor and its unsaved text. Switching
documents or reloading source asks before discarding unsaved changes. Browser reload/close warns
while edits or an ambiguous save exist; unsaved text is not persisted in browser storage.
Saved revisions survive server/browser restarts in the same QA_DATA_DIR.

After a lost/malformed success response or 5xx, editing and document selection lock; Retry same
save reuses the exact payload and idempotency key. This intent survives Studio navigation in the tab,
not browser reload. After reload inspect revision history before saving the proposal again.
Revision/source conflicts retain local edits and require explicit reconciliation with current content.

## API and storage

Public QA-Version remains 2026-09-15. Paths use catalog document IDs, never arbitrary filesystem paths.
The catalog is bounded by the installed registry; no uploaded attachment, remote fetch or RAG index
is implied by the term Knowledge base.

| Endpoint | Permission | Behavior |
|---|---|---|
| GET /api/v1/knowledge | skills:read | Metadata catalog, installed package hash/version, can_edit |
| GET /api/v1/knowledge/{document_id} | skills:read | Installed text, latest draft, saved diff, recent revisions |
| POST /api/v1/knowledge/{document_id}/drafts | skills:read + skills:write | Append revision with Idempotency-Key and optimistic concurrency |
| GET /api/v1/knowledge/{document_id}/drafts/{revision}/export | skills:read | Export immutable saved proposal, including when source is unavailable |

Draft writes include expected_revision (0 initially), source_sha256, package_sha256, content and
change_note. Content is 1–100,000 characters; change summary is 1–1,000. Blank/null-containing text
and unknown fields are rejected. A stale revision or source returns 409 with a specific code.

knowledge_drafts is an additive schema-2 table keyed by tenant/document/revision. A BEGIN IMMEDIATE
transaction checks the latest revision, stores the event and commits its immutable receipt together.
Receipt replay precedes installed-source validation, allowing safe retry after source drift.
The catalog verifies source hashes; an unavailable/invalid package fails closed with 503. Cached
draft exports remain readable. Source comparison is an editorial safeguard, not runtime activation.

Existing review/feedback API keys gain no editorial access. Grant skills:read explicitly; grant both
scopes for editing. The key provisioning helper accepts these scopes but retains its existing default
review/feedback scope set. Local loopback Vesta mode includes editorial access, as other local tools do.
Tenant identity always comes from authentication. No tenant body/header selector is accepted.
Audit notes represent the authenticated tenant credential, not a verified individual clinician.

## Validation and next steps

Tests cover catalog provenance, private manual paths, deterministic-gate labeling, immutable
runtime snapshots, receipt replay, source/revision conflicts, persistence, restoration, exports,
tenant isolation, permissions, unavailable source, navigation preservation and ambiguous UI retry.
No paid model calls or clinical content revisions are needed to test this tool.

Local acceptance: open the tool, inspect a skill/reference/manual, edit and compare, save a revision,
reload/reopen, restore an older revision and export. Confirm report drafts and copy controls remain
familiar. Browser-rendered verification was blocked in this environment; desktop/mobile visual and
accessibility acceptance remain to be performed locally.

Future extensions: clinically governed evaluation-and-release UI, document-level reviewers, richer
diffs, revision search, controlled knowledge-source ingestion and a versioned tenant package selection.
They should preserve this editor's installed/draft distinction and the separate skill framework.
