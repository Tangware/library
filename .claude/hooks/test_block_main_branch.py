#!/usr/bin/env python3

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "block_main_branch.py")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import block_main_branch as hook  # noqa: E402


def clean_env(**extra: str) -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")} | extra


GIT_ENV = clean_env(
    GIT_AUTHOR_NAME="test",
    GIT_AUTHOR_EMAIL="test@example.invalid",
    GIT_COMMITTER_NAME="test",
    GIT_COMMITTER_EMAIL="test@example.invalid",
    GIT_CONFIG_GLOBAL=os.devnull,
    GIT_CONFIG_SYSTEM=os.devnull,
)
HOOK_ENV = clean_env()


def git(*args: str, cwd: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, env=GIT_ENV, capture_output=True, text=True, check=True
    ).stdout


def git_dirs(path: str) -> tuple[str, str]:
    out = git("-C", path, "rev-parse", "--path-format=absolute",
              "--git-dir", "--git-common-dir", cwd=path).split()
    return out[0], out[1]


class HookCase(unittest.TestCase):

    root: str
    main: str
    wt: str
    outside: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = os.path.realpath(tempfile.mkdtemp(prefix="block-main-branch-test-"))
        cls.main = os.path.join(cls.root, "main")
        cls.wt = os.path.join(cls.root, "worktree")
        cls.outside = os.path.join(cls.root, "outside")
        os.makedirs(cls.main)
        os.makedirs(cls.outside)
        git("init", "-b", "main", cls.main, cwd=cls.root)
        with open(os.path.join(cls.main, "tracked.txt"), "w") as fh:
            fh.write("contents\n")
        git("add", "-A", cwd=cls.main)
        git("commit", "-m", "initial", cwd=cls.main)
        git("worktree", "add", "-b", "feature", cls.wt, cwd=cls.main)

        # Positive control on the fixture itself — if it silently produced the wrong paths,
        # allow-cases would pass without ever exercising the branch they name.
        main_dir, main_common = git_dirs(cls.main)
        assert main_dir == main_common, f"fixture main checkout is not one: {main_dir} != {main_common}"
        wt_dir, wt_common = git_dirs(cls.wt)
        assert wt_dir != wt_common, f"fixture worktree is not linked: {wt_dir} == {wt_common}"
        probe = subprocess.run(["git", "-C", cls.outside, "rev-parse", "--git-dir"],
                               env=GIT_ENV, capture_output=True, text=True)
        assert probe.returncode != 0, (
            f"fixture 'outside' dir is inside a git repo ({probe.stdout.strip()}) -- "
            "the no-repo cases below would not be testing what they claim"
        )

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.root, ignore_errors=True)


    def decide(self, payload: dict, cwd: str) -> dict:
        proc = subprocess.run([sys.executable, HOOK], input=json.dumps(payload),
                              capture_output=True, text=True, cwd=cwd, env=HOOK_ENV)
        self.assertEqual(proc.returncode, 0, f"hook exited {proc.returncode}: {proc.stderr}")
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError as exc:  # pragma: no cover - only on a broken hook
            self.fail(f"hook emitted non-JSON {proc.stdout!r}: {exc}")

    def bash(self, command: str, cwd: str) -> dict:
        return self.decide(
            {"hook_event_name": "PreToolUse", "tool_name": "Bash",
             "tool_input": {"command": command}}, cwd)

    def write(self, file_path: str, cwd: str, tool: str = "Write") -> dict:
        return self.decide(
            {"hook_event_name": "PreToolUse", "tool_name": tool,
             "tool_input": {"file_path": file_path}}, cwd)


    def assertAllowed(self, result: dict, msg: str = "") -> None:
        self.assertEqual(result, {}, f"expected allow, got {result}. {msg}")

    def _reason(self, result: dict) -> str:
        self.assertIn("hookSpecificOutput", result, f"expected a deny, got {result}")
        out = result["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PreToolUse")
        self.assertEqual(out["permissionDecision"], "deny", f"expected deny, got {result}")
        return out["permissionDecisionReason"]

    def assertDeniedAsMainCheckout(self, result: dict, msg: str = "") -> None:
        reason = self._reason(result)
        self.assertIn("Feature work must happen in an isolated worktree", reason, msg)
        self.assertNotIn(
            "Could not resolve", reason,
            f"a confirmed main-checkout write must NOT be reported as unresolvable. {msg}")

    def assertDeniedAsUnresolvable(self, result: dict, target: str, cwd: str, msg: str = "") -> None:
        reason = self._reason(result)
        self.assertIn("Could not resolve", reason,
                      f"an unresolvable target must not be reported as a confirmed write. {msg}")
        self.assertIn(repr(target), reason, msg)
        self.assertIn(cwd, reason, msg)
        self.assertIn("NOT a confirmed main-checkout write", reason, msg)
        self.assertIn("Feature work must happen in an isolated worktree", reason, msg)


