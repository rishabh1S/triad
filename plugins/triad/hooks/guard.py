"""Block tool calls that would break the triad planner's or reviewer's read-only role.

Reads a PreToolUse hook payload on stdin. Exits 2 with a reason on stderr to block the
call, or 0 to let the normal permission flow continue.
"""

import json
import os
import re
import sys

# Don't leave __pycache__ in the plugin or .claude folder.
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bash_check import find_write  # noqa: E402

ROLES = {
    "triad:planner": "planner",
    "triad-planner": "planner",
    "triad:reviewer": "reviewer",
    "triad-reviewer": "reviewer",
}
EDIT_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}
# The reviewer may read only these files under .triad/; everything else there holds the
# implementer's reasoning or earlier verdicts.
REVIEWER_TRIAD_FILES = {"plan.md", "base"}
PATH_KEYS = {"Read": ("file_path",), "Grep": ("path", "glob"), "Glob": ("path", "pattern")}
TRIAD_REF = re.compile(r"(?:^|(?<=[\s/'\"=(]))\.triad(?:/[^\s'\"`;|&()<>]*)?")


def block(role, reason):
    print(f"triad guard: the {role} is read-only. {reason}", file=sys.stderr)
    sys.exit(2)


def is_hidden_triad_path(path):
    parts = os.path.normpath(path).split(os.sep)
    if ".triad" not in parts:
        return False
    rest = parts[len(parts) - parts[::-1].index(".triad"):]
    return not (len(rest) == 1 and rest[0] in REVIEWER_TRIAD_FILES)


def independence_reason(target):
    return (
        f"It may not read {target}: only .triad/plan.md and .triad/base are allowed, "
        "because the build report, earlier reviews and archives would break the "
        "review's independence."
    )


def main():
    payload = json.load(sys.stdin)
    role = ROLES.get(payload.get("agent_type", ""))
    if role is None:
        return
    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}

    if tool in EDIT_TOOLS:
        block(role, f"{tool} is not allowed.")

    if tool == "Bash":
        command = tool_input.get("command", "")
        reason = find_write(command)
        if reason:
            block(
                role,
                f"Blocked {reason}. Use Bash only to inspect and to run the project's "
                "existing tests, build or lint.",
            )
        if role == "reviewer":
            for ref in TRIAD_REF.findall(command):
                if is_hidden_triad_path(ref):
                    block(role, independence_reason(ref))

    if role == "reviewer" and tool in PATH_KEYS:
        for key in PATH_KEYS[tool]:
            value = tool_input.get(key)
            if isinstance(value, str) and is_hidden_triad_path(value):
                block(role, independence_reason(value))


if __name__ == "__main__":
    main()
