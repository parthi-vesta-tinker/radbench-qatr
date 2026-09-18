# Backlog

F1–F3 are implemented. The following work remains deliberately outside the current release.

## Near term

- **F4 product acceptance:** integrated fresh-store walkthrough, accessibility/visual review, operator recovery guidance, and distributable handoff verification.
- **F5 bounded evaluation:** explicitly authorized live-provider runs and separately governed clinical adjudication.
- Add an intentional retained-data migration process only when prototype data becomes a product requirement; current schema cutovers use fresh stores.
- Reconcile conservative spend reservations with provider invoices or trusted usage exports if the prototype becomes an operational service.

## Product and operations

- Test/Production isolation, environment-specific credentials, deployment policy, monitoring, backups, retention, and incident response.
- Authenticated user identities and role management beyond tenant API credentials/local mode.
- PACS/RIS/HL7 ingestion, report delivery, notifications, and external messaging.
- Verified facility/radiologist identities and signed outcome attestations.
- A governed package approval, publication, rollback, and tenant release-selection UI.

## Evaluation

- Independently selected cohorts with predeclared inclusion/exclusion, reference standards, adjudicator qualifications, disagreement handling, and sufficient negative examples.
- Report-level and finding-level TP/FP/FN/TN definitions, coverage, exclusions, confidence intervals, and release-specific provenance.
- Clinically adjudicated versions of proposed skill fixtures. Controlled contract tests and user feedback remain separate from clinical evidence.

## Explicit non-goals for the current prototype

Image interpretation, automatic report editing, automatic delivery, self-modifying prompts, silent Studio draft activation, generic multi-agent infrastructure, vector search, and arbitrary workflow engines are not planned for the current foundation.
