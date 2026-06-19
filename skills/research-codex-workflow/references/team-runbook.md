# Adversarial Research Team Runbook

Load this file for full adversarial mode when the user wants a complete research team rather than a
single audit pass.

The team is orchestrator-mediated: the root Codex Orchestrator schedules roles, anonymizes artifacts,
integrates evidence, and asks the user for decisions. Subagents do not own final truth.

## Team State

Maintain these artifacts for every full run:

1. `00-charter.yaml` - Round 0 charter and decision links.
2. `01-dispatch-plan.yaml` - roles, ownership, permissions, stop conditions.
3. `round-a-findings/*.yaml` - independent first-pass findings or hypotheses.
4. `round-a-findings-index.yaml` - Orchestrator's routing surface for Round B (finding_id, source_role, claim_type, affected_decision, artifact_path).
5. `round-b-critiques/*.yaml` - anonymized cross-falsification.
5. `round-c-evidence-decisions.yaml` - Evidence Tribunal decisions.
6. `round-d-judge-scores/*.yaml` - independent judge scores.
7. `round-e-decision-ledger.yaml` - Orchestrator decisions and actions.
8. `round-f-user-checkpoint.md` - smallest blocking user decision set.
9. `progress-snapshots/*.yaml` - Loop Guard snapshots.
10. `agents/<agent_id>.json` - one retained debug record per dispatched subagent (role, round, status, output path, raw output) for replay and upgrades.
11. `round-g-final-report.yaml` and `round-g-final-report.md` - only after approved implementation or documentation.

## Round Owners (role lookup)

This table is a role lookup; the authoritative ordered procedure is the Dispatch Script below, and the
machine-readable shapes live in `01-dispatch-plan.yaml` `dispatch_groups[]`. All three must agree.

| Round | Shape | Sync | Owner | Required roles | Output gate |
|---|---|---|---|---|---|
| 0 Charter | gate | local | Orchestrator | Research Director, Relevance Arbiter when needed | task has a decision link |
| A Independent findings | Understand | barrier | Orchestrator | 3-6 scouts/auditors/generators | first-pass outputs isolated into an index |
| B Cross-falsification | Find->Verify | pipeline | Orchestrator | Falsifier, Methodologist, Relevance Arbiter | critiques target anonymized IDs |
| C Evidence Tribunal | Find->Verify | pipeline | Orchestrator (assembles packets from Evidence Auditor decisions) | Evidence Auditor, optional second auditor | unsupported claims downgraded |
| D Judge Panel | judge panel | barrier | Orchestrator | 2-3 Judges | judges see accepted packets only |
| E Decision ledger | synthesize | local | Orchestrator | Loop Guard when work repeats | every issue has one class |
| F User checkpoint | gate | local | Orchestrator | none | stop before contested edits |
| G Approved action | implementation incl. Migrate | per-site pipeline | Orchestrator | Experiment Engineer, Test Reviewer, Integrator | validation passes or claim downgraded |

## Dispatch Script (deterministic order)

This is the authoritative ordered sequence the Orchestrator follows; the Owners table is a role lookup
and the Orchestrator Algorithm below is per-step detail. Until `01-dispatch-plan.yaml` records
`dispatch_kind` for every group, this script is the source of truth for barrier vs pipeline.

0. Probe `multi_agent_v1` availability (`spawn_agent`). If present, use real subagents (the default);
   if absent, run the same rounds as sequential isolated passes and set
   `ran_as_sequential_fallback: true` in each round summary's `coverage_log`.
1. Round 0 (local): write charter + relevance gate; abort if no decision link.
2. Round A (**barrier**): spawn 3-6 first-pass agents up to the 12-open cap; `wait_agent` on all;
   collect `round-a-findings-index.yaml`; anonymize and assign stable IDs.
3. For each indexed finding, run a per-finding **pipeline** with no whole-set barrier:
   a. Round B: dispatch a falsifier on the anonymized finding as it becomes ready;
   b. Round C: stream the finding to the Evidence Auditor; the Orchestrator assembles an evidence
      packet only from an accepted/partially_supported decision.
   Keep in-flight fan-out within the 12-open cap; queue the remainder.
