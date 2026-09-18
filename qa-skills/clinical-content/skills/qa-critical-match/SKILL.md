---
name: qa-critical-match
description: "Identify report-supported potential critical findings and separately assess explicit current designation."
---

# Critical-finding review

Read the supplied critical-boundaries reference and the whole current report. Extract current
positive or suspected clinically consequential observations, retaining negation, uncertainty and
history. Use clinical knowledge to recognize meaning and patterns; keyword occurrence alone is
insufficient. Do not infer a new diagnosis from images, imagined symptoms or a weak association.

For each retained concern, choose catalog_match, outside_catalog or generic_provisional as
specified by the reference. Preserve source qualifiers and degree of certainty. Only claim a
catalog association when the applicable supplied binding supports it. A tenant may have the
43-entry draft evaluation catalog or generic review. Draft catalog association is never clinical
approval or proof of a policy violation. Without a catalog use generic_provisional.
For a catalog match retain the catalog ID, rule ID, exact source label, confidence and report
anchors privately. Preserve exact report exception evidence; do not invent doctor judgment.

Emit one CRIT candidate per distinct concern, with exact anchors, brief basis and concise
radiologist-directed action. A reporting inconsistency alone does not qualify; ordinary laterality
or measurement errors stay general unless a separate critical clinical condition is supported.
Retain comments even if explicitly flagged. Preserve an explicit conflict about the presence of a
critical condition as uncertainty; do not decide which statement is correct.

Independently return the current report designation and exact anchor when known. Missing or
conflicting flag assertions yield unknown. Do not infer a flag from a diagnosis or a call, and
never say a notification was missed. A report-level flag does not prove individual handling.

Use this sequence for each possible concern: identify the current positive or suspected assertion;
exclude negated, historical-only and explicitly resolved statements; preserve the report's certainty;
then decide whether the assertion itself is sufficiently consequential for generic provisional
review. A risk factor, symptom, procedure or recommendation is not a critical finding by itself.
When Findings and Impression conflict about presence, retain the concern as unresolved and request
confirmation without selecting which section is correct. Evaluate designation separately after all
concerns; the diagnosis text never supplies designation evidence.
