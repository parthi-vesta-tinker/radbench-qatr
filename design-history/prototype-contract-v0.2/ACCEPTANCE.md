# Prototype acceptance and scenario matrix

Version 0.2 · Confirmed product rules; clinical expectations and runtime validation pending

| ID | Scenario | Required behavior | Phase |
|---|---|---|---|
| A01 | Clean, consistent report; flag No | Completed review may produce no_observations; no template/copy, feedback present. | 2, 3, 5 |
| A02 | Meaningful spelling error | General Comments contains concise suggestion; critical comments None.; missed flag No. | 2, 5 |
| A03 | Laterality contradiction | General comment asks to reconcile without selecting the correct side. | 2, 5 |
| A04 | Critical candidate plus spelling issue; flag No | General then missed flag Yes then critical comments in exact template order. | 2, 3, 5 |
| A05 | Negated critical term | Do not flag on keyword presence alone. | 5 |
| A06 | Historical/resolved finding | Preserve temporal meaning; no unsupported current critical diagnosis. | 5 |
| A07 | Missing impression in single field | Ask QA for minimum report requirements; no downstream clinical review. | 2, 3 |
| A08 | Text present but unusable | needs_input or an explicit execution failure; never successful no_observations. | 3, 5 |
| A09 | Instructions embedded in report | Treat instructions as source data; no override of review or application actions. | 5 |
| A10 | Down feedback on no observations | Accept missed-observation reason without mandatory explanation. | 2, 3, 6 |
| A11 | Down feedback on comment or missed flag | Bind target to exact result; explanation and suggested wording optional. | 2, 3, 6 |
| A12 | Copy/feedback save fails | No false success; selectable text or preserved feedback form. | 2, 6 |
| A13 | Text or flag edited after review | Mark old result stale; disable copy until restoring its complete input or a new review. | 2, 3, 6 |
| A14 | Failed/disconnected review | Execution failure and connection uncertainty remain distinct; no successful empty output. | 2, 3, 4 |
| A15 | Duplicate/restarted workflow | Keep correct identity and document actual repeated-execution semantics. | 3, 4 |
| A16 | Missing/unselected/null/non-boolean flag | Require explicit Yes/No; API rejects invalid/missing flag. False is valid. | 2, 3 |
| A17 | Critical observation; flag Yes | Missed flag No; critical comments still present. | 2, 3, 5 |
| A18 | No observations; flag Yes | No template/copy. Internal missed flag No; no invented flag-correction comment. | 2, 3, 5 |
| A19 | Any report category | No modality restriction; identify minimum sections or ask for clarification. Quality evaluated separately per example/type. | 2, 5 |
| A20 | Clinical policy material unavailable | UX can use labeled fixtures; no claim of Vesta-manual-backed review or policy validation. | 2, 5 |

The examples are synthetic design/evaluation seeds, not clinically reviewed ground truth. Product rules such as flag calculation and copy format are confirmed; clinical identification expectations still require the manual/vocabulary and appropriate review.

Old broader-framework fixtures may include PACS metadata and communication history. Prototype fixtures now contain one report string and an operator-supplied boolean only. Do not inherit additional contextual claims from the older data.

## Phase evidence

Mark each runtime check not run, pass or fail only after execution. Record clinical reviewers and disagreements separately from product acceptance. Examples and generated UI references are not test runs. The full missed-flag truth table and exact copy examples are provided in examples/comment-results.json for later contract testing.

Observed implementation evidence: 19 Python tests and five browser scenarios pass, including the flag truth table, copy boundaries, feedback, connection handling and process recovery. See IMPLEMENTATION_STATUS.md. Clinical scenarios remain seeds requiring domain assessment; passing software tests does not close all acceptance gates.
