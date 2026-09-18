> Current implementation: application **0.12.0**, bundle **1.16**, foundation **F2**. [Decisions and verification](FOUNDATION_CHANGELOG.md) supersede older baseline statements below. Fresh schema 3 and API 2026-09-17 are implemented; F2 imports the pinned qatr references and tenant-bound snapshots; single-call execution and session-spend enforcement remain F3 work.

F2 adds `catalog` and `policy_source` knowledge document kinds, full qatr source attribution,
server-controlled tenant release profiles, and immutable complete composition snapshots.
See [foundation changelog](FOUNDATION_CHANGELOG.md) for implemented boundaries and evidence.

> Next-build authority (2026-09-17): [clean-start foundation plan](FOUNDATION_PLAN.md). The proposal below is historical. Three calls, legacy projections, absent catalog and missed-flag copy are not new-build requirements. Compatible source-safety rules remain.

> Implementation note, 15 September 2026: This is the original adoption proposal.
> Its host integration is implemented in this project; consult BLUEPRINT.md, API_DESIGN.md
> and IMPLEMENTATION_STATUS.md for actual behavior and verification. Package paths are
> prefixed qa-skills/. Approved policy/catalog support remains deferred: guidance is unvalidated.

# Web application skill adoption specification

Edition 0.1.0 · 14 September 2026 · Target: Vesta Report QA browser prototype

**Deliverable status:** specification, framework contract and authored draft clinical skills.
The running web application has not been modified. These skills are not yet loaded by its
Agents SDK. No qatr origin change, deployment, live inference or clinical approval is included.

## 1. Product decision

Keep one report paste field and the existing Review report action. Understand a richer report
when it is supplied, without requiring QA to split it into fields or configure review modules.
Return only two comment groups: noncritical/general comments and critical-finding comments.
Make each nonempty group independently copyable, while retaining Copy QA review for both.

The clinical review may be sophisticated; its user interaction stays compact. Internal skills
are not new tabs, agents to manage, a questionnaire or additional user-visible workflow steps.
The source qatr repository provides reusable clinical ideas, not the host runtime or UI contract.

## 2. What exists and what changes

Inspected baseline: web-app bundle 1.8, API contract 0.4, implementation 0.3.0.

| Area | Existing implementation | Adoption target |
|---|---|---|
| Instructions | BASE and TASKS strings in backend/reviewer.py | Versioned skills and references selected by a small application loader |
| Input | One report_text field; whole report already sent to all three model stages | Same input, richer section indexing and explicit clinical context handling |
| Execution | Five DBOS steps, three sequential AI checks | Same visible steps and initial call count |
| Output | General and critical arrays; full-template copy | Same two arrays; two group-copy actions in addition to full copy |
| Evidence | Exact quote required for known flag status | Internal source spans for every observation; evidence viewer remains deferred |
| Verification | Shape/flag checks and matching-text deduplication | Stage self-verification plus deterministic grounding, ownership and assembly checks |
| Policy | Optional tenant-specific manual text | Explicit versioned policy bindings; absent manual retains provisional generic review |
| Feedback | Result/observation/flag targets, required negative reason | Same interaction; internally attributable to skill, prompt, model and policy versions |

The prior real web-app smoke test completed six reviews with 18 provider responses. Both
models put the noncritical effusion laterality discrepancy in critical comments, activating
incorrect Studio guidance. This motivates a regression case; it is not evidence that new
skills fix the problem. Baseline documentation saying no live run occurred predates that test.

## 3. Independently managed artifacts

| Artifact | Owned decisions | Location in this deliverable |
|---|---|---|
| Adoption specification | UX, scope, integration, phases and acceptance | This document and integration/ |
| Skill framework 0.1.0 | Package format, loading rules, versioning, candidate schema and validation tooling | framework/ |
| Clinical content 0.1.0 | Actual SKILL.md instructions, reasoning references, categories and evaluation cases | clinical-content/ |
| Tenant policy | Supplied manual/catalog, applicability and approval metadata | Operator-controlled binding; no active policy supplied here |
| Host application | FastAPI, DBOS, data storage, API projection and clipboard/UI rendering | Existing web-app project; future implementation |

