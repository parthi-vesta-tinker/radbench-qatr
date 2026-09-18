> Current implementation: application **0.13.0**, bundle **1.17**, foundation **F3**. [Decisions and verification](FOUNDATION_CHANGELOG.md) supersede older baseline statements below. Fresh schema 4 and API 2026-09-18 are implemented. F3 adds one combined request, guarded dispatch and durable response checkpoints. F4/F5 remain separate gates.

> Next-build authority (2026-09-17): [clean-start foundation plan](FOUNDATION_PLAN.md). Current Workspace behavior supersedes the old state table. Keep independent drafts during accepted reviews; unknown provider outcome requires deliberate rerun, not automatic retry.

> **Current release 1.14 / application 0.10.0:** [Workspace specification](WORKSPACE_SPEC.md) governs the current UX. [Analytics specification](ANALYTICS_SPEC.md) defines the feedback inbox, stakeholder outcomes, metric denominators and unmeasured clinical performance. [Implementation status](IMPLEMENTATION_STATUS.md) records verification; [Backlog](BACKLOG.md) records deferred work. Earlier release-specific text below is historical where it conflicts. See [Skills Studio specification](SKILLS_STUDIO_SPEC.md) for the new content review and draft editor.

# Current refinement contract — v0.6 / bundle 1.10

Read [REFINEMENT_SPEC.md](REFINEMENT_SPEC.md) first. It supersedes conflicting baseline requirements below: missed-flag UI/copy is deferred; comments, progress and Studio layout are refined; inline headings, persistent review history and saved feedback are implemented. Preserve legacy API receipts and clinical instructions.

---

> Release note (15 September 2026): This planning/baseline document is retained for continuity.
> The current skill-enabled prototype is specified in BLUEPRINT.md and API_DESIGN.md;
> implemented features and verified outcomes are recorded in IMPLEMENTATION_STATUS.md.
> Local startup is documented in ../LOCAL_TESTING.md.

# Report-only UX states

Contract v0.3

| State | Center workspace | Actions |
|---|---|---|
| Empty | One paste field; findings/impression hint; output placeholder. | Review validates minimum input. No flag selector. |
| Ready | Pasted report is editable. | Review report submits report_text only. |
| Running | Original input snapshot is reviewed; truthful progress in Studio. | New submit waits; editing creates a draft, not a new job. |
| Observations | General and critical comments in the standard template. | Copy complete template; feedback enabled. |
| Unknown designation | Critical comments remain; missed flag says Cannot determine with a short note. | No metadata selection is requested. |
| No observations | “No actionable observations” / “In the supplied report.” | No template/flag/copy; feedback remains. |
| Needs input | Specific missing/ambiguous section message. | Correct report and request review again. |
| Failed | Safe error; no partial/empty successful result. | Retry as a new request when ready. |
| Changed report | Previous result visibly stale. | Copy/feedback disabled; restore submitted text or review the new report. |
| Reconnecting | Known result/run retained; current status unknown. | Resume polling same review; no fabricated completion. |
| Clipboard failure | Selectable exact copy text; no Copied success claim. | Manual selection/copy. |
| Feedback failure | Retain reason and optional text. | Retry unchanged feedback with the same idempotency key. |

No report automatically triggers review on paste. There is no flag default to carry across reports. Initial state and replacement flows have zero radio controls. Reload restores only the current v0.3 review identity/text, not a history list.

Thumbs-down requires one reason; explanation and suggested wording remain optional including Other. Default target is whole review; optional observation/missed-field targeting. Cancel does not edit the result. A successful save requires server acknowledgement. Copy never records delivery.
