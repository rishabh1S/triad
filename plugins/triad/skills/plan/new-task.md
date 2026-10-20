# Triad: start a new task

Shared by `/triad:plan` and `/triad:run`. Run from the project root.

## Set up `.triad/`

Create the `.triad/` directory if it does not exist. If `.triad/.gitignore` does not exist,
create it containing the single line `*` so git ignores the whole directory.

## Archive the previous task

If `.triad/plan.md` already exists, move `plan.md`, `build-report.md`, `review.md`, `base`
and `committed` (whichever exist) into `.triad/archive/<YYYYMMDD-HHMMSS>/`, so nothing from
the previous task carries over. Leave `commit-mode` in place; it is a project setting.
