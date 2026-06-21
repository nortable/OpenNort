# Round F Implementation Plan (Run 1 deliverable)

- Objective: Apply the accepted blocker before trusting the protocol claim.
- Approach: Adopt the winning judge pass; address the accepted blocker; defer the contested protocol choice to the user. Read-only until Run 2 is approved.
- Ordered steps (executed by a SEPARATE Run 2, not this run):
  1. Run 2 step 1: get user decision on the contested protocol choice (Round F checkpoint).
  2. Run 2 step 2: implement the accepted blocker fix in an isolated worktree.
  3. Run 2 step 3: rerun the Evidence Tribunal on the new result and update the ledger.
- Open decisions: contested protocol choice (needs user decision).
