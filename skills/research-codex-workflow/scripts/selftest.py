#!/usr/bin/env python3
"""One-command self-test for the research-codex-workflow deterministic substrate.

Generates the synthetic fixture, validates it (must pass), then applies a set of mutations and asserts
the validator REJECTS each one. This proves the harness actually catches failures rather than passing
everything (the original validator passed all of these). It only advertises guarantees the validator
implements: schema conformance, cross-artifact references, anonymization, and the checkpoint gate.

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


NEGATIVE_CONTROLS = [
    ("dropped required key", drop_required_key),
    ("dangling evidence_id", dangling_evidence_id),
    ("anonymization leak (author identity in a critique)", anonymization_leak),
    ("edit_permission_before_approval = True", edit_before_approval),
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
          "(schema + references + anonymization + checkpoint enforced)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
