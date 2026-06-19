# Experiment Card Reference

Load this file before any costly or claim-producing experiment, training run, evaluation, baseline
comparison, result-table row, or implementation branch that may support a paper or report claim.

No experiment may begin unless it has a Decision Link and an Experiment Card. Technical curiosity is
not enough.

## Gate Questions

Before approving an experiment, answer:

1. Can the result discriminate between live alternatives?
2. Is there a cheaper minimal test?
3. Are denominator, sample, split, metric, and control definitions frozen?
4. What will positive, negative, null, and failed outcomes change?
5. Could leakage, confounding, or implementation drift make the result uninterpretable?
6. What is the stopping condition?

Reject or redesign experiments that cannot answer the decision question.

## Experiment Card

```yaml
experiment_id: string
version: 1
decision_link:
  if_positive: string
  if_negative: string
  if_null: string
research_question: string
primary_hypothesis: string
null_hypothesis: string
alternative_hypotheses: []
falsification_condition: string
minimal_discriminating_test: string
dataset_or_sample_definition: string
inclusion_exclusion_rules: string
split_or_sampling_protocol: string
controls_and_baselines: []
primary_metric: string
secondary_metrics: []
success_threshold: string
failure_threshold: string
equivalence_or_inconclusive_rule: string
random_seeds_or_repetitions: []
known_confounders: []
resource_limits: string
stop_conditions: []
exact_run_command_or_runner: string
expected_artifacts: []
interpretation_table:
  positive: string
  negative: string
  null: string
  failed_run: string
downstream_decision_for_each_outcome: string
approved_by: []
spec_hash: string
```

## Priority Score

Use a configurable score when ranking work:

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

Default interpretation:

- no explicit decision consequence -> `REJECT`;
- low decision impact -> `PARK` unless using bounded exploration;
- below threshold -> `DEFER`;
- high information value within budget -> `RUN`;
- high cost, high risk, protocol change, or material scope expansion -> `HUMAN_REVIEW`.

## Mutation Rule

No implementation worker may silently change hypotheses, metrics, thresholds, splits, denominators,
controls, sample definitions, or acceptance criteria. A material change creates a new card version
and returns to relevance/method review.