class FileEditingTools(HookCase):

    def test_absolute_path_into_main_checkout_is_denied(self) -> None:
        for tool in ("Write", "Edit", "NotebookEdit"):
            with self.subTest(tool=tool):
                target = os.path.join(self.main, "new.txt")
                self.assertDeniedAsMainCheckout(self.write(target, self.wt, tool), tool)

    def test_absolute_path_into_a_worktree_is_allowed(self) -> None:
        for tool in ("Write", "Edit", "NotebookEdit"):
            with self.subTest(tool=tool):
                target = os.path.join(self.wt, "new.txt")
                self.assertAllowed(self.write(target, self.main, tool), tool)

    def test_absolute_path_in_no_repo_at_all_is_allowed(self) -> None:
        self.assertAllowed(self.write(os.path.join(self.outside, "new.txt"), self.main))

    def test_relative_path_from_the_main_checkout_is_denied_as_unresolvable(self) -> None:
        self.assertDeniedAsUnresolvable(self.write("new.txt", self.main), "new.txt", self.main)

    def test_relative_path_from_a_worktree_is_allowed(self) -> None:
        self.assertAllowed(self.write("new.txt", self.wt))

    def test_an_untracked_tool_is_allowed_even_into_the_main_checkout(self) -> None:
        self.assertAllowed(self.write(os.path.join(self.main, "tracked.txt"), self.main, "Read"))


class ReadOnlyCommandsAreAllowed(HookCase):

    def test_read_only_commands_are_allowed_in_the_main_checkout(self) -> None:
        for command in (
            "git status",
            "git status --porcelain",
            "git log --oneline -5",
            "git diff",
            "git rev-parse HEAD",
            "ls -la",
            "cat tracked.txt",
            "grep -rn contents .",
            "ls | grep tracked",
            "python3 -c 'print(1)'",
            "just test",
        ):
            with self.subTest(command=command):
                self.assertAllowed(self.bash(command, self.main))


