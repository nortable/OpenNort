# Agent Roster Reference

Load this file when using full adversarial, full-agent, red-team, multi-agent, or research-team
mode. The roster is not a concurrency target. Instantiate only roles needed for the current round.
Use `role-dispatch-templates.md` for concrete subagent prompts.

The Orchestrator is always the main Codex agent. Subagents are bounded workers that return artifacts;
they do not own final decisions.

## Orchestrator (reserved; not a worker)

The Orchestrator is the resident main Codex agent and is NOT one of the numbered worker roles. It owns
ALL deterministic control flow and makes no domain finding of its own:

- fan-out / dispatch and round sequencing;
- loop continuation and termination;
- all routing and the RUN/DEFER/PARK/REJECT/HUMAN_REVIEW action class (Round E ledger);
- prioritization, dedup, anonymization, and packet-id assignment;
- evidence-packet assembly from accepted Round C decisions;
- final synthesis and the user checkpoint.

Symmetric worker ban: no worker emits an action verb, assembles packets, or owns a final decision; the
Orchestrator emits no first-pass finding, critique, or score.

## Worker Roles (18)

1. **Research Director** - Maintains charter, decision objective, non-goals, success criteria.
2. **Relevance Arbiter** - Scores decision consequence, information value, redundancy, cost; returns a scored signal (RelevanceScore), never an action.
3. **Literature Scout** - Retrieves primary sources, contradictory evidence, source metadata. REQUIRES a web/fetch tool; if the runtime has none, this role is a no-op and every external-dependent claim is logged as a `claim_unverified` Completeness gap and in `coverage_log.external_verification_unavailable[]` (see `full-adversarial-workflow.md` "External-evidence honesty") — a local-only run never silently claims an external fact was verified.
4. **Data Auditor** - Checks datasets, splits, denominators, labels, leakage, sample definitions.
5. **Baseline Auditor** - Checks baseline fairness, feasibility, protocol alignment, missing controls.
6. **Claim Auditor** - Compares report or paper claims to inspectable evidence.
7. **Hypothesis Generator** - Produces null and materially different alternatives with falsifiers.
8. **Falsifier / Red Team** - Attacks strongest-case assumptions, confounders, circularity, leakage.
9. **Methodologist** - Reviews validity, controls, metrics, sample logic, stopping rules; returns validity_verdict data, never an action. Owns the **deep-insight lens** (below): every full audit assigns at least one Methodologist (or Methodologist-tasked finder) so the run produces `depth: deep` findings, not only surface drift.
10. **Code Red-Team** - Checks implementation drift, schemas, scripts, smoke tests, hidden assumptions.
11. **Experiment Engineer** - Implements approved experiments in isolated write scope.
12. **Test Reviewer** - Performs read-only fidelity and correctness verification.
13. **Replicator** - Independently reproduces important results in clean scope.
14. **Evidence Auditor** - Returns EvidenceDecision data (claim-to-evidence links, downgrades); does not assemble packets or decide.
15. **Judge** - Scores anonymized accepted evidence packets independently under a distinct emphasis lens; the Orchestrator synthesizes from the winning pass and grafts runner-up dissents.
16. **Integrator / Synthesizer** - Writes final docs or reports using accepted evidence only.
17. **Loop Guard** - Detects stagnation, repetition, low-value work, and scope drift; returns a StagnationSignal, never an action (the Orchestrator owns loop_guard_action).
18. **Completeness Critic** - Read-only; before the Round F checkpoint, returns a CompletenessCritique listing coverage gaps (a lens not run, a claim unverified, a source unread, a hypothesis untested). Must have produced none of the reviewed findings.

## Role Separation

Every Finding, Critique, EvidenceDecision, and JudgeScore carries an `agent_id`. The
generate/verify boundary is hard and machine-checked (`scripts/validate_artifacts.py` provenance
check): an artifact's author can never be its own skeptic, auditor, or judge.

- **Never-combine across generate/verify (hard, enforced):**
  - a Finding's `agent_id` may not equal the `agent_id` of any Critique targeting it, any
    EvidenceDecision on it, or any JudgeScore of a packet built from it;
  - an implementation worker cannot be the sole Test Reviewer or Replicator of its own change.
- Judges are read-only and cannot create missing evidence; Evidence Auditors are read-only.
- Only implementation and integration roles receive write permission.
- The Orchestrator may integrate but must preserve unresolved disagreement.
- Only **non-adversarial reader** roles may be merged (e.g. one agent reading several documents); no
  merge may place generation and verification of the same artifact in one `agent_id`.
- The Completeness Critic may not self-certify coverage: it must have produced none of the findings it
  reviews, so it cannot be folded into the Relevance Arbiter or Loop Guard.

## Dispatch Policy

