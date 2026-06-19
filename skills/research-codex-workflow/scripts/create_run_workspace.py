#!/usr/bin/env python3
"""Create a local transient Round 0-G workspace.

The directory manifest is the single canonical list in `scripts/schemas.py` (`ROUND_DIRS`), shared
with `run_synthetic_fixture.py` and `validate_artifacts.py` so the three never drift (R22).

Writer isolation (R20): a parallel write worker gets either a git worktree (when the run targets a real
repo) or, at a non-git location like `$HOME`, a disjoint per-writer directory under
`runs/<run_id>/writers/<worker_id>/` with an atomic plain-text `.lock` claim file. Read-only roles get
no writer directory. No SQLite/heartbeat lock machinery (that is product-build-gated).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schemas import ROUND_DIRS  # noqa: E402


def allocate_writer_dirs(run_root: Path, writer_ids: list[str], dry_run: bool) -> list[str]:
    """Create one disjoint, atomically-locked directory per writer. Raises on a lock collision so two
    workers can never claim the same workspace."""
    created: list[str] = []
    writers_root = run_root / "writers"
    for wid in writer_ids:
        wdir = writers_root / wid
        created.append(str(wdir))
        if dry_run:
            continue
        wdir.mkdir(parents=True, exist_ok=True)
        lock = wdir / ".lock"
        try:
            with open(lock, "x", encoding="utf-8") as fh:  # atomic create; fails if it exists
                fh.write(f"owner={wid}\n")
        except FileExistsError as exc:
            raise SystemExit(f"writer workspace already locked: {lock}") from exc
    return created


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_id")
    parser.add_argument("--root", type=Path, default=Path(".research-workflow") / "runs")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--writers", type=int, default=0, help="number of auto-named writer workspaces")
    parser.add_argument("--writer-ids", nargs="*", default=None, help="explicit writer ids")
    args = parser.parse_args()

    run_root = args.root / args.run_id
    paths = [run_root] + [run_root / name for name in ROUND_DIRS]
    if not args.dry_run:
        for path in paths:
            path.mkdir(parents=True, exist_ok=True)

    writer_ids = list(args.writer_ids) if args.writer_ids else [f"writer-{i+1}" for i in range(args.writers)]
    writer_dirs = allocate_writer_dirs(run_root, writer_ids, args.dry_run) if writer_ids else []

    print(json.dumps({
        "run_id": args.run_id,
        "run_root": str(run_root),
        "created": [str(p) for p in paths],
        "writer_dirs": writer_dirs,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
