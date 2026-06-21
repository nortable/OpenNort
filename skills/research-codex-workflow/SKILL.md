---
name: research-codex-workflow
description: Single enforced adversarial multi-agent research workflow — the cornerstone for research-oriented coding, repo reconnaissance, paper reproduction, experiment cleanup, research documentation, and baselines/evaluation/metrics/leakage/result-table/claim work. Fires on substantial research decisions and on explicit adversarial or multi-agent requests such as full-agent, red-team, research-team, 对抗模式, 多 Agent, 多智能体, 多个 agent, 最高规格, 最高级规格, 最高模式, or 最高强度. When it fires it runs in two separate invocations — Run 1 (Round 0→F) produces a literature-backed implementation plan and stops; Run 2 (Round G) is a separate, user-initiated implementation pass — decision-linked, evidence-gated, loop-bounded, and enforced by a completion gate that real subagents actually ran.
---

# Research Codex Workflow

**One mode, two runs.** When this skill fires, run the adversarial multi-agent research workflow as a
deterministic Orchestrator. There is no lighter mode and no router. If a task does not warrant the full
workflow, do **not** invoke this skill — handle it directly and lightweight. Once invoked, do not
collapse the workflow into a single-context synthesis; that shortcut is the documented failure mode and
the completion gate rejects it.

**Bias to action, not to self-inspection.** Your job is the research substance — findings, evidence, and
the plan — produced by spawning real subagents. This skill is the METHOD, not the SUBJECT: do not sit and
audit, narrate, or "fix" the workflow itself, and do not re-check your own process mid-run. The
validator is a SINGLE final gate you run once at the end, not an ongoing activity. If you ever notice
yourself reasoning about the workflow's correctness instead of the user's research, stop and dispatch a
Finder.

The Orchestrator is the resident main Codex agent. It owns ALL deterministic control flow (dispatch,
sequencing, loop continuation/termination, routing/the RUN/DEFER/PARK/REJECT/HUMAN_REVIEW action class,
dedup, anonymization, evidence-packet assembly, final synthesis) and makes NO first-pass finding of its
own. Subagents are bounded, single-purpose workers whose output IS one schema-conformant artifact; they
cannot see peers, own no final decision, and an artifact's author can never be its own
skeptic/auditor/judge.

## Two runs: Plan, then Implement (never fused)

The workflow is split into two SEPARATE invocations. Do not fuse them — running research, planning,
and implementation in one context overloads it and stalls the model.

- **Run 1 — Research & Plan (the default).** Round 0→F, fully READ-ONLY. Charter → (mandatory
  literature review when external facts are in play) → independent Finders → falsification → evidence
  tribunal → judge panel → decision ledger → a **detailed, literature-backed implementation plan**
  (`round-f-implementation-plan.{yaml,md}`) → user checkpoint. Then **STOP**. The deliverable is the
  PLAN, not code; do not edit project files.
- **Run 2 — Implementation (separate, user-initiated).** ONLY when the user explicitly asks to
  implement an approved plan does a FRESH run execute Round G: load `round-f-implementation-plan.yaml`
  as its input, dispatch implementer agents against its `ordered_steps` in isolated worktrees, verify
  each as it lands, and report. Run 2 executes the plan; it does not re-derive it.

A normal invocation ends at the plan and hands it to the user. Never roll forward from plan into
implementation inside the same run.

## When this skill fires (else stay lightweight without it)

- explicit adversarial / red-team / full-agent / multi-agent / research-team / 对抗模式 / 多 Agent /
  多智能体 / 多个 agent / 最高规格 / 最高级规格 / 最高模式 requests; OR
- a substantial research decision: experiments, baselines, metrics, leakage, data definitions, result
  tables, reviewer-facing claims, or research-document edits.

Ordinary repo reading, a narrow question, a small bugfix, or a CI/lint repair is handled directly
without this skill. An unfamiliar repository alone does not invoke it; auditing documents does not
authorize editing them.

## Hard Invariants

- The main Codex agent is the ONLY Orchestrator; it never emits a first-pass finding, critique, or score.
- **Real subagents by default.** Probe `multi_agent_v1` (`spawn_agent`) at Round 0 and dispatch
  independent first-pass Finders. If `spawn_agent` is unavailable, run the same rounds as sequential
  isolated passes, set `ran_as_sequential_fallback: true` in the round `coverage_log`, and STILL write
  one `agents/<agent_id>.json` record per pass — the completion gate binds in fallback too.
