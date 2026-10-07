"""Install VibeWise into an OpenCode config directory via symlinks/copies."""

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/install-opencode.py"
spec = importlib.util.spec_from_file_location("vibe_wise_install", SCRIPT)
install_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(install_module)


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="vibe-wise-install-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.dest = self.root / "opencode"
        self.repo = ROOT

    def run_script(self, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--dest", str(self.dest), *extra],
            capture_output=True,
            text=True,
        )

    def pieces(self):
        for src_rel, dst_rel in install_module.PIECES:
            yield self.repo / src_rel, self.dest / dst_rel

    def test_fresh_install(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        for src, dst in self.pieces():
            self.assertTrue(dst.exists(), f"missing {dst}")
            self.assertEqual(dst.resolve(), src.resolve(), f"wrong target {dst}")

    def test_idempotent_rerun(self):
        first = self.run_script()
        second = self.run_script()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("OK", second.stdout)
        # Re-run must not replace links; targets still resolve correctly.
        for src, dst in self.pieces():
            self.assertEqual(dst.resolve(), src.resolve())

    def test_conflict_rejected_without_force(self):
        conflict_dst = self.dest / install_module.PIECES[0][1]
        conflict_dst.parent.mkdir(parents=True)
        conflict_dst.write_text("someone else's file\n")
        result = self.run_script()
        self.assertEqual(result.returncode, 1)
        self.assertIn("CONFLICT", result.stdout)
        self.assertEqual(conflict_dst.read_text(), "someone else's file\n")

    def test_force_replaces_conflict(self):
        conflict_dst = self.dest / install_module.PIECES[0][1]
        conflict_dst.parent.mkdir(parents=True)
        conflict_dst.write_text("someone else's file\n")
        result = self.run_script("--force")
        self.assertEqual(result.returncode, 0, result.stderr)
        src, dst = next(self.pieces())
        self.assertEqual(dst.resolve(), src.resolve())

    def test_remove_uninstalls(self):
        self.run_script()
        result = self.run_script("--remove")
        self.assertEqual(result.returncode, 0, result.stderr)
        for _, dst_rel in install_module.PIECES:
            dst = self.dest / dst_rel
            self.assertFalse(dst.exists() or dst.is_symlink(), f"leftover {dst}")

    def test_remove_keeps_foreign_links(self):
        foreign = self.dest / "commands/learn.md"
        foreign.parent.mkdir(parents=True)
        foreign.symlink_to(self.root / "some-other-repo-file.md")
        result = self.run_script("--remove")
        self.assertEqual(result.returncode, 1)
        self.assertTrue(foreign.is_symlink())

    def test_missing_source(self):
        # Simulate a broken repo by calling the helper directly.
        src = self.root / "does/not/exist"
        dst = self.dest / "skills/learn"
        action, message = install_module.link_or_copy(src, dst, False, True)
        self.assertEqual(action, "ERROR")
        self.assertIn("missing source", message)


if __name__ == "__main__":
    unittest.main()