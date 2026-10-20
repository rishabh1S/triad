"""Spot shell commands that change state.

This is a heuristic, not a sandbox: it catches the ways an agent would normally write
(redirection, file utilities, git writes, package installs), but not, say, a Python
one-liner that opens a file for writing.
"""

import os
import re
import shlex

WRITE_COMMANDS = {
    "rm", "rmdir", "mv", "cp", "mkdir", "touch", "chmod", "chown", "chgrp", "ln",
    "truncate", "dd", "tee", "install", "unlink", "shred", "patch", "rsync", "scp",
    "sudo", "doas", "su", "vi", "vim", "nvim", "nano", "emacs", "ed", "ex", "wget",
    "mkfifo", "mknod", "kill", "pkill", "killall", "crontab",
}
WRAPPERS = {"env", "command", "builtin", "exec", "nohup", "nice", "time", "timeout"}
KEYWORDS = {"do", "then", "else", "elif", "if", "while", "until", "!", "{", "}"}
XARGS_FLAGS_WITH_VALUE = {"-n", "-I", "-L", "-P", "-d", "-s", "-E", "-a"}
WRAPPER_FLAGS_WITH_VALUE = {
    "env": {"-u", "--unset", "-C", "--chdir"},
    "exec": {"-a"},
    "nice": {"-n", "--adjustment"},
    "timeout": {"-s", "--signal", "-k", "--kill-after"},
}
ENV_SPLIT_FLAGS = {"-S", "--split-string"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
SAFE_REDIRECT_TARGETS = {"/dev/null", "/dev/stdout", "/dev/stderr"}
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

PACKAGE_WRITES = {
    "npm": {"install", "i", "ci", "add", "uninstall", "remove", "rm", "update", "up",
            "upgrade", "link", "unlink", "publish", "prune", "dedupe"},
    "pnpm": {"install", "i", "add", "remove", "rm", "update", "up", "link", "unlink",
             "publish", "prune"},
    "yarn": {"install", "add", "remove", "upgrade", "up", "link", "unlink", "publish"},
    "bun": {"install", "i", "add", "remove", "rm", "update", "link", "publish"},
    "pip": {"install", "uninstall", "download"},
    "pip3": {"install", "uninstall", "download"},
    "pipx": {"install", "uninstall", "upgrade"},
    "uv": {"add", "remove", "sync", "lock"},
    "poetry": {"add", "remove", "install", "update", "lock"},
    "cargo": {"add", "install", "remove", "uninstall", "update", "publish"},
    "go": {"get", "install"},
    "gem": {"install", "uninstall", "update"},
    "bundle": {"install", "add", "update", "remove"},
    "composer": {"require", "install", "remove", "update"},
    "brew": {"install", "uninstall", "upgrade", "reinstall", "remove", "tap", "link"},
    "apt": {"install", "remove", "purge", "upgrade", "update"},
    "apt-get": {"install", "remove", "purge", "upgrade", "update"},
    "dnf": {"install", "remove", "upgrade", "update"},
    "yum": {"install", "remove", "upgrade", "update"},
    "apk": {"add", "del", "upgrade", "update"},
    "conda": {"install", "remove", "create", "update"},
}

GIT_READ = {
    "status", "diff", "log", "show", "blame", "annotate", "ls-files", "ls-tree",
    "ls-remote", "cat-file", "rev-parse", "grep", "shortlog", "describe", "merge-base",
    "name-rev", "rev-list", "for-each-ref", "show-ref", "count-objects", "version", "help",
    "whatchanged", "diff-tree", "diff-files", "diff-index", "range-diff", "var",
    "check-ignore", "check-attr", "cherry", "show-branch", "verify-commit", "verify-tag",
}
GIT_GLOBAL_FLAGS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}
GIT_BRANCH_READ_FLAGS = {
    "--show-current", "-a", "--all", "-r", "--remotes", "-v", "-vv", "--verbose",
    "-l", "--list", "--contains", "--no-contains", "--merged", "--no-merged",
}


def find_write(command):
    """Return a short description of the first state-changing part of `command`, or None."""
    try:
        tokens = _tokenize(command)
    except ValueError:
        return "a command that could not be parsed (unbalanced quotes)"
    reason = _check_redirects(tokens)
    if reason:
        return reason
    # Command substitutions inside double quotes stay inside one token, so check them
    # separately.
    for inner in re.findall(r"\$\(([^()]*)\)", command):
        reason = find_write(inner)
        if reason:
            return reason
    for segment in _segments(tokens):
        reason = _check_segment(segment)
        if reason:
            return reason
    return None


def _tokenize(command):
    command = command.replace("\n", " ; ").replace("`", " ; ")
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.wordchars += "$@%+,:{}[]^!~="
    return list(lexer)


