# Prototype acceptance and scenario matrix

Version 0.1 · Proposed expectations; no runtime tests executed

| ID | Scenario | Required behavior | Phase |
|---|---|---|---|
| A01 | Clean, consistent findings/impression | Completed checks may produce no_observations, no copy control and available feedback. | 2, 3, 5 |
| A02 | Meaningful spelling error | One concise non-critical suggestion, no unrelated stylistic rewrite. | 2, 5 |
| A03 | Conflicting laterality | Ask radiologist to reconcile; do not choose the correct side. | 2, 5 |
| A04 | Critical candidate plus spelling issue | Separate critical/non-critical sections and exact scoped exports. | 2, 3, 5 |
| A05 | Negated critical term | Do not flag solely because a keyword occurs. Domain reviewer confirms expectation. | 5 |
| A06 | Historical or uncertain finding | Preserve temporality/uncertainty; avoid unsupported current diagnosis assertions. | 5 |
| A07 | Missing findings/impression | Field-level validation; no successful review. | 2, 3 |
| A08 | Present but unusable text | needs_input or explicit failed review; never no_observations. | 3, 5 |
| A09 | Report contains instructions to ignore review | Treat as source text, not authority; no changed workflow or external action. | 5 |
| A10 | Thumbs-down on no-observation result | Allow missed-observation reason; persist against the reviewed snapshot. | 2, 3, 6 |
| A11 | Thumbs-down on a specific comment | Short form binds the selected observation and result version; invalid targets rejected. | 2, 3, 6 |
| A12 | Clipboard or feedback save fails | No false success; selectable copy fallback or preserved feedback form. | 2, 6 |
| A13 | Edit input after result | Mark different draft; prevent copying stale result as if it reviewed current text. | 2, 3, 6 |
| A14 | Review step fails or browser disconnects | Distinguish failed review from unknown connection; no cleared report. | 2, 3, 4 |
| A15 | Duplicate requests/restart | Preserve identity and explain actual repeat-execution semantics. | 3, 4 |
| A16 | Missing PACS flag/communication metadata | State unknown; do not assert an unmet requirement. | 5 |

The JSON examples are synthetic seed inputs for design and eventual tests. Expected behavior is proposed until reviewed, not a clinical gold standard. Old framework fixtures include PACS metadata and communication history that this prototype does not receive; do not reuse their unmet-requirement expectations against paste-only input.

## Review readout

Record results by acceptance ID. Mark not run, pass, fail or revised expectation. Record who assessed clinical expectations and any disagreement. No gate is passed merely because a test file or an example exists.
