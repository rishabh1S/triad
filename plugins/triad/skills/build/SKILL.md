---
description: Implement the approved plan in .triad/plan.md with the triad implementer agent. Usage /triad:build [step numbers, default all remaining]
argument-hint: '[step numbers, e.g. "1 2" — default: all remaining]'
disable-model-invocation: true
---

# Triad: build

Steps requested: $ARGUMENTS (empty means all unchecked steps; `fix` means address the
latest review)

1. Read `.triad/plan.md`. If it does not exist, tell the user to run `/triad:plan <task>`
   first and stop.
2. Work out what to do:
   - `fix`: read `.triad/review.md` and collect its Blocker and Major findings (and Minor
     ones only if the user asked). If there is no review or no such findings, say so and stop.
   - step numbers: run those steps.
   - empty: run every step still marked `- [ ]`. If none remain, say so and suggest
     `/triad:review`.
3. Read `${CLAUDE_SKILL_DIR}/baseline.md` and follow it to record the baseline.
4. Delegate to the `triad:implementer` subagent with: the plan path `.triad/plan.md`, the
   exact step numbers or the exact findings to fix (copied verbatim), and any user
   instructions from this conversation since the plan was approved. Wait for its report
   before continuing.
5. Save the report to `.triad/build-report.md` (overwrite).
6. Relay to the user, briefly: which steps are done, files changed, verification results.
7. If any step is BLOCKED, show the blocker and stop. Do not try to fix it yourself and do
   not re-plan without the user's go-ahead.
8. If everything passed, suggest `/triad:review` as the next step.
