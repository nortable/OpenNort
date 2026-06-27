# OpenNort

## Codex multi-agent workflow for research

OpenNort is a disciplined multi-agent research workflow for Codex. It turns one Codex
session into a small research team: an Orchestrator plans and controls the run, while
bounded worker agents investigate, falsify, audit evidence, judge claims, and only then
move toward implementation.

It is built for research-oriented coding work where "looks plausible" is not enough:
paper reproduction, benchmark audits, baseline design, leakage checks, result tables,
reviewer-facing claims, and high-stakes repository reconnaissance.

OpenNort is packaged as a Codex extension and skill. The extension makes it easy to
install and discover; the skill contains the actual workflow contract.

## Why OpenNort exists

Research work fails in predictable ways:

- a single agent reads too broadly and turns uncertainty into confident prose;
- implementation starts before the experiment design has been challenged;
- baselines, metrics, and dataset assumptions drift without a traceable decision;
- "multi-agent" becomes a story in the final answer rather than an auditable process;
- external claims about prior work, SOTA, leakage, or provenance are asserted from memory.

OpenNort treats those as engineering problems. It forces research through a schema-gated
pipeline where each material claim needs evidence, each contestable claim gets challenged,
and implementation waits for an explicit user checkpoint.

## The Workflow

OpenNort runs as two separate passes.

### Run 1: Research and Plan

Run 1 is read-only. It produces a detailed, evidence-backed implementation plan and then
stops.

```text
Charter
  -> independent Finders
  -> anonymous Falsifiers
  -> Evidence Tribunal
  -> independent Judge Panel
  -> Decision Ledger
  -> Round F user checkpoint
```

Run 1 is the right mode for:

- understanding an unfamiliar research repository;
- auditing a paper reproduction plan;
- checking datasets, baselines, metrics, leakage, and evaluation design;
- reviewing claims before they go into a paper, report, or README;
- producing a plan that a later implementation run can execute.

### Run 2: Implement

Run 2 is a fresh, user-initiated pass. It loads the approved Run 1 plan and executes the
ordered implementation steps.

Run 2 does not re-invent the research plan. It implements, verifies, records evidence,
and reports what changed.

## Core Ideas

### One Orchestrator, Many Bounded Agents

The main Codex agent is the Orchestrator. It owns control flow, routing, deduplication,
the decision ledger, and final synthesis.

Worker agents are narrow by design. A Finder finds. A Falsifier challenges. An Evidence
Auditor checks support. A Judge scores. Workers return schema-validated artifacts, not
final decisions.

### Evidence Before Judgment

OpenNort separates discovery from verification:

- Finders surface multiple candidate findings.
- Falsifiers attack the findings without knowing the original author.
- The Evidence Tribunal accepts, downgrades, or rejects support.
- Judges score only assembled evidence packets.
- The Orchestrator writes the decision ledger from judged evidence.

This makes the path from claim to decision inspectable.

### Research First, Implementation Second

OpenNort deliberately separates planning from editing. A plan run that edits files or
slides into implementation is considered a fused run and fails the completion gate.

This is especially useful for research work, where premature implementation can hide
weak problem framing, leaky evaluation, or unsupported novelty claims.

### Proactive Literature Review

When a claim depends on facts outside the repository, OpenNort requires external
evidence. Prior art, SOTA comparisons, leakage safety, dataset provenance, and benchmark
claims cannot be treated as checked unless a source record or an explicit unavailable-log
exists.

### Auditable Multi-Agent Execution

Every real run leaves records:

- agent dispatch records in `agents/<agent_id>.json`;
- schema-validated round artifacts;
- evidence records with source paths, commands, outputs, or retrieved sources;
- judge scores for every assembled evidence packet;
- a decision ledger that links accepted issues back to judged evidence.

The completion gate rejects fake or incomplete multi-agent runs.

## What It Helps With

Use OpenNort for:

- paper reproduction planning;
- benchmark and baseline audits;
- dataset readiness checks;
- leakage and contamination reviews;
- result-table and metric validation;
- reviewer-response preparation;
- research repository reconnaissance;
- high-stakes code review where correctness, security, tests, and claims all matter.

Do not use it for every small edit. A narrow typo fix, simple lint repair, or quick local
question is better handled directly.

## Codex Extension Package

OpenNort is distributed as a Codex extension package:

```text
.codex-plugin/plugin.json
skills/research-codex-workflow/SKILL.md
skills/research-codex-workflow/references/
skills/research-codex-workflow/scripts/
```

The plugin manifest is the distribution layer. The skill remains the workflow authority.
Do not move orchestration rules, role contracts, schemas, or completion gates into the
manifest.

Validate the package surface with:

```powershell
python skills/research-codex-workflow/scripts/validate_extension_package.py
python C:/Users/nort/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
```

The extension compatibility plan is documented in
[`docs/codex-extension-compatibility-and-integration-tests.md`](docs/codex-extension-compatibility-and-integration-tests.md).

## Quick Start

Run the local checks:

```bash
python skills/research-codex-workflow/scripts/selftest.py
python skills/research-codex-workflow/scripts/fetch.py --selftest
python skills/research-codex-workflow/scripts/validate_extension_package.py
```

Gate a completed OpenNort run tree:

```bash
python skills/research-codex-workflow/scripts/validate_artifacts.py --audit-run <run-dir>
```

Invoke from Codex with a prompt like:

```text
Use the research-codex-workflow skill on this research repository.
Run Run 1: audit the repo, check prior work where needed, challenge the findings,
assemble evidence, judge the claims, and produce a detailed implementation plan.
Stop at the Round F checkpoint. Do not edit files yet.
```

After reviewing the plan, start a separate implementation pass:

```text
Use the approved OpenNort Run 1 plan and start Run 2 implementation.
Execute the ordered steps, verify each change, and produce the final report.
```

## Repository Layout

```text
.codex-plugin/
  plugin.json                         Codex extension manifest

skills/research-codex-workflow/
  SKILL.md                            skill entrypoint and invariants
  references/                         workflow, roles, artifact contracts, gates
  scripts/                            validators, selftests, run helpers, fetch helper
  assets/templates/                   artifact templates
  agents/openai.yaml                  optional Codex metadata

docs/
  codex-extension-compatibility-and-integration-tests.md
  redesign-mirror-claude-roadmap.md

examples/
  synthetic-run/                      deterministic Run 1 fixture
  integration-fit/                    schema-fit fixtures for external integrations
```

## Validation Philosophy

OpenNort is intentionally conservative.

- A README claim is not runtime proof.
- A generated summary is not evidence.
- A single-agent narrative is not a multi-agent run.
- A smoke test is not a full validation.
- Adapter feasibility is not direct baseline readiness.

The project favors bounded claims, reproducible artifacts, and explicit unsupported
findings over polished overconfidence.

## License

MIT. See [`LICENSE`](LICENSE).