class GitMutatingVerbs(HookCase):
    VERBS = [
        "apply", "checkout", "cherry-pick", "clean", "commit", "merge", "mv", "rebase",
        "reset", "restore", "revert", "rm", "stash", "switch",
    ]

    def test_the_verb_table_matches_the_hooks_own(self) -> None:
        self.assertEqual(set(self.VERBS), set(hook.GIT_MUTATING_VERBS))

    def test_every_mutating_verb_is_denied_when_it_targets_the_main_checkout(self) -> None:
        for verb in self.VERBS:
            with self.subTest(verb=verb):
                self.assertDeniedAsMainCheckout(
                    self.bash(f"git -C {self.main} {verb}", self.wt), verb)

    def test_every_mutating_verb_is_allowed_when_it_targets_a_worktree(self) -> None:
        for verb in self.VERBS:
            with self.subTest(verb=verb):
                self.assertAllowed(self.bash(f"git -C {self.wt} {verb}", self.main), verb)

    def test_a_bare_mutating_verb_in_the_main_checkout_is_denied_as_unresolvable(self) -> None:
        self.assertDeniedAsUnresolvable(self.bash("git commit -m x", self.main), ".", self.main)

    def test_a_bare_mutating_verb_in_a_worktree_is_allowed(self) -> None:
        self.assertAllowed(self.bash("git commit -m x", self.wt))

    def test_git_dir_override_is_honoured_in_both_directions(self) -> None:
        self.assertDeniedAsMainCheckout(
            self.bash(f"git --git-dir={self.main}/.git commit -m x", self.wt))
        self.assertAllowed(self.bash(f"git --git-dir={self.wt}/.git commit -m x", self.main))

    def test_the_last_dash_C_wins(self) -> None:
        self.assertDeniedAsMainCheckout(
            self.bash(f"git -C {self.wt} -C {self.main} commit -m x", self.wt))
        self.assertAllowed(self.bash(f"git -C {self.main} -C {self.wt} commit -m x", self.main))

    def test_a_flag_before_the_verb_does_not_hide_it(self) -> None:
        self.assertDeniedAsMainCheckout(
            self.bash(f"git --no-pager -C {self.main} commit -m x", self.wt))

    # Global flags with a separate-token operand, listed explicitly rather than looped from VERBS:
    # a live-table loop wouldn't catch an entry later deleted from it.

    def separate_operand_flags(self) -> dict[str, str]:
        return {
            "-c": "user.email=x",
            "-C": self.wt,
            "--attr-source": "HEAD",
            "--config-env": "user.email=TEST_EMAIL",
            "--git-dir": f"{self.wt}/.git",
            "--namespace": "ns",
            "--shallow-file": f"{self.wt}/shallow",
            "--work-tree": self.wt,
        }

    # Global flags that take no operand (like bare `--exec-path`). Adding one here lets the hook
    # step over the verb that follows and bypass the block.
    NO_OPERAND_FLAGS = [
        "-p", "-P", "--paginate", "--no-pager", "--bare", "--no-advice", "--exec-path",
        "--html-path", "--man-path", "--info-path", "--no-replace-objects", "--no-lazy-fetch",
        "--no-optional-locks", "--literal-pathspecs", "--glob-pathspecs", "--icase-pathspecs",
    ]

    def test_the_separate_operand_flag_tables_match_the_hooks_own(self) -> None:
        self.assertEqual(set(self.separate_operand_flags()),
                         set(hook.GIT_FLAGS_TAKING_SEPARATE_OPERAND))
        self.assertEqual({"-C", "--git-dir"}, set(hook.GIT_FLAGS_NAMING_THE_TARGET))
        self.assertLessEqual(hook.GIT_FLAGS_NAMING_THE_TARGET,
                             hook.GIT_FLAGS_TAKING_SEPARATE_OPERAND)
        self.assertEqual(set(), set(self.NO_OPERAND_FLAGS) & set(self.separate_operand_flags()))

    def test_the_dash_c_bypass_is_closed(self) -> None:
        self.assertDeniedAsMainCheckout(
            self.bash(f"git -c user.email=x -C {self.main} commit -m y", self.wt))

    def test_no_separate_operand_flag_hides_the_verb_behind_it(self) -> None:
        for flag, operand in sorted(self.separate_operand_flags().items()):
            with self.subTest(flag=flag):
                self.assertDeniedAsMainCheckout(
                    self.bash(f"git {flag} {operand} -C {self.main} commit -m y", self.wt), flag)

    def test_a_separate_operand_flag_targeting_a_worktree_is_still_allowed(self) -> None:
        for flag, operand in sorted(self.separate_operand_flags().items()):
            with self.subTest(flag=flag):
                self.assertAllowed(
                    self.bash(f"git {flag} {operand} -C {self.wt} commit -m y", self.main), flag)

    def test_a_separate_operand_flag_before_an_untracked_subcommand_is_allowed(self) -> None:
        # Guards against scanning past an operand also skipping the `status` bail-out — every
        # agent runs `git status` against main constantly.
        for flag, operand in sorted(self.separate_operand_flags().items()):
            with self.subTest(flag=flag):
                self.assertAllowed(
                    self.bash(f"git {flag} {operand} -C {self.main} status", self.wt), flag)

    def test_a_flag_taking_no_operand_must_not_swallow_the_verb(self) -> None:
        for flag in self.NO_OPERAND_FLAGS:
            with self.subTest(flag=flag):
                self.assertDeniedAsMainCheckout(
                    self.bash(f"git -C {self.main} {flag} commit -m y", self.wt), flag)

    def test_git_dir_separated_from_its_operand_is_honoured_in_both_directions(self) -> None:
        self.assertDeniedAsMainCheckout(
            self.bash(f"git --git-dir {self.main}/.git commit -m x", self.wt))
        self.assertAllowed(self.bash(f"git --git-dir {self.wt}/.git commit -m x", self.main))

    def test_work_tree_does_not_retarget_the_verdict_away_from_main(self) -> None:
        # `--work-tree` names a worktree, not a repo — honouring it would let a command retarget
        # the verdict away from main, so its operand is skipped; the target still comes from cwd.
        self.assertDeniedAsUnresolvable(
            self.bash(f"git --work-tree {self.wt} commit -m x", self.main), ".", self.main)

    def test_a_non_mutating_subcommand_targeting_main_is_allowed(self) -> None:
        for verb in ("status", "log", "diff", "fetch", "show"):
            with self.subTest(verb=verb):
                self.assertAllowed(self.bash(f"git -C {self.main} {verb}", self.wt), verb)