def _is_operator(token):
    return bool(token) and all(c in "();<>|&" for c in token)


def _check_redirects(tokens):
    for i, token in enumerate(tokens):
        if not _is_operator(token) or ">" not in token:
            continue
        target = tokens[i + 1] if i + 1 < len(tokens) else ""
        if token.endswith("&") and (target.isdigit() or target == "-"):
            continue
        if target in SAFE_REDIRECT_TARGETS:
            continue
        return f"output redirection to {target or 'a file'}"
    return None


def _segments(tokens):
    segment = []
    for token in tokens:
        if _is_operator(token) and ">" not in token and token not in ("<", "<<", "<<<"):
            if segment:
                yield segment
            segment = []
        else:
            segment.append(token)
    if segment:
        yield segment


def _command_word(tokens):
    i = 0
    while i < len(tokens):
        token = tokens[i]
        name = os.path.basename(token)
        if ASSIGNMENT.match(token) or token in KEYWORDS:
            i += 1
        elif name in WRAPPERS:
            i += 1
            with_value = WRAPPER_FLAGS_WITH_VALUE.get(name, set())
            while i < len(tokens) and tokens[i].startswith("-"):
                if name == "env" and tokens[i] in ENV_SPLIT_FLAGS:
                    # `env -S "rm x"` runs its value as a command line, like eval.
                    return "eval", tokens[i + 1:]
                i += 2 if tokens[i] in with_value else 1
            if name == "timeout" and i < len(tokens):
                i += 1
        elif name == "xargs":
            i += 1
            while i < len(tokens) and tokens[i].startswith("-"):
                i += 2 if tokens[i] in XARGS_FLAGS_WITH_VALUE else 1
        else:
            return name, tokens[i + 1:]
    return None, []


def _first_word(args):
    return next((a for a in args if not a.startswith("-")), None)


def _check_segment(tokens):
    name, args = _command_word(tokens)
    if name is None:
        return None
    if name in WRITE_COMMANDS:
        return f"`{name}`"
    if name in ("sed", "gsed", "perl") and any(
        a.startswith("--in-place") or re.match(r"-[nErsuzpla0]*i", a) for a in args
    ):
        return f"`{name} -i` (in-place edit)"
    if name == "curl" and any(
        a in ("--output", "--remote-name") or a.startswith("--output=")
        or re.fullmatch(r"-[a-zA-Z]*[oO]", a)
        for a in args
    ):
        return "`curl` writing to a file"
    if name == "find":
        return _check_find(args)
    if name in SHELLS:
        return _check_shell(args)
    if name == "eval":
        return find_write(" ".join(args))
    if name == "git":
        return _check_git(args)
    if re.fullmatch(r"python[0-9.]*", name) and "-m" in args:
        return _check_segment(args[args.index("-m") + 1:])
    if name == "uv" and _first_word(args) == "pip":
        return _check_segment(["pip"] + args[args.index("pip") + 1:])
    if name in PACKAGE_WRITES:
        sub = _first_word(args)
        if sub in PACKAGE_WRITES[name] or (name == "yarn" and sub is None):
            return f"`{name} {sub or ''}`".replace(" `", "`")
    return None


def _check_find(args):
    for i, arg in enumerate(args):
        if arg == "-delete" or arg.startswith("-fprint"):
            return f"`find {arg}`"
        if arg in ("-exec", "-execdir", "-ok", "-okdir"):
            reason = _check_segment(args[i + 1:])
            if reason:
                return reason
    return None


def _check_shell(args):
    for i, arg in enumerate(args):
        if re.fullmatch(r"-[a-z]*c", arg) and i + 1 < len(args):
            return find_write(args[i + 1])
    return None


def _check_git(args):
    i = 0
    while i < len(args) and args[i].startswith("-"):
        i += 2 if args[i] in GIT_GLOBAL_FLAGS_WITH_VALUE else 1
    if i >= len(args):
        return None
    sub, rest = args[i], args[i + 1:]
    if sub in GIT_READ:
        return None
    if sub == "hash-object" and "-w" not in rest:
        return None
    if sub == "branch" and all(a in GIT_BRANCH_READ_FLAGS for a in rest):
        return None
    if sub == "tag" and all(a in ("-l", "--list", "-n") for a in rest):
        return None
    if sub == "remote" and (not rest or rest[0] in ("-v", "--verbose", "show", "get-url")):
        return None
    if sub in ("stash", "worktree", "notes") and rest[:1] == ["list"]:
        return None
    if sub == "stash" and rest[:1] == ["show"]:
        return None
    if sub == "config" and rest[:1] and rest[0] in (
        "--get", "--get-all", "--get-regexp", "--list", "-l"
    ):
        return None
    if sub == "reflog" and (not rest or rest[0] == "show"):
        return None
    return f"`git {sub}`"
