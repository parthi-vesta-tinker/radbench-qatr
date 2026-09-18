# Critical-match guardrails

Proposed interpretation guidance. **Not policy.** The source text governs on any conflict.

## Qualifier preservation

The source writes these qualifiers; keep them exactly and add none:

`acute`, `new`, `active`, `tension`, `unstable`, `complex`, `high grade`, `significant`,
`critical`, `ruptured`, `impending rupture`

Entries written **without** a qualifier must not be narrowed by one. These five are the
recurring offenders — they are not restricted to complicated, large, or severe cases:

- Bowel Obstruction
- Appendicitis
- Diverticulitis
- Pulmonary Embolism
- Pseudoaneurysm

## Compound entries

Slash-separated source labels are preserved as written. A slash does not establish synonymy.
Specifically do not equate:

| Reported | Is not automatically | Source entry |
|---|---|---|
| Pneumatosis | proven ischemic bowel | Ischemic Bowel (Pneumatosis) |
| Pericardial effusion | cardiac tamponade | Cardiac Tamponade |
| Nonspecific apical changes | active tuberculosis | Active Tuberculosis |
| Aneurysm | ruptured or impending rupture | Ruptured aneurysm or impending rupture |

## Match confidence vocabulary

| Value | Meaning | Emit a message? |
|---|---|---|
| `explicit_diagnosis` | Report names the diagnosis | Yes |
| `cautious_semantic_equivalent` | Clear clinical equivalent of a source label | Yes |
| `descriptor_only_uncertain` | Descriptors suggest it; diagnosis not stated | Yes, retaining the uncertainty |
| `outside_catalog` | Concerning, no exact catalog match | Yes, as a radiologist-review clarification, never labeled a confirmed critical result |

## Known-finding exception

Source guardrail: *"Known findings will not be called unless there is a significant change -
per the doctor's judgment"*.

- Explicit "known", "unchanged", "stable since" language is evidence and must be preserved.
- An old comparison date does **not** establish "known".
- Silence does **not** establish "unchanged".
- A keyword does not reveal the doctor's notification decision.
- Where an explicit doctor determination establishes the exception, respect it.
- Where the exception would decide a current candidate but its application is unresolved,
  request radiologist review concisely. Do not instruct a repeat call.

## Unresolved policy questions

These are open for the clinical owner and must not be resolved by the model:

1. Do ambiguous qualifiers — `complex`, `unstable`, `significant`, `high grade`, `critical` —
   have defined thresholds?
2. Does "Cerebral hemorrhage/hematoma" include subarachnoid, subdural, epidural,
   intraventricular, and intraparenchymal?
3. What evidence satisfies the doctor-judgment known-finding exception?
4. How are suspected-but-unconfirmed diagnoses handled, apart from the abuse entry?
