---
name: qa-input-adequacy
description: "Define minimum report content and ambiguity handling for the deterministic input gate."
---

# Input adequacy contract

The host executes this gate; it is not an additional model call. Require one nonempty report
within the admitted input size with identifiable substantive Findings and Impression/Conclusion.
Recognize common colon or standalone headings, including singular variants. Preserve the full
raw report and build a separate section index; do not clip optional sections or rewrite evidence.

History, indication, technique, comparison and addenda can be assessed when present, but their
absence is not a minimum-input failure. A missing required section, ambiguous multiple-report
paste or empty clinical content yields needs_input with one specific request to QA. Never guess
which patient/study is current. Do not request identifiers, signature, facility or an external prior.

If the model later detects unresolved multiple-report ambiguity not caught structurally, it returns
input_problem in its stage envelope and no observations; the host transitions to needs_input.
Model context/output capacity is a host execution constraint, not a clinical quality observation.

Treat headings as structural labels only when they introduce substantive section content. Inline
labels and Conclusion as the impression-equivalent are allowed. A word such as “impression” inside
ordinary prose or an addendum does not start another report. When an addendum clearly corrects the
current report, preserve both the original and correction for downstream review; do not classify it
as a second report. Ask for one current report only when identity boundaries remain unresolved.
