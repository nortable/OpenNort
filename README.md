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
  per-instance schemas, cross-artifact referential integrity, anonymization, concurrency/budget caps,
  **judge coverage** (every assembled evidence packet must be scored), **ledger→packet coverage**
  (every accepted ledger issue must trace to a judged packet — a second discovery round cannot append
  straight to the ledger), and a scan that forbids decision verbs in worker artifacts. `--audit-run
  <dir>` gates any real run tree with these checks (not just the synthetic fixture).
- **Web research with a reproducible evidence contract** — `scripts/fetch.py` gives the Literature
  Scout a real retrieval primitive: it fetches a URL, caches the bytes, and emits a `source-record`
  (url + retrieval_date + content_sha256), so a web-backed claim is reproducible and tamper-evident.
  Treated as untrusted data; opt-in per charter; absent a web tool, external-dependent claims are
  logged as `external_verification_unavailable` rather than faked. See `references/web-research.md`.
- **Code review reuses the substrate** — point the Round 0→G pipeline at a diff with code lenses
  (correctness / security / performance / reuse / tests / compatibility); proportionate verification,
  judge coverage, and the Round F checkpoint all carry over unchanged. See `references/code-review.md`.
- **Retained per-subagent debug records** — each dispatched subagent persists `agents/<agent_id>.json`
  for replay, audit, and later upgrades.
- **A one-command self-test** (`scripts/selftest.py`) that generates a synthetic run, validates it, and
  proves the harness *rejects* a dropped key, a dangling reference, an anonymization leak, an
  edit-before-approval, an unjudged evidence packet, and an accepted ledger issue with no judged
  packet. (`scripts/fetch.py --selftest` separately proves the fetch/cache/hash path offline.)

## Layout

```
skills/research-codex-workflow/   the skill (router + references + scripts + templates)
  SKILL.md                        compact mode router and invariants
  references/                     protocol, roster, contracts, loop guard, runbook, dispatch,
                                  code-review, web-research
  scripts/                        schemas.py, validate_artifacts.py, run_synthetic_fixture.py,
                                  create_run_workspace.py, selftest.py, fetch.py
  assets/templates/               JSON-compatible YAML artifact templates
  examples/                       synthetic adversarial fixture
docs/                             design notes
examples/synthetic-run/          a fully worked Round 0→G run (the self-test output)
```

## Quick start

```bash
# install: symlink the skill into ~/.codex/skills and verify it (idempotent).
# A symlink means `git pull` instantly updates the installed skill — no manual re-sync.
./skills/research-codex-workflow/scripts/install.sh          # or --copy for a frozen snapshot
# CODEX_SKILLS_DIR=/path ./skills/.../install.sh             # custom skills dir

# (install.sh already runs both, but you can re-run them any time:)
python3 skills/research-codex-workflow/scripts/selftest.py   # substrate: clean run + 6 negative controls
python3 skills/research-codex-workflow/scripts/fetch.py --selftest   # web fetch/cache/sha256 + policy refusals
```

Gate any real run tree (Codex or otherwise) with the fixture-agnostic checks:

```bash
python3 skills/research-codex-workflow/scripts/validate_artifacts.py --audit-run <run-dir>
```

Then invoke from Codex:

> Use the research-codex-workflow skill in full adversarial mode on this research repository. Run Round
> 0 through Round E, stop at Round F, and do not edit research-protocol documents until I approve the
> contested decisions.

## License

MIT — see [LICENSE](LICENSE).
