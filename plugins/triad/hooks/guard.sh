#!/usr/bin/env bash
# PreToolUse hook. Plugin hooks fire for every tool call in every session, so bail out
# cheaply unless the caller is a triad agent.

input=$(cat)
role_pattern='"agent_type"[[:space:]]*:[[:space:]]*"triad[:-](planner|reviewer|implementer)"'
[[ $input =~ $role_pattern ]] || exit 0

if ! command -v python3 >/dev/null 2>&1; then
  echo "triad guard: python3 is required to check the ${BASH_REMATCH[1]}'s tool calls." >&2
  exit 2
fi

printf '%s' "$input" | python3 "$(dirname "${BASH_SOURCE[0]}")/guard.py"
