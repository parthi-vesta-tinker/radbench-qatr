# Revision and consistency notes

Version 0.2 / implementation handoff v1.6 · 14 September 2026

The user authorized prototype implementation after asking for typography, action placement and framework fidelity to be corrected. This handoff supersedes planning-only instructions in design-history. Current code implements the confirmed single-field input and separate required flag.

| Prior mismatch or ambiguity | Resolution |
|---|---|
| Report form had become a large left-side input pane | Restored Scope–Work–Studio: slim context left, input and comments center, actions/progress/guidance right. |
| Review button oversized or detached from its input | Compact primary action in the input action row next to the required flag. |
| Comments hidden behind a tab / QA brief too large | Comments are the center's visible deliverable; Studio contains compact operational context only. No evidence detail is in prototype scope. |
| Two clinical input boxes in early artifacts | One report_text field; heading recognizer extracts internal sections. |
| Flag unknown or optional in earlier drafts | Separate explicit required boolean; no default. It need not occur inside the pasted text. |
| Critical comments only for a missed flag | Retained for all detected critical observations, including flag Yes. Derived missed flag uses the four-case truth table. |
| Empty and failed states could be conflated | Successful no-observation result is separate from failed/needs_input; only completed observations have copy text. |
| Feedback Other might require explanation | Reason alone is sufficient for every down category. |
| Evidence/provenance expectations from the broad framework | No evidence UI. API retains input/source identity and explicitly unknown authorship/signature/upstream QA. |
| Finding type vs clinical urgency | Typed suggestion/discrepancy is separate from general/critical grouping. Unmet requirements require future explicit policy support. |
| Radiologist attention | Instructions request meaningful, concise issue/location/action comments. Domain evaluation still needs to measure unnecessary observations and wording. |
| Embedded flag metadata conflict | Not inferred from arbitrary prose. Separate operator flag is used. A future narrow conflict recognizer is an open enhancement, no implementation claim. |

Current implementation uses conservative English colon headings. This is an explicit prototype limit, not a modality restriction. Source clinical quality and sign-off are not verified by paste entry.

The generated concept is retained alongside screenshots of the actual browser. Follow UX_DESIGN_SYSTEM.md for precise sizing and behavior. The broad framework HTML is a future reference, not the running prototype. Current prototype README and implementation status take precedence over older package labels embedded in historical files.

The new backend and browser tests provide technical evidence; product UX acceptance, manual-backed criteria and real provider/domain evaluation remain open. There is no automatic permission requirement for ordinary continuation work already authorized by the user.
