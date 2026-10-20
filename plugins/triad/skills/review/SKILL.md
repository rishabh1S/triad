---
description: Independently review the current changes against .triad/plan.md with the read-only triad reviewer agent. Usage /triad:review [extra focus]
argument-hint: '[optional focus, e.g. "security" or "concurrency"]'
disable-model-invocation: true
---

# Triad: review

Extra focus from the user: $ARGUMENTS

1. Check that `.triad/plan.md` exists. If it does not, the reviewer has nothing to judge
   against: tell the user to run `/triad:plan` first, or offer to review the diff for
   general correctness only if they confirm.
2. Delegate to the `triad:reviewer` subagent. Give it only: the plan path
   `.triad/plan.md` and the extra focus above, if any. Do **not** pass it the implementer's
   report or your own opinion of the code; the review must be independent. Wait for its
   result before continuing.
3. Save the review to `.triad/review.md` (overwrite).
4. Show the user the verdict and the findings list, ordered Blocker → Major → Minor.
5. If the verdict is CHANGES_REQUESTED, suggest `/triad:build fix` to have the implementer
   address the Blocker and Major findings. Do not fix anything yourself here.
6. If the verdict is PASS, read `${CLAUDE_SKILL_DIR}/../commit/SKILL.md` and follow its
   "After a PASS" section.
