> Current implementation: application **0.13.0**, bundle **1.17**, foundation **F3**. [Decisions and verification](FOUNDATION_CHANGELOG.md) supersede older baseline statements below. Fresh schema 4 and API 2026-09-18 are implemented. F3 adds one combined request, guarded dispatch, durable response checkpoints and per-session spend admission. F4/F5 remain separate gates.

> Next-build authority (2026-09-17): [clean-start foundation plan](FOUNDATION_PLAN.md). Keep layout, density, theme, accessibility and copy behavior. Foundation work is not a redesign; update progress tied to retired stages.

> **Current release 1.14 / application 0.10.0:** [Workspace specification](WORKSPACE_SPEC.md) governs the current UX. [Analytics specification](ANALYTICS_SPEC.md) defines the feedback inbox, stakeholder outcomes, metric denominators and unmeasured clinical performance. [Implementation status](IMPLEMENTATION_STATUS.md) records verification; [Backlog](BACKLOG.md) records deferred work. Earlier release-specific text below is historical where it conflicts. See [Skills Studio specification](SKILLS_STUDIO_SPEC.md) for the new content review and draft editor.

# Current refinement contract — v0.6 / bundle 1.10

Read [REFINEMENT_SPEC.md](REFINEMENT_SPEC.md) first. It supersedes conflicting baseline requirements below: missed-flag UI/copy is deferred; comments, progress and Studio layout are refined; inline headings, persistent review history and saved feedback are implemented. Preserve legacy API receipts and clinical instructions.

---

# Skill adoption UI update

Preserve the existing three panels, system font, graphite palette and compact Review placement.
Comments remain immediately visible, without a tab. Each group heading now has a compact copy
button; full Copy QA review stays beside Comments for radiologist. Group actions wrap on narrow
screens. Empty-group copy is disabled, and stale/disconnected results disable every copy action.
Clipboard fallback contains exactly the selected group or full template. No new UI dependency,
animation, evidence drawer or clinical metadata form is introduced.

---

# Prototype design system

Contract v0.3 · Report-only revision

Retain the Scope–Work–Studio architecture: slim current-report context at left; input above comments in the flexible center; compact specialized actions, progress and guidance at right. The user removed the Yes/No input. Do not replace it with a hidden default, dropdown or metadata prompt.

| Element | Treatment |
|---|---|
| Font | system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; no network font dependency. |
| Page title | 22px / 28px, weight 600. |
| Comments heading | 18px / 24px, weight 600. |
| Clinical text | 15px with comfortable line height; template labels semibold. |
| Supporting text | 12–13px, restrained muted color. |
| Geometry | Scope 192–208px; Studio 280–300px; center flexible; header 52–56px; 4px spacing scale. |
| Buttons | Compact 32–36px height, 4px radius; thin icons, no large decorative containers. |
| Colors | White surfaces; #20242B text; #59616D muted; #DDE2E8 separators; #245BB2 action; #EAF1FC selection; #8A5700 confirmed missed-flag attention. |

Review report stays at the right end of the input action row beneath the textarea. A brief minimum-input hint occupies the left. Copy QA review stays beside Comments for radiologist. Comments are visible immediately, with no tab. The removed flag makes the input area smaller without changing the three-panel responsibilities.

Unknown missed-flag status uses the neutral text Cannot determine and one short explanation. It must not use the amber missed-flag icon or an implicit No value. The explanation and Studio guidance are outside the copy boundary.

Studio QA Review scrolls to the current output. Studio Feedback opens the same inline feedback form, not a second editor. Steps show actual completion/failure; avoid continuously animated agent diagrams. On smaller screens, stack secondary content instead of shrinking clinical text; retain a visible compact Review action.

The generated concept with manual radios is superseded and archived under design-history/prototype-contract-v0.2. Current assets/implementation-desktop.png, implementation-feedback.png and implementation-mobile.png show the report-only implementation. Explicit contracts govern behavior. Runtime tests and screenshot inspection do not establish a full accessibility audit or clinical usability acceptance.