class ShellMutators(HookCase):

    def test_every_shell_mutator_is_denied_when_it_writes_into_the_main_checkout(self) -> None:
        into_main = {
            "mv": f"mv {self.wt}/a {self.main}/b",
            "rm": f"rm -f {self.main}/a",
            "truncate": f"truncate -s 0 {self.main}/a",
            "tee": f"tee {self.main}/a",
            "mkdir": f"mkdir {self.main}/d",
            "rmdir": f"rmdir {self.main}/d",
            "patch": f"patch {self.main}/a",
            "cp": f"cp {self.wt}/a {self.main}/a",
            "install": f"install {self.wt}/a {self.main}/a",
            "ln": f"ln -s {self.wt}/a {self.main}/link",
            "sed": f"sed -i s/a/b/ {self.main}/a",
            "dd": f"dd if={self.wt}/a of={self.main}/a",
        }
        self.assertEqual(
            set(into_main), set(hook.SHELL_MUTATORS),
            "SHELL_MUTATORS and this test's table have drifted apart — a mutator with no case "
            "here is a mutator nothing checks")
        for name, command in sorted(into_main.items()):
            with self.subTest(mutator=name):
                self.assertDeniedAsMainCheckout(self.bash(command, self.wt), command)

    def test_every_shell_mutator_is_allowed_when_it_writes_inside_a_worktree(self) -> None:
        inside_wt = {
            "mv": f"mv {self.wt}/a {self.wt}/b",
            "rm": f"rm -f {self.wt}/a",
            "truncate": f"truncate -s 0 {self.wt}/a",
            "tee": f"tee {self.wt}/a",
            "mkdir": f"mkdir {self.wt}/d",
            "rmdir": f"rmdir {self.wt}/d",
            "patch": f"patch {self.wt}/a",
            "cp": f"cp {self.main}/a {self.wt}/a",
            "install": f"install {self.main}/a {self.wt}/a",
            "ln": f"ln -s {self.main}/a {self.wt}/link",
            "sed": f"sed -i s/a/b/ {self.wt}/a",
            "dd": f"dd if={self.main}/a of={self.wt}/a",
        }
        self.assertEqual(set(inside_wt), set(hook.SHELL_MUTATORS))
        for name, command in sorted(inside_wt.items()):
            with self.subTest(mutator=name):
                self.assertAllowed(self.bash(command, self.wt), command)

    def test_sed_without_in_place_is_a_read_only_filter(self) -> None:
        self.assertAllowed(self.bash(f"sed s/a/b/ {self.main}/tracked.txt", self.wt))
        self.assertAllowed(self.bash(f"sed -n 1p {self.main}/tracked.txt", self.wt))
        for flag in ("-i", "-i.bak", "--in-place", "--in-place=.bak"):
            with self.subTest(flag=flag):
                self.assertDeniedAsMainCheckout(
                    self.bash(f"sed {flag} s/a/b/ {self.main}/tracked.txt", self.wt), flag)

    def test_dd_reading_from_main_is_not_a_write_to_main(self) -> None:
        self.assertAllowed(self.bash(f"dd if={self.main}/a of={self.wt}/a", self.wt))
        self.assertDeniedAsMainCheckout(self.bash(f"dd if={self.wt}/a of={self.main}/a", self.wt))

    def test_mv_flags_both_operands_since_it_deletes_the_source(self) -> None:
        self.assertDeniedAsMainCheckout(self.bash(f"mv {self.main}/a {self.wt}/a", self.wt))

    def test_commands_outside_the_mutator_table_are_allowed(self) -> None:
        for command in (
            f"touch {self.main}/a",
            f"chmod +x {self.main}/a",
            f"cat {self.main}/a",
            f"gzip {self.main}/a",
            f"python3 script.py {self.main}/a",
        ):
            with self.subTest(command=command):
                self.assertAllowed(self.bash(command, self.wt))

    def test_relative_mutator_paths_split_on_the_hooks_own_cwd(self) -> None:
        self.assertDeniedAsUnresolvable(self.bash("mv a b", self.main), "a", self.main)
        self.assertDeniedAsUnresolvable(self.bash("mkdir d", self.main), "d", self.main)
        self.assertAllowed(self.bash("mv a b", self.wt))
        self.assertAllowed(self.bash("mkdir d", self.wt))
        self.assertAllowed(self.bash("rm -f a", self.outside))


