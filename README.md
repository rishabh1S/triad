# triad

A Planner → Implementer → Reviewer workflow for [Claude Code](https://code.claude.com/docs/en/overview), packaged as a plugin.

Instead of one long session that plans, codes and then grades its own work, triad gives each job to a separate subagent with its own context window, its own tools and its own instructions. Your main session becomes the orchestrator.

```
           /triad:plan                 /triad:build                 /triad:review
 task ──► ┌──────────┐   you approve  ┌─────────────┐              ┌──────────┐
          │ Planner  │ ─────────────► │ Implementer │ ───────────► │ Reviewer │ ──► PASS
          │ read-only│  .triad/plan.md│ edits + runs│   git diff   │ read-only│
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
| `/triad:run <task>` | The whole loop: plan → your approval → build → review → up to 2 fix rounds. |

Example:

```
/triad:run add rate limiting to the /api/orders endpoint using the existing Redis client
```

Everything the agents produce lands in `.triad/` in your project:

```
.triad/
├── plan.md            # the plan, with steps ticked off as they pass
├── build-report.md    # what the implementer did and what it verified
├── review.md          # the latest review
└── archive/           # previous plans
```

Add `.triad/` to `.gitignore` if you don't want these committed. Nothing is ever committed or pushed for you.

## Why it is built this way

- **The reviewer gets no context from the author.** It reads the plan and the diff, not the implementer's report. A reviewer that knows why each line was written tends to agree with it.
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
└── skills/                         # plan/, build/, review/, run/  → /triad:<name>
install.sh                          # copy into a project's .claude/ without the plugin system
```

## License

MIT
