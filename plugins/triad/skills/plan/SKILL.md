---
description: Plan a task with the read-only triad planner agent and save it to .triad/plan.md for your approval. Usage /triad:plan <task>
argument-hint: <what you want built or changed>
disable-model-invocation: true
---

# Triad: plan

Task from the user: $ARGUMENTS

If the task above is empty, ask the user what they want planned and stop.

1. Delegate to the `triad:planner` subagent. Pass it the task verbatim plus anything
   relevant already established in this conversation (constraints, files the user
   mentioned). Wait for its result before continuing.
2. Create the `.triad/` directory in the project root if it does not exist. If
   `.triad/.gitignore` does not exist, create it containing the single line `*` so git
   ignores the whole directory.
3. If `.triad/plan.md` already exists, move `plan.md`, `build-report.md`, `review.md` and
   `base` (whichever exist) into `.triad/archive/<YYYYMMDD-HHMMSS>/`, so nothing from the
   previous task carries over.
4. Save the planner's output, unchanged, to `.triad/plan.md`.
5. Show the user a short summary: the goal, the numbered step titles, and the top risks.
   Then stop and ask them to approve, edit `.triad/plan.md` directly, or ask for changes.

Do not implement anything in this command.
