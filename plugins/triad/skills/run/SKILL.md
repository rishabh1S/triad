---
name: run
description: Run the full triad loop — plan, your approval, implement, independent review, fix — for one task. Usage /triad:run <task>
argument-hint: <what you want built or changed>
disable-model-invocation: true
---

# Triad: run (full loop)

Task from the user: $ARGUMENTS

If the task above is empty, ask the user what they want built and stop.

You are the orchestrator. You coordinate three subagents and keep the user informed. You
do not write code, plans or reviews yourself; each phase belongs to its agent. Always wait
for a subagent's result before starting the next phase.

## Phase 1 — Plan
1. Delegate the task to `triad:planner`, with any relevant context from this conversation.
2. Read `${CLAUDE_SKILL_DIR}/../plan/new-task.md` and follow it: set up `.triad/`, then
   archive the previous task. Save the new plan to `.triad/plan.md`.
3. Show the user the goal, step titles and top risks.
4. **Stop and wait for approval.** Continue only on an explicit go-ahead. If the user asks
   for changes, send the plan and their feedback back to `triad:planner`, save the
   revision, and ask again. If they edited `.triad/plan.md` themselves, re-read it. Phase 2
   freezes the plan, so changes must happen here.

## Phase 2 — Implement
5. Read `${CLAUDE_SKILL_DIR}/../build/baseline.md` and follow it to record the baseline.
   Then delegate to `triad:implementer`: plan path `.triad/plan.md`, all unchecked steps.
6. Save its report to `.triad/build-report.md`. If any step is BLOCKED, show the blocker
   and stop for the user's decision.

## Phase 3 — Review
7. Read `${CLAUDE_SKILL_DIR}/../review/approved-plan.md` and follow it. Then delegate to
   `triad:reviewer` with only the plan path `.triad/plan.approved.md`. Never pass it the
   implementer's report or your own view of the code.
8. Save the result to `.triad/review.md`.

## Phase 4 — Fix loop (at most 2 rounds)
9. If the verdict is PASS, go to Finish.
10. If CHANGES_REQUESTED, send the Blocker and Major findings verbatim to
    `triad:implementer`, then follow `approved-plan.md` again and run a fresh review with
    `triad:reviewer` (plan path `.triad/plan.approved.md` only).
11. After 2 fix rounds without a PASS, stop and show the user the remaining findings.
    Do not keep looping; the plan itself may be wrong.

## Finish
12. Give the user a short summary: what was built, files changed, the final verdict, any
    remaining Minor findings, and the checks that ran.
13. If the final verdict is PASS, read `${CLAUDE_SKILL_DIR}/../commit/SKILL.md` and
    follow its "After a PASS" section. If the loop ended without a PASS, remind the user
    nothing has been committed.
