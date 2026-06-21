# OpenNort

A deterministic, adversarial, multi-agent **research workflow** for Codex — packaged as a skill. It
keeps research-oriented coding (paper reproduction, baselines, evaluation, leakage, result tables,
reviewer-facing claims) decision-linked, evidence-gated, and loop-bounded, with a hard separation
between the Orchestrator (which owns all control flow) and bounded worker subagents (which only return
schema-validated data).

The division of labor mirrors the Claude Code Workflow orchestration model, translated into the Codex
runtime (the main agent as Orchestrator plus `multi_agent_v1` subagents; no JS engine).

## What it gives you

- **One enforced mode, run as two separate passes.** No router, no lighter mode: invoking the skill
  commits to the full adversarial workflow, split into **Run 1 — Research & Plan** (Round 0→F,
  read-only, ends with a detailed literature-backed `round-f-implementation-plan`) and **Run 2 —
  Implementation** (Round G, a separate user-initiated run that executes the approved plan). Planning
  and implementation are never fused in one run — the run-mode gate rejects a plan run that produced a
  Round-G report.
- **A full adversarial protocol** (Round 0→G): independent findings → anonymous cross-falsification →
  Evidence Tribunal → independent Judge Panel → Orchestrator decision ledger → user checkpoint →
  approved implementation. Each round is mapped to a named Claude-Code phase shape (Understand /
  Find→Verify pipeline / judge panel / synthesize) with explicit `barrier` vs `pipeline` semantics; an
  "Orchestration model" section documents the primitive-by-primitive mapping and the honest Codex
  translation seams.
- **A completion gate that real subagents actually ran.** `--audit-run <dir>` fails a run with no/too-few
  `agents/<id>.json` spawn records, an artifact not traceable to a spawn, zero deep findings, a
  single-judge (non-panel) Round D, an edit-before-approval, or a fused plan/Round-G run — so a
  single-context synthesis that *claims* to have run the team cannot pass.
- **Discovery before judgment** — finders return multiple findings labeled `depth`
  (surface drift vs deep design/statistical-validity insight) and `contestability`; a mandatory
  deep-insight lens (power/MDE, resampling unit & effective-N, leakage, endpoint definition,
  confirmatory-vs-exploratory structure) keeps the audit from stopping at doc-vs-tree drift. A run with
  zero deep findings is a logged coverage gap.
- **Proportionate verification** — verification effort is routed by `contestability`: binary
  file-exists / number-vs-number facts get one confirmation pass, and the multi-lens falsifier/judge
  panel is reserved for genuinely contestable claims. No more spending a 3-lens panel on facts that
  cannot be overturned.
- **Two-tier hard role split** — workers return artifacts-as-data and own zero decisions; an artifact's
  author can never be its own skeptic, auditor, or judge (machine-checked `agent_id` provenance).
- **A deterministic substrate** — every artifact has a canonical schema
  (`scripts/schemas.py`) that a stdlib validator (`scripts/validate_artifacts.py`) actually enforces:
  strict per-instance schemas, evidence-record IDs that resolve to concrete records, core run
  artifacts, declared-round summaries, cross-artifact referential integrity, anonymization,
  generate/verify provenance including EvidenceDecision authors,
  concurrency/budget caps, writer-ownership overlap checks, **judge coverage** (every assembled
  evidence packet must be scored), **ledger→packet coverage** (every accepted ledger issue must name
  source claims and trace to a judged packet), Round F checkpoint gating, and a scan that forbids
  decision verbs in worker artifacts. `--audit-run <dir>` gates any complete real run tree with these
  checks (not just the synthetic fixture).
- **Proactive literature review on Codex's native tools.** When a claim turns on an external fact
  (novelty / prior-art / SOTA / leakage / provenance) the charter sets `external_evidence_needed: yes`
  and a Literature Scout is mandatory — it uses **Codex's native search + fetch + PDF tools** to find
  and *read* the papers (quoting the exact equation, the baseline method + dataset + metric, the
  implementation detail), not a generic summary. `scripts/fetch.py` is the optional deterministic
  archive that pins a `content_sha256` for reproducibility; it does not reinvent a fetcher/parser. The
  gate fails a `yes` charter that produced neither a `source-record` nor an `external_verification_unavailable`
  log.
- **Code review reuses the substrate** — point the same Round 0→F pipeline at a diff with code lenses
  (correctness / security / performance / reuse / tests / compatibility); proportionate verification,
  judge coverage, and the Round F checkpoint all carry over unchanged (ledger classes map to merge gates).
- **Retained per-subagent debug records** — each dispatched subagent persists `agents/<agent_id>.json`
  for replay, audit, and later upgrades.
- **A one-command self-test** (`scripts/selftest.py`) that generates a synthetic plan run, validates it,
  and proves the harness rejects 11 negative controls: a dropped required key, a dangling evidence id, an
  anonymization leak, an edit-before-approval, an unjudged packet, a ledger bypass, a faked run with no
  spawn records, a surface-only (zero-deep) discovery pass, a single-judge non-panel Round D, a declared
  literature run that produced no evidence, and a plan run fused with a Round-G report.
  (`scripts/fetch.py --selftest` separately proves the fetch/cache/hash path + SSRF policy offline.)

## Layout

```
skills/research-codex-workflow/   the skill (one lean enforced mode + references + scripts + templates)
  SKILL.md                        invariants, the two-run split, and the completion gate
  references/                     full-adversarial-workflow, team-runbook, agent-roster,
                                  role-dispatch-templates, artifact-contracts, worktrees-and-artifacts,
                                  loop-guard, experiment-card, experiment-gates
  scripts/                        schemas.py, validate_artifacts.py, run_synthetic_fixture.py,
                                  create_run_workspace.py, selftest.py, fetch.py
  assets/templates/               JSON-compatible YAML artifact templates (incl. implementation-plan)
  examples/                       synthetic adversarial fixture
docs/                             design notes (redesign-mirror-claude-roadmap)
examples/synthetic-run/          deterministic Run-1 plan-run fixture (the self-test output)
```

## Quick start

```bash
# install: symlink the skill into ~/.codex/skills and verify the installed target.
# A symlink means `git pull` instantly updates the installed skill — no manual re-sync.
./skills/research-codex-workflow/scripts/install.sh          # or --copy for a frozen snapshot
# CODEX_SKILLS_DIR=/path ./skills/.../install.sh             # custom skills dir

# (install.sh already runs both, but you can re-run them any time:)
python3 skills/research-codex-workflow/scripts/selftest.py   # substrate: clean run + 11 negative controls
python3 skills/research-codex-workflow/scripts/fetch.py --selftest   # web fetch/cache/sha256 + policy refusals
```

Gate any real run tree (Codex or otherwise) with the fixture-agnostic checks:

```bash
python3 skills/research-codex-workflow/scripts/validate_artifacts.py --audit-run <run-dir>
```

Then invoke from Codex:

> Use the research-codex-workflow skill on this research repository. Run Run 1 (Round 0→F): review the
> literature for prior-art/SOTA/leakage, run the adversarial findings → falsification → evidence →
> judge-panel pipeline, and produce a detailed implementation plan. Stop at the Round F checkpoint and
> do not edit anything — I will start Run 2 to implement once I approve the plan.

## License

MIT — see [LICENSE](LICENSE).
