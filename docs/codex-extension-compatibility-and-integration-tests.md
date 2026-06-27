# Codex Extension Compatibility And Integration Tests

This document defines how OpenNort should behave as a Codex extension package and how external
workflow integrations are tested before they are allowed to touch the core workflow.

## Codex Extension Compatibility

OpenNort has two compatibility surfaces:

- Plugin distribution: `.codex-plugin/plugin.json` points Codex at `./skills/`.
- Skill execution: `skills/research-codex-workflow/SKILL.md` remains the runtime contract Codex reads
  after explicit or implicit skill activation.

The plugin exists to distribute and present the package. The skill remains the authoritative workflow.
Do not move orchestration rules into the plugin manifest. Do not add MCP servers, apps, hooks, or
runtime dependencies to the manifest unless the companion files exist and are validated.

Codex skill compatibility requirements:

- `SKILL.md` has `name` and `description` frontmatter.
- The description front-loads the trigger scope so implicit activation can work under progressive
  disclosure.
- Long workflow instructions live in `references/`.
- Deterministic helpers live in `scripts/`.
- Templates and sample artifacts live in `assets/` or `examples/`.
- Optional Codex UI/policy metadata lives in `skills/research-codex-workflow/agents/openai.yaml`.

Local authoring and distribution are intentionally separate:

- Repository-local authoring can use `.agents/skills` in a consuming repo.
- User-local authoring can use `$HOME/.agents/skills`.
- This repo's reusable distribution path is the plugin manifest, not a one-off user install.

## Enablement Checks

Run these checks from the OpenNort repo root before publishing or reinstalling the extension:

```powershell
python skills/research-codex-workflow/scripts/validate_extension_package.py
python skills/research-codex-workflow/scripts/selftest.py
python skills/research-codex-workflow/scripts/fetch.py --selftest
python C:/Users/nort/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
```

On Unix-like environments, `python3` is fine if that interpreter has the plugin validator's PyYAML
dependency installed.

Manual Codex pickup checks:

- The plugin list shows `opennort`.
- The skill selector shows `research-codex-workflow`.
- Explicit invocation with `$research-codex-workflow` loads the full skill.
- A prompt containing `OpenNort Run 1` or `adversarial research workflow` matches the skill
  description.
- Disabling the skill through `[[skills.config]]` makes it unavailable without deleting files.

## Integration Test Plan

Every integration starts as a schema-fit test. It must map an external input into existing OpenNort
artifacts before any source-level adapter is accepted.

Required fixture shape:

- input fixture under `examples/integration-fit/`;
- source and version identifiers for external systems;
- validation command used for the metadata gate;
- expected OpenNort artifacts named in the fixture;
- expected mapping into existing OpenNort artifact fields;
- rejection criteria for unsafe or incomplete mappings;
- negative controls for the future semantic runner.

The metadata gate is necessary but not sufficient. A fixture passes semantic integration only when a
runner maps it to concrete OpenNort artifacts, validates those artifacts with
`validate_artifacts.py`, and proves the negative controls are rejected.

### Test 1: Spec Kit Mapping

Fixture: `examples/integration-fit/spec-kit-feature.json`

Goal: prove a Spec Kit feature can map to OpenNort without new core roles.

Expected mapping:

- Spec Kit constitution or principles -> `00-charter.yaml.known_high_risk_choices`
- feature/spec -> Round A findings or hypotheses
- plan/tasks -> `round-f-implementation-plan.yaml.ordered_steps`
- unresolved ambiguity -> `round-f-user-checkpoint.yaml`

Pass criteria:

- no new standing role is required;
- no implementation step bypasses Round F approval;
- every external source has a `source-record` or an unavailable log;
- validation can run without changing `schemas.py`.

Fail criteria:

- the mapping needs untracked state, hidden assumptions, or non-artifact instructions;
- tasks become implementation work inside Run 1;
- user-owned choices are converted into accepted facts.

### Test 2: GitHub PR Bridge

Fixture: `examples/integration-fit/github-pr-diff.json`

Goal: map a PR or diff into the existing code-review lens.

Expected mapping:

- base/head SHA -> charter scope and evidence records
- changed file hunks -> Code Reviewer Finder inputs
- review findings -> Round A finding artifacts
- merge-blocking issues -> Round E ledger classes

Pass criteria:

- every finding cites a file path and changed hunk or surrounding code context;
- each blocker has a concrete reproducer, test, or security rationale;
- low-contestability findings take the light verification route;
- accepted merge gates trace to judged packets.

Fail criteria:

- a finding is based only on model prose;
- a reviewer edits code during Run 1;
- base/head SHA is missing or ambiguous.

### Test 3: Skill Marketplace Audit

Fixture: `examples/integration-fit/marketplace-skill-listing.json`

Goal: audit a third-party skill or marketplace entry before importing any content.

Required checks:

- license and attribution;
- target harness and compatibility claim;
- dependency footprint;
- shell/network/write behavior;
- prompt-injection or instruction-shadowing risk;
- schema-fit cost;
- whether the asset should be mined, wrapped, deferred, or rejected.

Pass criteria:

- no wholesale import is recommended without individual review;
- every accepted candidate has a source URL, license observation, and dependency summary;
- unsafe scripts or ambiguous permissions are downgraded or rejected.

Fail criteria:

- a marketplace README claim is treated as runtime proof;
- executable scripts are trusted without review;
- the candidate requires broader permissions than OpenNort can bound.

### Test 4: Runtime Adapter Boundary

Fixture: `examples/integration-fit/runtime-adapter-boundary.json`

Goal: ensure LangGraph, OpenAI Agents SDK, Microsoft Agent Framework, OpenHands, SWE-agent, or Plandex
remain optional execution backends rather than hidden core dependencies.

Pass criteria:

- the adapter consumes an approved `round-f-implementation-plan.yaml`;
- the adapter returns a manifest of commands, files, outputs, hashes, and failures;
- OpenNort reruns the Evidence Tribunal and final report on adapter results;
- OpenNort can run without the adapter installed.

Fail criteria:

- the adapter changes hypotheses, metrics, thresholds, or split definitions;
- the adapter owns final truth instead of returning evidence;
- installing the adapter becomes required for basic skill use.

## Release Gates

A release candidate for the Codex extension package must pass:

- plugin manifest validation;
- extension package and fixture-metadata validation;
- OpenNort selftest;
- fetch selftest;
- at least one schema-fit fixture review for each newly advertised integration class;
- manual Codex activation check in a fresh thread.

Runtime adapters are explicitly not release gates for the core extension package.
