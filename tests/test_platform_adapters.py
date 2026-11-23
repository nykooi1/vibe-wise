import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


antigravity = load_module(
    "vibe_wise_antigravity",
    ROOT / "hooks/session_start_antigravity.py",
)
copilot = load_module(
    "vibe_wise_copilot",
    ROOT / "hooks/session_start_copilot.py",
)


class PlatformAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="vibe-wise-platform-")
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name).resolve() / "project"
        self.project.mkdir()
        (self.project / ".git").mkdir()
        self.state = self.project / ".vibe-wise"
        self.state.mkdir()
        (self.state / "profile.md").write_text(
            "# Learner Profile\nLearning mode: active\nOnboarding: complete\n",
            encoding="utf-8",
        )
        (self.state / "project-map.md").write_text(
            "# Project Map\nCLI -> service\n",
            encoding="utf-8",
        )
        (self.state / "progress.md").write_text(
            "# Learning Progress\n## Storage\nPending implementation approval\n",
            encoding="utf-8",
        )

    def test_antigravity_injects_start_context_and_uses_workspace_paths(self):
        result = antigravity.restore({"workspacePaths": [str(self.project)]})
        context = result["injectSteps"][0]["systemMessage"]["systemMessage"]
        self.assertIn(str(self.state), context)
        self.assertIn("Read profile.md and project-map.md", context)
        self.assertIn("not implementation approval", context)

    def test_antigravity_stays_quiet_without_active_profile(self):
        (self.state / "profile.md").write_text(
            "Learning mode: paused\n",
            encoding="utf-8",
        )
        self.assertIsNone(antigravity.restore({"workspacePaths": [str(self.project)]}))
        self.assertIsNone(antigravity.restore({"workspacePaths": []}))

    def test_copilot_additional_context_contract(self):
        result = copilot.restore({"cwd": str(self.project), "source": "startup"})
        self.assertIn(str(self.state), result["additionalContext"])
        self.assertIn("pending decisions", result["additionalContext"])

    def test_copilot_stays_quiet_when_profile_is_missing_or_paused(self):
        (self.state / "profile.md").unlink()
        self.assertIsNone(copilot.restore({"cwd": str(self.project)}))
        (self.state / "profile.md").write_text("Learning mode: paused\n")
        self.assertIsNone(copilot.restore({"cwd": str(self.project)}))

    def test_adapter_commands_execute_with_real_json_stdin(self):
        for script, payload, key in (
            (
                "hooks/session_start_antigravity.py",
                {"workspacePaths": [str(self.project)]},
                "injectSteps",
            ),
            (
                "hooks/session_start_copilot.py",
                {"cwd": str(self.project), "source": "startup"},
                "additionalContext",
            ),
        ):
            with self.subTest(script=script):
                result = subprocess.run(
                    [sys.executable, "-B", str(ROOT / script)],
                    input=json.dumps(payload),
                    text=True,
                    capture_output=True,
                    timeout=5,
                    check=True,
                )
                output = json.loads(result.stdout)
                if key == "injectSteps":
                    self.assertIn("injectSteps", output)
                else:
                    self.assertIn("additionalContext", output)

    def test_host_manifests_and_hook_configs_are_valid_json(self):
        for path in (
            ".antigravity-plugin/plugin.json",
            "hooks.json",
            "plugin.json",
            "com.github.copilot/hooks/hooks.json",
            ".github/plugin/marketplace.json",
        ):
            with self.subTest(path=path):
                json.loads((ROOT / path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
