"""Regression checks for learning-mode parsing and session restore."""

import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "vibe_wise_session_start", ROOT / "hooks" / "session_start.py"
)
HOOK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HOOK)


class LearningModeValidationTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="vibe-wise-mode-")
        self.addCleanup(tmp.cleanup)
        self.project = Path(tmp.name) / "project"
        self.project.mkdir()
        (self.project / ".git").mkdir()
        self.notes = self.project / ".vibe-wise"
        self.notes.mkdir()
        self.profile = self.notes / "profile.md"

    def write_profile(self, contents):
        self.profile.write_text(contents, encoding="utf-8")
        return HOOK.profile_is_active(self.profile)

    def test_explicit_modes(self):
        cases = {
            "active": True,
            "ACTIVE": True,
            "paused": False,
            "inactive": False,
            "disabled": False,
            "pausde": False,
            "active # typo": False,
            "": False,
        }
        for mode, expected in cases.items():
            with self.subTest(mode=mode):
                self.assertEqual(
                    self.write_profile(f"# Learner Profile\nLearning mode: {mode}\n"),
                    expected,
                )

    def test_indented_paused_mode(self):
        self.assertFalse(self.write_profile("# Profile\n  Learning mode: paused\n"))

    def test_legacy_profile_without_mode_is_compatible(self):
        self.assertTrue(self.write_profile("# Profile\nExperience: Beginner\n"))

    def test_invalid_mode_does_not_restore_session(self):
        self.write_profile("Learning mode: inactive\n")
        self.assertIsNone(HOOK.restore({
            "hook_event_name": "SessionStart", "cwd": str(self.project)
        }))


if __name__ == "__main__":
    unittest.main()
