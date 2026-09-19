# UI enhancement research — 2026-09-18

> **Status: research and decision log, not authority.** This document records observed UI problems,
> proposes enhancements, and records the verdict on each. It does not supersede
> [WORKSPACE_SPEC.md](WORKSPACE_SPEC.md), [ANALYTICS_SPEC.md](ANALYTICS_SPEC.md) or
> [SKILLS_STUDIO_SPEC.md](SKILLS_STUDIO_SPEC.md).

> **Constraint provenance — read before acting on §2.** The research in §§1–9 was carried out
> against the tree as of `36624c2`, before the documentation clean-up in `c1b5377`. That clean-up
> deleted `prototype/BLUEPRINT.md`, `prototype/UX_DESIGN_SYSTEM.md`, `prototype/UX_STATES.md` and
> `prototype/REFINEMENT_SPEC.md`, and rewrote `ANALYTICS_SPEC.md`. **Every constraint in the §2
> table below now exists nowhere in the repository except in this file** — the three-panel
> architecture, the graphite palette and 32–36px button rule, "no new UI dependency, animation",
> and Analytics' "no decorative chart or added visualization library" are all unwritten as of
> `c1b5377`. They are recorded here as the rationale that shaped these proposals, not as live
> requirements. Treat §2 as history unless and until those rules are restored to a current
> specification. This does not invalidate any accepted proposal: each constraint only pushed the
> choice toward the more conservative option, so what was accepted remains safe — it is simply no
> longer mandatory.

Scope: application 0.13.0, bundle 1.17, foundation F3. Frontend only — `frontend/src/*.tsx`
and `frontend/src/style.css`. No backend, API, schema or workflow change is proposed.

---

## 1. Method and what the evidence is worth

The screenshots in `prototype/assets/` predate this build: they show System status docked in the
right rail and a five-stage pipeline (`language_review`, `consistency_review`,
`critical_finding_review`). The shipped build moves health into a header popover and runs the
four F3 stages. Critiquing those assets would have described a UI that no longer exists.

So this research drove the **current** build: `vite` dev server, `frontend/src` unmodified,
Chromium via Playwright, with `/api/v1/*` fulfilled by fixtures shaped to `generated-api.ts`.
Layout, CSS, component logic and computed styles are therefore real. The **data** is synthetic
and chosen to exercise states the default demo store does not reach (a degraded DBOS component,
a failed review, populated acceptance rows, a non-zero feedback reason breakdown).

Fresh evidence is in `prototype/assets/ui-research/`. Reproduction scripts were scratch and are
not committed; regenerate by serving `frontend` and stubbing the routes listed in `api.ts`.

Each finding below is tagged:

- **Measured** — a number read out of the live DOM (`getBoundingClientRect`, `getComputedStyle`,
  `scrollWidth`). Reproducible.
- **Code** — a statement about `frontend/src` that can be checked by reading the file.
- **Judgement** — a design opinion. Argued, not proven. Disagree freely.

No usability testing was run. No radiologist or QA operator was observed. Everything in §6
("Sequenced build") is an engineering estimate, not a validated priority order.

---

## 2. Constraints any fix has to respect

These are not my preferences; they are written commitments in this repo. They rule out the
obvious fixes, which is why the recommendations below are shaped the way they are.

| Constraint | Source | Consequence |
|---|---|---|
| Three-panel Scope–Work–Studio architecture is retained | UX_DESIGN_SYSTEM.md *(deleted in c1b5377)* | No re-architecture of the shell. Panels may change *content*, not identity. |
| Graphite palette, system font, 4px spacing scale, 32–36px buttons | UX_DESIGN_SYSTEM.md *(deleted in c1b5377)* | New severity colour must come from the existing token set or extend it minimally. |
| "No new UI dependency, animation, evidence drawer" | UX_DESIGN_SYSTEM.md *(deleted in c1b5377)* | No popover library, no focus-trap package, no chart library. Hand-rolled or nothing. |
| "Foundation work is not a redesign" | UX_DESIGN_SYSTEM.md *(deleted in c1b5377)* | Changes must be surgical and defensible one at a time. |
| Analytics "contains no decorative chart or added visualization library" | ANALYTICS_SPEC.md *(removed in c1b5377)* | **Charts are a deliberate exclusion, not an oversight.** See A-3. |
| "Coverage (recorded, unknown and not recorded) must be visible beside acceptance percentages" | ANALYTICS_SPEC.md *(removed in c1b5377)* | The wide acceptance table cannot be narrowed by dropping columns. |
| "Keep unknown and missing responses visible; use null for unmeasured clinical performance" | AGENTS.md | The four "Not measured" tiles cannot be deleted or hidden behind a toggle that defaults closed without a decision. |
| Report text is untrusted; no claim of clinical validation | AGENTS.md, invariants | Disclaimers are a safety requirement, not clutter. They may be *reweighted*, never removed. |

**The central tension.** Most of the crowding the user is reacting to is caused by a correct
safety instinct: every number on the Analytics page is qualified so nobody mistakes an
operational count for clinical accuracy. That instinct is right and must survive. What has gone
wrong is *typographic*, not editorial — caveats are rendered at the same size, colour and
position as the data they qualify, so they compete with it instead of supporting it. The fix is
to change their weight and placement, not their content.

