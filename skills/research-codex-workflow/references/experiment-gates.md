# Experiment Gates Reference

Load this file before training, evaluation, ablation, baseline comparison, paper claim, or costly implementation.

## Research charter

No major research task begins without:

- user objective;
- concrete decision to support;
- scope and non-goals;
- definitions and assumptions;
- success criteria;
- risk tolerance;
- available budget;
- expected output format;
- approval gates if needed.

## Decision link

Every question, task, experiment, repair, or claim needs:

```text
If positive: which decision or action changes?
If negative: which decision or action changes?
If null/inconclusive: what happens next?
What current uncertainty does this reduce?
What downstream task does this unlock?
```

Reject or park work without a decision consequence, except for a small explicitly declared exploration budget.

## Priority score

Use a configurable score when ranking research work:

```text
priority = clamp(
    0.30 * decision_impact
  + 0.25 * expected_information_gain
  + 0.15 * current_uncertainty
  + 0.15 * actionability
  + 0.10 * novelty
  + 0.05 * dependency_unlock
  - 0.15 * normalized_cost
  - 0.10 * execution_risk
  - 0.15 * redundancy,
  0, 1
)
```

Default decisions:

- no decision consequence -> `REJECT`;
- decision impact below 0.30 -> `PARK` unless exploration budget applies;
- priority below 0.45 -> `DEFER`;
- priority at least 0.45 and within budget -> `RUN`;
- high cost, high risk, or material scope expansion -> `HUMAN_REVIEW`.

## Preregistration

An experiment spec must be signed or hashed before implementation when it affects a result, paper claim, benchmark row, or expensive run.

Include:

- research question and decision link;
- primary and null hypotheses;
- falsification condition;
- variables, controls, and baselines;
- dataset/sample definition and inclusion/exclusion criteria;
- train/validation/test split;
- metrics, units, primary metric, and secondary metrics;
- success, failure, and equivalence thresholds;
- statistics and sample-size rationale where applicable;
- seeds and repetitions;
- known confounders;
- resource and safety limits;
- exact command or runner interface;
- expected artifacts;
- interpretation table for positive, negative, null, and failed runs;
- stopping conditions;
- downstream decision for each outcome.

A code worker may not silently edit these fields. Material changes create a new spec version and return to method review.

## Kill criteria

Stop, park, or replan when:

- the metric does not correspond to the claim;
- data leakage or benchmark contamination cannot be ruled out;
- the baseline is unfair or broken;
- the experiment cannot discriminate between hypotheses;
- a smaller validation can answer the question;
- result would not change the next action;
- smoke has NaN loss, empty positives, no outputs, failed round-trip, or no finite metric;
- repair repeats more than twice;
- the same hypothesis gets more than three experiment rounds without increased information gain;
- marginal expected information gain falls below marginal cost;
- drift from charter exceeds threshold.

## Loop Guard snapshot

After each research round, record:

- accepted new evidence count;
- resolved critical contradictions;
- uncertainty change for top questions;
- decision readiness change;
- new primary sources;
- completed experiment/replication artifacts;
- repeated task signatures;
- cost since prior snapshot;
- drift score relative to charter.

On stagnation, choose exactly one:

- `CONTINUE` with a specific new evidence target;
- `REPLAN` once at current scope;
- `BRANCH` into an approved question;
- `ABANDON`;
- `HUMAN_REVIEW`.

Never recover with a generic "try again".

## Judge rubric

Default weights:

```text
Decision relevance              20
Factual and technical validity  20
Evidence quality                15
Methodological validity         15
Reproducibility                 10
Alternative explanations        10
Scope adherence                  5
Clarity and calibrated language  5
```

Hard failures:

- unsupported material claim;
- citation does not support the claim;
- test or experiment result misreported;
- data leakage or invalid control;
- preregistration violation not disclosed;
- circular evidence;
- ignored contradictory high-quality evidence;
- unsafe or unauthorized external action;
- material scope drift;
- invented consensus.
