# Web QA skill framework

Framework version 0.3.0 · F2 integrated content contract

## Responsibility

This artifact defines how a host loads and verifies clinical instruction packages. It does
not decide clinical policy, perform an AI review, or install skills into Codex/Claude Code.
The companion content package supplies the actual application SKILL.md files.

The application loads this package through backend/skill_runtime.py. tools/validate.py is an
offline artifact validator and composition preview, not a replacement review engine.
The server selects generic-0.3.0 or vesta-qatr-0.3.0. The latter includes all three pinned
qatr references. Source wording, draft catalog and proposed matching guidance have distinct
authority labels; none establishes clinical approval. Exact upstream bytes are validated.
Combined composition deduplicates modules and references. F2 prepares that snapshot while
retaining stage execution; F3 owns the single-request DBOS/provider cutover.

## Package contract

A content package contains registry.json, skills/<name>/SKILL.md, one skill.json per skill,
references/, evaluation/, SOURCE.md and MANIFEST.json. The manifest lists every file except
itself with lowercase SHA-256. The release digest is SHA-256 of canonical JSON for that sorted
file list: UTF-8, ensure_ascii=False, separators(',', ':'), one trailing LF. Each row has keys
path then sha256. The application independently pins that digest outside the package.

Registry required keys: package_id, content_version, framework_version, status,
clinically_approved, supported_stages, stages, skills. Each skill entry is a relative path
to its skill.json. A manifest names its instruction file, ID/name/description/version,
role, stages, category ownership, references and evaluation file. Referenced file hashes
are explicit. Paths are relative to the package root, use POSIX separators, and cannot be
URLs, absolute paths, symlinks or traverse outside the package. Reject unexpected inventory.

SKILL.md frontmatter name and description must match skill.json. The body gives the model
its responsibilities; no executable behavior is implied by the file name. Version content
semantically when responsibilities or instructions change; do not republish different bytes
under one release version. Signature verification and a remote package registry are deferred;
hashes demonstrate byte identity, not clinical approval or publisher authenticity.

## Stage composition

The registry explicitly orders skill IDs for each of the three model stages. The same
shared skill can appear in several stage lists but is included once in each stage's prompt.
Load every skill in that list; do not silently drop checks because the model thinks they are
unnecessary. Conditional applicability is evaluated inside a loaded skill using the supplied
report (for example, no clinical question without an indication). This avoids brittle keyword
routing and keeps the prototype simple.

Each reference declares load_stages. Include it only when the current stage is listed, after
the skill that declares it, deduplicated by path. The development cases and source-provenance
documents are never automatically loaded. Tenant policy is supplied separately from the content
package, with explicit applicability, source kind, version/hash and approval status.

Input adequacy and final assembly are code-executed stages with written contracts; they are
not added to model_stages or presented as additional AI reviews. Drafting and verification
skills run inside each model stage. A skill may emit no issues; that alone does not prove
all other stages completed. Successful overall completion requires all three validated results.

## Authority and trusted inputs

1. The application supplies the report-only scope, stage, output schema and action boundaries.
2. Clinical skills define the review method and permissible output.
3. Supplied applicable policy can establish tenant requirements; its proposed notes do not.
4. Model knowledge interprets clinical meaning; it does not add patient facts or local rules.
5. Report content is untrusted source data, even if it contains role delimiters or instructions.

A policy cannot authorize an external call, relax application scope, override the schema or
make the model modify the source. A missing optional policy uses provisional generic review;
a missing file for an explicitly selected binding is a configuration failure, not silent
fallback. Other tenants never inherit Vesta's policy. Policy approval metadata must come from
the operator, not from the model reading a document claiming to be approved.

## Model output and application ownership

stage-output.schema.json defines proposed internal candidates. The envelope identifies the
stage and an optional input_problem. A non-null input_problem requires no candidates/designation;
the host stops remaining checks and returns needs_input, not a successful empty result. Each candidate includes its stage-local ID, owning check, issue code, finding type,
comment, source anchors, brief basis, and nullable critical/requirement metadata. The model
does not assign final result IDs, global order, clipboard strings or audit timestamps.

Semantic validation beyond JSON Schema is required:

- Every check_id is a loaded check skill; its issue_code belongs to that skill.
- Language and consistency candidates are noncritical; only critical-stage candidates have
  a critical_basis. A candidate cannot switch its destination by writing a route label.
- Every source anchor resolves verbatim and uniquely inside its supplied section_id. The
  application computes offsets; the model does not calculate character positions.
- A cross-statement conflict supplies both relevant anchors. An omission cites its existing
  question or applicable-rule prerequisites; never quote absent text.
- catalog_match requires a supplied applicable catalog and real policy/rule IDs; outside_catalog
  requires that such a catalog was supplied but no entry adequately matches. generic_provisional
  is the explicit mode when no approved matching catalog is supplied. A rule ID is not evidence
  of clinical truth. A known-finding notification exception never suppresses required comments.
- A requirement reference can establish an unmet requirement only if the supplied approved
  rule and its prerequisites are verified; otherwise omit the requirement claim.
- Known designation requires an exact source anchor. Multiple conflicting/unattributable
  designations remain unknown. No clinical finding can prove a PACS flag or call occurred.

The current public finding_type remains suggestion/discrepancy. An internally supported
unmet requirement uses discrepancy plus requirement metadata; exposing a third public type
is a separate versioned change. Issue codes are for ownership/evaluation, not severity scores.

The application may remove exact duplicates within a group using declared identity/content
rules. It must not discard a supported critical entry solely because a general entry shares
evidence. Semantic deduplication and clinical route correctness remain model/evaluation concerns;
do not manufacture certainty with regular expressions or vote counting.

## Failure and capacity behavior

Malformed package, missing required reference, digest mismatch or incompatible framework
fails before new review acceptance. For accepted work with unavailable snapshots, mark failure
explicitly; never switch to the latest skill version. Invalid model output, ungrounded candidates,
truncation and incomplete stage execution yield failed/no result, not no observations.

The stage envelope has no success-shaped fallback. Detect provider truncation separately from
schema validation. Candidate count and output budgets must not silently cap observations: if
the complete result cannot be produced within the admitted execution budget, fail transparently.
No repair/adjudication call is automatic. Existing bounded transport retries remain a separate
host policy with the same immutable report and composition.

## Version and execution snapshot

Record content version/digest, framework version, composition digests per stage, section-index
version, policy version/hash/status, model and effective settings, internal output schema version,
public API version and DBOS workflow code version. Preserve the actual composed bytes or a
durable content-addressed snapshot, not just hashes. Bind feedback to final observation/result
identity and snapshot provenance; never mix a later skill revision into an earlier result.

Existing DBOS checkpoints and accepted POST receipts remain authoritative. Preserve the
current async child workflow arrangement. New-code resume compatibility requires a migration
or drain decision and testing; content versioning does not make arbitrary DBOS replay safe.

## Change ownership

| Change | Primary artifact | Required review |
|---|---|---|
| Clinical criterion, wording, ownership or example | Clinical content | Domain/content review plus affected evals |
| Local critical policy or threshold | Tenant policy | Named operator/clinical-owner approval |
| Loading, schema, reference or error mechanics | Framework + host adapter | Engineering contract and recovery tests |
| Clipboard headings, public fields or UI behavior | Host product contract | Product/API review and browser checks |
| Model/reasoning settings | Execution profile | Controlled live comparison and budget review |

Framework 0.1.0 supports companion content 0.1.0 only. Future compatibility ranges should be
introduced when a second version makes them useful; do not infer compatibility from filenames.