---

## 3. Finding group F — Service health popover

`frontend/src/SystemStatus.tsx`, `style.css:754–760`.
Evidence: `assets/ui-research/health-popover-open.png`, `health-popover-degraded.png`.

The user's report — "not very easy to close… no intuitive close button… not that well organized"
— is accurate, and the cause is more specific than it first appears.

### F-1 · The panel is a dialog in appearance and a disclosure in behaviour · **Measured + Code**

`SystemStatus` renders `<details className="system-status">` with the body absolutely positioned,
`z-index:20`, `border-radius:6px`, `box-shadow:0 6px 20px #0002`. Measured at 1536×1024 the panel
is **370 × 610px**, floating over the page from `top:53px`.

Everything about that presentation says *modal dialog*. The implementation provides none of the
affordances a dialog carries:

| Dismissal route a user will try | Result | Evidence |
|---|---|---|
| Click an X in the corner | No X exists | 2 buttons in the panel: `Refresh status`, `Check OpenAI connection` — measured |
| Click outside the panel | **Stays open** | measured: `details.open === true` after a click at (700,700) |
| Press Escape | **Only if `summary` still holds focus** | measured: open after Escape with `body` focused; closed with `summary` focused |
| Click the trigger again | Works — but the trigger is a 12px text label with no state marker | see F-2 |
| Double-click the trigger | **Explicitly forced back open** | see F-4 |

The Escape handler is `onKeyDown` on the `<details>` element (`SystemStatus.tsx:28`), so it only
fires while focus is inside the subtree. Clicking any non-focusable text in the panel — a
component message, the "Last checked" line — moves focus to `body` and silently disables Escape.
The user has then exhausted every dismissal route they know.

**Recommend.** Commit to one model. Dialog behaviour is the honest match for the visual
treatment, and it is achievable without a dependency:

- add `role="dialog"` + `aria-label="Service health"` to `.health-panel`;
- add a first-child close button — `<button className="icon-button" aria-label="Close service health"><X size={16}/></button>` — reusing the exact pattern already in `App.tsx:32` for the undo bar, so no new idiom is introduced;
- move the Escape listener to `document` while open, so focus position stops mattering;
- add a `pointerdown` listener on `document` that closes when the target is outside the panel;
- return focus to `summary` on every close path, which the current Escape path already does correctly and should be factored out.

That is roughly 20 lines and no new package.

### F-2 · The health trigger is the only disclosure in the app with its own marker suppressed · **Code**

This is the root cause of "no intuitive close button," and it is a one-line regression.

The app uses `<details>` in **seven** places: service health, stakeholder outcomes, saved feedback,
"What is needed to measure this?", original QA comment, saved revisions, source & release details.
Six of them keep the native ▸/▾ disclosure marker, so the user learns that a triangle means
"this opens and closes."

`style.css:755` sets `list-style:none` on `.system-status summary` — **only** there. The health
trigger is replaced by a 7px hollow circle (`summary::before`, line 756) that never changes
between open and closed and carries no rotation, fill or direction.

So the one disclosure the user most needs to close is the one stripped of the affordance the
other six taught them. They are not failing to find a close button; they were shown a widget that
denies being openable at all.

**Recommend.** Keep the status dot — it is doing useful work as a severity slot (F-5) — and add a
separate state marker: a chevron that rotates on `[open]`, or restore the native marker beside the
dot. Either restores parity with the other six disclosures.

> Spec note: UX_DESIGN_SYSTEM specifies "thin icons, no large decorative containers" and
> "static progress icons." A rotating chevron is a state indicator, not decoration, but it is
> the one place this proposal brushes against the no-animation rule. A static ▸/▾ swap satisfies
> both and is the safer choice — **decide before building**.

### F-3 · The panel covers the entire QA Studio navigation · **Measured**

With the panel open at 1536px, geometric overlap against `.studio-tools button` and the column
heading returns every one of them:

```
covered: ["QA Studio", "New report", "Review history", "Feedbacks", "Analytics", "Skills & knowledge"]
```

A user who opens health to check why a review failed loses the navigation to go anywhere about it,
and — per F-1 — cannot reliably dismiss the thing covering it. The two failures compound: this is
why it feels trapping rather than merely fiddly.

**Recommend.** F-1's outside-click dismissal resolves this on its own (clicking a Studio button
both closes the panel and performs the action). If the panel remains large after F-6 trims it,
constrain with `max-height:min(70vh, 520px); overflow-y:auto`.

### F-4 · Double-click is deliberately coded to prevent closing · **Code**

`SystemStatus.tsx:29`:

```tsx
<summary onDoubleClick={() => { if(panel.current) panel.current.open = true; }}>
```

A double-click on `<summary>` naturally toggles twice and lands closed. This handler forces it
back open. The application therefore contains an explicit instruction to ignore a close gesture.

`frontend/tests/workspace.spec.ts` then *depends* on the workaround — it opens the panel with
`.dblclick()` and asserts the heading is visible. The test encodes the bug as the contract, so
removing the handler turns the test red for the right reason.

