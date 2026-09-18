---
name: qa-internal-consistency
description: "Find incompatible assertions about the same observation across the current report."
---

# Internal consistency

Compare clinically linked statements across the entire current report. Establish shared identity
through compatible undisputed attributes; do not require the side/level/value being tested to
agree. Different lesions, dimensions and time points may legitimately differ. Do not force pairs.

Compare laterality/anatomy, measurements, current technique, chronology and Findings/Impression
meaning. Normalize equivalent units and reasonable rounding; do not infer growth from differing
axes. Distinguish contrast enhancement on a prior study from claims about a current noncontrast
scan. Respect explicit addendum corrections; do not flag a clearly resolved statement as unresolved.
A clinically reasonable Impression can synthesize descriptions without repeating their exact words.

One independent correction is one candidate: choose MEAS for numeric conflict, LAT for side/site/
level conflict, TECH for a technique conflict, COMP for a comparison/interval conflict and FIMP for
other descriptive contradictions. Two independent size and side corrections remain two issues,
even in one sentence. A side error visible in both Findings/Impression and laterality is one LAT,
not an additional FIMP. Recommendations and supplied-rule issues belong to qa-recommendations.

Cite both conflicting statements. Request reconciliation, not a chosen diagnosis/side/value.
Do not require every abnormality to be repeated in Impression. If a specific unanswered clinical
question is the issue, qa-clinical-question owns it. A potential critical condition may separately
be surfaced by critical review only with its own report-supported clinical basis.

For every proposed pair, state internally the shared entity, the disputed attribute and why the
statements cannot both describe that entity in the stated context. If any of those three elements is
missing, do not emit the contradiction. Normalize units before comparing measurements and retain
axis labels when present. Compare a current assertion with a prior assertion only when the report
claims an interval relationship. An explicit addendum correction resolves the superseded statement
unless the corrected text remains internally inconsistent.
