# Backlog

F1–F3 are implemented. The following work remains deliberately outside the current release.

## Near term

- **F4 product acceptance:** integrated fresh-store walkthrough, accessibility/visual review, operator recovery guidance, and distributable handoff verification.
- **F5 bounded evaluation:** explicitly authorized live-provider runs and separately governed clinical adjudication.
- Add an intentional retained-data migration process only when prototype data becomes a product requirement; current schema cutovers use fresh stores.
- Reconcile conservative spend reservations with provider invoices or trusted usage exports if the prototype becomes an operational service.

## Post-review guidance implementation plan

1. **Implemented, 2026-09-24:** rename and initialize the guidance section, gate numbered
   steps on completed current results, and separate the presentation component from pure
   content derivation. No storage or API change. Tests not run at the user's request.
2. **Implemented, 2026-09-24:** compact independent disclosures, two-step/group previews,
   Classification Overview naming, and a single feedback entry point. Subtype remains
   deferred until the classification contract supplies it; no inferred subtype mapping.
3. **Next:** define per-finding action identities and mapping from current classification
   results to guidance, including unavailable/indeterminate classifications and human-feedback
   precedence. Keep basic completed-review advice available while classification finishes.
4. **Then:** define support workflow configuration and radiologist preference ownership,
   tenant boundaries, precedence, defaults, and versioning; implement settings only after that
   contract is agreed. Keep preferences separate from governed clinical policy.
5. **Before acceptance of extensions:** verify state transitions, stale/restored text,
   review replacement, classification races/failures, tenant/preference isolation, and narrow
   layouts. Clinical recommendations need separate qualified assessment.

Requirements and boundaries: [Workspace contract](WORKSPACE_SPEC.md#post-review-guidance).

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
