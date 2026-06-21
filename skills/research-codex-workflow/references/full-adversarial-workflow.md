# Full Adversarial Workflow Reference

> Reminder: this is the METHOD, not the SUBJECT. Produce findings and the plan by dispatching real
> subagents; do not sit and audit your own process. The validator is one final command, not an ongoing
> activity.

This is the one workflow the skill runs (rounds 0→G), executed as TWO separate invocations: **Run 1 =
Round 0→F** (research + plan; read-only; STOPS at the implementation plan) and **Run 2 = Round G** (a
separate, user-initiated implementation pass). Never fuse them in one run. It is Orchestrator-mediated:
subagents return bounded artifacts to the root Orchestrator and do not directly debate one another
unless the installed runtime has verified peer-to-peer agent-team support.

Execution path: DEFAULT to real `multi_agent_v1` subagents
(`spawn_agent`/`wait_agent`/`send_input`/`close_agent`). The Orchestrator probes availability at
Round 0; if `spawn_agent` is unavailable it falls back to sequential artifact-producing passes that
preserve role separation, records `ran_as_sequential_fallback: true` in the coverage log, and STILL
writes one `agents/<agent_id>.json` record per pass (the completion gate binds in fallback too). Either
way maximum depth is 1 and the 12-open concurrency cap binds.

**Spawn footgun:** `multi_agent_v1` REJECTS `spawn_agent` when `fork_context: true` is combined with an
explicit `agent_type`. Round A needs independent ISOLATED contexts, so the canonical call is
`spawn_agent(agent_type=<role>, fork_context=false, prompt=...)` — pass `agent_type` with
`fork_context` false/omitted, OR `fork_context: true` with no `agent_type`, never both.

For a complete team run, also load `team-runbook.md` and `role-dispatch-templates.md`.

## Round Shape Map

Each round maps to a named Claude-Code phase shape and a sync mode. `barrier` means the Orchestrator
`wait_agent`s on ALL members of the round before advancing; `pipeline` means each item streams to the
next stage as it lands. Maximum subagent depth stays 1 in every round.

| Round | Master shape | Sync mode | Orchestrator pattern |
|---|---|---|---|
| 0 Charter | gate | local | charter + relevance gate, no fan-out |
| A Independent findings | Understand | barrier | parallel readers -> one `round-a-findings-index.yaml` |
| B Cross-falsification | Find->Verify | pipeline | each anonymized finding streams to a falsifier as it lands |
| C Evidence Tribunal | Find->Verify | pipeline | each finding streams to the Evidence Auditor; Orchestrator assembles packets |
| D Judge Panel | judge panel | barrier | wait for every judge score, then synthesize from the winner |
| E Decision ledger | synthesize (ledger) | local | one decision class + action per issue |
| F Plan + checkpoint | gate | local | write the implementation plan + smallest blocking decision set, then STOP (Run 1 ends) |
| G Implementation (Run 2) | implementation incl. a Migrate stage | per-site pipeline | SEPARATE user-initiated run: load the plan, transform each site in isolation, verify as it lands |

Rounds B and C are SEPARATE pipelined stages (not fused); Rounds A and D are barriers. The
authoritative ordered procedure is the Dispatch Script in `team-runbook.md`.

## Orchestration model (Codex translation of the Claude Code Workflow engine)

This workflow is a deliberate translation of the Claude Code `Workflow` engine onto the Codex substrate
(resident main agent + `multi_agent_v1`, depth 1, no JS runtime). The mapping:

