# Redesign: Mirror Claude Code Orchestration onto the Codex Research Workflow

Date: 2026-06-19
Goal: redesign `research-codex-workflow` so its **division of labor mirrors the Claude Code Workflow
orchestration model** ("the master template"), translated into Codex reality (no JS engine; only the
main Codex agent + `multi_agent_v1`; depth 1; `allow_product_build:false`; non-git `$HOME`).

Source: adversarial workflow run `wf_e0057248-1fd` (52 agents, 38 proposals -> 30 verified -> 25
deduped roadmap items: 3 P0 / 19 P1 / 3 P2). This file is the authoritative implementation spec and
resume point.

## IMPLEMENTATION PROGRESS (resume point)

**Status as of 2026-06-19: COMPLETE. All 25 items + real-`multi_agent_v1` default done; everything
validates green including the regenerated committed run and `selftest.py` (4 negative controls caught).**

- [x] **Batch 0** — R4, R17, R11, R1, R2.
- [x] **Batch 1** — R5, R6, R8, R3, R18, R9, R10.
- [x] **Batch 2** — R7, R12, R13, R14, R16, R19, R20, R22.
- [x] **Batch 3** — R15, R21.
- [x] **Batch 4** — R23, R24, R25.
- [x] Real `multi_agent_v1` default path with availability probe + sequential fallback
  (`ran_as_sequential_fallback` in coverage_log).
- [x] **Final** — committed run `research-workflow-runs/synthetic-v2-complete-team/` regenerated;
  `--run-root` green; `selftest.py` green.
- [x] Concurrency reconciled to **12 open / depth 1** (external edit had set 12/depth-2; user chose
  depth 1) across canonical block, validator, config, template, generator, contracts.

Verify: `python3 scripts/selftest.py` (one command) or
`python3 scripts/validate_artifacts.py --run-root research-workflow-runs/synthetic-v2-complete-team`.

Files changed (final): `scripts/schemas.py` (NEW), `scripts/selftest.py` (NEW),
`scripts/validate_artifacts.py`, `scripts/run_synthetic_fixture.py`, `scripts/create_run_workspace.py`,
`config.toml`, `SKILL.md`, `references/{agent-roster, full-adversarial-workflow, team-runbook,
role-dispatch-templates, loop-guard, artifact-contracts, modes, worktrees-and-artifacts}.md`,
`assets/templates/{dispatch-plan, judge-score, finding, critique, evidence-decision, progress-snapshot,
round-summary}.yaml`, and the regenerated `research-workflow-runs/synthetic-v2-complete-team/`.

## User decisions (2026-06-19)

1. Apply scope: **implement all 25 items** (batches 0-4).
2. Execution path: **enable real `multi_agent_v1` parallel** as the default, with an explicit
   runtime-availability guard that falls back to sequential artifact passes.
3. Concurrency cap: **keep 6** open subagents (codified by R17/R18; raising later is a 1-line change).
4. Worktree on non-git `$HOME`: **default to script-allocated disjoint locked dirs** (R20); reserve
   git worktrees for runs targeting a real repo.
5. `allow_product_build`: **keep false** (writer locks stay plain-text claim files; no SQLite/heartbeat).
6. Budget tier default: **standard** (`{economy:2, standard:4, deep:6}` Round-A fan-out ceilings); the
   shipped dispatch-plan template carries `deep` so it validates against the ceiling.
7. Role names: **keep existing names**, change only their OUTPUT contract (low-risk; no 6-file rename).

## Master template (adopted division-of-labor model)

