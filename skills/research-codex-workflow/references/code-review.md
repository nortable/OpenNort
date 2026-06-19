# Code Review Mode Reference

Load this file when the user asks for a code review, PR review, diff review, or "review my changes" —
as opposed to a research/documentation audit. Code review REUSES the full adversarial substrate
(Round 0→G, the Finding→Critique→Evidence-Tribunal→Judge pipeline, proportionate verification, judge
coverage, the decision ledger, and the Round F checkpoint); only the inputs and lenses change. Do not
build a parallel mechanism — point the existing machinery at a diff.

## What changes vs a research audit

- **Input is a diff, not a doc set.** Scope the run to a change: `git diff <base>..<head>`, a PR, or a
  named set of changed files. Finders read the hunks PLUS enough surrounding context to judge
  correctness (callers, the function being changed, the test that covers it). Record the base/head
  SHAs in the charter so the review is reproducible.
- **Findings are still `Finding` artifacts** (no new schema). A bug is a claim with severity, evidence
  (`file:line` in the diff), `depth`, and `contestability`:
  - `depth: surface` = style, naming, lint, a comment typo;
  - `depth: deep` = a real defect — wrong logic, a broken invariant, a security hole, a concurrency
    bug, a perf regression, a backward-incompatible API change.
  - `contestability: low` = obviously wrong / reproduces with a trivial input;
    `contestability: high` = a subtle race / edge case a skeptic could reasonably dispute.

## Review lenses (Round A finders)

Assign finders by lens, each returning multiple labeled findings:

1. **Correctness / bugs** — logic errors, off-by-one, null/empty/overflow, error handling, broken
   invariants, wrong control flow, regressions in changed behavior.
2. **Security** — injection, authz/authn gaps, unsafe deserialization, secrets, path/SSRF, unsafe
   defaults, untrusted input reaching a sink.
3. **Performance** — accidental O(n²), N+1 queries, work in hot loops, unbounded memory, blocking I/O
   on a hot path.
4. **Reuse / simplification** — duplicated logic that already exists, a simpler stdlib/library call,
   dead code, needless abstraction (quality, not bugs).
5. **Tests / regressions** — does the change have a test? does it break an existing contract? is a
   claimed fix actually exercised?
6. **API / compatibility** — signature, schema, config, or wire-format changes that break callers or
   persisted data.

At least one finder runs a **deep** pass (correctness + security are usually where the `deep` findings
are); a review that returns only style nits has not done the job.

## Proportionate verification, applied to code

Route Round B by `contestability` exactly as elsewhere:

- A clear bug that reproduces with a trivial input is `contestability: low` → ONE light confirmation
  (re-read the hunk, or note the reproducing input). Do not convene a 3-lens panel on an obvious
  off-by-one.
- A subtle defect (a race, an edge case, "is this input actually reachable?") is `medium|high` → the
  adversarial panel, and the Critique's `minimal_test_to_resolve` should be a concrete reproducing
  test or input, not prose. The single best refutation of a code-review finding is a failing/passing
  test, so prefer that over debate.

Adversarial verify is doubly valuable here: a code reviewer's most common failure is a confident false
positive ("this is a bug" on a path that cannot occur). Default `refute_disposition` to `refuted`
unless the reviewer can show the buggy path is reachable.

## Decision classes (ledger)

- `accepted_blocker` — must fix before merge (real bug, security, breaking change).
- `accepted_non_blocking` — worth fixing but not merge-blocking (nit, minor perf, cleanup).
- `rejected_or_unsupported` — false positive: the "bug" path is unreachable or the claim has no
  evidence.
- `needs_user_decision` — a design/trade-off choice the author owns (naming, an intended behavior
  change, an acceptable-risk call).

## Round F / Round G

- Round F: present the smallest blocking set (must-fix bugs) and stop. Do NOT edit the author's code
  before approval, same as the doc-audit checkpoint.
- Round G (after approval): apply fixes in isolated worktrees (one writer per non-overlapping area),
  add or update the test that proves each fix, rerun the Evidence Tribunal on the new state, and write
  the final review report from accepted evidence only. A fix with no test that demonstrates it is an
  unsupported claim.

## Team shape

See `team-runbook.md` "Code Review". Minimal team: Correctness, Security, and one of
Performance/Reuse finders; Falsifier (adversarial route); Evidence Auditor; 2 Judges. Scale finders to
diff size and risk, honoring the 12-open concurrency cap.
