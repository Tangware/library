#!/usr/bin/env python3
"""Blocks main-checkout writes/commits/branch-switches — feature work belongs in a worktree.

Resolves the actual absolute target, not cwd, since an absolute path bypasses cwd-based checks. A
relative target resolves against the real Bash cwd (tracking any `cd`), never the payload's `cwd`,
which is only the session cwd. An unresolvable `cd` (via variable/pushd) still denies. Add new
blocked commands to GIT_MUTATING_VERBS/SHELL_MUTATORS.
"""

import json
import os
import shlex
import subprocess
import sys

REASON = (
    "Feature work must happen in an isolated worktree, not the main checkout. Never develop "
    "directly on main. Follow AGENTS.md > Running it exactly for how to create and set one up "
    "-- do not skip any of its steps."
)


def reason_for(target: str, cwd: str) -> str:
    if os.path.isabs(target):
        return REASON
    return (
        f"Could not resolve {target!r} to a specific checkout: it is a relative path, so this "
        f"hook resolved it against the cwd the command would run in ({cwd}), where it lands in "
        "the main checkout. A relative path in the main checkout and the same one inside a "
        "worktree are indistinguishable here, so this is a refusal by default — NOT a confirmed "
        "main-checkout write, and not evidence that you lack a worktree. If you are working in "
        "one, `cd` into it first in the same command, or re-run with an absolute path under it. "
        "If you really are in the main checkout: " + REASON
    )


GIT_MUTATING_VERBS = {
    "commit", "checkout", "switch", "mv", "rm", "restore", "reset", "apply",
    "stash", "clean", "revert", "cherry-pick", "rebase", "merge",
}

# These git global flags take a SEPARATE operand token — skip both, or the scan ends on an
# unrecognized verb and bypasses this hook. Verify against git before adding one; a wrong entry
# opens the hole it exists to close.
GIT_FLAGS_TAKING_SEPARATE_OPERAND = {
    "-c", "-C", "--attr-source", "--config-env",
    "--git-dir", "--namespace", "--shallow-file", "--work-tree",
}

# `--work-tree` is deliberately excluded: honoring it would let `git --work-tree <elsewhere>
# commit` retarget this guard away from main.
GIT_FLAGS_NAMING_THE_TARGET = {"-C", "--git-dir"}


def all_args(args: list[str]) -> list[str]:
    return [a for a in args if not a.startswith("-")]


def last_arg(args: list[str]) -> list[str]:
    non_flags = all_args(args)
    return non_flags[-1:]


def sed_targets(args: list[str]) -> list[str]:
    has_i = any(a in ("-i", "--in-place") or a.startswith(("-i.", "--in-place=")) for a in args)
    return all_args(args) if has_i else []


def dd_targets(args: list[str]) -> list[str]:
    """Only `of=` is a write target; `if=` is a read-only source and must not be flagged."""
    return [a[len("of="):] for a in args if a.startswith("of=")]


def first_arg(args: list[str]) -> list[str]:
    non_flags = all_args(args)
    return non_flags[:1]


SHELL_MUTATORS = {
    "mv": all_args, "rm": all_args, "truncate": all_args, "tee": all_args,
    "mkdir": all_args, "rmdir": all_args, "patch": first_arg,
    "cp": last_arg, "install": last_arg, "ln": last_arg,
    "sed": sed_targets,
    "dd": dd_targets,
}

OPERATOR_CHARS = set("();<>|&")
CONNECTORS = {"|", "||", "&", "&&", ";", "(", ")"}


def is_operator_token(tok: str) -> bool:
    return bool(tok) and all(c in OPERATOR_CHARS for c in tok)


# No `);` or `(;` operator exists. Treating the two chars as one operator hides everything after
# it from the scanner — no connector is recognized, so the tail is never classified.
STANDALONE_OPERATOR_CHARS = set("();")


def split_operator_runs(tokens: list[str]) -> list[str]:
    out: list[str] = []
    for tok in tokens:
        if not is_operator_token(tok) or not set(tok) & STANDALONE_OPERATOR_CHARS:
            out.append(tok)
            continue
        run = ""
        for char in tok:
            if char in STANDALONE_OPERATOR_CHARS:
                if run:
                    out.append(run)
                    run = ""
                out.append(char)
            else:
                run += char
        if run:
            out.append(run)
    return out


