# Clinical behavior evaluation method

This package contains two different kinds of synthetic material:

- `suites/*.json`: 54 atomic-skill cases, six per skill, split into development and held-out partitions.
- `cases.json`: 25 earlier cross-stage regression cases retained for continuity.

All expected outcomes are `proposed_not_adjudicated`. They are design hypotheses—not clinical
truth, API replies or observed passes. The package is not clinically approved.

## Evaluation layers

1. **Artifact validation** checks skill identity, independent semantic version, changelog,
   stage scope, ownership, suite alignment, unique case IDs and pinned package bytes.
2. **Deterministic contract tests** run parser/gate cases and validate source grounding,
   output ownership and copy-safe output contracts without a provider call.
3. **Stage-model diagnostics** run one exact application stage with the same composed skill
   instructions and structured output used by the application. Only report text and its
   deterministic section index are sent; expectations are never sent to the model.
4. **Automatic scoring** checks expected issue code, finding type, source quote, observation
   count, forbidden codes, designation evidence and narrow comment-hygiene rules.
5. **Qualified adjudication** assesses clinical correctness, harmful overreach, routing,
   comment clarity and radiologist attention cost. Until this occurs, `clinical_pass` is null.

An automatic contract pass is not a clinical pass. Absence of an expected observation can reflect
a bad proposed expectation, model behavior or a skill defect and must be reviewed before changing
instructions. Keep variants of one clinical concept in one partition. Do not tune against held-out
cases and then continue calling them held out.

## Reproducible commands

```sh
python qa-skills/framework/tools/validate.py
uv run python scripts/evaluate_skills.py --skill qa-critical-match --partition development
uv run python scripts/evaluate_skills.py --skill qa-critical-match --partition development --max-cases 3 --execute --output .qa-data/evaluation/critical.json
uv run python scripts/score_skill_evaluations.py .qa-data/evaluation/critical.json --output .qa-data/evaluation/critical-scored.json
```

Planning is the default and performs no provider call. `--execute` requires `OPENAI_API_KEY`, a
configured model, an empty `QA_POLICY_PATH`, and explicit token/case ceilings. Results checkpoint
after each case. Record actual model, reasoning effort, usage, latency, skill versions and snapshot
hash. Provider usage is not exactly-once billing and the token ceiling is not a monetary account cap.

## Change discipline

Change one atomic skill when evidence identifies one owner. Bump that skill's version, describe the
reason in its changelog, change or add development cases, preserve held-out cases, rebuild the
package manifest/lock, and run the affected suite plus the complete contract regression. If a
shared or synthesis skill changes, rerun every stage that composes it.

Policy-bound checks require an explicitly supplied approved policy and a separately adjudicated
policy-bound suite. The current suites intentionally bind no policy. Do not activate a critical
catalog or remembered guideline to make a case pass.