These directories are independently versioned and can become separate repositories later.
Do not require a package registry, new service or dynamic skill marketplace for this prototype.
The web app should adopt an immutable copy of a content release and pin its digest. Developer
checkouts can override a local path explicitly; a review must always capture the resolved bytes.

The framework contains no critical-condition list. Clinical content contains no DBOS imports,
PACS connection, frontend code or credentials. Policy does not confer action permissions.
See [framework/FRAMEWORK.md](../qa-skills/framework/FRAMEWORK.md) for the normative package contract.

## 4. Rich report handling without a richer form

**Minimum retained:** one current report with identifiable, substantive Findings and Impression
or Conclusion. Recognize common colon headings and headings on their own line. Missing required
content yields needs_input with one specific request. Do not fabricate a section from unclear
narrative. Support for entirely unsectioned dictation is a later input-contract decision.

**Use when supplied in that report:** indication/reason for exam, clinical history, technique,
comparison, Findings, Impression/Conclusion and relevant addenda. They provide context and may
support an actionable question, recommendation or contradiction. Their absence does not create
a mandatory field or completeness finding. "Current report only" excludes retrieving patient
history; it does not mean ignoring history already pasted into the current report.

| Input situation | Required behavior |
|---|---|
| Simple Findings and Impression | Existing fast paste/review experience |
| Full report with optional sections | Index sections, preserve their boundaries and assess relationships across the complete text |
| Several observations or headings inside Findings | Keep all content and section occurrences; do not treat subheadings as separate studies |
| Prior comparison described in the report | Use the description as a current-report assertion; do not verify against an unseen prior or demand its upload |
| Embedded complete prior report or several studies pasted together | If a single current report cannot be reliably isolated, request the current report; never merge patients or studies |
| Addendum explicitly correcting an earlier assertion | Respect the explicit supersession for that assertion; retain both spans internally; do not flag an already resolved contradiction |
| Ambiguous conflicting addendum | Ask to reconcile the specific statements; do not pick the latest text solely by position |
| Missing/unclear flag documentation | Unknown, not evidence that a flag or call was missed |
| Long input within the existing 40,000-character cap | Review the whole source when it fits the selected model's request budget |
| Oversized request/model budget or truncated model output | Explicit bounded-input/configuration/failure state; never silent clipping or an empty successful review |

Retain the raw input and its hash. Build a derived section index with exact character offsets;
normalizing heading labels must not rewrite source text. Do not summarize, keyword-filter or
split a report into independent model chunks in this adoption. Such splitting could hide a
Findings/Impression conflict. Check the full instructions + policy + report + output allowance
before execution. Budget rejection occurs before model spend when it can be determined locally.

Metadata may be present. Do not judge patient identifiers, facility address, signatures or
notification logs as clinical defects. Existing authorship/signature/upstream-QA provenance
remains unknown unless a future explicit extraction contract is introduced. Explicit current
critical designation is the one already-supported narrow metadata extraction.

## 5. Map nine skills to the existing workflow

| Visible step | Content modules | Execution |
|---|---|---|
| Input validation | qa-input-adequacy | Deterministic structural gate; no new AI call |
| Language review | clinical-report-qa + qa-terminology-errors + drafting + verification | One existing model call |
| Consistency review | clinical-report-qa + qa-internal-consistency + qa-clinical-question + qa-recommendations + drafting + verification | One existing model call; optional checks apply only to supplied content |
| Critical finding review | clinical-report-qa + qa-critical-match + drafting + verification | One existing model call; includes report-documented designation assessment |
| Comment assembly | Output contract and deterministic assembly rules | Existing code-owned step; no claim of a fourth independent clinical review |

Each model stage sees the same complete report independently. The registry determines which
skills and references enter each stage. The model cannot self-install a skill, select a tenant
policy, browse for guidelines or call an external tool. SKILL.md is data until the application
loads it into trusted instructions.

Each stage checks its own proposed observations before returning them. Python then verifies
things it can establish: schema, allowed owner, source-span fidelity, IDs, flag quote grounding
and deterministic presentation. Those checks cannot prove clinical truth or recognize all
semantic duplicates. Add a fourth semantic reconciliation call only if measured residual
cross-stage failures justify its cost and latency; document that as a separate execution revision.

## 6. Use Astra's clinical knowledge deliberately