| Master template (the Workflow engine) | Codex round / mechanism |
|---|---|
| `parallel(thunks)` — barrier, await all | Round A and Round D (`wait_agent` on all members); Round G's tribunal-rerun / ledger / report |
| `pipeline(items, …stages)` — per-item, no inter-stage barrier | Rounds A→B→C stream per finding; Round G per site |
| `agent(prompt, {schema})` — validated structured output | one schema-conformant artifact per worker, checked by `validate_artifacts.py` + Orchestrator redispatch (≤2×) |
| adversarial verify (N skeptics, default-refuted, majority) | Round B adversarial route: ≥3 perspective-diverse refuters, `refute_disposition` defaults to `refuted`; majority → DOWNGRADE into the Round C tribunal (NOT vote-kill — evidence adjudicates) |
| perspective-diverse verify (distinct lenses) | Round B refuter lenses + Round D judge lenses (co-judges on a packet must differ) |
| judge panel (N attempts, synth-from-winner, graft) | Round D ≥2-judge panel; synthesize-from-winner recorded in `judge_synthesis` |
| loop-until-dry (dedup vs SEEN) | `stop_rule{loop_until_dry_K, dedup_against: all_seen}` |
| multi-modal sweep | Round A Finder lens menu (data / baseline / claim / code / hypothesis / deep) |
| completeness critic | Round E.5 Completeness Critic |
| worktree isolation for parallel writers | `create_run_workspace --writers` (git worktree if a repo, else a WEAKER disjoint locked dir) |
| `budget` token-scaled depth | coarse `budget_tier` fan-out ceilings (economy 2 / standard 4 / deep 6) |

**Translation seams — where the substrate forces a divergence (stated honestly, not hidden):**

1. **The Orchestrator IS the engine.** No JS runtime exists; the main Codex agent hand-executes
   `parallel` (= `wait_agent` on ALL members) and `pipeline` (= stream each finding to its next stage as
   it lands) via `spawn_agent`/`wait_agent`/`close_agent`. Workers never advance a group.
2. **Depth-1 flattening of nested panels.** The engine's `parallel(findings.map(f => parallel(lenses)))`
   is illegal at depth 1, so the Orchestrator spawns every (finding × lens) verifier ITSELF at depth 1
   within the 12-open cap and reassembles per finding — a Falsifier never spawns judges. This is forced
   by the `max_subagent_depth == 1` check, not a choice.
3. **The validator IS the schema layer.** `agent({schema})` retries transparently at the tool layer;
   Codex has no such layer, so the Orchestrator must explicitly validate each returned artifact
   (`--artifact … --type …`) and redispatch the same worker with the error appended (≤2×, then
   `status: failed` + log).
4. **Round A is an ITERATED barrier, not a single one.** loop-until-dry re-spawns finder rounds that
   interleave with findings already streaming through B/C — a shape the plain engine primitives do not
   model. Each finder round is its own barrier (wait members, dedup vs ALL SEEN) before deciding whether
   to re-spawn.
5. **What the completion gate proves — and does not.** It HARD-fails on: <3 distinct completed spawn
   records, missing generate(A)+verify(B/C/D) coverage, an artifact whose `agent_id` traces to no spawn
   record, a one-judge "panel", duplicate-lens co-judges, zero `depth: deep` findings, dangling
   references, an anonymization leak, an unjudged packet, or an edit-before-approval. It does NOT verify
   that B/C actually STREAMED rather than ran as three barriers (`dispatch_kind: pipeline` is a declared
   field plus an advisory warning, not a hard gate), and it cannot prove a real `multi_agent_v1` spawn
   occurred — it proves that ≥3 internally-consistent, cross-referenced spawn RECORDS exist and every
   artifact traces to one, which makes forging a green run strictly more expensive than running it.
   Proportionate-verification and no-silent-caps are convention + non-blocking warnings; only the
   zero-deep-findings subset is a hard failure.

## Round 0 - Charter and Relevance Gate

Create a Task Charter before dispatch:

```text
TaskCharter:
- run_id:
- objective:
- decision_to_support:
- decision_owner:
- scope:
- non_goals:
- success_criteria:
- known_high_risk_choices:
- likely_affected_files:
- required_evidence:
- budget_or_cost_constraints:
- user_checkpoint_required: yes|no|unknown
- edit_permission_before_checkpoint: yes|no
- external_evidence_needed: yes|no|unknown
```

