---
description: Commit the current triad task, or set how triad commits after a passing review. Usage /triad:commit [manual|auto|off|commit message]
argument-hint: '[manual | auto | off | commit message — empty: commit now]'
disable-model-invocation: true
---

# Triad: commit

Argument from the user: $ARGUMENTS

The commit mode lives in `.triad/commit-mode` (one word: `manual`, `auto` or `off`). The
mode is `auto` or `off` only when the file holds exactly that word; anything else,
including a missing or empty file, means `manual`.

- `manual`: after a PASS, ask the user for the commit message.
- `auto`: after a PASS, draft the message from the changes and wait for the user's yes.
- `off`: do not offer a commit after a PASS.

## Handle the argument

- **`manual`, `auto` or `off`** (exactly one of these words): create `.triad/` if needed,
  with a `.triad/.gitignore` containing `*` if it is missing. Write the word to
  `.triad/commit-mode` (overwrite), tell the user the new mode in one line, and stop.
- **Empty**: run the commit procedure below now. Use auto if the mode is `auto`, manual
  otherwise. The user asked explicitly, so `off` does not block it.
- **Anything else**: run the commit procedure below with that text as the commit message;
  skip the step that asks for or drafts one, but still show the files and wait for a yes.

## Commit procedure

Other triad commands also follow this section after a PASS. Run every git command from
the project root.

1. **Guards.**
   - If the project is not a git repo, say so and stop.
   - If `.triad/committed` exists, this task is already committed: show its SHA and stop.
   - If `.triad/review.md` is missing or its verdict is not PASS, warn the user and only
     continue if they confirm.
2. **Collect this task's files and nothing else.**
   - If `.triad/base` exists, read the commit from its `base: <sha>` line; the remaining
     lines are files that were untracked before the task.
     - Changed or deleted: `git diff --name-only <sha>`
     - New: `git ls-files --others --exclude-standard`, minus the files listed in
       `.triad/base`
     - Already dirty before the task: `git diff --name-only HEAD <sha>`. Any of these
       that also appear in the task's files will be committed whole, including the
       user's earlier edits; list them as a warning.
   - If there is no `.triad/base`, use `git status --porcelain` and warn that changes
     made before the task cannot be separated from it.
   - Never include anything under `.triad/`. If no files remain, say there is nothing to
     commit and stop.
3. **Get the message.** Always show the file list first (marking new, deleted and
   already-dirty files).
   - Manual: ask the user for the commit message. `cancel` aborts.
   - Auto: read `.triad/plan.md` for the goal and the diff of the task's files
     (`git diff <sha> -- <files>`, plus the new files). Check `git log --oneline -10` and
     match the repo's style. Write an imperative subject of at most 72 characters and,
     if useful, a short body saying what changed and why. Show the message and ask the
     user to reply yes, give an edited message, or cancel.
   - Do not commit until the user answers. On cancel, stop and say nothing was committed.
4. **Commit only those files.**
   ```bash
   git add -- <new files>
   git commit -F - -- <all task files> <<'EOF'
   <message>
   EOF
   ```
   Committing with a pathspec leaves anything else the user had staged untouched. Follow
   the session's usual commit conventions for the message. Never use `git add -A`,
   `git add .`, `--no-verify` or `--amend`, and never push. If a hook or the commit
   fails, show the output and stop; do not retry with hooks disabled.
5. **Record it.** Write the new commit's SHA (`git rev-parse HEAD`) to
   `.triad/committed`, then show `git log -1 --stat`. Tell the user nothing was pushed.