Clinical knowledge can interpret anatomy, disease terminology, modality descriptions,
mechanisms, time relationships, clinical significance and reasonable diagnostic synthesis.
Patient-specific facts must still come from the report. Mandatory requirements and policy
thresholds must come from supplied applicable rules. The skills define these boundaries,
not an exhaustive medical textbook or a fixed keyword classifier.

This permits recognizing a concerning reported pattern without the exact catalog phrase,
while distinguishing semantic equivalence from insufficient descriptors. Do not upgrade a
suggested diagnosis, choose the correct side of a conflict, invent a missing negation or
derive a treatment from model knowledge. An ordinary reporting error does not become a
critical finding because errors can affect care.

Use the configured Astra model through the existing gateway. Record effective model settings;
reasoning effort should be evaluated, not assumed optimal. First compare old instructions with
new skills under identical settings. Then compare reasoning settings separately. This document
does not certify an optimal Astra configuration or relax tracing, privacy or budget controls.

## 7. Two comment sections and copy contract

Keep the approved headings **General Comments:** and **Critical Findings comments:**. General
means noncritical observations. No third clinical-comment bucket is introduced. Grouping and
finding type are separate dimensions: a critical observation can be a suggestion to confirm
designation, while a general observation can be a discrepancy.

Each item should identify one issue, location and useful requested action in one concise
sentence, normally no more than 400 characters. This is an editorial target; retain the current
1,200-character public maximum until a versioned change is approved. Material uncertainty and
distinct actionable issues must not be dropped merely to meet a brevity target.

Critical comments contain the reported concern and a concise radiologist-directed action.
They do not assert that a notification was sent, prescribe treatment or declare a confirmed
policy violation without support. Longer operational instructions belong in Studio. No
PACS-specific paste destination is invented when configuration supplies none.

| Action | Clipboard payload |
|---|---|
| Copy general | QA review heading + General Comments heading + numbered general comments |
| Copy critical | QA review heading + report-derived missed-flag line + Critical Findings comments heading + numbered critical comments |
| Copy QA review | Existing full template: QA review, General Comments, missed-flag line, Critical Findings comments |

The missed-flag line remains associated metadata for critical review, not a third comments
section. It retains Yes / No / Cannot determine semantics. All text is plain text, generated
by the server from the same immutable validated result. Copy excludes evidence, internal IDs,
skill versions, UI notes and Studio instructions. The model never writes headings or timestamps.

When just one group is empty, show None. for it in the full template; its group-copy button is
disabled. When both are empty after completed checks, retain the no-action state and feedback,
with no template or copy actions. Failed/incomplete reviews have no copyable clinical result.

Read [integration/OUTPUT_CONTRACT.md](adoption-reference/OUTPUT_CONTRACT.md) for exact synthetic copy
examples and the treatment of source sections beyond Findings/Impression.

## 8. Preserve the familiar UI

Keep Scope–Work–Studio, existing neutral typography, Review report in the input action row,
comments directly below the input and no comments tab. Add a small Copy action beside each
comment-section heading. Retain the existing full-copy action and keyboard/native selection.
Show brief clipboard success/failure feedback without replacing the comments or moving focus.

Use compact comments by default; one-click expansion can show fuller review details later.
Do not add a skill-management screen, dense evidence dashboard or decorative agent activity.
The original pasted report and the QA output remain clearly separated. Studio displays actual
execution states and contextual guidance derived from the accepted result, not raw candidates.

Changing pasted input keeps prior results visibly stale and disables every copy/feedback
action until the reviewed snapshot is restored or a new review completes. A running review
continues against its original report and skill snapshot. No automatic review on paste.

## 9. Internal contract, public API and durability

Use the proposed [candidate schema](../qa-skills/framework/stage-output.schema.json) for model-stage output.
It separates clinical comments from check ownership, exact source anchors, critical basis and
optional requirement references. These support validation and future evidence inspection.
They are not automatically public API fields. Stable result observation IDs remain app-owned.

The current public report_section enum cannot represent History, Technique, Comparison or
Addendum. Do not falsely label those observations Findings or Impression. For this release,
extend that response enum deliberately under a new supported QA-Version; the exact version
identifier is assigned at implementation release. Retain existing labels and comment arrays.
Group copy_text fields are additive in that projection. Do not change the default version for
existing clients silently. The bundled browser pins the new supported version explicitly.

