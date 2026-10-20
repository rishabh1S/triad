#!/usr/bin/env bash
# Copy the triad agents and commands straight into a project's .claude/ folder
# (or your user-level ~/.claude/), without the plugin system.
#
# Usage:
#   ./install.sh [project-dir]     install into <project-dir>/.claude (default: current dir)
#   ./install.sh --user            install into ~/.claude for every project
#   ./install.sh --uninstall [dir|--user]
#
# Local installs drop the plugin namespace, so commands become /triad-plan,
# /triad-build, /triad-review, /triad-run and agents become triad-planner, etc.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$SCRIPT_DIR/plugins/triad"
AGENTS=(planner implementer reviewer)
SKILLS=(plan build review run)

uninstall=false
target=""
for arg in "$@"; do
  case "$arg" in
    --uninstall) uninstall=true ;;
    --user) target="$HOME" ;;
    -h|--help) sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) target="$arg" ;;
  esac
done
target="${target:-$PWD}"
dest="$target/.claude"

if [[ ! -d "$SRC/agents" || ! -d "$SRC/skills" ]]; then
  echo "error: run this script from the triad repository (missing $SRC)" >&2
  exit 1
fi

if $uninstall; then
  for a in "${AGENTS[@]}"; do rm -f "$dest/agents/triad-$a.md"; done
  for s in "${SKILLS[@]}"; do rm -rf "$dest/skills/triad-$s"; done
  echo "Removed triad from $dest"
  exit 0
fi

# Rewrite plugin-scoped names (triad:planner, /triad:plan) to local ones (triad-planner, /triad-plan).
localize() {
  sed -E \
    -e 's/triad:(planner|implementer|reviewer|plan|build|review|run)/triad-\1/g' \
    -e 's/^name: (planner|implementer|reviewer)$/name: triad-\1/' \
    "$1"
}

mkdir -p "$dest/agents" "$dest/skills"

for a in "${AGENTS[@]}"; do
  localize "$SRC/agents/$a.md" > "$dest/agents/triad-$a.md"
done

for s in "${SKILLS[@]}"; do
  mkdir -p "$dest/skills/triad-$s"
  localize "$SRC/skills/$s/SKILL.md" > "$dest/skills/triad-$s/SKILL.md"
done

echo "Installed triad into $dest"
echo "  agents:   triad-planner, triad-implementer, triad-reviewer"
echo "  commands: /triad-plan, /triad-build, /triad-review, /triad-run"
echo "Restart Claude Code if this is the first agent or skill in that folder."
