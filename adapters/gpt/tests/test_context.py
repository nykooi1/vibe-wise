import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'vibe-wise/scripts/context.py'
spec = importlib.util.spec_from_file_location('context_helper', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / '.git').mkdir()

    def notes(self, root=None, name='.vibe-wise', profile='Learning mode: active\n'):
        state = (root or self.root) / name
        state.mkdir()
        (state / 'profile.md').write_text(profile, encoding='utf-8')
        return state

    def test_new_project_read_only(self):
        result = module.inspect(self.root)
        self.assertEqual(result['status'], 'no_notes')
        self.assertEqual(result['project'], str(self.root))
        self.assertEqual([p.name for p in self.root.iterdir()], ['.git'])

    def test_nested_legacy_and_precedence(self):
        legacy = self.notes(name='.sensible-vibes')
        nested = self.root / 'src'
        nested.mkdir()
        self.assertEqual(module.inspect(nested)['state'], str(legacy))
        self.notes(profile='Learning mode: paused\n')
        self.assertEqual(module.inspect(nested)['status'], 'paused')

    def test_worktree_boundary(self):
        self.notes()
        child = self.root / 'worktree'
        child.mkdir()
        (child / '.git').write_text('gitdir: elsewhere')
        self.assertEqual(module.inspect(child)['status'], 'no_notes')

    def test_long_profile_pause_and_no_history_in_output(self):
        state = self.notes(profile='Learning mode: active\n' + 'old\n' * 10000 + 'Learning mode: paused\n')
        (state / 'progress.md').write_text('private learning evidence')
        before = {p.name: p.read_bytes() for p in state.iterdir()}
        result = module.inspect(self.root)
        self.assertEqual(result['status'], 'paused')
        self.assertNotIn('private learning evidence', json.dumps(result))
        self.assertEqual(before, {p.name: p.read_bytes() for p in state.iterdir()})

    def test_invalid_path_and_encoding(self):
        with self.assertRaises(ValueError):
            module.inspect('relative')
        state = self.notes()
        (state / 'profile.md').write_bytes(b'\xff')
        with self.assertRaises(ValueError):
            module.inspect(self.root)

    def test_link_rejected_without_fallback(self):
        self.notes(name='.sensible-vibes')
        try:
            (self.root / '.vibe-wise').symlink_to(self.root / 'missing', target_is_directory=True)
        except OSError as error:
            if getattr(error, 'winerror', None) == 1314:
                self.skipTest('Windows account cannot create symbolic links')
            raise
        with self.assertRaisesRegex(ValueError, 'state'):
            module.inspect(self.root)

    def test_cli(self):
        self.notes()
        result = subprocess.run([sys.executable, '-B', str(SCRIPT), '--cwd', str(self.root)],
                                capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout)['status'], 'active')


if __name__ == '__main__':
    unittest.main()