For full adversarial mode when subagents are available:

- Round A: three to six agents; each returns MULTIPLE findings labeled `depth`/`contestability`, and at least one runs the deep-insight lens.
- Round B: two to four agents — but routed by contestability, not flat. Low-contestability binary facts get ONE light confirmation pass; the multi-lens Falsifier panel is reserved for `medium|high`-contestability or high-stakes findings (see `full-adversarial-workflow.md` "Proportionate verification").
- Round C: one Evidence Auditor, with a second pass for high-impact disputes.
- Round D: two or three independent judge passes; the panel must cover EVERY assembled packet (split packets across judges — no scoring only the most critical one).
- Round E and F: local Orchestrator.
- Round G: only approved implementation and review agents.

Every dispatch must specify:

```text
Dispatch:
- role:
- objective:
- scope:
- non_goals:
- inputs:
- required_evidence:
- required_output_schema:
- permissions:
- files_owned:
- files_forbidden:
- validation:
- stop_conditions:
```

## Concurrency Policy (canonical)

This block is the single source of truth for concurrency, depth, and roster cardinality. SKILL.md and
the references cite it instead of restating numbers; the machine-enforced mirrors are
`assets/templates/dispatch-plan.yaml`, `references/artifact-contracts.md`,
`scripts/run_synthetic_fixture.py`, and `scripts/validate_artifacts.py`, which must change together.

1. Global cap: at most **12 open subagents at any instant**, regardless of round. Per-round fan-out
   caps (Round A 3-6, B 2-4, C 1-2, D 2-3) are ceilings on *new* spawns and never exceed the 12-open
   cap; queue the remainder.
2. Maximum nesting depth: **1** (the verified `multi_agent_v1` limit; subagents do not spawn subagents).
3. This cap is intentionally below Claude Code's `min(16, cores-2)` (~30 here) because the Codex
   substrate is Orchestrator-mediated and depth is 1; do not raise it to the core count. Raising the
   cap is a one-line change to this block plus `config.toml [agents].max_threads`.
4. Roster cardinality: exactly **18 worker roles plus the Orchestrator** (see the numbered list
   above). Instantiating the full roster simultaneously is forbidden; the 12-open cap binds regardless
   of roster size. The roster is a menu, not a swarm target.
5. Hygiene: do not duplicate assignments; prefer narrow prompts; close completed agents after
   integration; do not wait idly when non-overlapping local Orchestrator work exists; maintain
   first-pass isolation; route all cross-agent communication through artifacts or explicit
   Orchestrator relays; do not expose one judge's score to another before completion; do not show
   falsifiers the author identity of target findings.
6. No silent caps: whenever coverage is bounded (top-K, sampling, no-retry, dedup, sequential
   fallback, concurrency-cap queueing), record it in the round summary `coverage_log` so bounded
   coverage never reads as total coverage.

## Budget-Scaled Fan-Out

Scale Round-A fan-out to the run's `budget_tier` (declared in `01-dispatch-plan.yaml`). The ceiling is
the smallest tier that fits the task; `fanout_chosen` never exceeds it or the 12-open cap.

| budget_tier | Round-A fan-out ceiling |
|---|---|
| economy | 2 |
| standard | 4 |
| deep | 6 |

Canonical per-round fan-out ranges (ceilings on new spawns): A 3-6, B 2-4, C 1-2, D 2-3, E/F 0.
`scripts/validate_artifacts.py` value-checks these plus `max_subagent_depth==1`,
`1<=max_concurrent_subagents<=12`, and `agent_count_backstop` against a real plan.

## Deep-Insight Lens

A run that only finds doc-vs-tree drift (a missing file, a number-vs-number mismatch) has audited the
surface, not the research. At least one finder per full audit runs the deep-insight lens and returns
`depth: deep` findings that reason about whether the work is *correct*, not just whether the docs match
the tree:

- statistical power / minimum detectable effect vs the claimed effect size and the CI width;
- the resampling unit and effective-N (e.g. 27 scan-clusters vs 135 cases — a 5x difference that flows
  into every CI), and whether the bootstrap/variance components are stable at that N;
- train/test and pretraining-corpus leakage, and whether disjointness is verified or merely asserted;
- primary-endpoint / denominator definition and unit consistency (do not add bag counts to component
  counts);
- confirmatory-vs-exploratory family structure (a "core" claim parked in a secondary FDR family can
  never be confirmed by design).

If a discovery pass yields zero `depth: deep` findings, that is itself a coverage gap to log and
surface at Round E.5 — not evidence that the research is sound.

Fallback when subagents are unavailable:

- preserve role separation using sequential artifact-producing passes;
- minimize context between passes where possible;
- store each pass before starting the next;
- report that the run was sequentially simulated rather than genuinely parallel.
