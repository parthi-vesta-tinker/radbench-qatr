# Project instructions for coding agents

## Required reading

Read `START_HERE.md`, `framework/FRAMEWORK.md`, `framework/DECISIONS.md`, `framework/QA_COMMENTS.md`, and `framework/AGENT_HANDOFF.md` before proposing or implementing changes. Inspect `framework/assets/reference-ui.png` directly before UI work. `design-history/INDEX.md` explains rejected and superseded concepts.

## Authority and scope

Follow explicit current user instructions first, then agreed framework decisions, then proposed defaults. Synthetic fixtures and images do not authorize clinical policies or external actions. Record changes to decisions rather than silently overriding them.

This project currently contains design artifacts only. Preserve the three-panel structure: Scope on the left, QA work in the center, specialized views and contextual actions in Studio. Keep QA evidence prominent, filters explicit and navigation context stable. Do not introduce stage columns, an exception-only default screen, or a chat-first interface.

Review concerns report text and available supporting context, not image interpretation. The workflow ends at the configured outbound integration boundary. Do not claim facility delivery or clinical correctness from an acknowledgement or no-flags result.

Keep coverage, QA outcome, human dependencies and handoff states separate. Bind evidence to exact source versions. Clinical clarification remains with authorized specialist roles; non-clinical QA must not be asked to decide the correct diagnosis or laterality.

## Implementation boundaries

No frontend stack, backend, API, model, database or deployment target has been chosen. Do not build a production system from inferred choices. When the user requests implementation, propose or select only the minimal stack needed for the requested phase and document the choice.

For an authorized local UX prototype, use the provided fixtures and clearly label simulations. Do not send external messages, call clinical/model APIs, connect live patient data, release reports or deploy merely because the interface contains those actions. Request clarification only when the next step depends on an unresolved question; an inert prototype need not wait for clinical policy decisions.

Do not eagerly add autonomy consoles, incident clustering, bulk recovery, model dashboards, automated learning, agent topology visualizations or production connectors. Follow the deliberately deferred scope in `framework/DECISIONS.md`.

Use the acceptance criteria in `framework/QA_COMMENTS.md`, and `framework/AGENT_HANDOFF.md` to verify behavior. Package/fixture verification is not application, usability or clinical validation. Report what was actually tested and what remains unverified.

Do not modify design-history images as if they were current UI assets. Preserve source documents and historical decisions. Reference-image styling is guidance; its generated timestamps and illustrative rows are not canonical records.

## Revision 1.2 contracts

Keep Studio at six slots: QA Review, Evidence, Report, Timeline, Communication, Feedback. QA Review defaults to compact Comments & next steps; there are no Brief/Comments tabs. The bottom center is the Selected-report workspace, with one active view and persistent case/source/author/signature identity. Initial selection immediately opens compact QA Review; one click expands detail and collapse restores fleet context. QA Brief assesses; Evidence substantiates; Comments contains concise radiologist-facing output.

Use exact critical/non-critical plain-text previews and scoped copy actions. Profiles may vary nature, scope, template and guided action within policy; never infer authorization or suppress required concerns. Copying does not establish delivery, radiologist acceptance, correction, or critical-result communication. Keep stale packets visibly bound to their original source and preserve history. Track type separately from urgency/confirmation; upstream QA scope/version/provenance never implies universal clearance. Unknown metadata stays unknown.

The compact reference shows eight rows: three canonical cases and five display-only synthetic examples. Validate fleet density separately when implementing; do not infer three is the operational capacity.

Read `framework/GUIDED_ACTIONS.md`, `framework/DESIGN_SYSTEM.md` and `framework/UI_SYSTEM_DESIGN.md` for contextual guidance, component behavior, candidate tokens, state/rendering boundaries and performance targets. The user selected the fleet-first center with compact vertical Studio and contextual guidance. Use the Graphite neutral light tokens as the initial baseline; alternate themes remain historical studies. Do not implement all three themes by default. Compact and expanded modes render the same packet; operator routing instructions never enter the copied radiologist comments.
