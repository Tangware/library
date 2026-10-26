default:
    @just --list

install:
    cd model && uv sync

relock:
    cd model && uv lock

# Install git hooks (run once per clone, and once per worktree)
hooks:
    git config extensions.worktreeConfig true
    git config --worktree core.hooksPath .githooks
    chmod +x .githooks/pre-commit .githooks/pre-push .githooks/land

lint:
    cd model && uv lock --check
    cd model && uv run ruff check .
    cd model && uv run ruff format --check .
    cd model && uv run mypy src/ tests/
    cd model && uv run lint-imports
    cd model && uv run ast-grep test --skip-snapshot-tests
    cd model && uv run ast-grep scan

test *args:
    cd model && uv run --locked pytest -n 4 --dist=worksteal {{args}}

lint-plugin:
    claude plugin validate .
    claude plugin validate plugin

# ── PRs: draft while iterating, `just land` to finish ───────────────────────────
# Every PR is born a draft. A push to it gets almost nothing from `.githooks/pre-push`: each
# commit was already checked by `.githooks/pre-commit` (static analysis, scoped to what that commit touched), and pre-push's
# only remaining job is refusing a push to an ALREADY-ready PR — see that file's own header.
#
# `just land` is the one path a PR is allowed to reach `main` through: it runs the full local
# suite, then flips the PR out of draft and merges. `.claude/hooks/require_draft_pr.py` denies
# `gh pr create` without `--draft`, `gh pr ready`, and `gh pr merge` directly, so reaching for any
# of them by habit is a wall, not a suggestion — and pre-push denies the push a direct
# `gh pr ready` would otherwise be followed by.

# Open a new PR as a draft — the only way a PR should be created. Extra flags pass through
# (`just pr "--title 'fix: X' --body 'Y'"`); with none, gh prompts interactively as usual.
pr *ARGS:
    gh pr create --draft {{ARGS}}

# Run the per-commit checks by hand: static analysis only, scoped to the diff against
# origin/main, including working-tree changes — the same check every commit runs, without
# committing.
check:
    .githooks/pre-commit --manual

# Land the PR: the full local suite (every test the diff selects), then ready, then merge — see
# the section header above. Safe to run speculatively: a local failure never touches the PR's
# draft/ready state, so this doubles as "check everything passes" with no side effects if it
# doesn't.
land:
    .githooks/land

# Publish the package to PyPI, once per version; the plugin's `cad` pins the version it runs.
release:
    #!/usr/bin/env bash
    set -euo pipefail
    cd model
    version="$(uv version --short)"
    grep -q "tangware==$version " ../plugin/bin/cad || { echo "plugin/bin/cad must pin tangware==$version" >&2; exit 1; }
    status="$(curl -s -o /dev/null -w '%{http_code}' "https://pypi.org/pypi/tangware/$version/json")"
    [ "$status" = 404 ] || { echo "tangware $version: PyPI answered $status, so it is published already or PyPI is unreachable" >&2; exit 1; }
    rm -rf dist
    uv build
    uv publish