Two-tier hard split + deterministic substrate. The resident main Codex agent is the ONLY Orchestrator:
it owns all deterministic control flow (fan-out/dispatch, sequencing, loop continuation/termination,
all routing = the RUN/DEFER/PARK/REJECT/HUMAN_REVIEW class, prioritization, dedup, anonymization,
evidence-packet assembly, final synthesis) and makes NO domain finding of its own. `multi_agent_v1`
workers are bounded, single-purpose, stateless; output IS the return value (one schema-conformant
artifact-as-data; recommendations only as a field, never the final choice); cannot see peers; own zero
final decisions; an artifact's author can never be its own skeptic/auditor/judge across the
generate/verify boundary. Control-flow primitives translated to Codex: `parallel`=BARRIER round
(`wait_agent` on all members, only when the next step needs the full set), `pipeline`=DEFAULT per-item
staging (verify each finding as it lands). Structured I/O = one canonical machine-readable schema
registry a stdlib validator actually enforces (required+types+enums+resolvable cross-artifact refs),
Orchestrator rejects+redispatches non-conforming artifacts. Quality patterns compose (adversarial /
perspective-diverse verify with default-refuted, judge panel synth-from-winner, loop-until-dry dedup
vs SEEN, completeness critic, no silent caps). Parallel writers get isolated workspaces; read-only
roles stay read-only; human stays in the loop at checkpoints.

## Roadmap (25 items)

### P0
- **R1 [M]** Strip worker decision-verbs; re-home action tokens to Orchestrator. Relevance Arbiter ->
  RelevanceScore; Methodologist -> validity_verdict{sufficient|insufficient|fatal_flaw}; Loop Guard ->
  StagnationSignal (no CONTINUE/ABANDON; output line -> StagnationSignal). Remove loop_guard_action
  from progress-snapshot/round-summary REQUIRED worker keys; drop recommended_action from finding.
  Keep role names; append "returns a scored signal, never an action". Validator: forbidden-token scan
  over round-a-findings/round-b-critiques/relevance/stagnation bodies for
  {RUN,DEFER,PARK,REJECT,CONTINUE,REPLAN,BRANCH,ABANDON} EXEMPTING round-e ledger action,
  decision_class/final_class/support_status enums, HUMAN_REVIEW-as-checkpoint. Files:
  role-dispatch-templates.md, loop-guard.md, progress-snapshot.yaml, round-summary.yaml, finding.yaml,
  artifact-contracts.md, agent-roster.md, validate_artifacts.py.
- **R2 [M]** Demote Evidence Auditor: returns EvidenceDecision data, does NOT remove items; Orchestrator
  assembles evidence-packets from accepted/partially_supported decisions and assigns packet_ids.
  team-runbook Round-C owner -> Orchestrator. Validator: referential check that every packet's
  source_claim_ids trace to an accepted/partially_supported round-c decision. Files:
  full-adversarial-workflow.md, team-runbook.md, validate_artifacts.py.
- **R3 [S]** Fix validate-then-redispatch runbook so it does NOT invoke a non-existent `--artifact` CLI
  mode (gate the literal command on R5). Until R5 lands, runbook says Orchestrator validates against
  the contract manually + logs failures. SKILL.md:86 reworded. Depends R5. Files: team-runbook.md,
  full-adversarial-workflow.md, SKILL.md.

### P1
- **R4 [M]** Single canonical `scripts/schemas.py` (SCHEMAS: name -> {required, optional, enums,
  item_required}) + CLASS_MAP{'rejected':'rejected_or_unsupported'} + assert_conforms(). Imported by
  validator AND generator. Encode omitted judge fields (warning_score/technical_validity/
  methodological_validity/reproducibility) + finding.uncertainty. Unify JudgeScore.final_class on
  'rejected_or_unsupported' (artifact-contracts.md:108 + judge-score.yaml:12). Note final_class vs
  decision_class are DISTINCT fields linked by CLASS_MAP. Files: schemas.py, validate_artifacts.py,
  run_synthetic_fixture.py, artifact-contracts.md, judge-score.yaml, decision-ledger.yaml.
