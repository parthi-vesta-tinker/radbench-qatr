> Next-build authority (2026-09-17): [clean-start foundation plan](../prototype/FOUNDATION_PLAN.md). This broader framework is a design reference, not extra foundation scope. Preserve the current application's history, feedback, analytics and tenant drafts. Fresh data and one-call DBOS execution supersede older implementation assumptions; historical examples are not new runtime or clinical evidence.

# Revision 1.2 — consistency review

13 September 2026. Incorporates compact/expanded comments-first UX, context-specific guidance, UI system design and three restrained visual studies. Prior v1.1 review and packet examples remain in history/v1.1/.

## Changes and resolved inconsistencies

| Area | Resolution |
|---|---|
| Initial case selection | Replaced Report / Snapshot with compact QA Review showing comments and next step immediately. D32 explicitly superseded. |
| Hidden deliverable | Removed Brief/Comments tabs. Internal QA Brief becomes supporting expanded Review detail. D30 explicitly superseded. |
| Oversized overview | Flat comment rows, shared identity, small copy controls and about 60/40 fleet/overview target; readable content takes precedence. |
| Expansion | One click reveals detail in the same case. Collapse restores fleet context. Modes share identical packet/guidance records and do not invoke QA. |
| Operator guidance vs recipient text | Studio identifies actor, destination/field, section, prerequisite and completion. Routing instructions are excluded from the radiologist comment payload. |
| Real versus synthetic destinations | Demo PACS and QA comments are illustrative mappings, not verified RamSoft/SimpliRad paths. Unknown mapping blocks consequential action, not inspection. |
| Critical decision vs communication | Accepted designation and pending clinician communication remain independent. A PACS paste cannot complete the clinical communication task. |
| Source/provenance | Version, author/signature and scoped upstream QA remain visible or inspectable; none implies universal clearance. |
| Type versus urgency | Suggestions, discrepancies and unmet requirements remain separate from routing/confirmation. Non-critical findings do not automatically get urgent styling. |
| Shortening comments | New R-209 concise packet explicitly supersedes the archived prior draft; switching presentation modes never generates a different message. |
| Compact overflow | Required/urgent counts and uncertainty remain visible. Full-section copy requires complete preview; no hidden verbose or truncated payload. |
| Style versus behavior | Three candidate palettes use one component contract. Selection resolved by D41: fleet-first center, vertical Studio and neutral light tokens. Palette selection cannot change state meaning. |
| Browser performance | Separate local view state from authoritative records; summaries for fleet, selected-case detail loading, no continuous decorative animation. Performance targets are proposals. |

## Visual reference limits

The current combined reference anchors compact appearance; the earlier lavender expanded image is retained for behavior only. Three newer style studies explore Graphite, Warm Paper and Slate. None is an implemented app. Generated style images occasionally use oversized Studio controls or colored counts; component specifications override these details. Graphite's red R-207 icon is incorrect for that synthetic non-critical case and must be neutral in implementation.

The source header abbreviates the same author/signer as RAD-DEMO-B in style studies; implementation must retain explicit roles and show them separately when different. Eight fleet rows are supplied for reference density; only R-201, R-207 and R-209 are canonical case fixtures. The five remaining rows are labeled display-only examples. A later 20-row prototype is needed to validate fleet behavior.

## Scope and validation

Added design-system and UI architecture documents, token JSON/CSS, three guidance examples and five total current reference/style images. No live PACS/HL7, clipboard integration, model review, production stack, workflow engine, user study or browser performance result is claimed. Offline artifact checks establish consistency only. AC01–AC35 and the UI performance scenarios specify later validation.

## Design-system v0.2 consistency review

Resolved pending style statements in the framework, design system, tokens and coding-agent entry points. Replaced two-column Studio sizing with a compact vertical list. Archived the prior compact reference. Preserved all synthetic cases, comment exports, source evidence and guidance. Image typography and spacing remain illustrative; exact text/data and component contracts take precedence. No interactive UI, clinical workflow or performance testing was performed.
