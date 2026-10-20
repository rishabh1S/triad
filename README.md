# triad

**Plan it, build it, check it, commit it, with three focused AI agents instead of one.**

triad is a [Claude Code](https://code.claude.com/docs/en/overview) plugin. It splits every coding task between three agents: a **Planner**, an **Implementer** and a **Reviewer**. Your main Claude session coordinates them, and you approve the key decisions.

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

## Why use it

When one AI session plans, writes and then checks its own code, it tends to agree with itself. triad separates those jobs:

- **A plan you can check first.** The Planner explores your code and writes a step-by-step plan, but it can't edit anything. You read the plan and approve it before any code is written, which is the cheapest time to catch a wrong approach.
- **Code that follows the plan.** The Implementer carries out the approved steps one by one and runs each step's check. If the plan turns out to be wrong, it stops and tells you instead of improvising.
- **An honest second opinion.** The Reviewer sees only the plan and the code changes. It never sees the Implementer's reasoning, so it judges the result, not the excuses. It replies **PASS** or **CHANGES_REQUESTED**, with each finding pointing to a file and line.
- **A clean commit at the end.** When the review passes, triad offers to commit just that task's files, using either your commit message or one it drafts for you.

Each agent runs in its own context window with only the tools it needs, so your main session stays uncluttered.

### Why not plan mode and `/code-review`?

Claude Code already has plan mode and built-in review commands, and for many tasks they're enough. triad adds three things on top:

- **A reviewer that never saw the work being done.** When the session that wrote the code also reviews it, the review is shaped by the reasoning behind the code. triad's Reviewer starts fresh and is explicitly barred from reading the build report or earlier reviews.
- **A review against a written plan.** The Reviewer checks each acceptance criterion from the approved plan and flags anything that was added out of scope, not just generic code quality.
- **Commits scoped to the task.** Work you had in progress before the task isn't reviewed or committed.

If you don't need those, plan mode plus a review command is cheaper.

## Setup

You need [Claude Code](https://code.claude.com/docs/en/overview) installed. Your project should be a git repository for change tracking, scoped reviews and commits to work.

### Option 1: Install as a plugin (recommended)

Inside Claude Code, run:

```
/plugin marketplace add rishabh1S/triad
/plugin install triad@triad-agents
```

Or run the same thing from your terminal:

```bash
claude plugin marketplace add rishabh1S/triad
claude plugin install triad@triad-agents
```

That's it. The commands are now available in every project as `/triad:plan`, `/triad:run` and so on.

To get updates later:

```
/plugin marketplace update triad-agents
/reload-plugins
```

### Option 2: Copy it into one project

Use this to check the agents into a repository so everyone on the team gets them without installing a plugin:

```bash
git clone https://github.com/rishabh1S/triad.git
./triad/install.sh /path/to/your/project     # into one project's .claude/ folder
./triad/install.sh --user                    # or for your user account, in every project
```

> **Command names differ between install methods.** Plugin installs use a colon (`/triad:run`). Copied installs use a dash: `/triad-plan`, `/triad-build`, `/triad-review`, `/triad-run` and `/triad-commit`. The rest of this README uses the plugin names.

To remove it: `./triad/install.sh --uninstall /path/to/your/project`

## How to use it

### The quick way: one command

```
/triad:run add rate limiting to the /api/orders endpoint using the existing Redis client
```

This is what happens:

1. **Plan.** The Planner explores your code and writes a plan. You see the goal, the steps and the main risks.
2. **You approve.** Reply to go ahead, ask for changes, or edit `.triad/plan.md` yourself. Nothing is built until you say so.
3. **Build.** The Implementer carries out the steps and checks each one.
4. **Review.** The Reviewer checks the changes against the plan.
5. **Fix.** If the Reviewer requests changes, the Implementer fixes them and the code is reviewed again. This happens at most twice; after that triad stops and shows you the remaining findings, because the plan itself may need rethinking.
6. **Commit.** On a PASS, triad stops and offers to commit (see [Committing](#committing)).

**How strictly does the Implementer follow the plan?** It may touch the files a step names, plus the tests and imports those changes need. Small adjustments are fine and are listed under "Deviations" in its report. It stops only when a step is impossible, unsafe or clearly wrong given the code. It doesn't pause for every small difference.

### What the output looks like

An abbreviated plan for the task above:

```markdown
# Plan: Rate-limit /api/orders

## Goal
Requests to /api/orders beyond 100 per minute per API key get a 429 response.

## Steps
- [ ] 1. Add a sliding-window limiter on the existing Redis client
  - Files: src/lib/rateLimit.ts
  - Change: ...
  - Verify: npm test -- rateLimit
- [ ] 2. Apply the limiter to the orders route
  ...

## Acceptance criteria
- The 101st request in a minute returns 429 with a Retry-After header
- Other endpoints are unaffected
```

And an abbreviated review that sends the work back:

```markdown
## Review

**Verdict:** CHANGES_REQUESTED

### Findings
1. **[Major]** `src/lib/rateLimit.ts:42` — The key expiry is set only on the first
   request, so a Redis restart leaves keys without a TTL. Why: those clients stay
   blocked indefinitely. Fix: set the expiry on every write.

### Checks run
- `npm test` → 48 passed
```

### Step by step

For more control, run each stage yourself:

| Command | What it does |
|---|---|
| `/triad:plan <task>` | Writes a plan for you to approve or edit. |
| `/triad:build` | Builds every step not yet done. Pass step numbers to build only those, e.g. `/triad:build 1 2`. |
| `/triad:review` | Reviews the changes against the plan. Add a focus if you like, e.g. `/triad:review security`. |
| `/triad:build fix` | Fixes the serious findings (Blocker and Major) from the last review. |
| `/triad:commit` | Commits the current task now. Add a message to use it directly: `/triad:commit Add order rate limiting`. |
| `/triad:commit manual\|auto\|off` | Chooses what happens after a review passes. |

A typical manual flow: `/triad:plan …` → read and approve → `/triad:build` → `/triad:review` → `/triad:build fix` if needed → `/triad:review` again → commit.

Tip: you don't have to use every stage. Running only `/triad:review` after your normal workflow gives you most of the benefit of an independent review.

## Committing

When a review passes, triad pauses and offers to commit the task. Nothing is committed until you say yes.

Choose how it works with one command. The setting is saved per project and kept between tasks.

| Mode | Command | After a PASS |
|---|---|---|
| **Manual** (default) | `/triad:commit manual` | Shows the changed files and asks you for the commit message. |
| **Auto** | `/triad:commit auto` | Drafts a message from the changes and the plan, then waits for you to accept it, edit it or cancel. "Auto" refers to drafting the message: it never commits without your confirmation. |
| **Off** | `/triad:commit off` | Doesn't offer. Run `/triad:commit` yourself whenever you're ready. |

You don't need to set anything up: a fresh install uses **manual**.

triad is careful about what goes into the commit:

- **Only this task's files.** Before building, triad notes which changes you already had, and leaves those out of the commit.
- **Your staged work stays put.** Anything else you had staged stays staged and is not included.
- **A warning when files overlap.** If a file had your own uncommitted edits before the task and triad also changed it, you're told that the whole file will be committed.
- **No shortcuts.** Git hooks always run, nothing is amended, and nothing is ever pushed.

## Where things are saved

Everything the agents produce goes into a `.triad/` folder in your project:

```
.triad/
├── plan.md            # the plan; steps are ticked off as they're done
├── build-report.md    # what the Implementer did and checked
├── review.md          # the latest review
├── base               # a snapshot reference taken before building
├── committed          # the commit ID, once the task is committed
├── commit-mode        # your commit setting (manual, auto or off)
└── archive/           # earlier tasks, one folder each
```

- **Hidden from git.** The folder has its own `.gitignore`, so it never shows up in `git status` or in commits. Delete `.triad/.gitignore` if you want to keep these files in your repository.
- **Your earlier changes are left alone.** The snapshot in `base` is taken with `git stash create`, which doesn't touch your files or your stash list. The Reviewer only looks at changes made after it, so work you already had in progress isn't reviewed or committed.
- **Old tasks are archived.** Starting a new plan moves the previous task's files into `archive/`.

## Customizing

- **Project rules (easiest).** All three agents read your project's `CLAUDE.md`, so rules you put there apply to them automatically, whichever way you installed triad.
- **Models.** The Implementer uses `sonnet` to keep costs down. The Planner and Reviewer use the same model as your session. If your session runs a stronger model, the code is written by a less capable model than the one that planned and reviews it. That trade-off is deliberate, but for difficult changes you may want to set the Implementer to `inherit`. Accepted values are `sonnet`, `opus`, `haiku`, `fable`, `inherit` or a full model ID.
- **Your conventions.** Add your team's rules to the agent prompts. For example, add "Every new endpoint needs an integration test" to `reviewer.md`.

Where to edit the agent files depends on how you installed:

- **Copied install:** edit `.claude/agents/triad-*.md` in your project, or in `~/.claude/agents/` for a `--user` install.
- **Plugin install:** the installed files are managed by Claude Code and are replaced when you update the plugin. To customize, fork this repository, edit `plugins/triad/agents/*.md`, and install from your fork. Then run `/reload-plugins`.

## Good to know

- **It costs more tokens than a single session.** Each agent starts fresh and re-reads the files it needs, so save `/triad:run` for real features and risky changes, not one-line fixes.
- **The plan is the handoff.** Agents pass work to each other through files, so anything the Planner didn't write down is lost. A clear task description gives you a better plan.
- **A wrong plan can still pass review.** The Reviewer checks correctness, safety and tests, but it judges the code against the plan's goal and acceptance criteria. If the plan aims at the wrong thing, the review won't catch that, so the plan approval step is where your attention matters most.
- **Independent, but the same kind of model.** Keeping the Reviewer's context separate stops it from approving its own reasoning. It doesn't give you a different set of blind spots, so a PASS doesn't replace human review of important changes.
- **One task at a time.** Each project has a single active task in `.triad/`, and starting a new plan archives the current one. Finish or commit a task before switching branches, because the snapshot in `base` refers to the branch you started on.
- **Not for small or exploratory work.** For quick fixes or "try this and see", the hand-offs cost more than they save.
- **It never starts on its own.** triad only runs when you type one of its commands.

## Project layout

```
.claude-plugin/marketplace.json     # makes this repo installable as a marketplace
plugins/triad/
├── .claude-plugin/plugin.json      # plugin manifest
├── agents/                         # planner.md, implementer.md, reviewer.md
└── skills/                         # plan, build, review, run, commit → /triad:<name>
install.sh                          # copies triad into a project without the plugin system
```

## License

MIT
