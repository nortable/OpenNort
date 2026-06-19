---
name: research-codex-workflow
description: Research workflow cornerstone for research-oriented coding, repo reconnaissance, paper reproduction, experiment cleanup, research documentation, baselines/evaluation/metrics/leakage/result-table work, and explicit adversarial or multi-agent requests such as full-agent, red-team, research-team, 对抗模式, 多 Agent, 多智能体, or 多个 agent. Use to keep research work decision-linked, evidence-gated, loop-bounded, and separated into lightweight, standard, full-adversarial, or product-build modes.
---

# Research Codex Workflow

Act as a deterministic research Orchestrator. Do not let one context freely mix exploration, hypothesis generation, implementation, verification, judging, and claim writing.

This skill (its `SKILL.md` and references) is the authoritative skill-first execution configuration. The current configuration sets `allow_product_build: false`, so do not build a standalone `research-team` CLI unless the user explicitly changes that.

## Hard Invariants

- Choose the smallest mode that fits the user request.
- Full adversarial mode requires an explicit adversarial or multi-agent request.
- Treat Codex subagent communication as Orchestrator-mediated unless native peer-to-peer capability is verified.
- Follow the canonical Concurrency Policy in `references/agent-roster.md` (12 open subagents, depth 1, 18 worker roles plus the Orchestrator); do not restate or override the numbers elsewhere.
- Require decision consequences before experiments, repairs, extended searches, or costly work.
- Audit evidence before judging. Model prose alone is not evidence.
- Stop at a user checkpoint before contested protocol, dataset, baseline, metric, claim, publication-readiness, or research-document edits.
- Give write workers disjoint ownership or isolated worktrees. Read-only roles stay read-only.
- Preserve user configuration and existing project instructions.

## Mode Router

1. **Mode 0 - Lightweight reconnaissance**: ordinary repo reading, a narrow question, small bugfix, localized code review, CI/test/lint repair, or unfamiliar repo orientation. Inspect relevant files, run minimal validation, and avoid research bureaucracy.
2. **Mode 1 - Standard research**: tasks affecting experiments, baselines, metrics, leakage, data definitions, result tables, reviewer-facing claims, or research documentation without an explicit full-panel request. Write a short Task Charter, use bounded evidence checks, and create an Experiment Card for costly or claim-producing work.
3. **Mode 2 - Full adversarial**: explicit requests for adversarial, red-team, full-agent, multi-agent, research-team, multiple agents, 对抗模式, 多 Agent, 多智能体, or equivalent. Load `references/full-adversarial-workflow.md` and run Round 0 through Round F (Round G only after user approval).
4. **Mode 3 - Product-build**: only when the user explicitly authorizes the standalone `research-team` product or changes `allow_product_build` to true. Load `references/product-build-spec.md`; otherwise reject product scaffolding and stay skill-first.

Negative routing:

- An unfamiliar repository alone does not trigger full adversarial mode.
- A request to audit documents does not authorize editing them.
- A large role roster does not authorize instantiating the full 18-worker roster simultaneously; the 12-open cap binds regardless of roster size.
- Majority vote never overrides failed tests, invalid evidence, leakage, or protocol mutation.

Load `references/modes.md` when routing is ambiguous.

## Standard Research Loop

For Mode 1:

1. Inspect project context, run commands, relevant docs, schemas, and risky assumptions.
2. Write a compact Task Charter: objective, decision to support, scope, non-goals, success criteria, evidence needed, validation, and checkpoint needs.
3. Apply the Decision Link and importance gate before extended work.
4. Implement or audit in small slices.
5. Run the smallest meaningful validation.
6. Separate accepted evidence, unsupported claims, residual risk, and next decision.

Load `references/experiment-card.md` before experiments, baseline comparisons, paper claims, costly implementation, or result-table work. Load `references/loop-guard.md` when work repeats or stops changing decision readiness.

## Full Adversarial Protocol

For Mode 2, load these references:

