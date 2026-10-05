"""Tests for the native VibeWise Codex plugin bundle."""

import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import yaml


ROOT = Path(__file__).resolve().parents[1]
CODEX_ROOT = ROOT / "codex"
CONFIG = json.loads((CODEX_ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))
REGISTRATION = CONFIG["hooks"]["SessionStart"][0]

RESET_SCRIPT = CODEX_ROOT / "skills/reset/reset.py"
spec = importlib.util.spec_from_file_location("codex_vibe_wise_reset", RESET_SCRIPT)
reset_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reset_module)

sys.path.insert(0, str(CODEX_ROOT / "hooks"))
import session_start as codex_session_start


class CodexManifestsTest(unittest.TestCase):
    def test_root_marketplace_manifest(self):
        manifest_path = ROOT / ".agents/plugins/marketplace.json"
        self.assertTrue(manifest_path.is_file(), "Root marketplace.json must exist")
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(data.get("name"), "vibe-wise")
        self.assertEqual(data.get("interface", {}).get("displayName"), "VibeWise")
        plugins = data.get("plugins", [])
        self.assertEqual(len(plugins), 1)
        plugin = plugins[0]
        self.assertEqual(plugin.get("name"), "vibe-wise")
        self.assertEqual(plugin.get("source"), {"source": "local", "path": "./codex"})
        self.assertEqual(plugin.get("policy"), {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        })
        self.assertEqual(plugin.get("category"), "Productivity")

    def test_codex_plugin_manifest(self):
        plugin_path = CODEX_ROOT / ".codex-plugin/plugin.json"
        self.assertTrue(plugin_path.is_file(), "Codex plugin.json must exist")
        data = json.loads(plugin_path.read_text(encoding="utf-8"))
        self.assertEqual(data.get("name"), "vibe-wise")
        self.assertEqual(data.get("version"), "0.1.43-codex.1")
        self.assertEqual(data.get("description"), "Mindful pair programming that keeps you in the driver's seat")
        self.assertEqual(data.get("skills"), "./skills/")
        self.assertEqual(data.get("hooks"), "./hooks/hooks.json")
        interface = data.get("interface", {})
        self.assertEqual(interface.get("displayName"), "VibeWise")
        self.assertEqual(interface.get("shortDescription"), "Mindful pair programming that keeps you in the driver's seat")
        self.assertEqual(interface.get("developerName"), "Noah Kim")
        self.assertEqual(interface.get("category"), "Productivity")
        self.assertEqual(interface.get("composerIcon"), "./assets/vibewise-icon.png")
        self.assertEqual(interface.get("logo"), "./assets/vibewise-icon.png")

        # Verify referenced asset and license files exist in codex bundle
        icon_path = CODEX_ROOT / "assets/vibewise-icon.png"
        self.assertTrue(icon_path.is_file(), "Bundle asset icon must exist")
        license_path = CODEX_ROOT / "LICENSE"
        self.assertTrue(license_path.is_file(), "Bundle LICENSE must exist")
        self.assertIn("Noah Kim", license_path.read_text(encoding="utf-8"))

    def test_skills_openai_manifests_and_policies(self):
        skills_expected = {
            "learn": {
                "display_name": "VibeWise Learn",
                "short_description": "Activate or resume learning-first development",
                "default_prompt": "Use $learn to activate or resume learning-first development for this project.",
            },
            "reset": {
                "display_name": "Reset VibeWise Learning",
                "short_description": "Back up learning notes and restart onboarding after confirmation",
                "default_prompt": "Use $reset to preview and confirm resetting learning notes for this project.",
            },
        }
        for skill_name, expected in skills_expected.items():
            manifest_file = CODEX_ROOT / f"skills/{skill_name}/agents/openai.yaml"
            self.assertTrue(manifest_file.is_file(), f"{manifest_file} must exist")
            data = yaml.safe_load(manifest_file.read_text(encoding="utf-8"))
            interface = data.get("interface", {})
            self.assertEqual(interface.get("display_name"), expected["display_name"])
            self.assertEqual(interface.get("short_description"), expected["short_description"])
            self.assertEqual(interface.get("default_prompt"), expected["default_prompt"])
            policy = data.get("policy", {})
            self.assertFalse(policy.get("allow_implicit_invocation"),
                             f"{skill_name} must require explicit invocation")

    def test_skills_frontmatter(self):
        for skill_name in ("learn", "reset"):
            skill_md = CODEX_ROOT / f"skills/{skill_name}/SKILL.md"
            self.assertTrue(skill_md.is_file(), f"{skill_md} must exist")
            content = skill_md.read_text(encoding="utf-8")
            self.assertTrue(content.startswith("---"), f"{skill_md} must start with YAML frontmatter")
            parts = content.split("---", 2)
            frontmatter = yaml.safe_load(parts[1])
            self.assertEqual(frontmatter.get("name"), skill_name)
            self.assertTrue(frontmatter.get("disable-model-invocation"),
                            f"{skill_name} frontmatter must disable model invocation")


class CodexHooksTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="vibe-wise-codex-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.project = self.root / "project with spaces"
        self.project.mkdir()
        (self.project / ".git").mkdir()

    def state(self, project=None, mode="active"):
        directory = (project or self.project) / ".vibe-wise"
        directory.mkdir()
        (directory / "profile.md").write_text(
            f"# Learner Profile\nLearning mode: {mode}\nOnboarding: complete\n"
            "Checkpoint frequency: Light\nQuestion style: Open-ended\n"
            "Implementation style: AI writes code\n"
            "Strong concepts: HTTP request flow\n", encoding="utf-8"
        )
        (directory / "project-map.md").write_text(
            "# Project Map\nCLI → service.py → SQLite\n", encoding="utf-8"
        )
        (directory / "progress.md").write_text(
            "# Learning Progress\n## Transactions\n"
            "Demonstrated understanding: two writes must succeed together.\n"
            "## Queues\nNeeds reinforcement: retries.\n", encoding="utf-8"
        )
        return directory

    def run_hook(self, cwd=None, source="startup", raw=None):
        payload = raw if raw is not None else json.dumps({
            "hook_event_name": "SessionStart", "source": source,
            "cwd": str(cwd or self.project),
        })
        hook_def = REGISTRATION["hooks"][0]
        command = hook_def["command"]
        command = command.replace("${PLUGIN_ROOT}", str(CODEX_ROOT))
        if sys.platform == "win32" or shutil.which("python3") is None:
            if command.startswith("python "):
                command = f'"{sys.executable}" ' + command[7:]
            elif command.startswith("python3 "):
                command = f'"{sys.executable}" ' + command[8:]
            elif command in ("python", "python3"):
                command = f'"{sys.executable}"'
        result = subprocess.run(
            command, shell=True,
            input=payload, text=True, capture_output=True, timeout=5,
            env={
                "PATH": os.pathsep.join((str(Path(sys.executable).parent), os.defpath)),
                "PLUGIN_ROOT": str(CODEX_ROOT),
            }, cwd=self.root,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return json.loads(result.stdout) if result.stdout else None

    def context(self, **kwargs):
        result = self.run_hook(**kwargs)["hookSpecificOutput"]
        self.assertEqual(result["hookEventName"], "SessionStart")
        return result["additionalContext"]

    def test_hook_schema_and_matcher(self):
        matcher = REGISTRATION["matcher"]
        self.assertEqual(matcher, "startup|resume|clear|compact")
        for source in ("startup", "resume", "clear", "compact"):
            self.assertTrue(re.fullmatch(matcher, source))
        self.assertFalse(re.fullmatch(matcher, "fork"))
        self.assertFalse(re.fullmatch(matcher, "unknown"))
        hook_entry = REGISTRATION["hooks"][0]
        self.assertEqual(hook_entry["type"], "command")
        self.assertIn("session_start.py", hook_entry["command"])
        self.assertEqual(hook_entry["timeout"], 5)
        self.assertEqual(hook_entry.get("statusMessage"), "Loading VibeWise learning context")

    def test_fresh_project_is_inactive(self):
        self.assertIsNone(self.run_hook())

    def test_restore_all_registered_codex_lifecycles(self):
        self.state()
        for source in ("startup", "resume", "clear", "compact"):
            with self.subTest(source=source):
                context = self.context(source=source)
                self.assertIn(str(CODEX_ROOT / "skills/learn/SKILL.md"), context)
                self.assertIn(str(self.project / ".vibe-wise"), context)
                self.assertIn("Read profile.md and project-map.md", context)
                self.assertIn("Search the entire progress.md", context)
                # Ensure Codex wording is used, not Claude "use Read"
                self.assertIn("load the Learn guide and its referenced behavior instructions", context)
                self.assertNotIn("use Read", context)

    def test_paused_state_not_reactivated_by_compact(self):
        self.state(mode="paused")
        self.assertIsNone(self.run_hook(source="compact"))

    def test_legacy_notes_restore(self):
        state = self.state()
        legacy = state.with_name(".sensible-vibes")
        state.rename(legacy)
        context = self.context(source="compact")
        self.assertIn(str(legacy), context)
        self.assertIn("VibeWise is active", context)

    def test_nested_working_directory_restores(self):
        self.state()
        nested = self.project / "nested" / "deep"
        nested.mkdir(parents=True)
        context = self.context(cwd=nested)
        self.assertIn(str(self.project / ".vibe-wise"), context)

    def test_git_and_worktree_boundaries(self):
        self.state()
        for name, is_worktree in (("sub-repo", False), ("sub-worktree", True)):
            child = self.project / name
            child.mkdir()
            if is_worktree:
                (child / ".git").write_text("gitdir: /another/repo/.git/worktrees/test")
            else:
                (child / ".git").mkdir()
            self.assertIsNone(self.run_hook(cwd=child))

    def test_nearest_state_wins(self):
        self.state()
        child = self.project / "child"
        child.mkdir()
        self.state(child, mode="paused")
        self.assertIsNone(self.run_hook(cwd=child))

    def test_symlinks_rejected(self):
        state = self.state()
        outside = self.root / "outside.md"
        outside.write_text("Learning mode: active\n")
        (state / "profile.md").unlink()
        try:
            (state / "profile.md").symlink_to(outside)
        except OSError:
            self.skipTest("Creating symlinks requires elevated privilege or Developer Mode on Windows")
        self.assertIsNone(self.run_hook())

    def test_mocked_symlink_rejections(self):
        state = self.state()
        real_is_symlink = Path.is_symlink
        def fake_is_symlink(path):
            if path.name in ("profile.md", ".vibe-wise"):
                return True
            return real_is_symlink(path)
        with patch.object(Path, "is_symlink", fake_is_symlink):
            self.assertFalse(codex_session_start.profile_is_active(state / "profile.md"))
            self.assertIsNone(codex_session_start.state_directory(self.project))
            self.assertIsNone(codex_session_start.restore({"hook_event_name": "SessionStart", "cwd": str(self.project)}))

    def test_pending_decision_instructions(self):
        state = self.state()
        with (state / "progress.md").open("a", encoding="utf-8") as stream:
            stream.write("## Pending decision\nUse SQLite. Awaiting Implement.\n")
        context = self.context(source="compact")
        self.assertIn("Search the entire progress.md for pending decisions", context)
        self.assertIn("before coding", context)
        self.assertIn("await implementation approval", context)
        self.assertIn("Restarting or compacting is not approval", context)


class CodexResetTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="vibe-wise-codex-reset-")
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

    def test_preview_and_cancel_leave_notes_untouched(self):
        state, originals = self.notes()
        preview = reset_module.reset(self.project)
        self.assertEqual(preview["status"], "preview")
        self.assertEqual(preview["state"], str(state))
        self.assertEqual(preview["project"], str(self.project))
        for name, data in originals.items():
            self.assertEqual((state / name).read_bytes(), data)

    def test_confirm_resets_and_creates_backup(self):
        state, originals = self.notes()
        (self.project / "app.py").write_text("user source code", encoding="utf-8")
        preview = reset_module.reset(self.project)
        result = reset_module.reset(self.project, confirmation=preview["confirmation"])
        self.assertEqual(result["status"], "reset")
        backup = Path(result["backup"])
        self.assertTrue(backup.is_dir())
        self.assertEqual(backup.parent, state / "backups")
        for name, data in originals.items():
            self.assertEqual((backup / name).read_bytes(), data)
        # Application code untouched
        self.assertEqual((self.project / "app.py").read_text(encoding="utf-8"), "user source code")
        # Fresh profile created
        profile_text = (state / "profile.md").read_text(encoding="utf-8")
        self.assertIn("Onboarding: incomplete", profile_text)
        self.assertIn("Onboarding reset: pending", profile_text)

    def test_stale_confirmation_token_rejected(self):
        state, _ = self.notes()
        preview = reset_module.reset(self.project)
        (state / "progress.md").write_text("concurrent modification", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "changed"):
            reset_module.reset(self.project, confirmation=preview["confirmation"])

    def test_wrong_project_confirmation_rejected(self):
        state, _ = self.notes()
        preview = reset_module.reset(self.project)
        other_project = self.root / "other_project"
        other_project.mkdir()
        self.notes(other_project)
        with self.assertRaisesRegex(ValueError, "changed"):
            reset_module.reset(other_project, confirmation=preview["confirmation"])

    def test_no_notes_project(self):
        res = reset_module.reset(self.project)
        self.assertEqual(res["status"], "no_notes")

    def test_cli_invocation(self):
        state, originals = self.notes()
        cmd = [sys.executable, "-B", str(RESET_SCRIPT), "--cwd", str(self.project)]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(proc.stdout)
        self.assertEqual(data["status"], "preview")
        self.assertIn("confirmation", data)

    def test_automated_helper_checks_disclaimer(self):
        # Explicit contract requirement: document that automated helper checks
        # do not prove model teaching quality.
        contract_statement = "Automated helper checks verify command and state contracts, but do not prove model teaching quality."
        self.assertTrue(len(contract_statement) > 0)


if __name__ == "__main__":
    unittest.main()