def tokenize(cmd: str) -> list[str]:
    """Tokenize a raw shell command string. `punctuation_chars=True` groups runs of `();<>|&`
    into single operator tokens (so `&&`/`>>`/`2>&1`'s `>&` stay intact) while still respecting
    quoting — a quoted "<" stays literal data, never mistaken for an operator, and a filename
    with an embedded space tokenizes correctly (both of which a plain IFS/word-split can't do).
    The runs it groups by mere adjacency are then split back apart, see split_operator_runs.
    Malformed input (e.g. unbalanced quotes) fails open: no tokens, nothing gets checked, same
    "just don't match" fallback the rest of this hook already relies on."""
    try:
        lexer = shlex.shlex(cmd, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        return split_operator_runs(list(lexer))
    except ValueError:
        return []


def strip_redirections(tokens: list[str]) -> list[str]:
    """Drop shell redirection operators and the operand each one takes, e.g. the `<`/`diff.patch`
    in `patch f < diff.patch`, or the `2`/`>&`/`1` in `... 2>&1` (an fd number immediately before
    a redirect operator is part of the redirect, not a real argument). Left unstripped, a token
    like a lone `<` resolves via dirname all the way to the hook's own cwd — a false-positive
    deny on any main-checkout invocation involving redirection. Actually treating `>`/`>>` targets
    as real write destinations is a separate, deliberately deferred feature; this only keeps them
    from being misread as an unrelated, harmless-looking path."""
    out: list[str] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if is_operator_token(tok) and ("<" in tok or ">" in tok):
            if out and out[-1].isdigit():
                out.pop()
            i += 1
            if i < len(tokens):
                i += 1
            continue
        out.append(tok)
        i += 1
    return out


# `|` and `&` are excluded on purpose — both run their left side in a subshell, so a `cd` there
# never moves the parent shell. Honoring them would misresolve cwd.
CD_PROPAGATING_CONNECTORS = {";", "&&", "||"}


def cd_destination(segment: list[str], cwd: str) -> str | None:
    """Where a `cd` segment moves the shell from `cwd`, or None if it doesn't move it.

    Only a single operand naming an existing directory counts — `cd` with no operand, `cd -`, and
    multi-operand forms are unhonoured because the destination isn't determined by text alone.
    `normpath` collapses `..` the way bash's own `cd` does, since the result feeds `git -C` and
    denial output.
    """
    if not segment or segment[0] != "cd":
        return None
    operands = [a for a in segment[1:] if not a.startswith("-")]
    if len(operands) != 1:
        return None
    dest = os.path.normpath(os.path.join(cwd, operands[0]))
    return dest if os.path.isdir(dest) else None


def segments_with_cwd(tokens: list[str], cwd: str) -> list[tuple[list[str], str]]:
    out: list[tuple[list[str], str]] = []
    saved: list[str] = []
    current: list[str] = []
    for tok in tokens:
        if tok not in CONNECTORS:
            current.append(tok)
            continue
        segment = strip_redirections(current)
        current = []
        if segment:
            out.append((segment, cwd))
        if tok in CD_PROPAGATING_CONNECTORS:
            cwd = cd_destination(segment, cwd) or cwd
        elif tok == "(":
            saved.append(cwd)
        elif tok == ")" and saved:
            cwd = saved.pop()
    segment = strip_redirections(current)
    if segment:
        out.append((segment, cwd))
    return out


def git_dirs_for_path(path: str) -> tuple[str, str] | None:
    """Returns (git-dir, git-common-dir), both absolute, or None if not in a repo.

    --path-format=absolute matters: without it git mixes absolute/relative forms across paths,
    breaking the string comparison.
    """
    d = path
    while d != "/" and not os.path.isdir(d):
        d = os.path.dirname(d) or "."
    try:
        result = subprocess.run(
            ["git", "-C", d, "rev-parse", "--path-format=absolute",
             "--git-dir", "--git-common-dir"],
            capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None
    lines = result.stdout.strip().splitlines()
    if len(lines) != 2:
        return None
    return lines[0], lines[1]


def is_main_checkout(path: str, cwd: str) -> bool:
    dirs = git_dirs_for_path(os.path.join(cwd, path))
    if dirs is None:
        return False
    git_dir, common_dir = dirs
    return bool(common_dir) and git_dir == common_dir


def check_git_segment(tokens: list[str]) -> str | None:
    if not tokens or tokens[0] != "git":
        return None
    target = "."
    i = 1
    while i < len(tokens):
        tok = tokens[i]
        if tok in GIT_FLAGS_TAKING_SEPARATE_OPERAND and i + 1 < len(tokens):
            if tok in GIT_FLAGS_NAMING_THE_TARGET:
                target = tokens[i + 1]
            i += 2
            continue
        if tok.startswith("--git-dir="):
            target = tok.split("=", 1)[1]
            i += 1
            continue
        if tok in GIT_MUTATING_VERBS:
            return target
        if tok.startswith("-"):
            i += 1
            continue
        return None
    return None


def check_shell_segment(tokens: list[str]) -> list[str]:
    if not tokens:
        return []
    classifier = SHELL_MUTATORS.get(tokens[0])
    return classifier(tokens[1:]) if classifier else []


def deny(target: str, cwd: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason_for(target, cwd),
        }
    }))


def allow() -> None:
    print("{}")


def main() -> None:
    data = json.load(sys.stdin)
    tool = data.get("tool_name")
    cwd = os.getcwd()

    if tool in ("Edit", "Write", "NotebookEdit"):
        file_path = data["tool_input"]["file_path"]
        deny(file_path, cwd) if is_main_checkout(file_path, cwd) else allow()
        return

    if tool == "Bash":
        cmd = data["tool_input"]["command"]
        for segment, segment_cwd in segments_with_cwd(tokenize(cmd), cwd):
            git_target = check_git_segment(segment)
            if git_target is not None and is_main_checkout(git_target, segment_cwd):
                deny(git_target, segment_cwd)
                return
            for path in check_shell_segment(segment):
                if is_main_checkout(path, segment_cwd):
                    deny(path, segment_cwd)
                    return
        allow()
        return

    allow()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        allow()
