# Agent Roster Reference

The roster is not a concurrency target. Instantiate only roles needed for the current round.
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

## Worker Roles (lean roster)

The standing roster is small on purpose: a long role menu is what made earlier runs heavy enough to
shortcut. Five read-only roles carry the adversarial spine, and the **Finder** absorbs the old
specialist auditors as *lenses* rather than separate standing roles. Round G adds on-demand write roles
only after user approval.

1. **Finder** (read-only) — the Round A discovery role; dispatch several with DISTINCT lenses, at least
   one running the deep-insight lens. Declare the lens in the dispatch: *data* (splits, denominators,
   labels, leakage, sample definitions), *baseline* (fairness, feasibility, missing controls), *claim*
   (report/paper claims vs inspectable evidence), *code red-team* (implementation drift, schemas, smoke
   tests, hidden assumptions), *hypothesis* (null + materially different alternatives with falsifiers),
   and the mandatory **deep-insight / methodology lens** (validity, controls, metrics, stopping rules —
   produces `depth: deep` findings). Each Finder returns MULTIPLE findings labeled `depth` and
   `contestability`, and scored signals, never an action verb. External evidence (REQUIRED, not
   optional, when the charter set `external_evidence_needed: yes` or a claim turns on novelty / prior-art
   / SOTA / leakage / provenance): a Finder uses **Codex's NATIVE search + fetch/PDF tools** to find and
   READ the papers — extracting the exact equation, the baseline method + dataset + split + metric +
   reported number, and the implementation detail (not a generic summary) — and OPTIONALLY pins a
   tamper-evident `content_sha256` via `scripts/fetch.py <url>` → a `source-record`. Do not reinvent a
   fetcher/parser. If no native tool and fetch.py can both reach the network, every external-dependent
   claim is logged as a `claim_unverified` Completeness gap and in
   `coverage_log.external_verification_unavailable[]` (see `full-adversarial-workflow.md`
   "External-evidence honesty") — a local-only run never silently claims an external fact was verified.
2. **Falsifier / Red Team** (read-only) — attacks an anonymized finding it did NOT produce: strongest-
   case assumptions, confounders, circularity, leakage. Defaults `refute_disposition` to `refuted` when
   uncertain; records its `lens`.
3. **Evidence Auditor** (read-only) — returns `EvidenceDecision` data (claim-to-evidence links,
   downgrades); does NOT assemble packets or decide. The Orchestrator assembles packets.
4. **Judge** (read-only) — scores anonymized accepted evidence packets independently under a distinct
   emphasis lens; the Orchestrator synthesizes from the winning pass and grafts runner-up dissents.
5. **Completeness Critic** (read-only) — before the Round F checkpoint, returns a `CompletenessCritique`
   of coverage gaps (a lens not run, a claim unverified, a source unread, a hypothesis untested). Must
   have produced none of the reviewed findings, so it cannot self-certify.

Round 0 charter, relevance gating, dedup, anonymization, packet assembly, loop-guard / stop-rule
evaluation, the decision ledger, and final synthesis are all **Orchestrator-owned** (the main Codex
agent), not dispatched roles. Round G implementation, test-review, and replication are on-demand
roles run in a SEPARATE user-initiated Run 2 (a fresh invocation that loads
`round-f-implementation-plan.yaml`), never auto-continued from the Run-1 plan and never part of the
standing read-only roster.

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
  reviews, so it cannot be a Finder from this run or the Orchestrator's own coverage scan.

## Dispatch Policy

When subagents are available:

- Round A: three to six agents; each returns MULTIPLE findings labeled `depth`/`contestability`, and at least one runs the deep-insight lens.
- Round B: two to four agents — but routed by contestability, not flat. Low-contestability binary facts get ONE light confirmation pass; the multi-lens Falsifier panel is reserved for `medium|high`-contestability or high-stakes findings (see `full-adversarial-workflow.md` "Proportionate verification").
- Round C: one Evidence Auditor, with a second pass for high-impact disputes.
- Round D: two or three independent judge passes; the panel must cover EVERY assembled packet (split packets across judges — no scoring only the most critical one).
- Round E and F: local Orchestrator; Run 1 ends at the plan.
- Round G: Run 2 only (separate, user-initiated) — approved implementation and review agents.

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
4. Roster cardinality: **5 standing read-only worker roles** (Finder, Falsifier, Evidence Auditor,
   Judge, Completeness Critic) plus on-demand Round G write roles, plus the Orchestrator. Finder lenses
   are a menu, not a swarm target; the 12-open cap binds regardless of how many lenses are queued.
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
