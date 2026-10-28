"""Exercise the registered vault sync hook commands against real git repositories."""

import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "hooks/hooks.json").read_text())
LEARN = "/vibe-wise:learn"
SESSION = "session-1"


def registered_command(event, mode):
    """Find the command the plugin registers for an event, as Claude Code runs it."""
    suffix = f"vault_sync.py\" {mode}"
    for entry in CONFIG["hooks"].get(event, []):
        for hook in entry["hooks"]:
            if hook["command"].endswith(suffix):
                return hook["command"]
    raise AssertionError(f"no {mode} command registered for {event}")


def git(*args, cwd):
    # Setup commands need a committer identity; the hook under test never does.
    # Ignore the user's git config so signing or hook setups can't break the suite.
    settings = ("-c", "user.name=Test", "-c", "user.email=test@example.com",
                "-c", "commit.gpgsign=false")
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
    subprocess.run(
        ("git", *settings, *args), cwd=cwd, check=True, capture_output=True, text=True,
        env=env,
    )


class VaultSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="vibe-wise-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.vault = self.root / "my vault"
        self.vault.mkdir()
        self.data = self.root / "plugin data"
        self.data.mkdir()
        self.home = self.root / "home"
        self.home.mkdir()
        self.repo = self.make_repo("project-one")
        self.remote = self.vault / "project-one"
        self.local = self.repo / ".vibe-wise"

    def make_repo(self, name):
        repo = self.root / name
        repo.mkdir()
        git("init", "-q", cwd=repo)
        git("commit", "-q", "--allow-empty", "-m", "init", cwd=repo)
        return repo

    def run_hook(self, event, mode, payload=None, raw=None, env=None, **fields):
        if raw is None:
            payload = {"session_id": SESSION, "cwd": str(self.repo), **(payload or {})}
            payload.update(fields)
            raw = json.dumps(payload)
        base = {
            "PATH": os.pathsep.join((
                str(Path(sys.executable).parent), os.defpath,
                str(Path(shutil.which("git")).parent),
            )),
            "CLAUDE_PLUGIN_ROOT": str(ROOT),
            "CLAUDE_PLUGIN_DATA": str(self.data),
            "CLAUDE_PLUGIN_OPTION_VAULT_PATH": str(self.vault),
            "HOME": str(self.home),
        }
        for key, value in (env or {}).items():
            if value is None:
                base.pop(key, None)
            else:
                base[key] = value
        result = subprocess.run(
            registered_command(event, mode), shell=True, input=raw, text=True,
            capture_output=True, timeout=30, env=base, cwd=self.root,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def pull(self, prompt=LEARN, **kwargs):
        self.run_hook("UserPromptSubmit", "pull", prompt=prompt, **kwargs)

    def resume(self, **kwargs):
        self.run_hook("SessionStart", "resume", source="resume", **kwargs)

    def push(self, **kwargs):
        self.run_hook("SessionEnd", "push", **kwargs)

    @property
    def marker(self):
        return self.data / "vault-sync" / "sessions" / SESSION

    @property
    def log(self):
        path = self.data / "vault-sync" / "sync.log"
        return path.read_text() if path.exists() else ""

    def write(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    @property
    def records(self):
        folder = self.data / "vault-sync" / "bases"
        return {path.name: json.loads(path.read_text())
                for path in folder.glob("*.json")} if folder.is_dir() else {}

    def mark(self, repo=None):
        self.marker.parent.mkdir(parents=True, exist_ok=True)
        self.marker.write_text(f"{repo or self.repo}\n")

    def test_registration(self):
        hooks = CONFIG["hooks"]
        first = hooks["SessionStart"][0]
        self.assertEqual(first["matcher"], "startup|resume|clear|compact|fork")
        self.assertEqual(first["hooks"], [{
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/session_start.py\"",
            "timeout": 5,
        }])
        script = "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/vault_sync.py\""
        self.assertEqual(hooks["SessionStart"][1], {"matcher": "resume", "hooks": [{
            "type": "command", "command": f"{script} resume", "timeout": 30,
        }]})
        self.assertEqual(hooks["UserPromptSubmit"], [{"hooks": [{
            "type": "command", "command": f"{script} pull", "timeout": 30,
        }]}])
        self.assertEqual(hooks["SessionEnd"], [{"hooks": [{
            "type": "command", "command": f"{script} push", "timeout": 30,
        }]}])
        self.assertEqual(len(hooks["SessionStart"]), 2)

    def test_learn_prompts_pull_and_mark_session(self):
        self.write(self.remote / "progress.md", "remote progress")
        self.write(self.remote / "topics" / "http.md", "nested note")
        for prompt in (LEARN, f"  {LEARN} some task", f"{LEARN}\nmore", f"\n\t{LEARN}\tx"):
            with self.subTest(prompt=prompt):
                shutil.rmtree(self.local, ignore_errors=True)
                self.marker.unlink(missing_ok=True)
                self.pull(prompt=prompt)
                self.assertEqual((self.local / "progress.md").read_text(), "remote progress")
                self.assertEqual((self.local / "topics/http.md").read_text(), "nested note")
                self.assertEqual(self.marker.read_text(), f"{self.repo}\n")
        self.assertIn("[pull] pulled", self.log)

    def test_learn_prompt_from_subdirectory_uses_toplevel(self):
        self.write(self.remote / "a.md", "a")
        nested = self.repo / "src" / "deep"
        nested.mkdir(parents=True)
        self.pull(cwd=str(nested))
        self.assertEqual((self.local / "a.md").read_text(), "a")
        self.assertEqual(self.marker.read_text(), f"{self.repo}\n")

    def test_other_prompts_do_nothing(self):
        self.write(self.remote / "a.md", "a")
        for prompt in ("hello", "/vibe-wise:learner", "/vibe-wise:reset", "",
                       "say /vibe-wise:learn", None, 42):
            with self.subTest(prompt=prompt):
                self.pull(prompt=prompt)
                self.assertFalse(self.marker.exists())
                self.assertFalse(self.local.exists())
        self.assertEqual(self.log, "")

    def test_push_without_marker_does_nothing(self):
        self.write(self.local / "a.md", "local")
        self.push()
        self.assertFalse(self.remote.exists())
        self.assertEqual(self.log, "")

    def test_unmarked_session_in_synced_repo_pushes(self):
        self.mark()
        self.write(self.local / "a.md", "v1")
        self.push()
        # Learning resumes on its own in a new session that never runs the learn prompt.
        self.write(self.local / "a.md", "resumed learning")
        (self.repo / "src").mkdir()
        self.push(session_id="no-learn-prompt", cwd=str(self.repo / "src"))
        self.assertEqual((self.remote / "a.md").read_text(), "resumed learning")

    def test_unpushed_local_edit_survives_next_learn(self):
        # Day 1: learn, take notes, end the session.
        self.pull(session_id="day-1")
        self.write(self.local / "progress.md", "day 1")
        self.push(session_id="day-1")
        self.assertEqual((self.remote / "progress.md").read_text(), "day 1")
        # Day 2: learning resumes without the learn prompt; the session dies unpushed.
        self.write(self.local / "progress.md", "day 2")
        # Day 3: the learn prompt must not bring day 1 back.
        self.pull(session_id="day-3")
        self.assertEqual((self.local / "progress.md").read_text(), "day 2")
        self.assertIn("(0 updated, 1 kept newer, 0 conflicts)", self.log)
        self.push(session_id="day-3")
        self.assertEqual((self.remote / "progress.md").read_text(), "day 2")

    def test_reset_in_unmarked_session_survives_next_learn(self):
        self.write(self.remote / "profile.md", "old profile")
        self.pull(session_id="first")
        self.push(session_id="first")
        # /vibe-wise:reset rewrites the profile in a session that never ran learn.
        self.write(self.local / "profile.md", "fresh profile")
        self.pull(session_id="second")
        self.assertEqual((self.local / "profile.md").read_text(), "fresh profile")

    def test_changes_on_both_sides_keep_destination(self):
        self.mark()
        self.write(self.remote / "a.md", "v1")
        self.resume()
        before = self.records
        self.assertEqual(len(before), 1)
        self.write(self.local / "a.md", "local edit")
        self.write(self.remote / "a.md", "vault edit")
        conflict = "conflict a.md: changed on both sides since last sync; kept"
        for _ in range(2):
            self.resume()
            self.assertEqual((self.local / "a.md").read_text(), "local edit")
        self.assertEqual(self.log.count(f"[resume] {conflict} local copy"), 2)
        self.assertIn("(0 updated, 0 kept newer, 1 conflicts)", self.log)
        self.push()
        self.assertEqual((self.remote / "a.md").read_text(), "vault edit")
        self.assertIn(f"[push] {conflict} vault copy", self.log)
        # The record still holds v1, so the next sync reports the conflict again.
        self.assertEqual(self.records, before)

    def test_vault_change_reaches_unchanged_local(self):
        self.mark()
        self.write(self.local / "a.md", "v1")
        self.push()
        self.write(self.remote / "a.md", "v2 from another computer")
        self.resume()
        self.assertEqual((self.local / "a.md").read_text(), "v2 from another computer")
        self.assertIn("[resume] pulled", self.log)
        self.assertIn("(1 updated, 0 kept newer, 0 conflicts)", self.log)

    def test_without_a_record_the_source_wins(self):
        self.mark()
        self.write(self.local / "a.md", "local")
        self.write(self.remote / "a.md", "vault")
        self.resume()
        self.assertEqual((self.local / "a.md").read_text(), "vault")
        [record] = self.records.values()
        self.assertEqual(record["remote"], str(self.remote))
        self.assertEqual(list(record["files"]), ["a.md"])
        # A record kept for another vault folder doesn't count as a last sync.
        other = self.root / "other vault"
        self.write(other / "project-one" / "a.md", "other vault")
        self.write(self.local / "a.md", "local again")
        self.resume(env={"CLAUDE_PLUGIN_OPTION_VAULT_PATH": str(other)})
        self.assertEqual((self.local / "a.md").read_text(), "other vault")

    def test_record_failures_are_logged_and_sync_continues(self):
        self.mark()
        self.write(self.remote / "a.md", "a")
        self.resume()
        [name] = self.records
        record = self.data / "vault-sync" / "bases" / name
        record.write_text("{")
        self.write(self.local / "a.md", "local")
        self.write(self.remote / "a.md", "b")
        self.resume()
        self.assertEqual((self.local / "a.md").read_text(), "b")
        self.assertIn("ignoring unreadable sync record", self.log)
        shutil.rmtree(record.parent)
        record.parent.write_text("not a directory")
        self.write(self.remote / "a.md", "c")
        self.resume()
        self.assertEqual((self.local / "a.md").read_text(), "c")
        self.assertIn("could not save sync record", self.log)
        self.assertEqual(self.log.count("[resume] pulled"), 3)

    def test_unreachable_vault_is_quiet_for_sessions_that_would_not_sync(self):
        missing = {"CLAUDE_PLUGIN_OPTION_VAULT_PATH": str(self.root / "not mounted")}
        self.write(self.local / "a.md", "a")
        self.pull(prompt="hello", env=missing)
        self.resume(env=missing)
        self.push(env=missing)
        self.assertEqual(self.log, "")

    def test_pulled_files_do_not_take_vault_permissions(self):
        mask = os.umask(0)
        os.umask(mask)
        self.mark()
        self.write(self.remote / "new.md", "new")
        self.write(self.remote / "old.md", "remote")
        self.write(self.local / "old.md", "local")
        # drvfs mounts report every file as 0o777.
        (self.remote / "new.md").chmod(0o777)
        (self.remote / "old.md").chmod(0o777)
        (self.local / "old.md").chmod(0o640)
        self.resume()
        self.assertEqual((self.local / "old.md").read_text(), "remote")
        self.assertEqual(stat.S_IMODE((self.local / "new.md").stat().st_mode), 0o666 & ~mask)
        self.assertEqual(stat.S_IMODE((self.local / "old.md").stat().st_mode), 0o640)

    def test_leftover_temporary_files_are_not_copied(self):
        self.mark()
        self.write(self.remote / ".vault-sync-abc123", "partial")
        self.write(self.remote / "sub" / ".vault-sync-x", "partial")
        self.write(self.remote / "a.md", "a")
        self.resume()
        self.assertEqual(sorted(p.relative_to(self.local).as_posix()
                                for p in self.local.rglob("*") if p.is_file()), ["a.md"])

    def test_push_with_marker_overwrites_and_adds(self):
        self.mark()
        self.write(self.local / "a.md", "new local")
        self.write(self.local / "sub" / "b.md", "added")
        self.write(self.remote / "a.md", "old remote")
        self.push()
        self.assertEqual((self.remote / "a.md").read_text(), "new local")
        self.assertEqual((self.remote / "sub/b.md").read_text(), "added")
        self.assertTrue(self.marker.exists())
        self.assertRegex(
            self.log, r"\[push\] pushed .+ \(2 updated, 0 kept newer, 0 conflicts\)")
        self.assertRegex(
            self.log.splitlines()[0],
            r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d[+-]\d\d:\d\d \[push\] ",
        )
        # A resumed session that ends again pushes again.
        self.write(self.local / "a.md", "third")
        self.push()
        self.assertEqual((self.remote / "a.md").read_text(), "third")

    def test_resume_without_marker_does_nothing(self):
        self.write(self.remote / "a.md", "remote")
        self.resume()
        self.assertFalse(self.local.exists())
        self.assertEqual(self.log, "")

    def test_resume_with_marker_pulls(self):
        self.mark()
        self.write(self.remote / "a.md", "remote")
        self.write(self.local / "a.md", "stale")
        self.resume()
        self.assertEqual((self.local / "a.md").read_text(), "remote")
        self.assertIn("[resume] pulled", self.log)

    def test_marker_pointing_at_missing_repo_is_logged(self):
        self.mark(self.root / "gone")
        self.resume()
        self.push()
        self.assertEqual(self.log.count("marked repo no longer resolvable"), 2)
        self.assertFalse(self.remote.exists())

    def test_nothing_is_deleted_in_either_direction(self):
        self.mark()
        self.write(self.local / "only-local.md", "L")
        self.write(self.remote / "only-remote.md", "R")
        self.resume()
        self.assertEqual((self.local / "only-local.md").read_text(), "L")
        self.assertEqual((self.local / "only-remote.md").read_text(), "R")
        (self.local / "only-remote.md").unlink()
        self.push()
        self.assertEqual((self.remote / "only-local.md").read_text(), "L")
        self.assertEqual((self.remote / "only-remote.md").read_text(), "R")

    def test_identical_files_are_not_rewritten(self):
        self.mark()
        self.write(self.remote / "a.md", "same")
        self.write(self.local / "a.md", "same")
        os.utime(self.local / "a.md", (1_000_000, 1_000_000))
        self.resume()
        self.assertEqual((self.local / "a.md").stat().st_mtime, 1_000_000)
        self.assertIn("(0 updated, 0 kept newer, 0 conflicts)", self.log)
        # Differing content with the same size and mtime is still detected.
        self.write(self.remote / "a.md", "diff")
        os.utime(self.remote / "a.md", (1_000_000, 1_000_000))
        self.resume()
        self.assertEqual((self.local / "a.md").read_text(), "diff")

    def test_no_temporary_files_are_left_behind(self):
        self.mark()
        self.write(self.local / "a.md", "x")
        self.write(self.remote / "a.md", "y")
        self.push()
        self.assertEqual([p.name for p in self.remote.iterdir()], ["a.md"])

    def test_worktree_uses_main_repository_vault_folder(self):
        worktree = self.root / "linked-worktree"
        git("worktree", "add", "-q", str(worktree), "-b", "feature", cwd=self.repo)
        self.write(self.remote / "a.md", "shared")
        self.pull(cwd=str(worktree))
        self.assertEqual((worktree / ".vibe-wise/a.md").read_text(), "shared")
        self.assertFalse((self.vault / "linked-worktree").exists())
        self.assertEqual(self.marker.read_text(), f"{worktree}\n")
        self.write(worktree / ".vibe-wise/b.md", "from worktree")
        self.push(cwd=str(worktree))
        self.assertEqual((self.remote / "b.md").read_text(), "from worktree")

    def test_desktop_ini_is_never_copied(self):
        self.mark()
        self.write(self.remote / "desktop.ini", "r")
        self.write(self.remote / "sub" / "Desktop.INI", "r")
        self.write(self.remote / "a.md", "a")
        self.write(self.local / "desktop.ini", "l")
        self.resume()
        self.assertEqual(sorted(p.name for p in self.local.rglob("*") if p.is_file()),
                         ["a.md", "desktop.ini"])
        self.assertEqual((self.local / "desktop.ini").read_text(), "l")
        self.push()
        self.assertEqual((self.remote / "desktop.ini").read_text(), "r")

    def test_symlinked_local_state_is_refused(self):
        outside = self.root / "outside"
        outside.mkdir()
        self.local.symlink_to(outside, target_is_directory=True)
        self.write(self.remote / "a.md", "a")
        self.pull()
        self.assertEqual(list(outside.iterdir()), [])
        self.assertIn("refusing symlinked state dir", self.log)
        self.assertFalse(self.marker.exists())

    def test_symlinked_remote_state_is_refused(self):
        outside = self.root / "outside"
        outside.mkdir()
        self.remote.symlink_to(outside, target_is_directory=True)
        self.mark()
        self.write(self.local / "a.md", "a")
        self.push()
        self.assertEqual(list(outside.iterdir()), [])
        self.assertIn("refusing symlinked state dir", self.log)

    def test_symlinks_inside_state_are_skipped(self):
        self.mark()
        outside = self.root / "outside"
        outside.mkdir()
        self.write(outside / "secret.md", "secret")
        self.remote.mkdir()
        (self.remote / "link.md").symlink_to(outside / "secret.md")
        (self.remote / "linkdir").symlink_to(outside, target_is_directory=True)
        self.write(self.remote / "a.md", "a")
        self.resume()
        self.assertEqual([p.name for p in self.local.iterdir()], ["a.md"])

    def test_never_writes_through_destination_symlinks(self):
        self.mark()
        outside = self.root / "outside"
        outside.mkdir()
        self.write(outside / "keep.md", "original")
        self.write(self.remote / "dir" / "keep.md", "remote")
        self.write(self.remote / "file.md", "remote")
        self.local.mkdir()
        (self.local / "dir").symlink_to(outside, target_is_directory=True)
        (self.local / "file.md").symlink_to(outside / "keep.md")
        self.resume()
        self.assertEqual((outside / "keep.md").read_text(), "original")
        self.assertEqual([p.name for p in outside.iterdir()], ["keep.md"])
        self.assertIn("skipped dir/keep.md", self.log)
        self.assertIn("skipped file.md", self.log)

    def test_directory_in_place_of_file_is_skipped(self):
        self.mark()
        self.write(self.remote / "a.md", "a")
        self.write(self.remote / "b.md", "b")
        (self.local / "a.md").mkdir(parents=True)
        self.resume()
        self.assertTrue((self.local / "a.md").is_dir())
        self.assertEqual((self.local / "b.md").read_text(), "b")
        self.assertIn("skipped a.md", self.log)

    def test_missing_vault_directory_is_logged(self):
        missing = self.root / "not mounted"
        self.write(self.local / "a.md", "a")
        self.mark()
        self.push(env={"CLAUDE_PLUGIN_OPTION_VAULT_PATH": str(missing)})
        self.assertFalse(missing.exists())
        self.assertIn(f"vault path does not exist: {missing}", self.log)

    def test_relative_vault_path_is_rejected(self):
        self.mark()
        self.write(self.local / "a.md", "a")
        self.push(env={"CLAUDE_PLUGIN_OPTION_VAULT_PATH": "my vault"})
        self.assertIn("vault path does not exist: my vault", self.log)
        self.assertFalse((self.root / "my vault" / "project-one").exists())

    def test_tilde_in_vault_path_is_expanded(self):
        (self.home / "Drive").mkdir()
        self.write(self.local / "a.md", "a")
        self.mark()
        self.push(env={"CLAUDE_PLUGIN_OPTION_VAULT_PATH": "~/Drive"})
        self.assertEqual((self.home / "Drive/project-one/a.md").read_text(), "a")

    def test_symlinked_vault_root_is_allowed(self):
        link = self.root / "vault-link"
        link.symlink_to(self.vault, target_is_directory=True)
        self.mark()
        self.write(self.local / "a.md", "a")
        self.push(env={"CLAUDE_PLUGIN_OPTION_VAULT_PATH": str(link)})
        self.assertEqual((self.remote / "a.md").read_text(), "a")

    def test_unset_or_blank_configuration_does_nothing(self):
        self.mark()
        self.write(self.local / "a.md", "a")
        self.write(self.remote / "b.md", "b")
        snapshot = sorted(p.relative_to(self.root) for p in self.root.rglob("*"))
        for env in ({"CLAUDE_PLUGIN_OPTION_VAULT_PATH": None},
                    {"CLAUDE_PLUGIN_OPTION_VAULT_PATH": ""},
                    {"CLAUDE_PLUGIN_OPTION_VAULT_PATH": " \t "},
                    {"CLAUDE_PLUGIN_DATA": None},
                    {"CLAUDE_PLUGIN_DATA": ""}):
            with self.subTest(env=env):
                self.push(env=env)
                self.resume(env=env)
                self.pull(env=env)
                self.assertEqual(
                    snapshot, sorted(p.relative_to(self.root) for p in self.root.rglob("*")))
        self.assertEqual(self.log, "")

    def test_data_directory_is_created_on_first_use(self):
        shutil.rmtree(self.data)
        self.write(self.remote / "a.md", "a")
        self.pull()
        self.assertTrue(self.marker.exists())
        self.assertEqual((self.local / "a.md").read_text(), "a")

    def test_invalid_session_ids_are_rejected(self):
        self.write(self.remote / "a.md", "a")
        for session in ("../x", "a/b", "", "bad id", "x\ny", None, 7, ["a"]):
            with self.subTest(session=session):
                self.pull(session_id=session)
                self.resume(session_id=session)
                self.push(session_id=session)
                self.assertFalse(self.local.exists())
        self.assertEqual(list((self.data / "vault-sync/sessions").iterdir()), [])
        self.assertFalse((self.data / "vault-sync/x").exists())
        self.assertIn("invalid session_id", self.log)

    def test_missing_session_id_is_rejected(self):
        self.write(self.remote / "a.md", "a")
        self.run_hook("UserPromptSubmit", "pull",
                      raw=json.dumps({"prompt": LEARN, "cwd": str(self.repo)}))
        self.assertFalse(self.local.exists())
        self.assertIn("invalid session_id", self.log)

    def test_malformed_input_does_not_crash_or_copy(self):
        self.mark()
        self.write(self.remote / "a.md", "a")
        for mode, event in (("pull", "UserPromptSubmit"), ("resume", "SessionStart"),
                            ("push", "SessionEnd")):
            for raw in ("", "{", "[]", "null", "42", '"text"', "\x00", "{" * 5000):
                with self.subTest(mode=mode, raw=raw[:10]):
                    self.run_hook(event, mode, raw=raw)
        self.assertFalse(self.local.exists())

    def test_invalid_cwd_is_logged(self):
        self.write(self.remote / "a.md", "a")
        for cwd in ("relative/dir", None, 5):
            with self.subTest(cwd=cwd):
                self.pull(cwd=cwd)
        self.assertFalse(self.local.exists())
        self.assertFalse(self.marker.exists())

    def test_cwd_outside_git_repository_is_logged(self):
        plain = self.root / "plain"
        plain.mkdir()
        self.write(self.remote / "a.md", "a")
        self.pull(cwd=str(plain))
        self.assertIn("cwd is not a git repo", self.log)
        self.assertEqual(list(plain.iterdir()), [])
        self.assertFalse(self.marker.exists())
        self.pull(cwd=str(self.root / "does-not-exist"))
        self.assertEqual(self.log.count("cwd is not a git repo"), 2)

    def test_missing_git_is_logged_and_silent(self):
        self.write(self.remote / "a.md", "a")
        # A PATH holding only python stands in for a machine without git.
        bin_dir = self.root / "python-only-bin"
        bin_dir.mkdir()
        (bin_dir / "python3").symlink_to(sys.executable)
        self.pull(env={"PATH": str(bin_dir)})
        self.assertIn("cwd is not a git repo", self.log)
        self.assertFalse(self.local.exists())

    def test_legacy_state_directory_is_used_when_new_one_is_absent(self):
        legacy = self.repo / ".sensible-vibes"
        self.write(self.remote / "a.md", "remote")
        self.write(legacy / "old.md", "old")
        self.pull()
        self.assertEqual((legacy / "a.md").read_text(), "remote")
        self.assertFalse(self.local.exists())
        self.push()
        self.assertEqual((self.remote / "old.md").read_text(), "old")

    def test_new_state_directory_wins_over_legacy(self):
        self.write(self.remote / "a.md", "remote")
        self.local.mkdir()
        (self.repo / ".sensible-vibes").mkdir()
        self.pull()
        self.assertEqual((self.local / "a.md").read_text(), "remote")
        self.assertEqual(list((self.repo / ".sensible-vibes").iterdir()), [])

    def test_dangling_new_state_symlink_does_not_fall_back_to_legacy(self):
        (self.repo / ".sensible-vibes").mkdir()
        self.local.symlink_to(self.root / "missing", target_is_directory=True)
        self.write(self.remote / "a.md", "remote")
        self.pull()
        self.assertEqual(list((self.repo / ".sensible-vibes").iterdir()), [])
        self.assertIn("refusing symlinked state dir", self.log)

    def test_missing_sources_are_logged(self):
        self.mark()
        self.resume()
        self.assertIn("no vault folder yet for project-one, skipping pull", self.log)
        self.push()
        self.assertIn(f"no local state in {self.repo}, skipping push", self.log)
        self.assertFalse(self.remote.exists())
        self.assertFalse(self.local.exists())

    def test_unknown_mode_is_logged(self):
        # No command is registered for a bogus mode, so invoke the script directly.
        result = subprocess.run(
            [sys.executable, str(ROOT / "hooks/vault_sync.py"), "bogus"],
            input=json.dumps({"session_id": SESSION}),
            text=True, capture_output=True, timeout=30, env={
                "CLAUDE_PLUGIN_DATA": str(self.data),
                "CLAUDE_PLUGIN_OPTION_VAULT_PATH": str(self.vault),
            },
        )
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        self.assertIn("[bogus] unknown mode", self.log)

    def test_unwritable_data_directory_still_exits_cleanly(self):
        blocker = self.root / "blocker"
        blocker.write_text("a file, not a directory")
        self.write(self.remote / "a.md", "a")
        self.pull(env={"CLAUDE_PLUGIN_DATA": str(blocker)})
        self.assertFalse(self.local.exists())


if __name__ == "__main__":
    unittest.main()
