# triad

A Planner → Implementer → Reviewer workflow for [Claude Code](https://code.claude.com/docs/en/overview), packaged as a plugin.

Instead of one long session that plans, codes and then grades its own work, triad gives each job to a separate subagent with its own context window, its own tools and its own instructions. Your main session becomes the orchestrator.

```
           /triad:plan                 /triad:build                 /triad:review
 task ──► ┌──────────┐   you approve  ┌─────────────┐              ┌──────────┐
          │ Planner  │ ─────────────► │ Implementer │ ───────────► │ Reviewer │ ──► PASS ──► commit?
          │ read-only│  .triad/plan.md│ edits + runs│   git diff   │ read-only│     (you confirm)
          └──────────┘                └─────────────┘              └──────────┘
                                             ▲    CHANGES_REQUESTED     │
                                             └──── /triad:build fix ◄───┘
```

| Agent | Tools | Job |
|---|---|---|
| `planner` | Read, Grep, Glob, Bash (inspect only), web | Explores the code, writes a step-by-step plan with verification per step. Cannot edit files. |
| `implementer` | Read, Edit, Write, Bash | Executes approved steps exactly, runs each step's check, ticks it off. Stops instead of improvising when the plan is wrong. |
| `reviewer` | Read, Grep, Glob, Bash (inspect + tests) | Sees only the plan and the diff, never the implementer's reasoning. Returns PASS or CHANGES_REQUESTED with `file:line` findings. |

## Install

### As a plugin (recommended)

Push this repo to GitHub, then anyone can run these inside Claude Code:

```
/plugin marketplace add rishabh1S/triad
/plugin install triad@triad-agents
```

Or from a shell:

```bash
claude plugin marketplace add rishabh1S/triad
claude plugin install triad@triad-agents
```

To try it locally before pushing:

```bash
claude plugin marketplace add ./triad
claude plugin install triad@triad-agents
```

### Copied into one project (no plugin system)

Useful when you want the agents checked into a repo so the whole team gets them:

```bash
git clone https://github.com/rishabh1S/triad.git
./triad/install.sh /path/to/your/project     # or: ./triad/install.sh --user
```

Local installs drop the plugin namespace, so commands become `/triad-plan`, `/triad-build`, `/triad-review`, `/triad-run`. Remove with `./triad/install.sh --uninstall /path/to/your/project`.

## Use

| Command | What it does |
|---|---|
| `/triad:plan <task>` | Planner writes `.triad/plan.md`, you get a summary and approve or edit it. |
| `/triad:build [steps]` | Implementer runs all unchecked steps, or only the numbers you pass. |
| `/triad:review [focus]` | Reviewer checks the diff against the plan. Optional focus, e.g. `security`. |
| `/triad:build fix` | Implementer fixes the Blocker and Major findings from the last review. |
| `/triad:run <task>` | The whole loop: plan → your approval → build → review → up to 2 fix rounds → commit offer. |
| `/triad:commit [message]` | Commit the current task now, optionally with your own message. |
| `/triad:commit manual\|auto\|off` | Choose what happens after a PASS (see below). |

Example:

```
/triad:run add rate limiting to the /api/orders endpoint using the existing Redis client
```

Everything the agents produce lands in `.triad/` in your project:

```
.triad/
├── .gitignore         # contains `*`, so git ignores the whole folder
├── plan.md            # the plan, with steps ticked off as they pass
├── base               # git baseline recorded before the first build
├── build-report.md    # what the implementer did and what it verified
├── review.md          # the latest review
├── committed          # SHA of the task's commit, once made
├── commit-mode        # manual, auto or off (kept across tasks)
└── archive/           # one folder per previous task
```

`.triad/` ignores itself, so it never shows up in `git status` or in commits. Delete `.triad/.gitignore` if you want to commit these files.

### Committing

When a review passes, triad stops and offers to commit the task. Pick how with `/triad:commit <mode>`:

| Mode | After a PASS |
|---|---|
| `manual` (default) | Shows the files and asks you for the commit message. |
| `auto` | Drafts the message from the diff and the plan, then waits for your yes, an edit, or cancel. |
| `off` | Doesn't offer; run `/triad:commit` yourself whenever you like. |

Only the task's own files are committed: triad uses the baseline to leave out changes you had before the task, and commits by path so anything else you had staged stays staged. It warns you when a task file also had your earlier uncommitted edits. Nothing is committed without your yes, hooks are never skipped, and nothing is ever pushed.

Before the first build, triad records a baseline using `git stash create`, which does not change your working tree or stash list. The reviewer only judges changes made since then, so uncommitted work you already had is left out of the review. Starting a new plan moves all of the previous task's files into `archive/`.

## Why it is built this way

- **The reviewer gets no context from the author.** It reads the plan and the diff, not the implementer's report or earlier reviews. A reviewer that knows why each line was written tends to agree with it.
- **Planner and reviewer can't edit files.** Tool restrictions keep the planner from sliding into coding and the reviewer from quietly "fixing" what it should report.
- **You approve the plan.** The cheapest place to catch a wrong design is before any code exists.
- **The fix loop is capped at 2 rounds.** If review keeps failing, the plan is usually the problem, and a human should look.
- **Commands only run when you call them** (`disable-model-invocation: true`), so the workflow never starts on its own.

## Customize

- **Models**: the implementer runs on `sonnet` to save cost; planner and reviewer inherit your session's model. Change the `model:` line in `plugins/triad/agents/*.md` (`sonnet`, `opus`, `haiku`, `fable`, `inherit`, or a full model ID).
- **Your stack**: add your conventions to the agent prompts, e.g. "Spring Boot services use constructor injection; every new endpoint needs a MockMvc test" in `reviewer.md`.
- **Project rules**: agents load your project's `CLAUDE.md`, so repo-wide rules there apply to all three.

After editing a plugin installed from a local folder, run `/reload-plugins` in your session.

## Costs and limits

- Each subagent starts cold and re-reads files, so one `/triad:run` costs several times more tokens than doing the change directly. Use it for real features and risky changes, not one-line fixes.
- Handoffs go through files and summaries. Anything the planner knew but didn't write down is lost, so a good plan matters.
- Start small: running only `/triad:review` after your normal workflow gets most of the value of independent review.

## Layout

```
.claude-plugin/marketplace.json     # marketplace catalog (lets people install from this repo)
plugins/triad/
├── .claude-plugin/plugin.json      # plugin manifest
├── agents/                         # planner.md, implementer.md, reviewer.md
└── skills/                         # plan/, build/, review/, run/, commit/  → /triad:<name>
install.sh                          # copy into a project's .claude/ without the plugin system
```

## License

MIT