The older projection continues reading stored older results unchanged. A request for a new rich
result through an older projection that cannot represent its sections fails explicitly with an
upgrade-required error; it must not mislabel or omit observations. At adoption cutover,
new skill executions require the new API version. Old-version create requests return a documented
upgrade-required error before acceptance; the host does not run two clinical engines solely for
this prototype. Existing accepted receipts still replay unchanged. Keep the legacy default
version for old clients; do not silently route them into new semantics. The bundled browser pins
the new version. This compatibility limitation must be documented and tested before release.

Preserve tenant identity from authentication, immutable POST receipts and existing outbox
transactions. Resolve skill/policy/model configuration before acceptance and store immutable
composition bytes or a durable content-addressed reference with a retention guarantee. A digest
alone is not enough if its files can be replaced or removed. Model retries and DBOS recovery
must use the accepted versions, never reread the latest files. Follow the existing async DBOS
child workflow pattern; do not claim cross-code-version recovery or exactly-once model billing.

## 10. Phased implementation handoff

| Phase | Concrete work | Exit evidence |
|---|---|---|
| A — Specification and content | This framework, nine authored skills, references, stage mappings and eval inputs | Package/reference consistency checked; content explicitly unvalidated |
| B — Loader and richer input | Implement verified composition, immutable snapshot, richer section index and fail-closed errors | Offline loading, missing/drifted refs, section offsets, report replacement and recovery tests |
| C — Output and UX | Grounded internal candidates, versioned public section vocabulary, exact two-group copy and full copy | Contract tests; browser clipboard equality, stale-state blocking and no-empty-success checks |
| D — Live model comparison | Real authorized Astra runs against reviewed baseline/rich-report cases; account for failures/usage | Actual outputs, classification/grounding errors, radiologist attention and latency/cost recorded |
| E — Review and adopt | Resolve observed regressions; pin accepted content/runtime release | Product review and qualified clinical review; explicit remaining limitations |

Do not rebuild the web application or add an agent service. Specific code touchpoints and
acceptance cases are in [integration/IMPLEMENTATION_PLAN.md](adoption-reference/IMPLEMENTATION_PLAN.md).

## 11. Decisions, assumptions and deferrals

| Decision | Basis |
|---|---|
| Separate framework and clinical content artifacts | User explicitly requested independently managed skills similar to qatr |
| Preserve one paste field and five visible steps | User explicitly retained the familiar workflow |
| Review optional rich sections when supplied | User explicitly requested qatr-like handling of richer content |
| Keep identifiable Findings and Impression minimum | Existing confirmed minimum retained; richer content does not imply unsectioned input support |
| Two groups with independent copy plus full copy | User explicitly emphasized both groups being easy to copy |
| Keep missed-flag metadata | Earlier explicit output contract retained; no third comments section |
| Do not activate qatr catalog automatically | Source catalog differs from prototype examples and has no established active tenant approval |
| Keep generic provisional critical review without a manual | Existing app behavior; absence of policy is not a clean assessment or a Vesta-approved one |
| Keep feedback simple and non-learning | Existing user contract; feedback is a signal for evaluation, not automatic ground truth |
| Three model calls initially | Practical reuse of the implemented DBOS structure; more calls require evidence of value |
| New API projection for richer sections | Required by the existing closed section enum; avoid misrepresenting source location |

Deferred: external priors, image interpretation, report editing, fleet intake, HL7/PACS/chat
delivery, evidence UI, model training, automatic policy adoption and unattended release.
Clinical-owner decisions remain for policy approval, ambiguous critical thresholds and
evaluation acceptance targets. They do not block this specification or provisional content.

## 12. Provenance and verification limits

The package draws on the original qatr skills at commit
`b906151a2bdef8c206325de64d46b61cdf5b7ad7`, plus the existing web-app requirements and the
local analysis of inconsistencies. It is a new web-specific adaptation, not an upstream qatr
release. No original repository was changed. Source terms and clinical-policy approval are
not inferred from code access. See [clinical-content/SOURCE.md](../qa-skills/clinical-content/SOURCE.md).

The supplied development validator checks packaging and composition contracts only. The
evaluation scenarios contain synthetic report inputs and proposed expectations; no generated
model response is presented as real. See VALIDATION.md for actual checks completed on this
deliverable. Prior CLI tests do not count as tests of the web-app adoption.
