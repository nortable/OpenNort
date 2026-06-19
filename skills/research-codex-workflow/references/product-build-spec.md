# Product Build Spec Reference

Load this file only when the user explicitly authorizes the standalone `research-team` product or
changes `allow_product_build` to true.

This skill (its `SKILL.md` and references) is the authoritative skill-first configuration.

The current execution configuration sets:

```yaml
execution_target: skill_first
allow_product_build: false
```

Therefore, ordinary adversarial research-agent redesign must update the skill and references only.
Do not scaffold a CLI, SQLite state store, provider adapter layer, or product test suite while product
build is disabled.

When product build is explicitly authorized later:

1. Re-read the authoritative prompt and any newer user instruction.
2. Inspect the target repository, installed Codex capabilities, tests, and configuration.
3. Create an implementation plan and ADR.
4. Build vertical slices with a deterministic supervisor, typed artifacts, offline mocks, worktree
   isolation, evidence audit, loop guard, judging, resumability, and evaluation.
5. Validate with unit, integration, end-to-end demo, lint, and type checks where supported.

The product phase must remain compatible with the skill artifact contracts.
