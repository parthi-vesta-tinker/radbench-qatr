# Revision 1.1 — consistency review

13 September 2026. Reviewed the framework, decisions, handoff, reference UI, case fixtures, comment packets, exports and agent entrypoints together. This is an artifact review, not usability or clinical validation.

## Requests and changes

| Request | Framework contract | Concrete artifact |
|---|---|---|
| Authorship/signature with version | Source identity includes separate author, signer, document status and signature; unknown stays unknown | Persistent workspace header; three signed synthetic sources; AC17/25 |
| Upstream QA provenance | Producer, check scope, source version, time, claimed result, evidence and trust; never blanket clearance | R-207 upstream spelling-only example; AC18 |
| Finding type | Suggestion, discrepancy, unmet requirement, separate from urgency and confirmation | All three types represented; AC19/30 |
| Radiologist attention cost | Short actionable text, no duplicate questions, compatible routine grouping, critical independent | R-207 clarification variants; QA_COMMENTS section 8; AC23/24/29 |
| Distinct panel meanings | Lower center is a selected-report container; Report, QA Brief, Comments and Evidence answer different questions | Six-slot Studio; named tool/subview; AC20 |
| Copy-ready QA comments | Two critical/non-critical sections; exact plain-text preview; recipient/version/profile binding | Three structured packets and seven text exports; AC21/22 |
| Radiologist variation | Nature, scope, template and guided action vary within explicit authority | Two hypothetical profile examples; no settings console; AC23/27 |

## Inconsistencies resolved

1. **QA Brief vs center area:** renamed the Studio tool QA Review, retained Brief as its internal assessment subview, and named the center container Selected-report workspace. Its initial Snapshot is source context, not another findings summary. Opening QA Review makes QA assessment explicit and prominent.
2. **Potential critical vs finding type:** removed potential critical as a competing fourth type. It is an independent confirmation/routing label; the sample missing-flag concern is an unmet requirement under an illustrative policy.
3. **Completion vs signature:** completed or final does not mean signed. A signed source cannot be overwritten because a communication preference permits minor corrections.
4. **Upstream pass vs local coverage:** the upstream sample claims spelling coverage only, is unverified, and earns no automatic local QA credit. Version or scope mismatch stays visible.
5. **Copy vs communication:** copied, human-recorded paste, integration confirmation, radiologist acceptance, verified amendment and critical-result communication are different facts.
6. **Brevity vs required action:** optional suggestions may follow preferences; required concerns and material uncertainty cannot be removed for brevity. Routine batching must not delay critical communication.
7. **Existing reply vs new message:** the R-207 packet asks only for the unresolved side and amended version following the prior reply, rather than repeating the original request.
8. **Source change vs current comments:** source/finding changes make prior composed text need re-review. History remains accessible; already copied text cannot be recalled.
9. **Empty section vs clearance:** the UI retains section counts/assessment status; exports omit empty sections without asserting no critical findings. Unclassified urgency remains visibly unresolved.
10. **Reference vs examples:** current reference is R-209 Comments; the prior R-207 Evidence image is historical. Both views remain supported; the generated image is illustrative, and exact export files govern copy text.

## Proposed defaults, not newly approved clinical rules

Report / Snapshot on initial selection, the QA Review label and Brief/Comments tabs, three type values, plain-text packet structure and profile resolution are explicit design proposals. Clinical routing, required inputs, release rules, real profile ownership, destination constraints and amendment authority remain open integration decisions.

The reference shows only three canonical rows to make Comments readable. It does not validate density for 10–20 concurrent reports. It shows an explicitly opened Comments view, not the initial selection state. In the image, type chips and Evidence links are UI annotations outside the text output; exports define the exact copied headings and content.

Draft text can be previewed and copied for preparation, with its status visible; copying is not authorization to send. A future live send action must satisfy the applicable review/authority requirements. Example profiles are alternatives, not conflicting simultaneous assignments.