Decide `external_evidence_needed` deliberately: set **yes** if any claim depends on facts outside the
repo (novelty, prior-art, SOTA comparison, leakage/contamination, external dataset or pretraining-corpus
provenance). `yes` makes a Literature Scout MANDATORY in Round A; if no web tool reaches the network,
every such claim is logged in `coverage_log.external_verification_unavailable`. The completion gate
fails a `yes` charter that produced neither a `source-record` nor an unavailable-log.

For each proposed task, create a Decision Link:

```text
DecisionLink:
- if_positive_what_changes:
- if_negative_what_changes:
- if_null_or_inconclusive_what_changes:
- current_uncertainty_reduced:
- downstream_action_unlocked:
```

Gate rules:

- no decision consequence -> `REJECT` or `PARK`;
- only curiosity value -> use a small explicit exploration budget or park;
- protocol, dataset, baseline, metric, or headline-claim change -> user checkpoint;
- expensive work without a discriminating outcome -> reject or redesign;
- a claim depends on external facts (novelty/prior-art/SOTA/leakage/provenance) ->
  `external_evidence_needed: yes` and a Literature Scout is dispatched in Round A;
- no full panel until the Orchestrator accepts the charter.

## Round A - Independent Findings and Candidate Hypotheses (Understand shape, barrier)

Dispatch three to six independent agents when subagents are available and authorized. Do not show an
agent another agent's first pass.

Round A is a **barrier**: the Orchestrator waits for every first-pass agent, then collects the findings
into a single `round-a-findings-index.yaml` (`finding_id`, `source_role`, `claim_type`,
`affected_decision`, `artifact_path`) — the routing surface for Round B. The index does NOT pre-assign
anonymized IDs; Round B owns anonymization.

Round A (and Round B) may **loop until dry**: keep spawning finders until `loop_until_dry_K` consecutive
rounds add nothing new, deduping each finding against everything SEEN this run (not only what was
accepted). Log every dropped or deduped finding — no silent caps — and respect the
`agent_count_backstop`.

Typical audit roles:

- Data Auditor;
- Baseline Auditor;
- Methodologist;
- Code Red-Team;
- Claim Auditor;
- Relevance Arbiter.

Typical open research roles:

- Literature Scouts with different search strategies;
- Hypothesis Generators, including a null hypothesis;
- Data or Methodology Auditor;
- Relevance Arbiter.

**Literature Scout is MANDATORY (not optional) when the charter set `external_evidence_needed: yes`** —
or whenever a finding makes a novelty / prior-art / SOTA / leakage / provenance claim that local
inspection cannot settle. Dispatch it as a Round A Finder lens that retrieves with `scripts/fetch.py`
and emits `source-record` evidence. If no web tool reaches the network it is a no-op and every such
claim is logged in `coverage_log.external_verification_unavailable` — proactively reach for it; do not
wait to be asked.

Every output uses the Finding contract from `artifact-contracts.md`. Findings are provisional until
the Evidence Tribunal accepts them.

**Discovery depth (do not stop at surface drift).** Each finder returns MULTIPLE findings, not one,
and labels every finding with `depth` (`surface` = a doc-vs-tree / number-vs-number / file-exists
mismatch a grep settles; `deep` = a design, statistical-validity, or scientific-soundness insight that
requires reasoning about whether the research itself is correct) and `contestability`
(`low|medium|high`). At least one team member MUST run the **deep-insight lens** — statistical power /
MDE vs the claimed effect, the resampling unit and effective-N, leakage and pretraining contamination,
endpoint definition, confirmatory-vs-exploratory structure — so the run does not return only surface
drift. A discovery pass that produces zero `depth: deep` findings is a coverage gap: log it and
surface it at Round E.5 (`validate_artifacts.py` warns when no finding is `deep`).

## Round B - Anonymous Cross-Falsification (Find->Verify pipeline)

Rounds A->B->C form a per-finding **pipeline**: once Round A's barrier releases, each anonymized
finding streams independently through falsification (Round B) and evidence audit (Round C) as it lands
— one finding can be in Round C while another is still in Round B. The only whole-set barrier is held
at Round D. In-flight fan-out never exceeds the 12-open concurrency cap (queue the remainder); keep
Round C before any judging.

