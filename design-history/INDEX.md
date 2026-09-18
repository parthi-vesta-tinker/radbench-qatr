# Historical evidence scope — 2026-09-17

[FOUNDATION_PLAN.md](../prototype/FOUNDATION_PLAN.md) governs the next build. This directory
preserves prior contracts, images and tests; these are not current implementation instructions.
Current Workspace UX supersedes older fleet concepts. Fresh database permission does not remove
history, feedback or analytics as product capabilities.

# UI design history

The only current visual anchor is [`../framework/assets/reference-ui.png`](../framework/assets/reference-ui.png). It is the final corrected framework reference. Historical images preserve exploration, not implementation authority.

| Image | Status | Design lesson |
|---|---|---|
| [01-flow-observatory.png](01-flow-observatory.png) | Rejected as default | Stage lanes did not suit concurrent fleet review. |
| [02-attention-desk.png](02-attention-desk.png) | Rejected as default | Exception-first screen did not provide the desired autonomous fleet experience. |
| [03-case-ledger.png](03-case-ledger.png) | Concept retained | Timeline and evidence became specialized case views. |
| [04-live-review-matrix.png](04-live-review-matrix.png) | Foundation; superseded visually | Multi-report comparison and three-panel architecture retained; detailed check matrix made optional. |
| [05-living-report.png](05-living-report.png) | Exploratory case view | Inline evidence and document inspection inform the Report tool. |
| [06-review-replay.png](06-review-replay.png) | Exploratory case view | History and evidence synchronization inform Timeline; animated replay is not required initially. |
| [07-studio-blueprint.png](07-studio-blueprint.png) | Superseded | Studio palette and central evidence introduced; framework definitions subsequently tightened. |
| [08-framework-draft.png](08-framework-draft.png) | Superseded | Draft used All active although an acknowledged case was present; final reference corrects the scope to This shift. |

The corrected image generated after 08-framework-draft is preserved as 09-framework-v1.0.png. It was the previous current reference.

The current project bundle is v1.3 and includes framework v1.2. Earlier bundle v1.1 contained framework v1.0.

## External inspiration

Google NotebookLM inspired the three-panel architecture and specialized Studio tools. Source: [Google design overview](https://blog.google/innovation-and-ai/models-and-research/google-labs/notebooklm-new-features-december-2024/). The included reference capture is for attribution and design study, not a Vesta design or a production asset.

[NotebookLM source capture](../references/notebooklm-three-panel-reference.jpg)

## Framework v1.1 revision

Current implementation anchor is `../framework/assets/reference-ui.png`: R-209 QA Review / Comments, author/signature header, critical/non-critical sections and contextual copy actions. The selected-case container is explicitly named. Exact text and behavior are governed by the framework and exports.

`09-framework-v1.0.png` preserves the previously current R-207 Evidence view. It remains useful as evidence-view history, but its QA Brief top-level label and implicit selected-report container are superseded by v1.1. Do not restore those labels. All other earlier images remain historical explorations.

## Framework v1.2 and design-system studies

Current interaction references are `../framework/assets/reference-ui.png` (compact) and `../framework/assets/reference-expanded.png` (expanded). `10-framework-v1.1-comments-tabs.png` preserves the superseded tab-based design. Comments are now immediately visible; source-first selection and Brief/Comments tabs are superseded. Graphite, Warm Paper and Slate images are candidate visual styles, not additional workflow options. Consult DESIGN_SYSTEM.md before applying a palette.

- `11-framework-v1.2-compact-lavender.png`: superseded compact appearance. Current approved reference uses fleet-first center and compact vertical Studio. Earlier expanded image retained only for behavior, not current styling.

- `handoff-v1.4/`: prior fleet-first coding-agent entry points, superseded for current prototype by the manual paste-and-review plan on 14 September 2026.
