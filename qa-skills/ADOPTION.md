# Host adoption — F2

Application 0.12.0 adopts content/framework 0.3.0 for prototype evaluation, without clinical
approval. The package imports all three qatr references and 43 catalog entries at the pinned
revision documented in [SOURCE.md](clinical-content/SOURCE.md).

`backend/content.py` owns explicit release bindings, source validation, authority labels and
bounded combined composition. `backend/skill_runtime.py` verifies inventories and snapshots
selected bytes, independent module versions and check ownership. `backend/knowledge.py`
exposes selected references/catalog for tenant-scoped draft editing. Drafts never activate.

The combined prompt deduplicates modules and references and omits input-gate instructions,
evaluation cases, changelogs and drafts. No retrieval or catalog pruning occurs. F2 retains
the existing three-stage runtime; F3 executes the combined request with guarded DBOS dispatch.
The input allowance helper is a context-window bound, not a cost control.

Technical contract tests are not model or clinical evaluation. Existing six-case skill suites
remain proposed, with catalog fixtures added separately for source relationships and matching
expectations. See the [foundation changelog](../prototype/FOUNDATION_CHANGELOG.md).
