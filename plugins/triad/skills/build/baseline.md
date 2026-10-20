# Triad: record the baseline

Shared by `/triad:build` and `/triad:run`. The baseline freezes the approved plan and lets
the review and the commit cover only this task's changes.

## Freeze the approved plan

If `.triad/plan.approved.md` does not exist, copy `.triad/plan.md` to it. Never overwrite
it. The reviewer judges the change against this copy, so later edits to `plan.md` cannot
soften what was approved. Do this even when the project is not a git repo.

## Record the git baseline

Skip this if `.triad/base` already exists (never overwrite it), or if the project is not a
git repo with at least one commit. Otherwise run from the project root:

```bash
base=$(git stash create); base=${base:-$(git rev-parse HEAD)}
{ echo "base: $base"
  git ls-files --others --exclude-standard | while IFS= read -r f; do
    printf '%s\t%s\n' "$(git hash-object -w -- "$f")" "$f"
  done
} > .triad/base
```

`git stash create` and `git hash-object -w` only write objects into git's store; they do
not touch the working tree, the index or the stash list. The blob hashes let the review
and commit spot untracked files the task later changes.
