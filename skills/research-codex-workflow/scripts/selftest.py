#!/usr/bin/env python3
"""One-command self-test for the research-codex-workflow deterministic substrate.

Generates the synthetic fixture, validates it (must pass), then applies a set of mutations and asserts
the validator REJECTS each one. This proves the harness actually catches failures rather than passing
everything (the original validator passed all of these). It only advertises guarantees the validator
implements: schema conformance, cross-artifact references, anonymization, the checkpoint gate, judge
coverage, the subagent-spawn completion gate, and the deep-discovery requirement.

Usage: python3 scripts/selftest.py   (exit 0 = harness healthy)
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

SCRIPTS = Path(__file__).resolve().parent
GENERATOR = SCRIPTS / "run_synthetic_fixture.py"
VALIDATOR = SCRIPTS / "validate_artifacts.py"


def generate(out_root: Path) -> Path:
    subprocess.run(
        [sys.executable, str(GENERATOR), "--out-root", str(out_root)],
        check=True, capture_output=True, text=True,
    )
    return out_root / "synthetic-v2"


def validate(run_root: Path) -> int:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--run-root", str(run_root)],
        capture_output=True, text=True,
    ).returncode


def _patch(path: Path, mutate: Callable[[dict], None]) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def drop_required_key(run_root: Path) -> None:
    _patch(run_root / "round-a-findings" / "F-VALID-BLOCKER-1.yaml", lambda d: d.pop("claim", None))


def dangling_evidence_id(run_root: Path) -> None:
    def mutate(d: dict) -> None:
        d["decisions"][0]["evidence_ids"] = ["E-DOES-NOT-EXIST"]
    _patch(run_root / "round-e-decision-ledger.yaml", mutate)


def anonymization_leak(run_root: Path) -> None:
    def mutate(d: dict) -> None:
        d["critique_claim"] = d["critique_claim"] + " (per Synthetic Scout)"
    _patch(run_root / "round-b-critiques" / "C-UNSUPPORTED-1.yaml", mutate)


def edit_before_approval(run_root: Path) -> None:
    _patch(run_root / "round-f-user-checkpoint.yaml",
           lambda d: d.__setitem__("edit_permission_before_approval", True))


def unjudged_packet(run_root: Path) -> None:
    """Assemble a second, valid evidence packet (traceable to the accepted finding) but give it NO
    judge score. validate_judge_coverage must reject the run — no silent promotion of unjudged
    evidence."""
    src = run_root / "evidence-packets" / "P-F-VALID-BLOCKER-1.yaml"
    data = json.loads(src.read_text(encoding="utf-8"))
    data["packet_id"] = "P-UNJUDGED-1"
    (run_root / "evidence-packets" / "P-UNJUDGED-1.yaml").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def no_spawn_records(run_root: Path) -> None:
    """Delete every agents/<id>.json spawn record. validate_spawn_evidence must reject the run — a
    final answer with no proof any subagent ran is the core fake-run failure mode."""
    for path in (run_root / "agents").glob("*.json"):
        path.unlink()


def shallow_pass_only(run_root: Path) -> None:
    """Set every Round A finding to depth=surface (zero deep findings). The completion gate must reject
    it — a surface-only pass audited the docs, not the research."""
    for path in (run_root / "round-a-findings").glob("*.yaml"):
        _patch(path, lambda d: d.__setitem__("depth", "surface"))


def plan_run_with_round_g_report(run_root: Path) -> None:
    """Add a Round-G final report to a plan run = a FUSED run. validate_run_mode_gate must reject it: a
    plan run (run_mode=plan) must STOP at Round F and never produce Round-G output."""
    report = {
        "run_id": "fused", "mode": "adversarial", "summary_zh": "x", "decision_ledger": [],
        "accepted_evidence": [], "user_checkpoints": [], "protected_files_not_edited": True,
        "next_highest_value_action": "x",
    }
    (run_root / "round-g-final-report.yaml").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def external_evidence_declared_but_missing(run_root: Path) -> None:
    """Charter declares external evidence is needed, but the run produced no source-record and logged
    nothing unavailable. validate_external_evidence must reject it — a Literature Scout was promised and
    never ran, so a SOTA/novelty/leakage claim would rest on local inspection alone."""
    _patch(run_root / "00-charter.yaml",
           lambda d: d.__setitem__("external_evidence_needed", "yes"))


def single_judge_panel(run_root: Path) -> None:
    """Delete the second judge's scores, leaving one judge per packet. validate_judge_coverage must
    reject it — a one-judge "panel" cannot do synthesize-from-winner, so it is not the judge-panel
    pattern the master template requires."""
    for path in (run_root / "round-d-judge-scores").glob("J2-*.yaml"):
        path.unlink()


def ledger_issue_without_judged_packet(run_root: Path) -> None:
    """Append an accepted ledger issue that traces to NO judged packet (a second-discovery finding
    written straight to the ledger). validate_ledger_packet_coverage must reject it."""
    def mutate(d: dict) -> None:
        d["decisions"].append({
            "issue_id": "ISS-ORPHAN-2ND-PASS", "title": "second-pass finding appended to ledger",
            "decision_class": "accepted_non_blocking", "action": "DEFER", "evidence_ids": [],
            "affected_files": [], "recommended_change": "none", "alternatives": [],
            "user_decision_needed": False, "edit_after_approval": False,
        })
    _patch(run_root / "round-e-decision-ledger.yaml", mutate)


NEGATIVE_CONTROLS = [
    ("dropped required key", drop_required_key),
    ("dangling evidence_id", dangling_evidence_id),
    ("anonymization leak (author identity in a critique)", anonymization_leak),
    ("edit_permission_before_approval = True", edit_before_approval),
    ("evidence packet with no judge score", unjudged_packet),
    ("accepted ledger issue with no judged packet", ledger_issue_without_judged_packet),
    ("no subagent spawn records (faked run)", no_spawn_records),
    ("surface-only discovery (zero deep findings)", shallow_pass_only),
    ("single-judge round D (not a panel)", single_judge_panel),
    ("external evidence declared but no literature run", external_evidence_declared_but_missing),
    ("plan run fused with a Round-G report", plan_run_with_round_g_report),
]


def main() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # Positive control: a clean generated run must validate.
        clean = generate(root / "clean")
        if validate(clean) != 0:
            failures.append("POSITIVE control failed: a clean generated run did not validate")

        # Negative controls: each mutation must be REJECTED (exit != 0).
        for label, mutate in NEGATIVE_CONTROLS:
            run_root = generate(root / label.split()[0])
            mutate(run_root)
            if validate(run_root) == 0:
                failures.append(f"NEGATIVE control NOT caught: {label}")
            else:
                print(f"  caught: {label}")

    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        return 1
    print("OK: self-test passed — clean run validates and all negative controls are rejected "
          "(schema + references + anonymization + checkpoint + judge-panel coverage + spawn-gate + "
          "deep-discovery + plan/implement run-mode split enforced)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