**Recommend.** Delete the handler; update `workspace.spec.ts` to open with a single `.click()`;
add an assertion that a click outside closes the panel. This is the cheapest high-value fix in
this document — roughly a 4-line change.

### F-5 · Component severity is invisible · **Measured**

`health-popover-degraded.png` renders a DBOS checkpoint timeout and an OpenAI auth failure. Both
appear in the same graphite as the three healthy rows: status words `ok` / `degraded` / `error`
share one `.meta` style (`style.css:661`), no icon, no colour, no ordering change. The only
severity signal in the whole feature is the summary label flipping to "Needs attention."

`configurationError` does get `.error` treatment (`SystemStatus.tsx:31`), but that is a separate
banner about configuration, not about which component is broken.

Note what this costs in the real failure case: DBOS degraded means *queued reviews may not
resume*. That is the single most operationally urgent thing this panel can say, and it is
typographically indistinguishable from "API responds."

**Recommend.** Encode severity on the component row: reuse `--danger` for `error`, `--attention`
(`#8A5700` light / `#edc078` dark — already defined, currently reserved for confirmed missed-flag)
for `degraded`, neutral for `ok`. Colour alone is insufficient — pair it with a `lucide-react`
icon already bundled (`AlertCircle`, `Check`), matching the `ProgressSummary` and `Studio` step
convention. Sort non-ok components first.

### F-6 · The panel is organised as prose, not as status · **Judgement**

Reading order today: heading → optional config error → caveat → component list → 2 actions →
optional probe result → caveat → timestamp. Three of the nine blocks are caveats, and the two
action buttons sit *between* the data and two more paragraphs about that data.

Both caveats are worth keeping — "Local checks do not verify model inference" is exactly the kind
of honesty this product needs. But in the healthy case the panel spends 610px and five identical
rows to say "everything is fine."

**Recommend.**

- Lead with a one-line verdict — `All 5 checks passed · 4:11:19 PM`.
- In the all-healthy case collapse the five rows behind "View all checks"; when anything is
  non-ok, show non-ok rows expanded and healthy ones collapsed.
- Move the two caveats to a single footer line above the actions, keeping the OpenAI-probe caveat
  adjacent to the button it qualifies rather than below it.
- Keep both buttons; they are correct and `Check OpenAI connection` correctly stays disabled
  until OpenAI reports `configured` (asserted by `diagnostics.spec.ts` — preserve that).

### F-7 · Mobile makes the popover a layout jump · **Code**

`style.css:827` sets `.system-status {position:static}` and reflows `.health-panel` into normal
flow at ≤650px. Opening health pushes the entire page down. Combined with no visible close
control, the mobile experience is worse than desktop.

**Recommend.** Fold into F-1. Once a close button exists, the static-flow mobile treatment is
defensible; without one it is not.

---

## 4. Finding group A — Analytics

`frontend/src/AnalyticsView.tsx`, `style.css:779–805`.
Evidence: `assets/ui-research/analytics-desktop-full.png`, `analytics-mobile-full.png`.

The user's report — "extremely complicated… very crowded… I don't understand" — is the most
important signal in this document, because the page is not actually dense with *data*. It is
dense with *qualification*. Measured on the live page:

| Measure | Value |
|---|---|
| Pane height, 1536×1024 viewport | **1918px** — 1.9 screens |
| Total words in the pane | 299 |
| Words inside `p.meta` / `.analytics-boundary` | **118 (39.5%)** |
| Disclaimer paragraphs | **8** |
| `<h2>` computed font-size, all four sections | **16px — identical** |
| Interactive controls on the entire page | **4** |
| Values reading "Not measured" | **4** |
| Height of the all-"Not measured" section | **345px (18% of the page)** |

That profile — two fifths qualifying text, no size hierarchy, almost nothing to interact with —
is the definition of "crowded but not informative." The reader has no way to tell what is a
number, what is a warning about the number, and what is not a number at all.

### A-1 · Four section headings at one size, no scan path · **Measured**