class Redirection(HookCase):

    def test_a_redirect_source_in_main_is_not_a_write_target(self) -> None:
        self.assertAllowed(self.bash(f"patch {self.wt}/a < {self.main}/diff.patch", self.wt))
        self.assertAllowed(self.bash(f"tee {self.wt}/a < {self.main}/tracked.txt", self.wt))

    def test_an_fd_number_before_a_redirect_is_not_a_path(self) -> None:
        # Unstripped, the "2" of `2>&1` resolves via dirname to the hook's cwd (the main
        # checkout), wrongly denying a worktree-only command.
        self.assertAllowed(self.bash(f"rm -f {self.wt}/a 2>&1", self.main))
        self.assertAllowed(self.bash("rm -f a 2>&1", self.wt))

    def test_a_quoted_operator_stays_literal_data(self) -> None:
        self.assertAllowed(self.bash('grep "<" tracked.txt', self.main))

    def test_a_write_into_main_still_denies_alongside_a_redirect(self) -> None:
        self.assertDeniedAsMainCheckout(self.bash(f"rm -f {self.main}/a 2>&1", self.wt))


class CompoundCommands(HookCase):
    def test_a_mutator_after_a_connector_is_still_seen(self) -> None:
        for command in (
            f"git status; mv {self.main}/a {self.main}/b",
            f"ls && rm -f {self.main}/a",
            f"ls || rm -f {self.main}/a",
            f"cat x | tee {self.main}/a",
            f"( mkdir {self.main}/d )",
        ):
            with self.subTest(command=command):
                self.assertDeniedAsMainCheckout(self.bash(command, self.wt))

    def test_a_compound_command_touching_only_a_worktree_is_allowed(self) -> None:
        self.assertAllowed(self.bash(f"git status && rm -f {self.wt}/a && ls", self.wt))

    def test_an_operator_run_grouped_by_adjacency_does_not_hide_what_follows(self) -> None:
        # shlex groups `);` into one token since they're adjacent, hiding the connector entirely
        # -- a bypass a single space avoids. Both spellings must decide identically.
        for spacing in ("(ls); {cmd}", "( ls ) ; {cmd}", "(ls);{cmd}"):
            with self.subTest(spacing=spacing):
                self.assertDeniedAsMainCheckout(
                    self.bash(spacing.format(cmd=f"rm -f {self.main}/a"), self.wt), spacing)
                self.assertAllowed(
                    self.bash(spacing.format(cmd=f"rm -f {self.wt}/a"), self.wt), spacing)

    def test_genuine_multi_character_operators_survive_the_split(self) -> None:
        self.assertEqual(hook.tokenize("a && b || c"), ["a", "&&", "b", "||", "c"])
        self.assertEqual(hook.tokenize("a 2>&1 >> f"), ["a", "2", ">&", "1", ">>", "f"])
        self.assertEqual(hook.tokenize("(a); b"), ["(", "a", ")", ";", "b"])
        self.assertAllowed(self.bash(f"rm -f {self.wt}/a 2>&1", self.main))
        self.assertAllowed(self.bash(f"patch {self.wt}/a < {self.main}/diff.patch", self.wt))


