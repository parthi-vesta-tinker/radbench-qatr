# Prototype design-system alignment

Version 0.2 · 14 September 2026 · Revised visual reference pending user review

## 1. Preserve the approved framework

The previously approved structure was Scope → central work and selected review → Studio. The first paste prototype wrongly made the source editor a wide permanent left panel. That changed the mental model and produced three competing headings. This revision restores the original architecture while preserving the smaller functional scope.

| Earlier framework | Current prototype mapping |
|---|---|
| Left Scope, low-frequency context | Slim Current report context; no history or new navigation features. |
| Center fleet above selected review | Center report input above its QA output. The prototype has no fleet to display. |
| Center comments visible by default | Full concise standard output immediately visible after completion; no Comments tab. |
| Right compact vertical Studio | QA Review and Feedback only, followed by supporting step status and guidance. Other capabilities remain deferred, not disabled placeholders. |
| Evidence and internal QA Brief | Still deferred; logical review steps are not evidence or model reasoning. |

Functional scope is intentionally smaller; spatial responsibilities remain familiar. Do not widen Scope merely to fill unused space. The single selected scope item is sufficient for the current-report prototype.

## 2. Typography

Use the existing shared system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif stack. No new font download or decorative display face is necessary. Visual quality comes from consistent scale, weight, spacing and alignment, not a font brand.

| Role | Desktop target | Weight / line height |
|---|---|---|
| Product label | 18px | 600 / 24px |
| Current-report title | 22px | 600 / 28px |
| Comments section title | 18px | 600 / 24px |
| Section headings / Studio heading | 15–16px | 600 / 22px |
| Report and clinical comments | 15px | 400 / 22–23px |
| Labels and button text | 14px | 400–500 / 20px |
| Metadata and supporting notes | 12–13px | 400 / 18–20px |

No oversized bold template headings. Match the template hierarchy with 15px semibold labels and regular comment text. Keep a comfortable reading width and permit wrapping/zoom without shrinking clinical text. The exact font metrics in generated images are illustrative; these rules govern implementation.

## 3. Geometry and colors

Reuse the Graphite semantic palette in framework/design-tokens.json: white surface, #20242B text, #59616D muted text, #DDE2E8 separators, #245BB2 accent, #EAF1FC selection and #8A5700 attention. The bright blue/gradient appearance in generated examples is not a replacement token. Do not color all completed checks or use large status circles.

Desktop targets: Scope 192–208px, Studio 280–300px, center flexible. Header 52–56px. Main gutters 24px. Spacing multiples of 4px. Buttons 32–36px high; 4px radius. Studio rows 32–36px. Icons 16–18px with consistent thin stroke. On narrower screens collapse secondary context and stack input/result rather than compressing the reading column.

Use separators before boxes and boxes before shadows. Keep most of the interface still; at most a short selection transition, reduced-motion support, no continuous per-step animation. Performance claims require a later browser test.

## 4. Action placement

The Review report button belongs to the report input action row: flag label/radios on the left, compact primary action on the right. It must not be a full-width banner at the bottom of a separate left pane. Group both required inputs and validation feedback with that action.

Copy QA review belongs in the output header beside Comments for radiologist. It is a compact secondary action and appears only for a completed observations result. This separates input submission from result use through location and hierarchy. Copy is read-only and has no send implication.

When input is invalid, preserve a clear route to validation feedback; never substitute an implicit flag default. The illustrative completed screen shows No selected, while initial state has neither selected. Reviewing an unchanged completed input can be an explicit repeat; do not auto-trigger duplicate jobs.

Feedback remains adjacent to the result. Studio Feedback opens/focuses the same form and must not create a second feedback editor or hide comments behind a tab. Its action is unavailable until there is a completed result.

## 5. Visual acceptance

Verify the three-panel responsibilities, type scale, button dimensions/placement, neutral status styling and exact template independently of the generated image. The image is a visual proposal; it cannot establish accessibility or performance compliance. Omit the incidental implementation-facing caption “No displayed evidence.” from the product UI. The scope statement can simply say “Report text and supplied flag only.”

The image shows the completed mixed scenario. Empty, running, needs-input, no-observation, failure and feedback states follow UX_STATES.md and need interaction validation during the authorized prototype phase.