- **R5 [M]** validate_instance(name,data) (subset-required, enum membership, item_required, per-field int
  bounds from schema) + ARTIFACT_ROUTING globs incl. #decisions[] wrappers; `--artifact PATH --type
  NAME` mode. Depends R4. Files: validate_artifacts.py.
- **R6 [M]** validate_references: critique.target_finding_id in finding_ids; judge.packet_id in
  packet_ids; packet.source_claim_ids in finding_ids; ledger.evidence_ids in evidence_id_universe;
  unique IDs; "dangling ref" per failure. Depends R4,R5. Files: validate_artifacts.py.
- **R7 [M]** Hard never-combine generate/verify list (author != own Falsifier/Evidence-Auditor/Judge) +
  agent_id on Finding/Critique/EvidenceDecision/JudgeScore (contracts+templates+schemas+generator);
  validator provenance check. Depends R3,R4,R5. Files: agent-roster.md, artifact-contracts.md,
  finding/critique/evidence-decision/judge-score.yaml, run_synthetic_fixture.py, validate_artifacts.py.
- **R8 [S]** Generator write_artifact(path,data,schema_name) self-validates every schema-bearing write.
  Depends R4,R5. Files: run_synthetic_fixture.py.
- **R9 [S]** Orchestrator-only control-flow charter block in agent-roster; de-list Orchestrator from the
  numbered worker list (workers 1-17); propagate count to SKILL.md. Depends R1. Files: agent-roster.md,
  SKILL.md, team-runbook.md.
- **R10 [S]** Common Header -> "your output IS the return value" (one artifact; recommendations only in
  fields; Orchestrator owns every decision; can't see peers; null+uncertainty on gaps). Depends R1.
  Files: role-dispatch-templates.md, SKILL.md.
- **R11 [M]** dispatch_groups[] {group_id, round, dispatch_kind: barrier|pipeline, members, next_group,
  barrier_reason} + `_doc` rule string; runbook barrier/pipeline semantics; validator presence +
  dispatch_kind enum + A->B->C single-pipeline warning on real plan. Files: dispatch-plan.yaml,
  team-runbook.md, validate_artifacts.py.
- **R12 [M]** Rounds A->B->C as per-finding Find->Verify pipeline; whole-set barrier at Round D; honor
  6-open cap. Depends R2,R11,R17. Files: full-adversarial-workflow.md, team-runbook.md.
- **R13 [L]** Round Shape Map table + canonical Dispatch Script; name Round A Understand, Round G
  Migrate-stage; round-a-findings-index.yaml. Depends R11. Files: full-adversarial-workflow.md,
  team-runbook.md.
- **R14 [S]** Round D: perspective-diverse lenses over same rubric + synthesize-from-winner grafting
  runners-up; cross-ref existing hard-gate+median rule (don't restate). Depends R4. Files:
  full-adversarial-workflow.md, team-runbook.md, agent-roster.md.
- **R15 [M]** Round B: N>=3 perspective-diverse refuters, default refuted=true; majority-refuted ->
  DOWNGRADE into Round C tribunal (not vote-kill); add refute_disposition+lens to Critique
  contract+template+schema. Depends R4,R5,R12. Files: full-adversarial-workflow.md,
  artifact-contracts.md, critique.yaml, schemas.py, validate_artifacts.py.
- **R16 [M]** New role 19 Completeness Critic (read-only, produced none of reviewed findings) + Round
  E.5 returning CompletenessCritique; Orchestrator closes every must_close gap or surfaces it at Round
  F. Full-adversarial mode only. Depends R4. Files: full-adversarial-workflow.md, agent-roster.md,
  artifact-contracts.md.
- **R17 [S]** Canonical Concurrency Policy block in agent-roster (6 open cap; depth 1; fan-out ceilings
  never exceed 6; 18-role roster != swarm; reason it's below Claude's min(16,cores-2)); SKILL.md cites
  it, reconcile the "14-18" straggler. Files: agent-roster.md, SKILL.md.
- **R18 [M]** validate_dispatch_plan: depth==1, 1<=max_concurrent<=6, fallback non-empty; per-round
  fanout FANOUT_RANGE A(3,6)B(2,4)C(1,2)D(2,3)E(0,0)F(0,0), G chosen<=cap; budget_tier enum
  {economy:2,standard:4,deep:6} (template=deep); agent_count_backstop; config.toml [agents]
  max_threads=6 max_depth=1 (merge-not-overwrite). Depends R11,R17. Files: dispatch-plan.yaml,
  agent-roster.md, validate_artifacts.py, config.toml.
- **R19 [M]** Top-level stop_rule {max_rounds, loop_until_dry_K=2, agent_count_backstop=18,
  token_budget_target|null, dedup_against:all_seen}; Orchestrator maintains new_findings/
  consecutive_dry_rounds, dedup vs ALL SEEN, stop at K dry / backstop (log cap). Loop Guard reports
  dry-streak as data. Depends R1,R11. Files: dispatch-plan.yaml, team-runbook.md,
  full-adversarial-workflow.md, loop-guard.md, progress-snapshot.yaml.
- **R20 [M]** Workspace-selection rule (git worktree if repo, else disjoint per-writer dir under
  runs/<id>/writers/<worker_id>/ at non-git home; never worktree there; read-only roles get no writer
  dir); create_run_workspace.py --writers/--writer-ids + atomic .lock via open(x); read-only-role guard
  in validate_dispatch_plan (exact role match). Depends R18. Files: worktrees-and-artifacts.md,
  create_run_workspace.py, SKILL.md, validate_artifacts.py.
- **R21 [S]** round-summary coverage_log {findings_deduped_against_seen,
  findings_killed_by_majority_refute, items_truncated_or_sampled[], lenses_or_sources_not_run[],
  concurrency_cap_hit, ran_as_sequential_fallback}; required key; new "Round Summary" contract section.
  Depends R4,R19. Files: round-summary.yaml, validate_artifacts.py, agent-roster.md,
  artifact-contracts.md.
- **R22 [L]** Unify ROUND_DIRS in one place (new scripts/round_pipeline.py or schemas.py) imported by
  create_run_workspace + run_synthetic_fixture; per-round completeness in validate_run_output;
  validate_anonymization (finding role + dispatch role terms must not appear in critiques/packets).
  Depends R4,R5. Files: validate_artifacts.py, create_run_workspace.py, run_synthetic_fixture.py.

### P2
- **R23 [S]** Mode->phase-shape map in modes.md (correct: Round E = Decision Ledger not Synthesize;
  Round G = Implementation incl. Migrate stage); fix SKILL.md:29 "Round F/G" -> "through Round F (G
  only after approval)". Depends R13. Files: modes.md, SKILL.md.
- **R24 [M]** Fold Worker Ownership Contract into dispatch-plan dispatches[] fields (keep
  expected_output); remove duplicated block from artifact-contracts.md + SKILL.md L92-103; Common
  Envelope -> template+schema or prose-only mixin. Depends R4. Files: artifact-contracts.md, SKILL.md,
  validate_artifacts.py.
- **R25 [M]** scripts/selftest.py: generate fixture in tempdir, positive run exit 0, then 4 negative
  controls (dropped key, dangling evidence_id, author-identity leak, edit_permission_before_approval)
  each exit!=0; SKILL.md success line only claims implemented guarantees. MUST land last (after
  R5/R6/R22). Files: selftest.py, SKILL.md.

## Sequencing (batches; validator touched by R1,R2,R4,R5,R6,R7,R11,R18,R20,R21,R22 = ordered commits)
- Batch 0: R4, R17, R11, R1, R2
- Batch 1: R5, R6, R8, R3, R18, R9, R10
- Batch 2: R7, R12, R13, R14, R16, R19, R20
- Batch 3: R15, R21
- Batch 4: R23, R24, R25 (last)
- Re-run `scripts/validate_artifacts.py --run-root <committed run>` after each batch; regenerate the
  committed synthetic run from the updated generator so --run-root stays green.

## Rejected (not carried): partial-panel-may-not-decide clause (contradicts budget-exhaustion rule);
no-op agent_role check on evidence-packet; "two divergent enums in one field" mischaracterization;
fabricated FANOUT_RANGE['G']; single generic int bound. See run wf_e0057248-1fd output for detail.