class CdMovesWhereRelativesResolve(HookCase):

    def test_a_relative_write_after_cd_into_a_worktree_is_allowed(self) -> None:
        self.assertAllowed(self.bash(f"cd {self.wt} && mkdir -p .brief", self.main))
        self.assertAllowed(self.bash(f"cd {self.wt} && mv a b", self.main))
        self.assertAllowed(self.bash(f"cd {self.wt} && git commit -m x", self.main))
        self.assertAllowed(self.bash(f"cd {self.wt}; rm -f a", self.main))
        self.assertAllowed(self.bash(f"cd {self.wt} || exit; rm -f a", self.main))

    def test_the_same_relative_write_with_no_cd_is_still_denied(self) -> None:
        self.assertDeniedAsUnresolvable(
            self.bash("mkdir -p .brief", self.main), ".brief", self.main)
        self.assertDeniedAsUnresolvable(self.bash("mv a b", self.main), "a", self.main)
        self.assertDeniedAsUnresolvable(self.bash("git commit -m x", self.main), ".", self.main)

    def test_an_absolute_path_into_main_is_denied_from_any_cd(self) -> None:
        for prefix in (f"cd {self.wt} && ", f"cd {self.outside} && ", ""):
            with self.subTest(prefix=prefix):
                self.assertDeniedAsMainCheckout(
                    self.bash(f"{prefix}rm -f {self.main}/a", self.wt), prefix)
                self.assertDeniedAsMainCheckout(
                    self.bash(f"{prefix}rm -f {self.main}/a", self.main), prefix)
                self.assertDeniedAsMainCheckout(
                    self.bash(f"{prefix}git -C {self.main} commit -m x", self.wt), prefix)

    def test_cd_into_the_main_checkout_makes_a_relative_write_resolve_there(self) -> None:
        self.assertDeniedAsUnresolvable(
            self.bash(f"cd {self.main} && mkdir d", self.wt), "d", self.main)
        self.assertDeniedAsUnresolvable(
            self.bash(f"cd {self.main} && git commit -m x", self.wt), ".", self.main)

    def test_a_relative_cd_operand_resolves_against_the_cwd_it_starts_from(self) -> None:
        self.assertAllowed(self.bash("cd ../worktree && mkdir d", self.main))
        self.assertDeniedAsUnresolvable(
            self.bash("cd ../main && mkdir d", self.wt), "d", self.main)

    def test_a_cd_the_shell_would_not_honour_does_not_move_the_resolution_point(self) -> None:
        missing = os.path.join(self.root, "no-such-dir")
        for command in (
            f"cd {missing}; mkdir d",
            f"cd {self.wt} | mkdir d",
            f"cd {self.wt} & mkdir d",
            f"( cd {self.wt} ); mkdir d",
            f"( cd {self.wt} && ls ); mkdir d",
            "cd; mkdir d",
            "cd -; mkdir d",
            f"cd {self.wt} {self.outside}; mkdir d",
        ):
            with self.subTest(command=command):
                self.assertDeniedAsUnresolvable(self.bash(command, self.main), "d", self.main)

    def test_a_cd_inside_a_subshell_still_applies_within_it(self) -> None:
        self.assertAllowed(self.bash(f"( cd {self.wt} && mkdir d )", self.main))
        self.assertDeniedAsMainCheckout(self.bash(f"( cd {self.wt} && mkdir {self.main}/d )",
                                                  self.main))

    def test_a_cd_survives_its_own_redirection(self) -> None:
        self.assertAllowed(self.bash(f"cd {self.wt} > /dev/null && mkdir d", self.main))

    def test_the_denial_names_the_cwd_it_actually_resolved_against(self) -> None:
        reason = self._reason(self.bash(f"cd {self.main} && mkdir d", self.wt))
        self.assertIn(self.main, reason)
        self.assertNotIn(self.wt, reason)

    def test_the_payload_cwd_field_is_not_read(self) -> None:
        """A real payload's `cwd` field is the session cwd Claude Code spawns the hook in, not the Bash command's own cwd.

        Trusting it would reopen the absolute-path bypass, so it can neither rescue nor condemn a
        write.
        """
        for cwd, extra, expect_allow in (
            (self.main, self.wt, False),
            (self.wt, self.main, True),
        ):
            with self.subTest(cwd=cwd):
                result = self.decide(
                    {"hook_event_name": "PreToolUse", "cwd": extra, "tool_name": "Bash",
                     "tool_input": {"command": "mkdir d"}}, cwd)
                self.assertEqual(result == {}, expect_allow, result)

    def test_cd_state_does_not_leak_between_tool_calls(self) -> None:
        self.assertAllowed(self.bash(f"cd {self.wt} && mkdir d", self.main))
        self.assertDeniedAsUnresolvable(self.bash("mkdir d", self.main), "d", self.main)


class FailsOpen(HookCase):
    """Every unrecognised shape allows.

    A hook that crashed or denied on a payload it didn't understand would block the session
    outright.
    """

    def test_malformed_payloads_allow(self) -> None:
        for payload in (
            {"tool_name": "Bash", "tool_input": {}},
            {"tool_name": "Write", "tool_input": {}},
            {"tool_name": "Bash"},
            {"tool_input": {"command": "rm -rf /"}},
            {},
        ):
            with self.subTest(payload=payload):
                self.assertAllowed(self.decide(payload, self.main))

    def test_empty_stdin_allows(self) -> None:
        proc = subprocess.run([sys.executable, HOOK], input="", capture_output=True,
                              text=True, cwd=self.main, env=HOOK_ENV)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout), {})

    def test_an_unparseable_command_allows(self) -> None:
        self.assertAllowed(self.bash(f'mv "{self.main}/a', self.main))


class KnownGaps(HookCase):

    def test_a_shell_redirect_into_the_main_checkout_is_not_treated_as_a_write(self) -> None:
        self.assertAllowed(self.bash(f"echo hi > {self.main}/a", self.wt))


if __name__ == "__main__":
    unittest.main(verbosity=2)
