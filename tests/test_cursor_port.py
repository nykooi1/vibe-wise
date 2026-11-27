"""The copied Cursor port must be self-contained and stay in sync with the source."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PORT = ROOT / "ports/cursor"
CURSOR = PORT / ".cursor"

REFRESH = ROOT / "scripts/refresh-cursor-port.py"

DOCS = (
    CURSOR / "rules/vibe-wise.mdc",
    CURSOR / "commands/learn.md",
    CURSOR / "commands/reset.md",
)


class CursorPortTests(unittest.TestCase):
    def test_vendored_copies_are_current(self):
        result = subprocess.run(
            [sys.executable, str(REFRESH), "--check"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_referenced_paths_live_inside_the_copied_tree(self):
        for doc in DOCS:
            text = doc.read_text(encoding="utf-8")
            self.assertNotIn("../", text, f"{doc} reaches outside the copied tree")
            for ref in re.findall(r"([\w./-]*skills/[\w./-]+)", text):
                with self.subTest(doc=doc.name, ref=ref):
                    self.assertTrue(
                        ref.startswith(".cursor/vibe-wise/"),
                        f"{doc} refers to {ref} outside the copied tree",
                    )
                    self.assertTrue((PORT / ref).is_file(), f"{doc} refers to missing {ref}")

    def test_copied_tree_runs_from_a_project_root(self):
        with tempfile.TemporaryDirectory(prefix="vibe-wise-cursor-") as temp:
            project = Path(temp) / "project with spaces"
            project.mkdir()
            (project / ".git").mkdir()
            shutil.copytree(CURSOR, project / ".cursor")
            result = subprocess.run(
                [
                    sys.executable,
                    ".cursor/vibe-wise/skills/reset/reset.py",
                    "--cwd",
                    str(project),
                ],
                capture_output=True,
                text=True,
                cwd=project,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "no_notes")


if __name__ == "__main__":
    unittest.main()
