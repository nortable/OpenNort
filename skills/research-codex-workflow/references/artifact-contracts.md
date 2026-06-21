# Artifact Contracts Reference

Load this file when creating or validating full adversarial artifacts.

> Machine source of truth: `scripts/schemas.py` (the `SCHEMAS` registry) is authoritative for
> required keys, enums, int bounds, and list-element contracts. Both `validate_artifacts.py` and
> `run_synthetic_fixture.py` import it, so the prose below and the templates can never drift from
> what is enforced. `JudgeScore.final_class` and the ledger `decision_class` are DISTINCT fields that
> share a vocabulary; they are linked by `CLASS_MAP` (`rejected` normalizes to
> `rejected_or_unsupported`).

Recommended transient workspace:

```text
.research-workflow/
└── runs/
    └── <run_id>/
        ├── 00-charter.yaml
        ├── 01-dispatch-plan.yaml
        ├── round-a-findings/
        ├── round-b-critiques/
        ├── round-c-evidence-decisions.yaml
        ├── round-d-judge-scores/
        ├── evidence-packets/
        ├── round-e-decision-ledger.yaml
        ├── round-f-user-checkpoint.yaml
        ├── round-f-user-checkpoint.md
        ├── experiment-cards/
        ├── progress-snapshots/
        ├── round-g-final-report.yaml
        └── round-g-final-report.md
```

Keep transient workspaces uncommitted by default unless the user asks for a durable evidence bundle.

## Common Envelope

A prose-only mixin (no standalone producer or template): these fields may be layered onto any worker
artifact when a richer status envelope is needed. `scripts/schemas.py` carries a `common-envelope`
schema for `--artifact` validation, but no run artifact is required to be a bare envelope.

```yaml
run_id: string
task_id: string
artifact_id: string
agent_role: string
status: completed | blocked | failed | needs_review
summary: short decision-relevant summary
evidence_ids: []
artifact_paths: []
uncertainties: []
risks: []
recommended_next_actions: []
stop_signal: null
```

## Subagent Record

One retained JSON file per dispatched subagent (`agents/<agent_id>.json`), kept after the run for
debugging and later upgrades.

```yaml
agent_id: string
role: string
round: string
dispatch_kind: barrier | pipeline
status: completed | blocked | failed | needs_review
output_artifact_path: string        # the artifact (or dir) this subagent produced
raw_output: null                    # optional: the subagent's full raw output
model: null
tokens: null
prompt_summary: null
redispatch_count: 0
schema_validated: true
error: null
```

## Completeness Critique

Returned by the Completeness Critic in Round E.5, before the Round F checkpoint.

```yaml
gap_id: string
gap_type: lens_not_run | claim_unverified | source_unread | hypothesis_untested
severity: must_close | should_close | acceptable
suggested_action: string
produced_reviewed_findings: false   # the critic must not have authored any reviewed finding
unresolved_must_close: []
```

## Finding

```yaml
finding_id: string
agent_id: string   # author identity for the generate/verify provenance check
role: string
claim: string
claim_type: observation | inference | recommendation
provisional_severity: blocker | warning | info | unsupported
affected_decision: string
evidence:
  - file_path: null
    line_or_symbol: null
    command: null
    output_summary: null
    statistic_or_observation: null
    source_identifier: null
    retrieval_date: null
    artifact_path: null
    artifact_hash: null
counterevidence: []
uncertainty: string
validity_verdict: null | sufficient | insufficient | fatal_flaw   # data, not an action verb
```

## Critique

```yaml
critique_id: string
agent_id: string   # must differ from the target finding's agent_id
target_finding_id: string
attack_type: evidence_gap | wrong_scope | wrong_denominator | confounder | implementation_misread | irrelevant | circularity | leakage | other
critique_claim: string
evidence: []
minimal_test_to_resolve: string
expected_decision_impact: string
verdict: valid_attack | partial_attack | weak_attack | unsupported_attack
refute_disposition: refuted | not_refuted | uncertain   # default refuted when uncertain (R15)
lens: string   # the refuter's distinct perspective (e.g. correctness, methodology, decision-impact)
```

## Evidence Decision

```yaml
claim_or_critique_id: string
agent_id: string
support_status: accepted | partially_supported | unsupported | contradicted | needs_evidence | needs_user_decision
evidence_quality: high | medium | low | none
accepted_evidence_ids: []
required_followup: string
downgraded_severity: blocker | warning | info | unsupported
reason: string
```