- **Spawn footgun:** `spawn_agent` REJECTS `fork_context: true` combined with an explicit `agent_type`.
  For independent Round A contexts always pass `agent_type` with `fork_context: false` (or omit it);
  never both. Canonical call: `spawn_agent(agent_type=<role>, fork_context=false, prompt=...)`.
- Follow the canonical Concurrency Policy in `references/agent-roster.md` (12 open subagents, depth 1);
  do not restate or override the numbers elsewhere.
- Author ≠ skeptic ≠ judge across the generate/verify boundary (machine-checked).
- **Discovery before verification:** each Finder returns multiple findings; at least one is
  `depth: deep` (design / statistical-validity, not surface doc-vs-tree drift). Zero deep findings is a
  coverage gap — the gate fails the run, it is not a clean bill.
- Audit evidence before judging (model prose is not evidence); score every assembled packet — no
  cherry-picking.
- Verify proportionately: one confirmation pass for low-contestability binary facts; the
  perspective-diverse falsifier/judge panel for contestable or high-stakes claims.
- **Literature review is proactive, not opt-in.** If ANY claim depends on facts outside the repo —
  novelty, prior-art, SOTA comparison, leakage/contamination, external dataset or pretraining-corpus
  provenance — set `external_evidence_needed: yes` in the charter and dispatch a Literature Scout in
  Round A (it retrieves via `scripts/fetch.py`). Never assert novelty / SOTA / leakage-safety from
  local inspection alone. Be honest about reach: when no web tool reaches the network, log each such
  claim as unverified (`coverage_log.external_verification_unavailable`) — never as checked. The gate
  FAILS a run that declared `external_evidence_needed: yes` but produced neither a `source-record` nor
  an unavailable-log.
- Stop at a user checkpoint (Round F) before contested protocol, dataset, baseline, metric, claim,
  publication-readiness, or research-document edits.
- Run 1 (Round 0→F) is READ-ONLY and ends at the implementation plan; never edit project files or roll
  into implementation in the same run. Implementation is a separate, user-initiated Run 2.
- Read-only roles stay read-only; give parallel writers disjoint ownership or isolated worktrees.
- Preserve user configuration and existing project instructions.

## Workspace — one layout, always

Create every run with `python3 scripts/create_run_workspace.py` (it materializes the canonical tree
including `agents/` and `writers/`). Never hand-roll a folder and never invent ad-hoc result files
(no `agentic_synthesis.md`, no improvised structure): the canonical tree — `00-charter.yaml`,
`01-dispatch-plan.yaml`, `round-a-findings/`, `round-b-critiques/`, `round-c-evidence-decisions.yaml`,
`evidence-packets/`, `round-d-judge-scores/`, `round-e-decision-ledger.yaml`,
`round-f-user-checkpoint.{yaml,md}`, `round-g-final-report.{yaml,md}`, `agents/<id>.json`,
`progress-snapshots/` — is the ONLY layout the completion gate accepts. Use
`.research-workflow/runs/<run_id>/` unless the project has an established location.

## The workflow (Run 1 = Round 0→F plan; Run 2 = Round G)

Load references LAZILY — pull each one at the round that needs it, not all up front (front-loading the
whole library before any research is itself a stall risk). To START, load only
`references/full-adversarial-workflow.md` (rounds + phase shapes) and `references/team-runbook.md`
(dispatch script, judge aggregation, stop conditions). Then, on demand: `references/agent-roster.md`
(roster + Concurrency Policy + deep-insight lens) and `references/role-dispatch-templates.md` (subagent
prompts) when you actually dispatch; `references/artifact-contracts.md` when you write an artifact;
`references/worktrees-and-artifacts.md` only in Run 2; `references/experiment-card.md` +
`references/experiment-gates.md` only before an experiment/baseline/result-table; `references/loop-guard.md`
only when work repeats. For a PR/diff review, record base/head SHAs in the charter and point Finders at
the diff with correctness/security/perf lenses — same 0→G substrate split across the two runs.