4. Round D (**barrier**): `wait_agent` on all judge scores, then synthesize from the winning pass.
5. Round E (local): write the decision ledger (one class + action per issue).
6. Round F (local): stop before contested edits; present the smallest blocking decision set.
7. Round G (per-site pipeline, only after approval): transform each site in isolation, verify as it
   lands; rerun the Evidence Tribunal, update the ledger, and write the final report as global steps.

## Loop-Until-Dry (Orchestrator-owned)

`01-dispatch-plan.yaml.stop_rule` is the SOLE termination authority the Orchestrator evaluates
(`max_rounds`, `loop_until_dry_K` default 2, `dedup_against: all_seen`, optional
`token_budget_target`); the top-level `agent_count_backstop` is the hard spawn ceiling. Per-dispatch
`stop_conditions` are advisory inputs, not the authority.

Each finding round, the Orchestrator maintains `new_findings_this_round` and `consecutive_dry_rounds`,
deduping every finding against ALL findings SEEN this run (rejected and surfaced, not only accepted).
It stops spawning finders at `consecutive_dry_rounds >= loop_until_dry_K`, and stops unconditionally at
`agent_count_backstop` (logging the cap — no silent truncation). The until-dry loop never relaxes the
existing per-hypothesis round caps in `loop-guard.md`; the tighter bound wins.

The loop must actually RUN, not be nominal. A single Round A pass that goes straight to verification is
only valid if that first round was itself dry (it surfaced everything and a re-spawn would dedup to
nothing); otherwise spawn a second finder round before falsifying. Every finding round records
`consecutive_dry_rounds` AND `deep_findings_count` in its round-summary `coverage_log`, so "we stopped
because discovery was exhausted" is auditable and distinct from "we stopped after one shallow pass".
Discovery effort is the budget that matters most: spend agents finding more (and deeper) before
spending them re-judging the few you have.

## Mode-Specific Team Shapes

Use the smallest complete team for the job.

### Documentation or Claim Audit

- Data Auditor;
- Baseline Auditor;
- Methodologist **(runs the deep-insight lens: power/MDE, resampling unit & effective-N, leakage,
  endpoint definition, confirmatory-vs-exploratory structure — not just doc-vs-tree drift)**;
- Code Red-Team;
- Claim Auditor;
- Relevance Arbiter;
- Falsifier;
- Evidence Auditor;
- 2 Judges.

Route Round B by contestability (see `full-adversarial-workflow.md` "Proportionate verification"):
the doc-vs-tree existence findings from Data/Baseline/Code/Claim auditors are mostly
`contestability: low` → light confirmation pass; reserve the multi-lens Falsifier panel for the
Methodologist's deep statistical-validity findings, where a wrong call actually costs something.

### Code Review (PR / diff review)

Load `references/code-review.md`. Reuses the full Round 0→G substrate pointed at a diff; record
base/head SHAs in the charter.

- Correctness/bug finder;
- Security finder;
- Performance or Reuse/Simplification finder (by diff risk);
- Tests/regressions + API/compatibility finder;
- Falsifier (adversarial route, with a reproducing test as `minimal_test_to_resolve`);
- Evidence Auditor;
- 2 Judges.

Route Round B by contestability: an obvious bug that reproduces trivially is `contestability: low` →
one light confirmation; a subtle race/edge case is `medium|high` → adversarial panel, refuted-by-
default unless the buggy path is shown reachable. Ledger classes map to merge gates: `accepted_blocker`
= must-fix-before-merge, `accepted_non_blocking` = nit, `rejected_or_unsupported` = false positive,
`needs_user_decision` = author's design call. Stop at Round F before editing the author's code; apply
approved fixes (each with a test that proves it) in isolated worktrees at Round G.

### Open Literature or Design Research

- 2-4 Literature Scouts with distinct source strategies;
- 2-3 Hypothesis Generators including a null hypothesis;
- Falsifier;
- Methodologist;
- Relevance Arbiter;
- Evidence Auditor;
- 2 Judges.

### Experiment Planning

- Research Director;
- Relevance Arbiter;
- Methodologist;
- Data Auditor;
- Falsifier;
- Evidence Auditor;
- Loop Guard.

Do not assign Experiment Engineer until an Experiment Card passes relevance and method gates.

