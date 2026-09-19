# Skills & knowledge contract

Skills & knowledge is a tenant-scoped editorial tool inside QA Studio. It can inspect verified installed instructions and references, compare proposed text, save immutable draft revisions, restore an older revision as a new proposal, and export a saved proposal. It makes no provider call.

## Content boundary

The catalog is built from the verified installed package and includes skill documents, shared references, qatr source/catalog documents, and configured tenant guidance. It shows actual combined-request usage. Host validation references are labeled as such and are not presented as model instructions.

Running installed instructions against a report is the Playground's job, not this editor's; see [PLAYGROUND_UX_SPEC.md](PLAYGROUND_UX_SPEC.md). Framework schemas, runtime code, package manifests, evaluation answers, credentials, private server paths, and release controls are outside the editor. Installed content is not automatically clinically approved.

## Drafts are never active

Saving appends a `draft_not_active` record in the application database. It does not write installed files, change package hashes or locks, alter a review, enter prompt composition, or modify old snapshots.

Activation requires an intentional package release with qualified review, affected document versions and changelogs, evaluation updates, manifest/reference/lock regeneration, package validation, and appropriate model/clinical evaluation. The browser has no publish button.

## Interaction

Users can filter/search the catalog, inspect purpose/version/usage, edit plain Markdown text, compare with installed content, enter a required change summary, save, browse recent revisions, restore content into the editor, and export an immutable saved revision. Switching Studio tools preserves mounted unsaved edits. Switching documents or reloading source warns before discarding changes.

An ambiguous save retains the exact payload and idempotency key and locks conflicting editing until retried or reconciled. Revision and source-hash conflicts preserve local edits. Saved revisions survive restarts in the same application store; unsaved browser text does not.

## API and isolation

Knowledge routes use bounded document IDs from the verified catalog, never caller-supplied filesystem paths. Draft writes require expected revision, source/package hashes, content, change note, and an idempotency key. Receipt lookup precedes current source validation so an accepted write can replay after source drift.

`skills:read` is explicit; writes require both `skills:read` and `skills:write`. Existing review/feedback credentials gain no editorial access. All catalog, draft, revision, receipt, and export operations are tenant scoped. A tenant without the Vesta release never inherits Vesta content.
