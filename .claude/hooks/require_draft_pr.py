#!/usr/bin/env python3

import json
import shlex
import sys

REQUIRE_DRAFT_REASON = (
    "Every PR must be opened as a draft, never ready — use `just pr` instead of `gh pr create`. "
    "`just land` runs the full suite, then readies, then merges. See AGENTS.md > Running it."
)

REQUIRE_LAND_REASON = (
    "Use `just land` instead of `{cmd}` — it runs the full local suite, flips the PR ready, "
    "and merges. {cmd} on its own skips some "
    "of that sequence. See AGENTS.md > Running it."
)


def tokenize(cmd: str) -> list[str]:
    try:
        lexer = shlex.shlex(cmd, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        return list(lexer)
    except ValueError:
        return []


CONNECTORS = {"|", "||", "&", "&&", ";"}


def is_operator_token(tok: str) -> bool:
    return bool(tok) and all(c in "();<>|&" for c in tok)


def segments(tokens: list[str]) -> list[list[str]]:
    out: list[list[str]] = []
    current: list[str] = []
    for tok in tokens:
        if tok in CONNECTORS or is_operator_token(tok):
            if current:
                out.append(current)
            current = []
            continue
        current.append(tok)
    if current:
        out.append(current)
    return out


def denial_for(segment: list[str]) -> str | None:
    if segment[:2] == ["gh", "stack"] and len(segment) >= 3:
        if segment[2] == "merge":
            return REQUIRE_LAND_REASON.format(cmd="gh stack merge")
        if segment[2] == "submit":
            return REQUIRE_DRAFT_REASON
        return None
    if segment[:2] != ["gh", "pr"] or len(segment) < 3:
        return None
    sub = segment[2]
    rest = segment[3:]
    if sub == "ready":
        return None if "--undo" in rest else REQUIRE_LAND_REASON.format(cmd="gh pr ready")
    if sub == "merge":
        return REQUIRE_LAND_REASON.format(cmd="gh pr merge")
    if sub == "create":
        has_draft = any(t in ("--draft", "-d") for t in rest)
        return None if has_draft else REQUIRE_DRAFT_REASON
    return None


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )


def allow() -> None:
    print("{}")


def main() -> None:
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        allow()
        return
    cmd = data["tool_input"]["command"]
    for segment in segments(tokenize(cmd)):
        reason = denial_for(segment)
        if reason is not None:
            deny(reason)
            return
    allow()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Fail open on anything unexpected (malformed stdin, missing fields, ...), the same
        # fallback block_main_branch.py uses.
        allow()