- `references/full-adversarial-workflow.md` for Round 0 through Round G.
- `references/team-runbook.md` for the complete research-team operating procedure.
- `references/agent-roster.md` for role contracts and dispatch.
- `references/role-dispatch-templates.md` when assigning subagents or sequential isolated passes.
- `references/artifact-contracts.md` for artifact schemas and templates.
- `references/experiment-card.md` for preregistered experiments.
- `references/loop-guard.md` for stagnation and repair-loop termination.
- `references/worktrees-and-artifacts.md` for write isolation and reportable evidence.

Round summary:

1. Round 0: Task Charter and relevance gate.
2. Round A: independent findings or hypotheses with isolated first-pass contexts.
3. Round B: anonymous cross-falsification.
4. Round C: Evidence Tribunal.
5. Round D: independent Judge Panel.
6. Round E: Orchestrator decision ledger with `accepted_blocker`, `accepted_non_blocking`, `rejected_or_unsupported`, or `needs_user_decision`.
7. Round F: user checkpoint; stop here when decisions or protected edits are required.
8. Round G: approved implementation, verification, and documentation only after user approval.

Execution path: full adversarial mode already requires an explicit multi-agent request, so DEFAULT to real `multi_agent_v1` subagents (`spawn_agent` / `wait_agent` / `send_input` / `close_agent`) for fan-out. Probe availability once at Round 0; if `spawn_agent` is unavailable, fall back to sequential artifact-producing passes that preserve role separation, and set `ran_as_sequential_fallback: true` in the round summary `coverage_log` (no silent downgrade). Communication stays Orchestrator-mediated (depth 1, 12-open cap) unless verified peer-to-peer support exists.

## Artifact Discipline

For full adversarial runs, write or maintain inspectable artifacts rather than relying only on chat history. Use `.research-workflow/runs/<run_id>/` for transient run workspaces unless the project has an established location.

Every material claim must have at least one accepted evidence record: file path and location, command and output summary, dataset statistic plus reproduction command, source with retrieval date and support location, artifact path plus hash, or test/experiment invocation.

Use templates under `assets/templates/` when creating artifacts. Validate every worker artifact against its contract before acting on it — `scripts/validate_artifacts.py --artifact <path> --type <schema>` — and reject + redispatch on failure (at most twice, then record `status: failed` and log the exclusion). `scripts/schemas.py` is the single source of truth the validator and generator share. For offline verification of the complete team loop, run `scripts/run_synthetic_fixture.py` and validate the generated run root with `--run-root`. `scripts/selftest.py` is the one-command self-test: it generates the fixture, validates it (exit 0), then asserts the validator catches a dropped required key, a dangling reference, an anonymization leak, and an edit-before-approval — proving the harness enforces schema, cross-artifact references, anonymization, and the checkpoint gate.

## Coding Ownership

Before parallel write work, express each worker's ownership as a `dispatches[]` entry in
`01-dispatch-plan.yaml` (`role`, `permissions`, `files_owned`, `files_forbidden`, `validation`, and
`required_output_schema` as the expected output) — a single producer, so ownership never drifts across
files. `scripts/validate_artifacts.py` rejects a read-only role that carries write permissions or owned
files.

Serialize shared contracts such as schemas, metrics, coordinate systems, configs, public APIs, state machines, result aggregators, and research protocol definitions.

Give each parallel writer an isolated workspace: a git worktree when the run targets a real repo, else a disjoint locked directory under `runs/<run_id>/writers/<worker_id>/` (`scripts/create_run_workspace.py --writers N`); read-only roles get no writer directory. See `references/worktrees-and-artifacts.md`.

## Completion Criteria

Final responses for research work must report:

1. mode used and roles/subagents used;
2. files changed and why;
3. validation commands and results;
4. evidence accepted, downgraded, or rejected;
5. experiments rejected, parked, or gated;
6. user decisions required;
7. claims still unsupported;
8. residual risk and next highest-value action.

Never claim an implementation, validation, or forward test succeeded without a command, artifact, or file path that demonstrates it.
