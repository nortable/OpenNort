#!/usr/bin/env bash
# Install the research-codex-workflow skill into a Codex skills dir, then verify it.
#
# Default is a SYMLINK so `git pull` instantly updates the installed skill (no manual re-sync).
# Use --copy for a frozen snapshot instead. Idempotent: re-running just re-points/refreshes.
#
#   ./scripts/install.sh                 # symlink into ~/.codex/skills (default)
#   ./scripts/install.sh --copy          # copy instead of symlink
#   CODEX_SKILLS_DIR=/path ./scripts/install.sh   # custom skills dir
set -euo pipefail

MODE="symlink"
for arg in "$@"; do
  case "$arg" in
    --copy) MODE="copy" ;;
    --symlink) MODE="symlink" ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="$(cd "$SCRIPT_DIR/.." && pwd)"          # .../skills/research-codex-workflow
DEST_ROOT="${CODEX_SKILLS_DIR:-$HOME/.codex/skills}"
DEST="$DEST_ROOT/research-codex-workflow"

mkdir -p "$DEST_ROOT"

# Back up an existing real directory (never silently clobber the user's copy).
if [ -L "$DEST" ]; then
  rm -f "$DEST"
elif [ -e "$DEST" ]; then
  BAK="$DEST.bak.$(date +%s)"
  echo "note: $DEST exists; backing up to $BAK"
  mv "$DEST" "$BAK"
fi

if [ "$MODE" = "symlink" ]; then
  ln -s "$SKILL_SRC" "$DEST"
  echo "linked: $DEST -> $SKILL_SRC"
else
  cp -r "$SKILL_SRC" "$DEST"
  rm -rf "$DEST/scripts/__pycache__"
  echo "copied: $SKILL_SRC -> $DEST"
fi

echo "verifying..."
python3 "$SKILL_SRC/scripts/selftest.py"
python3 "$SKILL_SRC/scripts/fetch.py" --selftest

echo "installed. Codex discovers the skill at $DEST/SKILL.md"
echo "gate any real run with: python3 $DEST/scripts/validate_artifacts.py --audit-run <run-dir>"
