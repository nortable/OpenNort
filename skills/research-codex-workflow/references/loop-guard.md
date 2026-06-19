# Loop Guard Reference

Load this file when research, repair, search, debate, or experiment work repeats or stops changing
decision readiness.

## Progress Snapshot

Record a snapshot after each full adversarial round and before every expensive spawn:

```yaml
round: string
accepted_new_evidence_count: 0
resolved_critical_contradictions: 0
unresolved_high_impact_contradictions: 0
decision_readiness_delta: 0.0
new_primary_sources: 0
new_reproducible_artifacts: 0
repeated_task_signatures: []
repair_count_by_artifact: {}
cost_or_budget_delta: null
scope_drift: low | medium | high
loop_guard_action: CONTINUE | REPLAN | BRANCH | ABANDON | HUMAN_REVIEW
specific_next_evidence_target: null
```

## Loop or Stagnation Triggers

Declare loop risk when any condition holds:

- two consecutive rounds add no accepted material evidence;
- decision readiness does not change across two rounds;
- a normalized task, query, repair, or experiment signature repeats;
- the same artifact fails repair more than two times;
- the same hypothesis receives more than three experiment rounds without greater information value;
- most active work lacks a Decision Link;
- marginal expected information gain falls below marginal cost;
- debate repeats positions without a new evidence target;
- scope drift from the Task Charter becomes high;
- agents repeatedly rephrase the same unsupported claim.

## Required Action (Orchestrator-owned)

The Loop Guard worker REPORTS a `StagnationSignal` (information_gain, repeated_signatures,
scope_drift, suggested_new_evidence_target, consecutive_dry_rounds) and does NOT choose the action or
own the spawn/stop decision. The Orchestrator reads that signal, evaluates `stop_rule` (loop-until-dry,
deduping against everything SEEN), and records exactly one `loop_guard_action` in the
progress-snapshot / Round E ledger. The until-dry loop never relaxes the per-hypothesis round caps
below; the tighter bound always wins:

- `CONTINUE` with a specific new evidence target;
- `REPLAN` once at the current scope;
- `BRANCH` into an explicitly approved new question;
- `ABANDON` the task or hypothesis;
- `HUMAN_REVIEW`.

Invalid recovery instructions:

- try again;
- search more;
- run another experiment;
- keep iterating.

These are valid only if accompanied by a new discriminating evidence target.

## Hard Caps

- Three research or experiment rounds per hypothesis.
- Two repair rounds per implementation artifact.
- One automatic global replan.
- One or two response rounds in cross-falsification.
- Configured token, cost, wall-clock, and tool-call budgets when available.

## Round Coverage Log (canonical fields)

Every round summary carries a `coverage_log` so bounded coverage never reads as total coverage. Record
these keys (omit a key only when it does not apply):

```yaml
coverage_log:
  findings_deduped_against_seen: 0          # loop-until-dry dedup count this round
  consecutive_dry_rounds: 0                 # so "stopped because dry" is distinct from "stopped after one pass"
  deep_findings_count: 0                    # depth: deep findings produced (0 is a coverage gap, not a clean bill)
  verification_route_counts: {light: 0, adversarial: 0}   # proportionate-verification split
  findings_killed_by_majority_refute: 0
  items_truncated_or_sampled: []            # any top-K / no-retry / sampling bound
  lenses_or_sources_not_run: []
  external_verification_unavailable: []     # external-dependent claims no web/fetch tool could settle
  concurrency_cap_hit: false
  ran_as_sequential_fallback: false
```

`deep_findings_count == 0` and a non-empty `external_verification_unavailable` are both surfaced at
Round E.5 (Completeness Critic) and, if material, in the Round F checkpoint — never silently dropped.
