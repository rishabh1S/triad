"""Keep the triad implementer from changing the plan it is judged against.

The implementer may tick steps in .triad/plan.md (`- [ ]` -> `- [x]`) and nothing else
under .triad/. Edits are checked by applying them to the current file and comparing the
result line by line.
"""

import os
import re

from bash_check import find_write
from triad_paths import TRIAD_REF, triad_file

EDIT_PATH_KEYS = {"Edit": "file_path", "MultiEdit": "file_path", "Write": "file_path",
                  "NotebookEdit": "notebook_path"}
UNTICKED = re.compile(r"^(\s*-\s+)\[ \](.*)$")


def find_plan_violation(tool, tool_input, cwd):
    """Return why this tool call would change the plan or other triad files, or None."""
    if tool == "Bash":
        command = tool_input.get("command", "")
        if TRIAD_REF.search(command) and find_write(command):
            return ("Bash may not write under .triad/. Tick finished steps in "
                    ".triad/plan.md with the Edit tool.")
        return None

    path = tool_input.get(EDIT_PATH_KEYS.get(tool, ""))
    if not isinstance(path, str):
        return None
    name = triad_file(path)
    if name is None:
        return None
    if name != "plan.md" or tool == "NotebookEdit":
        return f"It may not change {path}; only ticking steps in .triad/plan.md is allowed."

    current = _read(path if os.path.isabs(path) else os.path.join(cwd or "", path))
    if current is None:
        return None
    updated = _apply(tool, tool_input, current)
    if updated is not None and not _only_ticks(current, updated):
        return ("This edit changes more than checkboxes in .triad/plan.md. Change only "
                "`- [ ]` to `- [x]` for finished steps; report plan problems instead of "
                "editing the plan.")
    return None


def _read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def _apply(tool, tool_input, content):
    if tool == "Write":
        return tool_input.get("content", "")
    edits = tool_input.get("edits") if tool == "MultiEdit" else [tool_input]
    for edit in edits or []:
        old, new = edit.get("old_string", ""), edit.get("new_string", "")
        if not old or old not in content:
            # The tool itself will reject an edit that does not match.
            return None
        count = -1 if edit.get("replace_all") else 1
        content = content.replace(old, new, count)
    return content


def _only_ticks(before, after):
    old_lines, new_lines = before.split("\n"), after.split("\n")
    if len(old_lines) != len(new_lines):
        return False
    for old, new in zip(old_lines, new_lines):
        if old == new:
            continue
        match = UNTICKED.match(old)
        if not match or new != f"{match.group(1)}[x]{match.group(2)}":
            return False
    return True
