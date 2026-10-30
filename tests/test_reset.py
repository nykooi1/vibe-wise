"""Reset only confirmed project notes, preserving recoverable originals."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/reset/reset.py"
spec = importlib.util.spec_from_file_location("vibe_wise_reset", SCRIPT)
reset_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reset_module)


class ResetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="vibe-wise-reset-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.project = self.root / "project with spaces"
        self.project.mkdir()
        (self.project / ".git").mkdir()

    def notes(self, project=None, legacy=False):
        state = (project or self.project) / (".sensible-vibes" if legacy else ".vibe-wise")
        state.mkdir()
        originals = {
            "profile.md": b"Learning mode: paused\nOnboarding: complete\nAdvanced\n",
            "progress.md": b"## Pending decision\nAwaiting implementation approval\n",
            "project-map.md": b"# Project Map\nCLI -> service -> SQLite\n",
        }
        for name, data in originals.items():
            (state / name).write_bytes(data)
        return state, originals

    def preview(self, cwd=None):
        return reset_module.reset(cwd or self.project)

    def confirm(self, cwd=None):
        preview = self.preview(cwd)
        return reset_module.reset(cwd or self.project, preview["confirmation"])

    def assert_originals(self, state, originals):
        self.assertEqual(originals, {name: (state / name).read_bytes() for name in originals})

    def test_preview_and_cancel_leave_notes_untouched(self):
        state, originals = self.notes()
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--cwd", str(self.project)],
            capture_output=True, text=True, check=True,
        )
        preview = json.loads(result.stdout)
        self.assertEqual(preview["status"], "preview")
        self.assertEqual(preview["state"], str(state))
        self.assertEqual(preview["project"], str(self.project))
        self.assert_originals(state, originals)
        self.assertEqual(set(p.name for p in state.iterdir()), set(originals))
        # Cancel means no confirmed command is run; preview has no side effects.

    def test_reset_backs_up_only_notes_and_restarts_onboarding(self):
        state, originals = self.notes()
        (self.project / "app.py").write_text("important source\n")
        (state / "custom.md").write_text("keep this\n")
        sibling = self.root / "another-project"
        sibling.mkdir()
        other, other_originals = self.notes(sibling)
        result = self.confirm()
        self.assertEqual(result["status"], "reset")
        backup = Path(result["backup"])
        self.assertEqual(backup.parent, state / "backups")
        self.assert_originals(backup, originals)
        self.assertEqual(set(p.name for p in backup.iterdir()), set(originals))
        profile = (state / "profile.md").read_text()
        self.assertIn("Learning mode: active", profile)
        self.assertIn("Onboarding: incomplete", profile)
        self.assertIn("Onboarding reset: pending", profile)
        self.assertNotIn("Advanced", profile)
        self.assertNotIn("Pending decision", (state / "progress.md").read_text())
        self.assertNotIn("SQLite", (state / "project-map.md").read_text())
        self.assertEqual((self.project / "app.py").read_text(), "important source\n")
        self.assertEqual((state / "custom.md").read_text(), "keep this\n")
        self.assert_originals(other, other_originals)
        self.assertTrue((self.project / ".git").is_dir())
        hook = subprocess.run(
            [sys.executable, "-B", str(ROOT / "hooks/session_start.py")],
            input=json.dumps({"hook_event_name": "SessionStart", "source": "compact",
                              "cwd": str(self.project)}),
            text=True, capture_output=True, check=True,
        )
        context = json.loads(hook.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn(str(state), context)
        self.assertIn("Read profile.md and project-map.md", context)
        self.assertIn("If onboarding is incomplete", context)
        self.assertNotIn("Awaiting implementation approval", context)

    def test_nested_directory_and_legacy_notes(self):
        state, originals = self.notes(legacy=True)
        nested = self.project / "src"
        nested.mkdir()
        result = self.confirm(nested)
        self.assertEqual(result["state"], str(state))
        self.assert_originals(Path(result["backup"]), originals)
        self.assertFalse((self.project / ".vibe-wise").exists())

    def test_preferred_state_resets_without_touching_legacy(self):
        state, _ = self.notes()
        legacy, originals = self.notes(legacy=True)
        self.assertEqual(self.confirm()["state"], str(state))
        self.assert_originals(legacy, originals)

    def test_nearest_state_and_worktree_boundaries(self):
        parent_state, originals = self.notes()
        nested = self.project / "package"
        nested.mkdir()
        state, _ = self.notes(nested, legacy=True)
        self.assertEqual(self.confirm(nested)["state"], str(state))
        self.assert_originals(parent_state, originals)
        for name, worktree in (("nested-repo", False), ("worktree", True)):
            child = self.project / name
            child.mkdir()
            if worktree:
                (child / ".git").write_text("gitdir: /another/repo/.git/worktrees/test")
            else:
                (child / ".git").mkdir()
            self.assertEqual(self.preview(child)["status"], "no_notes")

    def test_no_git_folder_never_resets_parent_notes(self):
        parent = self.root / "documents"
        parent.mkdir()
        state, originals = self.notes(parent)
        plain = parent / "plain-project"
        plain.mkdir()
        self.assertEqual(self.preview(plain)["status"], "no_notes")
        self.assert_originals(state, originals)

    def test_no_state_and_empty_state_do_not_create_files(self):
        self.assertEqual(self.preview()["status"], "no_notes")
        self.assertEqual(list(self.project.iterdir()), [self.project / ".git"])
        state = self.project / ".vibe-wise"
        state.mkdir()
        self.assertEqual(self.preview()["status"], "no_notes")
        self.assertEqual(list(state.iterdir()), [])

    def test_partial_state_and_repeated_resets_preserve_each_backup(self):
        state, originals = self.notes()
        (state / "progress.md").unlink()
        (state / "project-map.md").unlink()
        first = Path(self.confirm()["backup"])
        self.assertEqual(list(first.iterdir()), [first / "profile.md"])
        self.assertEqual((first / "profile.md").read_bytes(), originals["profile.md"])
        second = Path(self.confirm()["backup"])
        self.assertNotEqual(first, second)
        self.assertEqual((first / "profile.md").read_bytes(), originals["profile.md"])

    def test_stale_confirmation_rejected_before_writes(self):
        state, _ = self.notes()
        token = self.preview()["confirmation"]
        (state / "progress.md").write_text("new understanding\n")
        with self.assertRaisesRegex(ValueError, "changed"):
            reset_module.reset(self.project, token)
        self.assertEqual((state / "progress.md").read_text(), "new understanding\n")
        self.assertFalse((state / "backups").exists())

    def test_confirmation_cannot_target_a_different_project(self):
        self.notes()
        other = self.root / "another-project"
        other.mkdir()
        state, originals = self.notes(other)
        with self.assertRaisesRegex(ValueError, "changed"):
            reset_module.reset(other, self.preview()["confirmation"])
        self.assert_originals(state, originals)
        self.assertFalse((state / "backups").exists())

    def test_symlinked_state_is_not_followed(self):
        outside = self.root / "outside"
        outside.mkdir()
        target, originals = self.notes(outside)
        (self.project / ".vibe-wise").symlink_to(target, target_is_directory=True)
        self.assertEqual(self.preview()["status"], "no_notes")
        self.assert_originals(target, originals)

    def test_non_regular_notes_rejected(self):
        state, _ = self.notes()
        path = state / "profile.md"
        path.unlink()
        path.symlink_to(state / "progress.md")
        with self.assertRaisesRegex(ValueError, "non-regular"):
            self.preview()
        path.unlink()
        path.mkdir()
        with self.assertRaisesRegex(ValueError, "non-regular"):
            self.preview()
        self.assertFalse((state / "backups").exists())

    def test_symlinked_backup_directory_rejected_before_notes_change(self):
        state, originals = self.notes()
        outside = self.root / "outside"
        outside.mkdir()
        (state / "backups").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "Backup path"):
            self.confirm()
        self.assert_originals(state, originals)
        self.assertEqual(list(outside.iterdir()), [])

    def test_backup_failure_does_not_modify_active_notes(self):
        state, originals = self.notes()
        original_write = Path.write_bytes

        def fail_backup(path, data):
            if path.name == "progress.md":
                raise OSError("simulated disk failure")
            return original_write(path, data)

        with patch.object(Path, "write_bytes", fail_backup):
            with self.assertRaisesRegex(ValueError, "did not complete"):
                self.confirm()
        self.assert_originals(state, originals)

    def test_replacement_failure_keeps_complete_backup_and_reports_failure(self):
        state, originals = self.notes()
        replace = reset_module.os.replace

        def fail_replace(source, target):
            if target.name == "progress.md":
                raise OSError("simulated write failure")
            replace(source, target)

        with patch.object(reset_module.os, "replace", fail_replace):
            with self.assertRaisesRegex(ValueError, "Backup location"):
                self.confirm()
        backups = list((state / "backups").iterdir())
        self.assertEqual(len(backups), 1)
        self.assert_originals(backups[0], originals)


if __name__ == "__main__":
    unittest.main()
