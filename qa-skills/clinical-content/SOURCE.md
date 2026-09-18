# Content 0.3.0 provenance

The web-specific nine-module package is integrated for prototype evaluation, not clinically
approved. Upstream: https://github.com/parthi-vesta-tinker/qatr at immutable commit
`b906151a2bdef8c206325de64d46b61cdf5b7ad7`.

Three references are copied byte-for-byte from
`src/qatr/_vendor/qa_skills/skills/qa-critical-match/references/`:
`critical-result-notification-source.txt`, `critical-rules.json`, `matching-guardrails.md`.
The registry records original Git blob IDs; manifest and reference records pin SHA-256.
The JSON preserves upstream CRLF. Source wording governs conflicting derived annotations.
The catalog has 43 entries, not 43 independent source documents; normalization is
`draft_for_review`, with no clinical approver, effective date or source version.

Two immutable release profiles use the same verified package: `vesta-qatr-0.3.0` includes the
complete three references; `generic-0.3.0` excludes Vesta references. Server configuration
selects a tenant's profile. Default local Vesta uses the former; other tenants use the latter.
Drafts never enter either profile. Every accepted review captures the profile, full selected
reference bytes/hashes, versions and exact composed instructions.

Existing report-only scope, two comment groups and radiologist-directed questions are retained.
Notification clauses remain source context; SLA, call completion and documentation checks are
excluded. Matching guidance is proposed, not policy. No repeat call or doctor judgment is
invented from an unresolved known-finding exception. Outside-catalog concerns remain questions.

F2 supplies deduplicated complete combined composition; the transitional runtime still uses
three stages until F3's coordinated DBOS/provider cutover. Source terms and clinical-owner
approval remain prerequisites for production use. No origin repository files were changed.