All four `<h2>` render at 16px. `.operational-analytics section` gives each an identical 1px top
rule and identical 24px margin (`style.css:800`). Two headings are questions ("Are stakeholders
accepting the work?", "Are critical findings being missed or overcalled?") and two are nouns
("Reviews submitted", "Feedback received"). There is no visual or grammatical cue to which
sections carry live data.

**Recommend.** Not a redesign — a hierarchy pass inside the existing type scale.

- Lift `<h2>` to 18px/600, matching the "Comments heading" rule already in UX_DESIGN_SYSTEM.
- Pick one heading voice. The business-question framing is the spec's own language
  (ANALYTICS_SPEC "Business question" column) and is more useful to a non-analyst reader — make
  all four questions, or make all four nouns with the question as a subtitle. Do not mix.
- Give each section a one-line status subtitle stating whether it has data:
  `128 reports · 71 outcomes recorded` vs `Not measured — no adjudicated cohort connected`.
  The reader then knows from the heading row alone whether to keep reading.

### A-2 · "Not measured" occupies 18% of the page, above the data · **Measured**

The critical-finding section renders four 14px `<h3>` tiles, each with a bold "Not measured",
a question, and a formula (`TP / (TP + FN)`). 345px, four identical negative results, positioned
*second* — above every populated section on the page.

Keeping it visible is required (AGENTS.md: "use null for unmeasured clinical performance"), and
that requirement is right: silently omitting the safety metric would be worse than showing it
empty. But "visible" does not mean "second, at full size, four times over."

**Recommend.** Preserve the disclosure; change its weight.

- Collapse the four tiles into one honest status block: heading, a single **Not measured**, one
  sentence of `critical_evaluation.reason`, and the existing `<details>` retained verbatim with
  the four formulas moved inside it.
- Move the section **below** the populated ones, above `.analytics-boundary`.
- Result: ~345px → ~110px, the safety statement stays on the page and stays first-class in the
  `<details>`, and the sections with real numbers surface.

This is the single largest readability win available and it removes no information.

### A-3 · A Period control with nothing that varies over time · **Judgement (spec conflict)**

The page offers `Last 7 days / Last 30 days / All time` but every value is a point-in-time scalar.
Switching period re-renders numbers with no basis for comparison, so the control cannot answer the
question it implies: *is this getting better or worse?* An 85.2% acceptance rate is unreadable
without knowing whether last week was 60% or 95%.

**This conflicts with a written product decision.** ANALYTICS_SPEC states the page "contains no
decorative chart or added visualization library," and AGENTS.md defers "advanced
trends/adjudication." That exclusion is defensible — a chart that invites clinical inference from
operational counts would be actively harmful here.

**Recommend — as a decision to make, not work to schedule.** Two options, both respecting
"no added visualization library":

1. **Comparison text only, no graphics.** Alongside each headline number show the prior
   equivalent period: `85.2% · previous 7 days: 81.4%`. Zero new dependency, zero new visual
   vocabulary, answers the direction question. Requires a backend period-comparison field.
2. **Hand-rolled CSS coverage bar** on the acceptance rows only — a single stacked bar of
   accepted / rejected / not-recorded, built from `<div>` widths, no SVG, no library. This makes
   the *coverage* point ANALYTICS_SPEC insists on ("coverage must be visible beside acceptance
   percentages") legible at a glance, which a 7-column table does not.

Option 1 is the smaller change and the smaller spec deviation. Neither should be built until
someone decides the exclusion was about decoration rather than about all visual encoding.

### A-4 · Three filters, two scopes, one visual treatment · **Code**

`Period` and `Source` are page-scoped and drive the API request (`AnalyticsView.tsx:18`).
`Assess acceptance of` is section-scoped and filters already-fetched rows client-side
(`AnalyticsView.tsx:38`). All three use the same `.history-filters` wrapper and render identically.

Nothing tells the reader that changing the third one leaves the other three sections untouched —
a user who sets it to "QA comments" and scrolls down may reasonably believe the feedback counts
below now describe QA comments too.

**Recommend.** Keep the page-scoped pair in the header row under the title. Restyle the
section-scoped control as an inline segmented pair (`Report | QA comments`) sitting on the
acceptance table's caption line, visually inside the table it governs. The `.history-filters`
class is doing triple duty across `ReviewHistory`, `FeedbackInbox`, `SkillsKnowledge`, `OutcomeLog`
and `AnalyticsView` — a `.section-filter` variant costs little and makes scope legible.

### A-5 · On mobile, 45% of the acceptance table is unreachable in practice · **Measured**

At 390px:

```
.acceptance-table clientWidth  358px
.acceptance-table scrollWidth  647px   →  289px (45%) off-screen
```

`.history-table {overflow-x:auto}` (`style.css:709`) means it *is* scrollable — the data is not
lost — and `document.scrollWidth <= innerWidth` still holds, so `diagnostics.spec.ts` passes.

But there is no scroll affordance whatsoever: no edge fade, no shadow, no hint text, no partial
column peeking at the cut. `analytics-mobile-full.png` shows the caption clipped mid-word
("…Latest per perspec") and the `Unknown`, `Not recorded` and `Acceptance` columns — including the
headline percentage, the whole point of the table — simply absent. A mobile user has no reason to
suspect horizontal scrolling exists.

This is the one finding here with a compliance edge: ANALYTICS_SPEC requires coverage to be
"visible beside acceptance percentages." On mobile neither is visible by default.

**Recommend.**

- Move `<caption>` out of the scroll container so the table's own label stops scrolling away.
- Add a right-edge gradient mask that disappears at `scrollLeft === scrollWidth - clientWidth`,
  plus `tabindex="0"` and `role="region"` on the scroller for keyboard reach (a standard
  accessible-table pattern, no dependency).
- Below 650px, consider transposing to one stacked card per perspective — each card carries all
  six counts plus the rate, nothing is hidden, nothing scrolls. Preferred if the work is affordable.

### A-6 · Failure counts styled identically to routine counts · **Measured**

`.metric-details` renders six rows — Queued 2, Running 1, Input needed 3, Failed 5, Completed with
comments 96, Completed without comments 21 — at identical size, colour and weight
(`style.css:806`). `Failed 5` and `Queued 2` are indistinguishable. Same pattern in
`ReviewHistory`, where the status column is raw lowercase enum text:

```
"completed"  rgb(32,36,43)  weight 400
"failed"     rgb(32,36,43)  weight 400   ← identical
```

**Recommend.** One shared `.status-pill` with three tiers (neutral / attention / danger) applied
in `ReviewHistory`, `AnalyticsView.metric-details`, the `.scope-nav` report rows and the health
panel (F-5). One idiom, four call sites, consistent with the existing "restrained semantic accent"
rule. Also capitalise the enum for display — `row.execution_status.replaceAll('_',' ')` currently
leaks storage casing into the UI.

### A-7 · The two metric grids are visually interchangeable · **Judgement**

"Reviews submitted" (128 / 117 / 14) and "Feedback received" (41 / 26 / 15) both render as
`.metric-grid` — three columns, 28px bold numerals, 12px grey labels. Scrolling past, they read as
one repeated component; the only differentiator is a 16px heading identical in size to every other
heading (A-1). Fixing A-1 largely fixes this; no separate work item.

---

## 5. Finding group X — cross-screen

### X-1 · Two navigation columns sandwich every screen · **Measured (spec conflict)**

`App.tsx:34–77` renders `.scope` ("Reports") and `.studio-column` ("QA Studio") on **every** view.
`.scope` lists drafts plus active and recent reports — relevant on Current report, dead weight on
Analytics, Feedbacks, Skills & knowledge and Review history. On Review history it is strictly
worse than dead: `review-history.png` shows the same four reports listed twice, once in the rail
and once in the table, with different truncation.

Mobile is where this stops being cosmetic. Measured at 390px on Analytics:

```
scope rail height          597px
studio column height       192px
chrome before content      880px
analytics content          2282px
total page                 3162px
```

`style.css:829` orders `.studio-column` first, `.scope` second, `.history-pane` third. A user who
taps "Analytics" is dropped at the top of **880px of navigation** — more than a full 844px
viewport — before the page they asked for begins.

**This conflicts with UX_DESIGN_SYSTEM's retained three-panel architecture**, so the full fix is a
product decision. Two tiers:

1. **Mobile ordering only — no spec conflict, ship it.** Give `.history-pane` a lower `order` than
   `.scope` in the ≤650px block so navigated content starts at the top; collapse `.scope` to a
   summary row. The three panels all still exist; only stacking order changes. This is a
   ~5-line CSS change and the highest-value-per-line item in this document.
2. **Desktop: hide `.scope` on non-`current` views** — requires the decision, since the panel
   would no longer be permanently present.

### X-2 · Seven disclosures, six summary styles · **Code**

`<details>` appears in `SystemStatus`, `OutcomeLog`, `Feedback`, `AnalyticsView`, `FeedbackInbox`
and twice in `SkillsKnowledge`. Their `summary` rules disagree on nearly every axis:

| Location | Weight | Colour | Marker |
|---|---|---|---|
| `.system-status` | 500 | inherit | **suppressed** (`list-style:none`) |
| `.outcome-log` | 600 | inherit | native ▸ |
| `.knowledge-history` | 600 | inherit | native ▸ |
| `.feedback-history` | inherit | `--muted` | native ▸ |
| `.inbox-list` | inherit | `--muted` | native ▸ |
| `.measurement-help` | inherit | inherit | native ▸ |

This is the systemic version of F-2: the app has no shared "this expands" idiom, so each instance
teaches the user something slightly different, and the one styled most differently is the one they
complained about. `Stakeholder outcomes` — a form that writes durable records — looks like
`Saved feedback`, a read-only list.

**Recommend.** One `.disclosure` base class: consistent marker, consistent 34px min hit area,
consistent focus ring. Two variants — *section* (600 weight, structural) and *aside* (muted,
supplementary). Reassign the seven call sites. Pure CSS plus className edits; no behaviour change,
no test churn. Do this **before** F-2, since F-2 is a special case of it.

### X-3 · Eight interactive targets under 40px on mobile · **Measured**

At 390px: theme toggle **30×30**, delete-draft **30×32**, health trigger 34px tall, "Current
report" 34px, `Refresh` 34px, three `<select>`s 35px, and `What is needed to measure this?`
**21px tall**. WCAG 2.2 AA (2.5.8) asks 24×24 minimum — most of these pass that floor — but
UX_DESIGN_SYSTEM's own 32–36px rule is violated by the two 30px icon buttons, and the 21px
`summary` is genuinely hard to hit.

**Recommend.** Raise `.icon-button` to 36px min on coarse pointers via
`@media (pointer:coarse)`; fold the 21px `summary` into X-2's 34px min-height. Small, uncontested.

### X-4 · The committed screenshots no longer describe the product · **Code**

`prototype/assets/implementation-desktop.png` and siblings show the pre-0.13 UI: System status in
the right rail, five pipeline stages, a "Try an example" selector. UX_DESIGN_SYSTEM tells the
reader to "inspect the actual screenshots and explicit sizing rules," and BLUEPRINT/README both
present these as current. Anyone following that instruction is designing against a dead build.

**Recommend.** Regenerate the three `implementation-*.png` assets from the current build, or mark
them historical in `prototype/README.md` the way superseded text is already marked elsewhere in
this repo. Cheap, and it protects every future design decision made from these docs.

> **Correction (2026-09-19).** This finding was made against `36624c2`. The documentation
> clean-up in `c1b5377` had already **deleted** `prototype/assets/implementation-desktop.png`,
> `implementation-feedback.png` and `implementation-mobile.png`, together with the
> UX_DESIGN_SYSTEM text that pointed at them. The only surviving references are inside
> `design-history/`, which holds its own copies of those files and is archived by definition.
> There is therefore nothing stale left to mislead a reader, and nothing to regenerate:
> re-adding current renders would introduce unreferenced binaries rather than correct anything.
> Current-build evidence is kept in `assets/ui-research/` instead, where it is cited.

---

## 6. Sequenced build

Ordered by user-visible relief per unit of risk. Estimates are engineering judgement only.

**Stage 1 — closes the two reported complaints. No spec conflict.**

| # | Change | Files | Size |
|---|---|---|---|
| 1 | Delete the `onDoubleClick` force-open; update `workspace.spec.ts` to single-click | `SystemStatus.tsx`, `tests/workspace.spec.ts` | ~4 lines |
| 2 | Health close button, document-level Escape, outside-click dismiss, `role="dialog"`, focus return | `SystemStatus.tsx`, `style.css` | ~20 lines |
| 3 | Restore a disclosure marker on the health trigger (F-2) | `style.css` | ~3 lines |
| 4 | Mobile ordering: content before nav (X-1 tier 1) | `style.css` | ~5 lines |
| 5 | Collapse the four "Not measured" tiles into one block; move below populated sections | `AnalyticsView.tsx`, `style.css` | ~25 lines |

Stage 1 removes ~235px from Analytics, ~790px of mobile pre-content chrome, and makes the health
panel dismissable by all four routes a user will attempt.

**Stage 2 — legibility. No spec conflict.**

| # | Change | Files |
|---|---|---|
| 6 | Unified `.disclosure` idiom across seven call sites (X-2) | `style.css` + 6 `.tsx` classNames |
| 7 | `.status-pill` severity tiers; apply in history, analytics, health, scope rail (A-6, F-5) | `style.css`, `ReviewHistory.tsx`, `AnalyticsView.tsx`, `SystemStatus.tsx` |
| 8 | Analytics heading hierarchy + one voice + per-section data-status subtitle (A-1) | `AnalyticsView.tsx`, `style.css` |
| 9 | Health panel: lead with verdict, collapse healthy rows, consolidate caveats (F-6) | `SystemStatus.tsx` |
| 10 | Mobile table: caption out of scroller, edge affordance, keyboard-reachable region (A-5) | `style.css`, `AnalyticsView.tsx` |
| 11 | Coarse-pointer tap targets (X-3) | `style.css` |
| 12 | Section-scoped filter restyle (A-4) | `AnalyticsView.tsx`, `style.css` |

**Stage 3 — requires a product decision first. Do not schedule as implementation work.**

| # | Decision needed |
|---|---|
| 13 | **A-3** — does "no decorative chart" forbid *all* visual encoding, or only ornament? If only ornament, build period-over-period comparison text (option 1) or the CSS coverage bar (option 2). |
| 14 | **X-1 tier 2** — may `.scope` be hidden on non-`current` desktop views, or is permanent three-panel presence load-bearing? |
| 15 | **F-2 marker** — static ▸/▾ swap or rotating chevron, given the no-animation rule? |
| 16 | **X-4** — regenerate `implementation-*.png`, or mark historical? |

---

## 7. Deliberately not recommended

Recording these so they are not re-proposed:

- **Removing or shortening safety disclaimers.** They are a stated invariant and correct for the
  domain. Every proposal above preserves their content and changes only weight and position.
- **Hiding "Not measured" behind a default-closed toggle.** AGENTS.md requires unmeasured clinical
  performance to stay visible. A-2 keeps it visible and first-class, just not four times over.
- **Dropping acceptance-table columns to fit mobile.** ANALYTICS_SPEC requires coverage beside the
  percentage. A-5 solves the width without losing a column.
- **Adding a charting library, popover library, or focus-trap package.** UX_DESIGN_SYSTEM forbids
  new UI dependencies. Every recommendation is hand-rollable in existing CSS plus the already
  bundled `lucide-react` icons.
- **Re-architecting Scope–Work–Studio.** Explicitly retained. X-1 tier 1 changes stacking order
  only; tier 2 is flagged as a decision, not a plan.
- **Animated transitions on the health panel.** "Avoid continuously animated agent diagrams" and
  "static progress icons" both point away from motion here.
- **A composite "report quality score"** to simplify Analytics. ANALYTICS_SPEC explicitly forbids
  inventing one, and it would be the most dangerous possible response to "the page is complicated."

---

## 8. Open questions

1. Who actually reads Analytics — QA leads, radiologists, facility administrators? A-1's heading
   voice and A-3's comparison framing both depend on the answer, and no persona is recorded in
   ANALYTICS_SPEC.
2. How often is the health panel opened, and in response to what? If it is mostly consulted after a
   failed review, F-6's verdict line should lead with the *failing* component rather than a roll-up.
3. Is the Period selector used at all? If no one changes it off the default, A-3 is moot and the
   control should arguably be removed instead of enriched.
4. Does any user reach this on a phone? Every mobile finding (A-5, X-1, X-3) is severe if yes and
   near-worthless if no, and the responsive CSS suggests someone thought it mattered.
5. Was `list-style:none` on the health summary (F-2) intentional — a deliberate "chrome affordance,
   not a disclosure" choice — or incidental? The answer changes whether F-2 is a regression fix or
   a design reversal.

---

## 9. Verification performed

Everything in this document is either a live-DOM measurement or a file reference; nothing is
inferred from the stale committed screenshots.

- Not run: no unit, DOM, or Playwright suite was executed. `npm install` was run in `frontend`
  to obtain Vite and Playwright; `frontend/src` was not modified.
- Not established: no accessibility audit, no contrast-ratio sweep, no screen-reader pass, no
  clinical or usability acceptance. WCAG 2.5.8 is cited in X-3 as a reference threshold only.
- Not implemented: no proposal here has been built, and no spec has been amended.

---

## 10. Decision log

Proposals are gated individually. Every verdict is recorded — Accepted, Parked and Rejected
alike — because parked items are a backlog and rejections are design rationale. A Parked item
stays alive and re-surfaces when this list is next reviewed; a Rejected item is not re-proposed
unless circumstances change.

Verdicts were given by Parthi on 2026-09-19 against rendered before/after mockups, not prose.

### Stage 1 — gated 2026-09-19

| # | Proposal | Verdict | Rationale recorded |
|---|---|---|---|
| P1 | Remove the `onDoubleClick` force-open from the health trigger; update `workspace.spec.ts` to a single click plus an outside-click assertion | **Accepted** | Accepted as proposed at the gate. No additional rationale given. |
| P2 | Health panel dismissable as a dialog: close button, document-level Escape, outside-click dismiss, `role="dialog"`, focus return | **Accepted** | Full dialog treatment chosen over the smaller disclosure-only variant, which was offered and not taken. |
| P3 | Restore a disclosure marker on the health trigger, **static ▸/▾** | **Accepted** | Static form chosen over a rotating chevron, consistent with the "static progress icons" rule. This also settles the open question listed as Stage 3 item 15, which is therefore closed. |
| P4 | Mobile: order navigated content above the Reports rail; collapse the rail to a summary row | **Accepted** | Accepted as proposed, over both a reorder-only variant and a park-pending-usage-data option. Note this commits effort to mobile while open question 4 (does anyone use this on a phone?) is still unanswered. |
| P5 | Collapse the four "Not measured" tiles into one verdict block and move the section below the populated ones | **Accepted** | Accepted with the move, over a collapse-in-place variant. Nothing is removed: the four formulas and the reason text stay inside the retained `<details>`. |

Stage 1 is gated in full. Stages 2 and 3 are not yet gated.

### Corrections to earlier statements in this document

- §6 Stage 1 previously implied a larger mobile saving than the measurements support. The
  measured figure is chrome before content **880px → ~283px, a ~597px saving** — the Reports
  rail moves below the content, it is not removed, and the header and Studio nav remain above.
- The `order` values sketched for P4 are illustrative. The existing ≤650px block already assigns
  `order` to five elements with implicit ties, and `.input-pane`/`.output-pane` sit inside
  `main.review-workspace` rather than directly in the flex container, so the exact cascade must
  be verified in the browser at implementation time rather than taken from the sketch.

### Not yet gated

Stage 2 (items 6–12) and Stage 3 (items 13, 14, 16 — item 15 closed by P3) remain open. No
implementation has started on any accepted item.

### Stage 2 — gated 2026-09-19

| # | Proposal | Verdict | Rationale recorded |
|---|---|---|---|
| P6 | One `.disclosure` idiom with *section* and *aside* variants across all seven call sites | **Accepted** | Accepted as proposed. Generalises P3 from a patch into a rule, and absorbs the 21px tap target from P11. |
| P7 | One `.status-pill` with danger / attention / neutral tiers, icon as well as colour, in Review history, Analytics, the health panel and the scope rail; non-ok health components sorted first; enum display text capitalised | **Accepted** | Full four-site application chosen over a health-panel-only variant. |
| P8 | Analytics heading hierarchy: 18px/600, one question voice, per-section data-status line | **Accepted** | Accepted including the copy change, over a sizing-and-status-only variant. Exact heading wording to be reviewed at implementation rather than taken from the mockup. |
| P9 | Health panel: verdict line first, healthy rows collapsed, non-ok expanded, caveats consolidated beside what they qualify | **Accepted** | Full reorganisation chosen over a verdict-line-only variant, accepting that `diagnostics.spec.ts` must expand "View all checks" before asserting the five component labels. |
| P10 | Mobile acceptance table transposed to one stacked card per perspective below 650px; caption out of the scroll container, edge affordance and keyboard-reachable region on desktop | **Accepted** | Stacked cards chosen over an affordance-only variant, so no column requires horizontal scrolling to reach. |
| P11 | `.icon-button` raised to 36px minimum under `@media (pointer:coarse)` | **Accepted** | Accepted as proposed. |
| P12 | Section-scoped acceptance filter restyled as an inline segmented control on the table's caption line, with a `.section-filter` variant | **Accepted** | Accepted as proposed. |

### Stage 3 — gated 2026-09-19

| # | Question | Verdict | Rationale recorded |
|---|---|---|---|
| 13 (A-3) | Does the Analytics chart exclusion cover all visual encoding, or only ornament? | **Comparison text only** | Show the prior equivalent period beside each headline number; no graphics. The hand-rolled CSS coverage bar was offered and not taken. **Not implementable in this change:** it requires a period-comparison field from the API, which is outside the frontend-only scope declared at the top of this document. Scoped as separate work. |
| 14 (X-1 tier 2) | May the Reports rail be hidden on desktop for the four navigated views? | **Rejected** | The rail stays permanently present on desktop. P4 addresses the mobile cost; the desktop cost (≈200px on four screens, and a duplicated listing on Review history) is accepted. Recorded as design rationale; not to be re-proposed. |
| 15 (F-2 marker) | Static ▸/▾ or rotating chevron? | **Closed by P3** | Settled when P3 was accepted with the static form. |
| 16 (X-4) | What should happen to the stale `implementation-*.png` assets? | **Regenerate** | Replace them from the current build rather than marking them historical. |

**Caveat on decisions 13 and 14.** Both were argued partly from written spec statements —
ANALYTICS_SPEC's "no decorative chart or added visualization library" and UX_DESIGN_SYSTEM's
retained three-panel architecture. As recorded in the constraint-provenance note at the top of
this document, neither statement survives in the repository as of `c1b5377`. The verdicts stand as
the product owner's intent; the justification offered for them at the gate no longer has a written
source. Decision 15 is affected in the same way by the now-unwritten no-animation rule.

---

## 11. Implementation record — 2026-09-19

All twelve accepted proposals are implemented. Frontend only: no backend, API, schema, workflow
or skill-content change. Decision 13 (period comparison) is **not** implemented — it needs an API
field and is out of this change's scope, as the gate recorded.

### Measured before and after

Both columns come from the same probe against the running build (Chromium, `/api/v1/*` stubbed to
`generated-api.ts` shapes), not from estimates.

| Measure | Before | After |
|---|---|---|
| Health panel height, all healthy | 610px | **285px** |
| Close controls in the health panel | 0 | **1** (`aria-label="Close service health"`) |
| Health panel ARIA role | none | **`dialog`** |
| Outside click dismisses | no | **yes** |
| Escape dismisses regardless of focus | no | **yes** |
| Double-click leaves it open | yes (forced) | **no** |
| Analytics pane height @1024 viewport | 1918px | **1670px** |
| Analytics `<h2>` sizes | 16/16/16/16px | **18/18/18/18px** |
| `failed` vs `completed` in history | identical `rgb(32,36,43)` w400 | **`rgb(156,36,27)` w600 vs `rgb(32,36,43)`** |
| Mobile chrome before navigated content | 880px | **283px** |
| Mobile acceptance table hidden width | 289px of 647px (45%) | **0px** (stacked cards) |
| Horizontal page scroll at 390px | none | **none** (unchanged) |

### A real defect found by the new test

The first implementation of the health dialog attached its Escape and outside-click listeners from
an effect keyed on React state set by `<details>`'s `onToggle`. That event is dispatched
**asynchronously**, so a dismissal arriving before it landed was silently lost: opening the panel
and pressing Escape immediately did nothing. `workspace.spec.ts` caught this; manual checks had
hidden it behind incidental waits.

The listeners are now mounted once and read `details.open` from the DOM, so no dismissal can race
the toggle event. The `open` state and `onToggle` handler were removed as redundant.

### Verification actually run

- `npx tsc -b` — clean.
- `npm run test:dom` — **19/19 pass**. Two tests were rewritten, not deleted: the health test now
  asserts all four dismissal routes and that a double-click no longer forces the panel open; the
  analytics test asserts the section-level `Not measured` verdict plus all four denominators
  inside the disclosure, preserving exactly what it was protecting.
- `npm run test:browser` — **8/8 pass** against the real FastAPI/DBOS backend in demo mode.
  `workspace.spec.ts` and `diagnostics.spec.ts` were updated where they encoded replaced
  behaviour; `f3.spec.ts` was not touched and still passes.
- `uv run python scripts/check_docs.py` — passes.

### Deviation from an accepted proposal

P4 was accepted as "reorder, and collapse the rail to a summary row". The reorder is implemented
and delivers the full measured saving (880px → 283px). The rail is **not** collapsed to a summary
row: it is moved below the content with its list capped at 220px and scrollable. A true collapse
needs a disclosure in `App.tsx` that would also affect desktop, which is beyond what was gated.
Nothing is hidden or unreachable in the shipped form. Say the word and the summary-row version is
a small follow-up.

### Not established

No usability testing, no accessibility audit, no contrast sweep, no screen-reader pass, and no
clinical or domain review. The measurements above are geometry and computed style; they do not
show that the screens are easier to use, only that the specific defects recorded in §§3–5 are gone.
