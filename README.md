<p align="center">
  <img src="plugins/triad/.claude-plugin/icon.png" alt="triad icon" width="140">
</p>

<h1 align="center">triad</h1>

<p align="center">
  <strong>Plan it, build it, check it, commit it, with three focused AI agents instead of one.</strong>
</p>

<p align="center">
  <a href="https://github.com/rishabh1S/triad/actions/workflows/ci.yml"><img src="https://github.com/rishabh1S/triad/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/rishabh1S/triad/releases/latest"><img src="https://img.shields.io/github/v/release/rishabh1S/triad" alt="Latest release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/rishabh1S/triad" alt="MIT license"></a>
</p>

triad is a [Claude Code](https://code.claude.com/docs/en/overview) plugin that splits a coding task between a **Planner**, an **Implementer** and a **Reviewer**. Your main session coordinates them, and you approve the decisions that matter.

```
 your task
     │
     ▼
┌──────────┐  you approve  ┌─────────────┐             ┌──────────┐
│ Planner  │ ────────────► │ Implementer │ ──────────► │ Reviewer │ ──► PASS ──► commit?
│ read-only│   the plan    │ writes code │  the diff   │ read-only│     (you confirm)
└──────────┘               └─────────────┘             └──────────┘
                                  ▲   changes requested    │
                                  └────────────────────────┘
```

## Why

When one session plans, writes and checks its own code, it tends to agree with itself. Plan mode and `/code-review` cover a lot, and if they're enough for you they're cheaper. triad adds three things:

- **A reviewer that never saw the work.** It gets the plan and the diff, nothing else. A bundled hook blocks it from reading the Implementer's notes or earlier reviews, so it judges the result, not the reasoning.
- **A review against a written plan.** You approve the plan before any code is written. The Reviewer then checks each acceptance criterion and flags anything out of scope, and every finding points to a file and line.
- **Commits scoped to the task.** Changes you had before the task aren't reviewed or committed, and your staged work stays where it is.

## Install

You need Claude Code, a git repository and `python3`, which the read-only guard uses.

```
/plugin marketplace add rishabh1S/triad
/plugin install triad@triad-agents
```

To update later: `/plugin marketplace update triad-agents`, then `/reload-plugins`.

**Without the plugin system,** you can copy triad into one project, which lets you check it into the repo for your team, or into your user folder:

```bash
git clone https://github.com/rishabh1S/triad.git
./triad/install.sh /path/to/project    # or --user; add --uninstall to remove
```

Copied installs name the commands with a dash (`/triad-run`) instead of a colon (`/triad:run`).

## Use

```
/triad:run add rate limiting to the /api/orders endpoint using the existing Redis client
```

1. **Plan.** The Planner explores the code and shows you the goal, steps and risks.
2. **Approve.** Say go, ask for changes, or edit `.triad/plan.md` yourself. Nothing is built before you agree, and building freezes the plan you approved.
3. **Build.** The Implementer does each step and runs its check. If the plan turns out to be wrong, it stops and tells you instead of improvising.
4. **Review.** The Reviewer replies **PASS** or **CHANGES_REQUESTED**.
5. **Fix.** The Implementer fixes the findings, and the code is reviewed again. After two rounds triad stops and shows you what's left, because the plan may need rethinking.
6. **Commit.** On a PASS, triad offers to commit the task's files.

<details>
<summary>What a plan and a review look like</summary>

```markdown
# Plan: Rate-limit /api/orders

[![HOL Guard](https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fplugin%3Fslug%3Drishabh1s%252Ftriad%26metric%3Dtrust)](https://hol.org/registry/plugins/rishabh1s%2Ftriad)

## Goal
Requests to /api/orders beyond 100 per minute per API key get a 429 response.

## Steps
- [ ] 1. Add a sliding-window limiter on the existing Redis client
  - Files: src/lib/rateLimit.ts
  - Verify: npm test -- rateLimit
- [ ] 2. Apply the limiter to the orders route
  ...

## Acceptance criteria
- The 101st request in a minute returns 429 with a Retry-After header
```

```markdown
## Review

**Verdict:** CHANGES_REQUESTED

### Findings
1. **[Major]** `src/lib/rateLimit.ts:42` — The key expiry is set only on the first
   request, so a Redis restart leaves keys without a TTL. Why: those clients stay
   blocked indefinitely. Fix: set the expiry on every write.
```

</details>

### Running one stage at a time

| Command | What it does |
|---|---|
| `/triad:plan <task>` | Writes a plan for you to approve or edit. |
| `/triad:build [steps]` | Builds the remaining steps, or only the ones you name (`/triad:build 1 2`). |
| `/triad:review [focus]` | Reviews the changes against the plan, optionally with a focus (`security`). |
| `/triad:build fix` | Fixes the Blocker and Major findings from the last review. |
| `/triad:commit [message]` | Commits the task now, with your message or a drafted one. |

You don't have to use every stage. Running just `/triad:review` after your usual workflow gets you most of the value of an independent review.

## Committing

Nothing is ever committed without your yes, and nothing is pushed. Choose what happens after a PASS with `/triad:commit manual|auto|off`. The choice is saved for the project.

- **manual** (default): shows the files and asks for your message.
- **auto**: drafts a message from the plan and the diff for you to accept, edit or cancel.
- **off**: doesn't offer; run `/triad:commit` when you're ready.

Before building, triad notes what you'd already changed. The commit includes only the task's files and leaves your other staged work alone. If the task also touched a file you'd already been editing, triad warns you that the whole file will be committed. Git hooks always run, and nothing is amended.

## Under the hood

- **Files, not memory.** Agents pass work through `.triad/` in your project: `plan.md`, `plan.approved.md` (the frozen copy the reviewer judges against), `build-report.md`, `review.md`, a `base` snapshot taken before building, and `archive/` for earlier tasks. The folder ignores itself in git. The snapshot uses `git stash create`, which doesn't touch your files or your stash list.
- **Read-only, enforced.** A `PreToolUse` hook stops the Planner and Reviewer from editing files or running commands that change state, such as redirects, `rm`, `sed -i`, git writes or package installs. It does nothing in other sessions. It's a guard, not a sandbox: a script that writes files from inside, such as a Python one-liner, gets through.
- **Models.** The Planner and Reviewer use your session's model. The Implementer uses `sonnet` to keep costs down. For hard changes, set `model: inherit` in `implementer.md`.

## Customizing

All three agents follow your project's `CLAUDE.md`, which is the easiest place for rules. To change the agents themselves, for example to tell the Reviewer that every new endpoint needs an integration test, edit the agent files. In a copied install they're `.claude/agents/triad-*.md`. Plugin installs are replaced on update, so fork this repo, edit `plugins/triad/agents/`, and install from your fork.

## Limits

- **It costs more tokens.** Each agent starts fresh. Save it for real features and risky changes, not one-line fixes or "try this and see".
- **A wrong plan can still pass.** The Reviewer judges the code against the plan, so approving the plan is where your attention matters most.
- **The Reviewer is the same kind of model.** Its context is separate, but it has the same blind spots, so a PASS doesn't replace human review of important changes.
- **One task at a time per project.** Finish or commit before switching branches, because the snapshot belongs to the branch you started on.

## Development

```
plugins/triad/
├── agents/      planner, implementer, reviewer
├── skills/      plan, build, review, run, commit → /triad:<name>
└── hooks/       the read-only guard
install.sh       copies triad into a project without the plugin system
tests/           python3 -m unittest discover tests
```

## License

MIT
