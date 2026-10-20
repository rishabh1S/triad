"""Run with: python3 -m unittest discover tests"""

import json
import os
import subprocess
import unittest

GUARD = os.path.join(os.path.dirname(__file__), "..", "plugins", "triad", "hooks", "guard.sh")


def run_guard(agent_type, tool, tool_input):
    payload = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input}
    if agent_type:
        payload["agent_type"] = agent_type
    result = subprocess.run(
        ["bash", GUARD], input=json.dumps(payload), capture_output=True, text=True
    )
    return result.returncode, result.stderr


def bash(agent_type, command):
    return run_guard(agent_type, "Bash", {"command": command})


class OtherAgents(unittest.TestCase):
    def test_main_session_is_untouched(self):
        self.assertEqual(bash(None, "rm -rf build")[0], 0)

    def test_implementer_is_untouched(self):
        self.assertEqual(bash("triad:implementer", "rm -rf build")[0], 0)
        self.assertEqual(run_guard("triad:implementer", "Write", {"file_path": "a"})[0], 0)

    def test_other_plugins_reviewer_is_untouched(self):
        self.assertEqual(bash("acme:reviewer", "rm x")[0], 0)


class EditTools(unittest.TestCase):
    def test_edit_tools_blocked_for_both_roles(self):
        for role in ("triad:planner", "triad-reviewer"):
            for tool in ("Edit", "Write", "NotebookEdit"):
                code, err = run_guard(role, tool, {"file_path": "src/a.py"})
                self.assertEqual(code, 2, (role, tool))
                self.assertIn("read-only", err)


class BashWrites(unittest.TestCase):
    BLOCKED = [
        "rm -rf build",
        "echo hi > notes.txt",
        "git diff >> out.patch",
        "ls; touch x",
        "cat a | tee b",
        "sed -i '' s/a/b/ f.txt",
        "sed -Ei 's/a/b/' f.txt",
        "perl -pi -e 's/a/b/' f",
        "git commit -m wip",
        "git -C sub checkout main",
        "git stash",
        "git branch -D old",
        "git config user.name x",
        "npm install lodash",
        "python3 -m pip install requests",
        "uv pip install x",
        "yarn",
        "find . -name '*.tmp' -delete",
        "find . -exec rm {} \\;",
        "ls | xargs -n 1 rm",
        "bash -c 'mv a b'",
        "sh -lc \"cp a b\"",
        "eval rm x",
        "echo \"$(rm -rf x)\"",
        "FOO=1 env BAR=2 rm x",
        "timeout 10 mkdir out",
        "curl -sSLo f https://x",
        "sudo ls",
        "ls\nrm x",
        "echo 'unbalanced",
    ]
    ALLOWED = [
        "git status --porcelain",
        "git diff abc123 -- src/",
        "git -C sub log --oneline -5",
        "git --no-pager show HEAD:README.md",
        "git ls-files --others --exclude-standard",
        "git hash-object -- src/a.py",
        "git branch --show-current",
        "git stash list",
        "git config --get user.name",
        "npm test",
        "npm run lint",
        "npx jest src/",
        "python3 -m pytest -q",
        "uv run pytest",
        "cargo test 2>&1 | tail -20",
        "ls -la > /dev/null 2>&1",
        "cat a.txt >&2",
        "grep -rn 'rm -rf' src/",
        "sed -n '1,20p' f.txt",
        "perl -Mstrict -ne 'print'",
        "find . -name '*.py' -newer x",
        "curl -sSL https://example.com",
        "while read f; do wc -l \"$f\"; done < files.txt",
        "diff <(git show HEAD:a) a",
    ]

    def test_blocked(self):
        for role in ("triad:planner", "triad:reviewer"):
            for command in self.BLOCKED:
                with self.subTest(role=role, command=command):
                    code, err = bash(role, command)
                    self.assertEqual(code, 2, err)
                    self.assertIn("triad guard", err)

    def test_allowed(self):
        for role in ("triad:planner", "triad:reviewer"):
            for command in self.ALLOWED:
                with self.subTest(role=role, command=command):
                    code, err = bash(role, command)
                    self.assertEqual(code, 0, err)


class ReviewerIndependence(unittest.TestCase):
    def test_reviewer_may_read_plan_and_base(self):
        self.assertEqual(run_guard("triad:reviewer", "Read", {"file_path": "/p/.triad/plan.md"})[0], 0)
        self.assertEqual(bash("triad:reviewer", "head -1 .triad/base")[0], 0)
        self.assertEqual(bash("triad:reviewer", "tail -n +2 \"$PWD/.triad/base\"")[0], 0)

    def test_reviewer_may_not_read_other_triad_files(self):
        cases = [
            ("Read", {"file_path": "/p/.triad/build-report.md"}),
            ("Read", {"file_path": "/p/.triad/review.md"}),
            ("Read", {"file_path": "/p/.triad/archive/20261020-101010/plan.md"}),
            ("Grep", {"pattern": "TODO", "path": ".triad"}),
            ("Glob", {"pattern": ".triad/**/*.md"}),
            ("Bash", {"command": "cat .triad/build-report.md"}),
            ("Bash", {"command": "ls .triad/"}),
        ]
        for tool, tool_input in cases:
            with self.subTest(tool=tool, tool_input=tool_input):
                code, err = run_guard("triad-reviewer", tool, tool_input)
                self.assertEqual(code, 2, err)
                self.assertIn("independence", err)

    def test_grep_for_the_string_triad_is_fine(self):
        self.assertEqual(run_guard("triad:reviewer", "Grep", {"pattern": ".triad", "path": "src"})[0], 0)

    def test_planner_may_read_triad(self):
        self.assertEqual(run_guard("triad:planner", "Read", {"file_path": ".triad/review.md"})[0], 0)


if __name__ == "__main__":
    unittest.main()
