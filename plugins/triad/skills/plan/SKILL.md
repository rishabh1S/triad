---
name: plan
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
2. Read `${CLAUDE_SKILL_DIR}/new-task.md` and follow it: set up `.triad/`, then archive
   the previous task.
3. Save the planner's output, unchanged, to `.triad/plan.md`.
4. Show the user a short summary: the goal, the numbered step titles, and the top risks.
   Then stop and ask them to approve, edit `.triad/plan.md` directly, or ask for changes.

Do not implement anything in this command.