The Orchestrator must:

1. remove author identity and persuasive framing;
2. assign stable IDs such as `F-A1`, `F-B2`, or `H-3`;
3. assign each Falsifier a finding or hypothesis it did not produce;
4. prevent self-review;
5. limit debate to one initial critique and at most one bounded response;
6. require evidence or a minimal resolvable test;
7. ask the Relevance Arbiter whether the dispute changes the next decision.

Unsupported rhetorical attacks remain unsupported.

**Proportionate verification (route by contestability — do this BEFORE assigning refuters).** Scale
verification effort to each finding's `contestability`; do not run a flat multi-lens panel on every
finding. The Orchestrator routes each finding:

- `contestability: low` — a binary doc-vs-tree / number-vs-number / file-exists fact that a single
  `ls`, `rg`, or command settles → the **light route**: exactly ONE confirmation pass (a single
  Falsifier, or fold the check straight into the Round C Evidence Auditor). A fact that cannot be
  argued with does not need three skeptics.
- `contestability: medium|high`, or any high-stakes blocker whose mis-call is costly (a power,
  leakage, fairness, endpoint, or methodological judgment) → the **adversarial route**: the full
  perspective-diverse refuter panel below.

Record each finding's `verification_route` and the light/adversarial split in the round summary
`coverage_log.verification_route_counts`. The whole point is to move the verification budget OFF binary
facts and ONTO the few genuinely contestable claims: a 3-lens panel on file-exists findings spends
agents where nothing can be overturned (the failure mode is "keeps judging" with zero findings
overturned), while a single pass on a statistical-power claim misses the downgrade.

**Perspective-diverse refuters (adversarial route only).** Assign at least three independent refuters
per finding, each under a distinct lens (e.g. correctness, methodology, decision-impact), each
defaulting `refute_disposition` to `refuted` when uncertain (recorded with its `lens` in the Critique).
A finding that a majority refutes is DOWNGRADED and routed INTO the Round C Evidence Tribunal — it is
NOT vote-killed before evidence adjudication, preserving evidence-before-judging and "unsupported
attacks remain unsupported". Honor the concurrency cap with top-K or serialized batches,
smallest-mode-that-fits.

## Round C - Evidence Tribunal

The Evidence Auditor evaluates findings and critiques before any judge panel. It RETURNS
`EvidenceDecision` artifacts (`support_status`, `evidence_quality`, `accepted_evidence_ids`,
`downgraded_severity`, reason) as data and does NOT remove items or assemble packets. The Orchestrator
(not the auditor) assembles `evidence-packets/` from those decisions — only `accepted` or
`partially_supported` decisions become packets — and assigns `packet_id`s. Packet assembly is an
Orchestrator integration step, keeping the worker free of any final-decision authority.

Acceptable evidence includes at least one of:

- file path plus line, symbol, or structured location;
- command plus output summary and exit status;
- dataset statistic plus reproduction command or query;
- source URL or source identifier plus retrieval date and exact support location;
- artifact path plus hash or immutable run ID;
- test or experiment result plus environment and invocation details.

Rules:

- model output alone is not evidence;
- plausible unevidenced concerns become `needs_evidence`, not blockers;
- separate observation, inference, and recommendation;
- preserve contradictory, negative, and null evidence;
- verify that a citation or artifact supports the claim;
- downgrade severity when evidence is weak;
- mark project-owner policy choices as `needs_user_decision`;
- do not pass unsupported persuasive text to judges as accepted evidence.

**External-evidence honesty.** Some claims can only be settled against facts OUTSIDE the repo — a
public dataset's patient list (leakage), a prior-art or SOTA number, a pretraining-corpus provenance.
The Literature Scout settles the external part with **Codex's native search + fetch/PDF tools** —
reading the actual paper and quoting the exact equation / baseline+dataset+metric / provenance — and
optionally pins a `content_sha256` via `scripts/fetch.py` for reproducibility. The Evidence Auditor
accepts what the source actually supports and returns `needs_evidence` for anything still unread; the
Orchestrator records the gap in `coverage_log.external_verification_unavailable[]` and as a
`claim_unverified` Completeness gap, rather than letting a local-only check read as fully verified. If
no native web tool AND fetch.py can reach the network, the Literature Scout is a no-op and EVERY
external-dependent claim is logged this way — never silently treated as closed. (A pure local audit is
legitimate; claiming it verified an external fact it could not reach is not.)

