"""Hermes adapter contract tests; real-loader validation is documented separately."""

import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("vibewise_hermes", ROOT / ".hermes-plugin" / "__init__.py")
plugin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plugin)


class RecordingContext:
    def __init__(self):
        self.skills = {}
        self.hooks = {}

    def register_skill(self, name, path, description=""):
        self.skills[name] = (path, description)

    def register_hook(self, name, callback):
        self.hooks[name] = callback


class HermesTests(unittest.TestCase):
    def test_registration_resolves_guides_independently_of_cwd(self):
        ctx = RecordingContext()
        with patch("os.getcwd", side_effect=AssertionError("No process cwd")):
            plugin.register(ctx)
        self.assertEqual(set(ctx.skills), {"learn", "reset"})
        for name, (path, description) in ctx.skills.items():
            self.assertEqual(path, ROOT / "skills" / name / "SKILL.md")
            self.assertTrue(path.is_file())
            self.assertTrue(description)
        self.assertEqual(set(ctx.hooks), {"pre_llm_call"})

    def test_every_turn_restores_without_reading_host_notes(self):
        with patch.object(Path, "open", side_effect=AssertionError("No host reads")):
            first = plugin.restore_context(session_id="a", is_first_turn=True)
            resumed = plugin.restore_context(session_id="a", is_first_turn=False,
                                             future_payload_field=True)
            other = plugin.restore_context(session_id="b", platform="telegram")
        self.assertEqual(first, resumed)
        self.assertEqual(first, other)
        self.assertLess(len(first["context"]), 3000)

    def test_delegated_sessions_do_not_enter_learning(self):
        self.assertIsNone(plugin.restore_context(parent_session_id="parent"))
        self.assertIsNotNone(plugin.restore_context(parent_session_id=""))


if __name__ == "__main__":
    unittest.main()
