# OpenNort

A deterministic, adversarial, multi-agent **research workflow** for Codex — packaged as a skill. It
keeps research-oriented coding (paper reproduction, baselines, evaluation, leakage, result tables,
reviewer-facing claims) decision-linked, evidence-gated, and loop-bounded, with a hard separation
between the Orchestrator (which owns all control flow) and bounded worker subagents (which only return
schema-validated data).

The division of labor mirrors the Claude Code Workflow orchestration model, translated into the Codex
runtime (the main agent as Orchestrator plus `multi_agent_v1` subagents; no JS engine).

## What it gives you

- **Four modes** — lightweight reconnaissance, standard research, full adversarial, and a gated
  product-build mode — chosen by an explicit router (`skills/research-codex-workflow/SKILL.md`).
- **A full adversarial protocol** (Round 0→G): independent findings → anonymous cross-falsification →
  Evidence Tribunal → independent Judge Panel → Orchestrator decision ledger → user checkpoint →
  approved implementation. Each round is mapped to a named phase shape (Understand / Find→Verify
  pipeline / judge panel / synthesize) with explicit `barrier` vs `pipeline` semantics.
- **Two-tier hard role split** — workers return artifacts-as-data and own zero decisions; an artifact's
  author can never be its own skeptic, auditor, or judge (machine-checked `agent_id` provenance).
- **A deterministic substrate** — every artifact has a canonical schema
  (`scripts/schemas.py`) that a stdlib validator (`scripts/validate_artifacts.py`) actually enforces:
  per-instance schemas, cross-artifact referential integrity, anonymization, concurrency/budget caps,
  and a scan that forbids decision verbs in worker artifacts.
- **Retained per-subagent debug records** — each dispatched subagent persists `agents/<agent_id>.json`
  for replay, audit, and later upgrades.
- **A one-command self-test** (`scripts/selftest.py`) that generates a synthetic run, validates it, and
  proves the harness *rejects* a dropped key, a dangling reference, an anonymization leak, and an
  edit-before-approval.

## Layout

```
skills/research-codex-workflow/   the skill (router + references + scripts + templates)
  SKILL.md                        compact mode router and invariants
  references/                     protocol, roster, contracts, loop guard, runbook, dispatch
  scripts/                        schemas.py, validate_artifacts.py, run_synthetic_fixture.py,
                                  create_run_workspace.py, selftest.py
  assets/templates/               JSON-compatible YAML artifact templates
  examples/                       synthetic adversarial fixture
docs/                             design notes
examples/synthetic-run/          a fully worked Round 0→G run (the self-test output)
```

## Quick start

```bash
# install: copy or symlink the skill into your Codex skills dir
cp -r skills/research-codex-workflow ~/.codex/skills/

# verify the deterministic substrate (generates a run, validates it, runs negative controls)
python3 skills/research-codex-workflow/scripts/selftest.py
```

Then invoke from Codex:

> Use the research-codex-workflow skill in full adversarial mode on this research repository. Run Round
> 0 through Round E, stop at Round F, and do not edit research-protocol documents until I approve the
> contested decisions.

## License

MIT — see [LICENSE](LICENSE).