## Round D - Independent Judge Panel

Use two or three independent judge passes for high-value decisions. Judges receive:

- anonymized packet IDs;
- accepted or partially accepted evidence;
- relevant counterevidence;
- the Task Charter and rubric;
- no agent identity;
- no other judge's score.

Judges must not invent evidence, override Evidence Tribunal hard failures, excuse invalid tests or
leakage by majority vote, or convert preference into a blocker.

Default rubric:

```text
Decision relevance              20
Technical validity              20
Evidence quality                15
Methodological validity         15
Reproducibility                 10
Alternative explanations        10
Scope adherence                  5
Calibrated language              5
```

### Panel aggregation (Orchestrator-owned)

The canonical hard-gate-first + median rule lives in `team-runbook.md` "Judge Aggregation"; do not
restate it. The panel adds three master-template elements on top of it:

- **Perspective-diverse lenses**: give each judge a distinct emphasis lens — decision-impact,
  methodology, reproducibility — over the SAME rubric, with no cross-score visibility. Diverse lenses
  catch failure modes that identical passes miss.
- **A real panel, not a single judge**: whenever any packet is assembled, Round D must have **≥2
  distinct judge `agent_id`s** — `validate_artifacts.py` (`validate_judge_coverage`) FAILS a run with
  one judge, because synthesize-from-winner has no winner to choose from a single pass. Every assembled
  `evidence-packets/*.yaml` must still receive at least one score (a judge may NOT score only "the most
  decision-critical" packet and leave the rest unscored). With 2-3 judges, split the packets across the
  panel so every packet is covered; when two judges score the SAME packet their emphasis lenses must be
  DISTINCT (the validator rejects duplicate-lens co-judges). (Packets are only assembled from accepted /
  partially_supported Round C decisions, so a Tribunal-rejected claim is never assembled and needs no
  score.)
- **Synthesize from the winner**: adopt the highest-scoring accepted pass's `final_class` and
  rationale as the spine, then GRAFT any blocker, counterevidence, or `hard_gate_failures` entry a
  runner-up raised that the winner omitted. Record the synthesis in the final report's `judge_synthesis`
  field — the winning packet, the per-packet judges and their lenses, the chosen median, and each
  `grafted_from` runner-up point — so the graft is auditable and never a silent drop. (A partial panel
  still produces an honest partial report per the budget-exhaustion rule — it is not silently
  disqualified.)

## Round E - Orchestrator Decision Ledger and Action Gate

Classify each material issue using exactly one primary class:

- `accepted_blocker`;
- `accepted_non_blocking`;
- `rejected_or_unsupported`;
- `needs_user_decision`.

For proposed work, assign one action:

- `RUN`;
- `DEFER`;
- `PARK`;
- `REJECT`;
- `HUMAN_REVIEW`.

Explain the decision consequence and cite accepted evidence IDs. If an issue requires an experiment,
create an Experiment Card and pass it through relevance and method gates before implementation.

## Round E.5 - Completeness Critic (pre-checkpoint)

Before the Round F checkpoint, dispatch one independent **Completeness Critic** (read-only; it must
have produced none of the reviewed findings — do not fold it into the Relevance Arbiter or Loop Guard,
which would recreate the same-role-generates-and-judges failure). It returns a `CompletenessCritique`
asking "what is missing?" — a lens not run, a claim unverified, a source unread, a hypothesis
untested. The Orchestrator must close every `must_close` gap or surface it verbatim in the Round F
checkpoint (no silent proceed).

## Round F - User Checkpoint

Stop here when a user decision, contested edit, costly action, or protected research-document edit is
required.

Checkpoint triggers include:

- evaluation split or cross-validation protocol;
- primary denominator or analysis unit;
- metric definitions or success thresholds;
- headline versus diagnostic baselines;
- external, pretrained, or potentially contaminated baselines;
- historical planning-document treatment;
- claims of superiority, novelty, leakage safety, readiness, or publication status;
- expensive paid runs or material scope expansion;
- destructive, external, or irreversible actions.

Checkpoint format:

```text
UserCheckpoint:
- decision_id:
- decision_required:
- why_it_matters:
- recommended_option:
- alternatives:
- evidence_ids:
- files_or_runs_affected:
- consequence_of_no_decision:
```

Ask only the smallest blocking set. Stop after presenting the checkpoint and do not edit affected files.

### Round F deliverable: the implementation plan (Run 1 ends here)

Round F also produces the run's actual product — a detailed, literature-backed
`round-f-implementation-plan.{yaml,md}` (schema `implementation-plan`): `objective`, `approach` (the
chosen design + alternatives considered), `literature_summary` (source-records, or what was logged
unverified), a file-level `change_list`, `ordered_steps` (each a discrete task a Run-2 implementer can
execute), `validation_strategy`, `risks`, and `open_decisions`. Then **STOP** — Run 1 (Research & Plan)
is read-only and ends here; hand the plan and the checkpoint to the user. Do NOT roll forward into
implementation in the same run; fusing planning and implementation overloads the context and stalls the
model.

## Round G - Implementation (Run 2: a SEPARATE, user-initiated run)

Round G is **Run 2**, started only when the user explicitly asks to implement an approved plan. It is a
FRESH invocation that loads `round-f-implementation-plan.yaml` as its input and executes its
`ordered_steps`; it does not re-derive the plan. Implementation incorporates a **Migrate shape**:
discover the edit or experiment sites, then transform each in an isolated worktree or disjoint workspace
as a per-site pipeline (verify each as it lands). The Evidence-Tribunal rerun, ledger update, and final
report stay GLOBAL Orchestrator barrier steps, not per-site. Use the worktree/disjoint-directory rule in
`worktrees-and-artifacts.md`; a disjoint working directory is weaker isolation than a git worktree and
must not be silently equated with one.

1. Write an edit or experiment plan.
2. Assign non-overlapping ownership.
3. Create an immutable Experiment Card when relevant.
4. Use isolated worktrees for concurrent writers.
5. Keep reviewers read-only.
6. Run focused tests, smoke checks, consistency checks, and reproduction commands.
7. Replicate high-impact or surprising results when justified.
8. Rerun the Evidence Tribunal on new results.
9. Update the decision ledger.
10. Synthesize a final report using accepted evidence only.

No worker may silently change hypotheses, metrics, thresholds, splits, denominators, or acceptance
criteria. A material change creates a new Experiment Card version and returns to the proper gate.

## Completion Gate (before any final answer)

The run is not finished when the prose reads well — it is finished when the substrate validates. Before
writing ANY final answer, run:

```
python3 scripts/validate_artifacts.py --audit-run .research-workflow/runs/<run_id>/
```

A non-zero exit means the run is incomplete: fix or redispatch, do not narrate a result. The gate is
fixture-agnostic and fails on missing/too-few `agents/<id>.json` spawn records, an artifact whose
`agent_id` traces to no spawn record, zero `depth: deep` findings, a generate round with no verify
round (or vice-versa), a single-judge (non-panel) Round D, dangling cross-references, an anonymization
leak, an unjudged evidence packet, `edit_permission_before_approval: true`, a plan run missing its
`round-f-implementation-plan.yaml`, or a plan run that contains a `round-g-final-report.yaml` (a fused
run). This is what makes a single-context synthesis that *claims* to have run the team impossible to
pass off as a real run. Record the result where the run ends: **Run 1** puts the `OK:` line +
`audit_run_ok: true` + `audit_run_command` in `round-f-implementation-plan.{yaml,md}`; **Run 2** puts
them in `round-g-final-report.{yaml,md}`.
