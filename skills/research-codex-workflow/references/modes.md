# Runtime Modes Reference

Load this file when deciding which research workflow mode to use.

## Mode -> phase-shape composition

Each mode composes the Claude-Code phase shapes (see the Round Shape Map in
`full-adversarial-workflow.md`):

- **Mode 0 Lightweight**: a single Understand pass; no panel, no judge.
- **Mode 1 Standard**: Understand -> bounded Find->Verify -> a small synthesize; one Orchestrator, an
  optional read-only pass.
- **Mode 2 Full adversarial**: the full Round 0->G composition — Understand (A), a per-finding
  Find->Verify pipeline (B->C), a judge panel (D), the Decision Ledger & Action Gate (E, NOT a report
  synthesis), the user checkpoint (F), and Approved Implementation incorporating a Migrate stage (G).
- **Mode 3 Product-build**: out of scope while `allow_product_build` is false.

Note: Round E is the Decision Ledger and Action Gate; the report synthesis is the later Round G step.
Round G is broader than the Migrate shape — it is implementation/verification/documentation that
incorporates a Migrate stage, not a bare migration.

## Mode 0 - Lightweight Reconnaissance

Use for:

- ordinary repository reading;
- narrow code or documentation questions;
- small bugfixes;
- localized test, lint, or CI repairs;
- unfamiliar repository orientation.

Behavior:

- do not create a multi-agent panel by default;
- do not require an Experiment Card unless the work becomes costly or claim-producing;
- inspect only relevant files;
- run the smallest meaningful validation;
- report risky assumptions and next steps concisely.

## Mode 1 - Standard Research Workflow

Use for tasks that affect:

- experiments;
- baselines;
- metrics;
- leakage;
- data definitions;
- result tables;
- reviewer-facing claims;
- research documentation.

Behavior:

- write a compact Task Charter;
- apply the Decision Link and importance gate;
- use one Orchestrator and optional narrow read-only passes;
- audit evidence before accepting claims;
- create an Experiment Card for costly or claim-producing work;
- request a user checkpoint only for genuinely contested choices.

## Mode 2 - Full Adversarial Workflow

Use only when the user explicitly requests:

- adversarial;
- red-team;
- full-agent;
- multi-agent;
- research-team;
- multiple agents;
- 对抗模式;
- 多 Agent;
- 多智能体;
- 多个 agent;
- an unambiguous equivalent.

Behavior:

- load `full-adversarial-workflow.md`;
- run Round 0 through Round F, and Round G only after approval;
- isolate first-pass findings;
- run the deep-insight lens so discovery reaches design/statistical validity, not only surface drift;
- route verification by contestability (light pass for binary facts, adversarial panel for contestable
  claims) — do not flat-falsify every finding;
- anonymize findings before falsification and judging;
- put evidence audit before judge scoring; score every assembled packet (no cherry-picking);
- log external-dependent claims as unverified when no web/fetch tool exists (never claim a local-only
  run verified an external fact);
- stop at Round F when a user decision is required;
- do not edit contested research documents before approval.

## Mode 3 - Product-Build Workflow

Use only when the user explicitly authorizes a standalone `research-team` product or changes
`allow_product_build` to true.

Behavior:

- load `product-build-spec.md`;
- build a deterministic local-first product only after explicit authorization;
- keep the skill-first artifact contracts compatible with the product phase.

## Negative Rules

- Do not escalate just because a repository is unfamiliar.
- Do not spawn every role because the roster is long.
- Do not treat model agreement as evidence.
- Do not let a judge restore a claim rejected by the Evidence Tribunal.
- Do not edit contested protocol documents before a user checkpoint.
