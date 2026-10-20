# Triad: check the approved plan

Shared by `/triad:review` and `/triad:run`. Run from the project root before every review.
The reviewer judges the change against `.triad/plan.approved.md`, the copy frozen when
building started.

1. If `.triad/plan.approved.md` does not exist (the task predates this file, or nothing was
   built through triad), copy `.triad/plan.md` to it and tell the user the plan was frozen
   now, not at approval time.
2. Compare the two files with checkbox state ignored:
   ```bash
   diff <(sed 's/^\([[:space:]]*-[[:space:]]*\)\[x\]/\1[ ]/' .triad/plan.approved.md) \
        <(sed 's/^\([[:space:]]*-[[:space:]]*\)\[x\]/\1[ ]/' .triad/plan.md)
   ```
   If anything differs, show the user the diff and warn that `plan.md` changed after
   approval. The review still uses `plan.approved.md`. If the user wants the edited plan
   to count, they can confirm and you copy `plan.md` over `plan.approved.md` before the
   review.