### Implementation After Approval

- Orchestrator;
- Experiment Engineer or implementation worker;
- Test Reviewer;
- Evidence Auditor;
- Integrator;
- Loop Guard when a repair repeats.

## Orchestrator Algorithm

1. Create `run_id` and workspace.
2. Write Round 0 charter and decision links.
3. Select the team shape; justify omitted roles.
4. Write a dispatch plan with read/write boundaries.
5. Run independent Round A tasks.
6. Normalize Round A outputs into `Finding` or `Hypothesis` artifacts. Validate each returned artifact
   against its contract — `scripts/validate_artifacts.py --artifact <path> --type <schema>` — and on
   failure redispatch the SAME worker with the validator error appended (it returns only the corrected
   artifact), at most twice; then record `status: failed` with an orchestrator_note, exclude it from
   evidence, and log the exclusion in the round summary (never a silent drop). Apply the same
   validate-then-redispatch step where Rounds B, C, and D collect artifacts (matching `--type`).
7. Strip author identity and assign stable packet IDs.
8. Run Round B cross-falsification with no self-review.
9. Run Round C evidence audit before any judging.
10. Build accepted evidence packets for judges; omit unsupported persuasive text.
11. Run Round D independent judges.
12. Aggregate without majority-overriding hard evidence failures.
13. Write Round E decision ledger.
14. Run Loop Guard snapshot.
15. Stop at Round F if any issue needs user decision or protected edits.
16. Start Round G only after user approval.

## Dispatch Group Shapes (barrier vs pipeline)

`01-dispatch-plan.yaml` declares `dispatch_groups[]`, each with `dispatch_kind: barrier | pipeline`.
This is the deterministic control-flow primitive (the Codex translation of `parallel()` vs
`pipeline()`); the Orchestrator owns group sequencing and workers never advance a group.

- **barrier** (`wait_agent` on ALL members before the next group): use only when the next step needs
  every result together. Round A is a barrier so all first-pass findings exist before anonymization
  and dedup; Round D is a barrier so panel synthesis sees every judge score.
- **pipeline** (stream each item to the next stage as it lands, no whole-set barrier): the default for
  multi-stage work. Rounds A->B->C run per finding — a finding can be in Round C while another is
  still in Round B — bounded by the 12-open concurrency cap.

`scripts/validate_artifacts.py` validates the `dispatch_kind` enum on a real plan and warns if Rounds
B and C are not both `pipeline`.

## Required Decision Classes

Use exactly one primary class per issue:

- `accepted_blocker` - must be fixed before the relevant claim, experiment, or document is trusted.
- `accepted_non_blocking` - true and useful but does not block the immediate decision.
- `rejected_or_unsupported` - do not act on it without new evidence.
- `needs_user_decision` - evidence cannot choose because the decision is normative, strategic, or scope-setting.

## Judge Aggregation

Judges are not voters over facts. Apply this order:

1. Evidence Tribunal hard failure -> rejected, regardless of judge preference.
2. Failed required test or invalid experiment fidelity -> blocker or revise.
3. Substantial judge disagreement -> targeted evidence request, not generic debate.
4. Median class can decide only when evidence packets are accepted and hard gates pass.
5. Budget exhaustion -> honest partial report.
6. When passes are accepted and hard gates pass, synthesize from the winning pass and graft
   runner-up blockers and `hard_gate_failures` rather than discarding them.

Coverage precondition: before aggregating, every assembled `evidence-packets/*.yaml` must carry at
least one judge score — judges split the packets, they do not score only the single "most important"
one and leave the rest to be promoted unscored. `validate_artifacts.py` rejects a run with any unjudged
packet (`validate_judge_coverage`).

## User-Facing Language

Use Chinese for the user-facing synthesis when the user is Chinese. Keep artifact field names in
English for machine consistency.

## Stop Conditions

Stop and ask the user when:

- the next action would edit contested research documents;
- the next action changes protocol, denominator, metric, baseline policy, or headline claim;
- evidence supports multiple valid project directions;
- a paid, destructive, or external action is required;
- Loop Guard returns `HUMAN_REVIEW`.

Do not create ceremonial checkpoints when there is no real decision for the user.