## Judge Score

```yaml
packet_id: string
judge_id: string
agent_id: string   # must differ from every source-claim finding author
blocker_score: 0
warning_score: 0
false_positive_risk: 0
decision_relevance: 0
evidence_quality: 0
technical_validity: 0
methodological_validity: 0
reproducibility: 0
final_class: accepted_blocker | accepted_non_blocking | rejected_or_unsupported | needs_user_decision
hard_gate_failures: []
rationale: concise evidence-based rationale
```

## Orchestrator Decision

```yaml
issue_id: string
title: string
decision_class: accepted_blocker | accepted_non_blocking | rejected_or_unsupported | needs_user_decision
action: RUN | DEFER | PARK | REJECT | HUMAN_REVIEW
evidence_ids: []
affected_files: []
recommended_change: string
alternatives: []
user_decision_needed: false
edit_after_approval: false
```

## Worker Ownership

Worker ownership is expressed as a `dispatches[]` entry in the Dispatch Plan below — `role`,
`permissions`, `files_owned`, `files_forbidden`, `validation`, and `required_output_schema` (the
expected output). There is a single producer of ownership (the dispatch plan), so the prose and the
machine artifact cannot contradict each other.

## Dispatch Plan

```yaml
run_id: string
dispatches:
  - role: string
    objective: string
    scope: string
    non_goals: []
    inputs: []
    required_evidence: []
    required_output_schema: string
    permissions: read-only | owned-write
    files_owned: []
    files_forbidden: []
    validation: string
    stop_conditions: []
dispatch_groups:                       # barrier vs pipeline per round (Codex parallel()/pipeline())
  - group_id: string
    round: string
    dispatch_kind: barrier | pipeline
    members: []
    next_group: string
    barrier_reason: string
    fanout_min: 0                       # optional; value-checked against the canonical per-round range
    fanout_max: 0
    fanout_chosen: 0
budget_tier: economy | standard | deep  # Round-A fan-out ceiling 2 | 4 | 6
agent_count_backstop: 18                # hard stop on total spawns
max_concurrent_subagents: 12
max_subagent_depth: 1
fallback_if_subagents_unavailable: sequential artifact-producing passes
```

## Round Summary

Written by the Orchestrator at the end of each round. `coverage_log` is required (no silent caps).

```yaml
run_id: string
round: string
roles_used: []
artifacts_created: []
decision_classes: {accepted_blocker: 0, accepted_non_blocking: 0, rejected_or_unsupported: 0, needs_user_decision: 0}
loop_guard_action: CONTINUE | REPLAN | BRANCH | ABANDON | HUMAN_REVIEW   # Orchestrator-owned
coverage_log:
  findings_deduped_against_seen: 0
  findings_killed_by_majority_refute: 0
  items_truncated_or_sampled: []
  lenses_or_sources_not_run: []
  concurrency_cap_hit: false
  ran_as_sequential_fallback: false
```

## Evidence Packet

Judges receive evidence packets, not raw persuasive findings.

```yaml
packet_id: string
source_claim_ids: []
accepted_evidence_ids: []
claim: string
claim_type: observation | inference | recommendation
decision_relevance: string
counterevidence: []
support_status: accepted | partially_supported
evidence_quality: high | medium | low
hard_gate_failures: []
excluded_unsupported_text: []
```

## User Checkpoint

```yaml
checkpoints:
  - decision_id: string
    decision_required: string
    why_it_matters: string
    recommended_option: string
    alternatives: []
    evidence_ids: []
    files_or_runs_affected: []
    consequence_of_no_decision: string
stop_round: F
edit_permission_before_approval: false
```

## Implementation Plan

The Round F deliverable — the product of Run 1 (Research & Plan). Run 2 (implementation) loads it.

```yaml
run_id: string
objective: string
decision_link: string            # optional
approach: string                 # chosen design + why
alternatives_considered: []      # optional
literature_summary: string       # source-records found, or what was logged unverified
change_list: []                  # file-level: [{path, change, owner}]
experiment_card_ids: []          # optional
ordered_steps: []                # each a discrete task a Run-2 implementer executes
validation_strategy: string
risks: []
open_decisions: []               # user decisions still required
```
