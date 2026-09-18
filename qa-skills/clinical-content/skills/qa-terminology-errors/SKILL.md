---
name: qa-terminology-errors
description: "Find actionable spelling, dictation and single-span terminology defects in supplied report text."
---

# Language and terminology

Read the whole report, including optional sections. Identify clear spelling/dictation mistakes,
meaning-changing terminology, unresolved placeholders or alternatives, and internally defective
single-span phrases. Preserve useful spelling corrections such as silhoutte to silhouette.
Do not enforce house style, expand all abbreviations, change valid uncommon terminology or
rewrite prose merely for preference. A clinically unusual assertion is not automatically a typo.

Suggest replacement wording only when unambiguous and meaning-preserving. Do not insert an
unstated "no", choose a side or change a diagnosis based on likelihood. Ask for clarification of
an ambiguous defect. Two separate assertions that conflict belong to consistency review, even
when a dictation mistake may have caused them. Critical designation belongs to critical review.

Emit TERM candidates with exact source anchors. Use suggestion for a clear editorial correction
and discrepancy for an unresolved defect materially affecting meaning. Keep one useful correction
per candidate, with location and requested action; do not write a full report rewrite.

Before emitting, classify the span as one of: unambiguous spelling/dictation correction,
unresolved placeholder/alternative, ambiguous meaning-changing phrase, or valid terminology.
Only the first three are actionable. Preserve negation, laterality, certainty and temporal status in
any proposed wording. When the intended replacement would require choosing among clinical meanings,
request clarification and do not supply a guessed replacement. Ignore grammar and punctuation that
do not impede professional use or alter meaning.
