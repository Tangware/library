#!/usr/bin/env python3

import json
import os
import subprocess
import sys
import unittest

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "require_draft_pr.py")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import require_draft_pr as hook  # noqa: E402


class HookCase(unittest.TestCase):

    def decide(self, payload: dict) -> dict:
        proc = subprocess.run(
            [sys.executable, HOOK], input=json.dumps(payload), capture_output=True, text=True
        )
        self.assertEqual(proc.returncode, 0, f"hook exited {proc.returncode}: {proc.stderr}")
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError as exc:  # pragma: no cover - only on a broken hook
            self.fail(f"hook emitted non-JSON {proc.stdout!r}: {exc}")

    def bash(self, command: str) -> dict:
        return self.decide(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": command},
            }
        )

    def assertAllowed(self, result: dict, msg: str = "") -> None:
        self.assertEqual(result, {}, f"expected allow, got {result}. {msg}")

    def _reason(self, result: dict) -> str:
        self.assertIn("hookSpecificOutput", result, f"expected a deny, got {result}")
        out = result["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PreToolUse")
        self.assertEqual(out["permissionDecision"], "deny", f"expected deny, got {result}")
        return out["permissionDecisionReason"]

    def assertDeniedForCreate(self, result: dict, msg: str = "") -> None:
        reason = self._reason(result)
        self.assertIn("just pr", reason, msg)
        self.assertIn("draft", reason, msg)

    def assertDeniedForLand(self, result: dict, msg: str = "") -> None:
        reason = self._reason(result)
        self.assertIn("just land", reason, msg)


class GhPrCreateWithoutDraft(HookCase):
    def test_bare_create_is_denied(self) -> None:
        self.assertDeniedForCreate(self.bash("gh pr create"))

    def test_create_with_title_and_body_but_no_draft_is_denied(self) -> None:
        self.assertDeniedForCreate(
            self.bash('gh pr create --title "add feature" --body "does the thing"')
        )

    def test_the_word_draft_inside_a_quoted_argument_does_not_count_as_the_flag(self) -> None:
        self.assertDeniedForCreate(self.bash('gh pr create --title "this needs draft review"'))

    def test_create_in_a_compound_command_is_still_denied(self) -> None:
        self.assertDeniedForCreate(self.bash("git push && gh pr create --title x"))
        self.assertDeniedForCreate(self.bash("gh pr create --title x; echo done"))


class GhPrCreateWithDraftIsAllowed(HookCase):
    def test_long_flag_allows(self) -> None:
        self.assertAllowed(self.bash("gh pr create --draft"))

    def test_short_flag_allows(self) -> None:
        self.assertAllowed(self.bash("gh pr create -d"))

    def test_draft_flag_anywhere_in_the_argument_list_allows(self) -> None:
        self.assertAllowed(self.bash('gh pr create --title x --draft --body "y"'))

    def test_what_just_pr_itself_runs_is_allowed(self) -> None:
        self.assertAllowed(self.bash("gh pr create --draft --title x --body y"))


class GhPrReady(HookCase):
    def test_bare_ready_is_denied(self) -> None:
        self.assertDeniedForLand(self.bash("gh pr ready"))

    def test_ready_with_an_explicit_target_is_denied(self) -> None:
        self.assertDeniedForLand(self.bash("gh pr ready 123"))
        self.assertDeniedForLand(self.bash("gh pr ready some-branch"))

    def test_ready_in_a_compound_command_is_still_denied(self) -> None:
        self.assertDeniedForLand(self.bash("just check && gh pr ready"))

    def test_undo_is_allowed(self) -> None:
        self.assertAllowed(self.bash("gh pr ready --undo"))


class GhPrMerge(HookCase):
    def test_bare_merge_is_denied(self) -> None:
        self.assertDeniedForLand(self.bash("gh pr merge"))

    def test_merge_with_flags_is_denied(self) -> None:
        self.assertDeniedForLand(self.bash("gh pr merge --squash --delete-branch"))

    def test_merge_in_a_compound_command_is_still_denied(self) -> None:
        self.assertDeniedForLand(self.bash("gh pr ready --undo; gh pr merge"))

    def test_stack_merge_is_denied(self) -> None:
        self.assertDeniedForLand(self.bash("gh stack merge"))
        self.assertDeniedForLand(self.bash("gh stack merge 846 --squash --yes"))

    def test_stack_submit_without_draft_is_denied(self) -> None:
        self.assertDeniedForCreate(self.bash("gh stack submit"))

    def test_reading_the_stack_is_allowed(self) -> None:
        self.assertAllowed(self.bash("gh stack view"))
        self.assertAllowed(self.bash("gh stack"))


class UntrackedCommandsAreAllowed(HookCase):
    def test_gh_pr_view_and_list_are_allowed(self) -> None:
        self.assertAllowed(self.bash("gh pr view"))
        self.assertAllowed(self.bash("gh pr view --json isDraft,state"))
        self.assertAllowed(self.bash("gh pr list"))

    def test_gh_issue_create_is_allowed(self) -> None:
        self.assertAllowed(self.bash("gh issue create --title x"))

    def test_ordinary_git_and_shell_commands_are_allowed(self) -> None:
        self.assertAllowed(self.bash("git commit -am 'wip'"))
        self.assertAllowed(self.bash("git status"))
        self.assertAllowed(self.bash("just check"))
        self.assertAllowed(self.bash("echo hello"))

    def test_just_land_itself_is_allowed(self) -> None:
        self.assertAllowed(self.bash("just land"))


class NonBashOrMalformedInputAllows(HookCase):
    def test_non_bash_tools_allow(self) -> None:
        for payload in (
            {"tool_name": "Edit", "tool_input": {"file_path": "x.py"}},
            {"tool_name": "Write", "tool_input": {"file_path": "x.py"}},
        ):
            with self.subTest(payload=payload):
                self.assertAllowed(self.decide(payload))

    def test_malformed_or_incomplete_payloads_allow(self) -> None:
        for payload in (
            {"tool_name": "Bash", "tool_input": {}},
            {"tool_name": "Bash"},
            {"tool_input": {"command": "gh pr ready"}},
            {},
        ):
            with self.subTest(payload=payload):
                self.assertAllowed(self.decide(payload))

    def test_empty_stdin_allows(self) -> None:
        proc = subprocess.run([sys.executable, HOOK], input="", capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout), {})

    def test_an_unparseable_command_allows(self) -> None:
        self.assertAllowed(self.bash('gh pr create "unbalanced'))


if __name__ == "__main__":
    unittest.main(verbosity=2)
