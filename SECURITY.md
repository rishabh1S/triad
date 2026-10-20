# Security Policy

## Supported versions

Only the latest release of triad gets security fixes. Update with `/plugin marketplace update triad-agents`, then `/reload-plugins`.

## Reporting a vulnerability

Please don't open a public issue. Report it privately through GitHub's [private vulnerability reporting](https://github.com/rishabh1S/triad/security/advisories/new) instead.

Include what you found, the steps to reproduce it and the triad version. You'll get a reply within a week.

## Scope

triad runs a `PreToolUse` hook (`plugins/triad/hooks/`) and ships `install.sh`. Reports about either are in scope, for example:

- the hook letting the Planner or Reviewer change files or state in a way it's meant to block
- the hook letting the Reviewer read the Implementer's notes under `.triad/`
- the hook letting the Implementer change the plan beyond ticking steps, or write anything else under `.triad/`
- `install.sh` writing outside the target `.claude/` folder

The read-only guard is a heuristic, not a sandbox, and the README says so. A script that writes files from inside, such as a Python one-liner, is a known limit, not a vulnerability.
