# Resume design or development

## Suggested prompt for Codex or Claude Code

> Read AGENTS.md, framework/FRAMEWORK.md, framework/DECISIONS.md framework/QA_COMMENTS.md and framework/AGENT_HANDOFF.md. Inspect framework/assets/reference-ui.png. We are building a reusable UX structure for autonomous teleradiology report QA, with a stable three-panel workspace and strong evidence inspection. Start by summarizing the agreed constraints and the proposed defaults. Then propose the smallest local interactive prototype that exercises AC01–AC08, AC17–AC24 and AC31–AC35 using fixtures.json. Keep routine, disputed and mixed-comment cases in the same shell. Do not implement advanced consoles, production integrations or real AI review. Identify only questions that block this prototype. Wait for my instruction before starting implementation.

The final sentence deliberately keeps this as a planning prompt. If you are ready for implementation, replace it with: “Proceed with the local fixture-based prototype, document the chosen stack, and verify the relevant interaction criteria.”

## What is already settled

- Stable left Scope, center QA work and right Studio.
- Filters/favorites rather than stage-partitioned screens.
- QA findings and tight source evidence remain prominent.
- Timeline, report, communication and feedback are specialized views in the same workspace.
- Report review and available source context only; no image interpretation.
- Main outbound boundary is the configured integration, not facility delivery.
- Framework first; complex operational features deferred.

## What still needs a later decision

The frontend stack, actual clinical check catalogue, required sources, release rules, role permissions, message routing, external edit verification and integration acknowledgement semantics. None prevents an inert fixture-based interaction prototype.

## Current artifacts versus history

Current reference: `framework/assets/reference-ui.png`.

The reading edition embeds this same final reference. Earlier concepts in `design-history/` include rejected directions and should be read only to understand the design evolution. See the index before reusing any visual.

Read `framework/GUIDED_ACTIONS.md`, `framework/DESIGN_SYSTEM.md` and `framework/UI_SYSTEM_DESIGN.md` for contextual guidance, component behavior, candidate tokens, state/rendering boundaries and performance targets. The user selected the fleet-first center with compact vertical Studio and contextual guidance. Use the Graphite neutral light tokens as the initial baseline; alternate themes remain historical studies. Do not implement all three themes by default. Compact and expanded modes render the same packet; operator routing instructions never enter the copied radiologist comments.