1. **Round 0** — Task Charter + relevance gate; no decision link → `REJECT`/`PARK`, no fan-out.
2. **Round A** (barrier) — independent first-pass Finders → `round-a-findings-index.yaml`; ≥1
   `depth: deep`; loop-until-dry, dedup against all SEEN.
3. **Round B** (pipeline) — anonymous cross-falsification, routed by contestability.
4. **Round C** (pipeline) — Evidence Tribunal returns decisions; the Orchestrator assembles
   `evidence-packets/` only from accepted/partially-supported decisions.
5. **Round D** (barrier) — independent judge panel; synthesize from the winner, graft runner-up
   blockers; every assembled packet scored.
6. **Round E** — decision ledger: exactly one class (`accepted_blocker` / `accepted_non_blocking` /
   `rejected_or_unsupported` / `needs_user_decision`) and one action per issue.
7. **Round F** — write the detailed `round-f-implementation-plan.{yaml,md}`, present the user
   checkpoint, and **STOP** (Run 1 ends here). The plan is the deliverable.
8. **Round G** — implementation, verification, documentation. This is **Run 2**: a SEPARATE,
   user-initiated invocation that loads the approved plan and executes its `ordered_steps`. Never
   auto-continued from Run 1.

## Artifact discipline and the Completion Gate

Every material claim needs at least one accepted evidence record (file path + location, command +
output, dataset statistic + reproduction command, source + retrieval date + support location, artifact
path + hash, or test/experiment invocation). Validate each worker artifact against its contract —
`python3 scripts/validate_artifacts.py --artifact <path> --type <schema>` — and reject + redispatch on
failure (at most twice, then record `status: failed` and log the exclusion). `scripts/schemas.py` is
the single source of truth the validator and generator share.

**COMPLETION GATE (non-negotiable).** Before writing ANY final answer, run

```
python3 scripts/validate_artifacts.py --audit-run .research-workflow/runs/<run_id>/
```

If it does not exit 0, the run is NOT done — fix or redispatch; do not narrate a result. The gate
fails on: missing/too-few `agents/<id>.json` spawn records, an artifact not traceable to a spawn, zero
deep findings, a single-judge (non-panel) Round D or duplicate-lens co-judges, dangling
cross-references, an anonymization leak, an unjudged evidence packet, an edit-before-approval, or a
plan run that contains a Round-G report (a fused run). Record the gate result where the run actually
ends: **Run 1** puts the `OK:` line + `audit_run_ok: true` + `audit_run_command` in
`round-f-implementation-plan.{yaml,md}` (it has no Round-G report); **Run 2** puts them in
`round-g-final-report.{yaml,md}`. Run `python3 scripts/selftest.py` (one command) to confirm the
harness itself still catches its negative controls.

## Coding ownership

Express each writer's ownership as a `dispatches[]` entry in `01-dispatch-plan.yaml` (`role`,
`permissions`, `files_owned`, `files_forbidden`, `validation`, `required_output_schema`). The validator
rejects a read-only role that carries write permissions or owned files. Serialize shared contracts
(schemas, metrics, coordinate systems, configs, public APIs, result aggregators, protocol definitions).
Give each parallel writer an isolated workspace: a git worktree for a real repo, else a disjoint locked
directory under `runs/<run_id>/writers/<worker_id>/` (`scripts/create_run_workspace.py --writers N`).
Read-only roles get no writer directory. See `references/worktrees-and-artifacts.md`.

## Completion criteria

**Run 1 (the default) ends with the plan.** The final response reports: the implementation plan
(`round-f-implementation-plan.{yaml,md}`) and its ordered steps; roles / subagents actually spawned
(list the `agent_id`s, or state the sequential fallback); the `--audit-run` `OK:` line; evidence
accepted, downgraded, or rejected; experiments parked or gated; user decisions required at the
checkpoint; claims still unsupported; residual risk and the next action. "Files changed" is **N/A** —
Run 1 is read-only. Then STOP and hand the plan to the user.

**Run 2 (implementation) ends with the result.** It additionally reports files changed and why,
validation commands and results, and the final report (`round-g-final-report.{yaml,md}`).

Never claim an implementation, validation, or forward test succeeded without a command, artifact, or
file path that demonstrates it. Use Chinese for the user-facing synthesis; keep artifact field names in
English.
