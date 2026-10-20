# Triad: record the baseline

Shared by `/triad:build` and `/triad:run`. The baseline lets the review and the commit
cover only this task's changes.

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
