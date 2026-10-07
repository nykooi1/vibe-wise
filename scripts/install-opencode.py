#!/usr/bin/env python3
"""Install VibeWise into OpenCode's global config directory.

Creates symlinks (or copies with --copy) from this repository into
~/.config/opencode/ so VibeWise works in every project. Idempotent:
re-running on an already-installed setup reports OK and changes nothing.
Use --remove to uninstall, --force to replace conflicting files.
"""

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# (relative source in repo, relative target under dest)
PIECES = [
    ("skills/learn", "skills/learn"),
    ("skills/reset", "skills/reset"),
    (".opencode/commands/learn.md", "commands/learn.md"),
    (".opencode/commands/reset.md", "commands/reset.md"),
    (".opencode/plugins/vibe-wise.ts", "plugins/vibe-wise.ts"),
]


def link_or_copy(src, dst, copy, force):
    """Install one piece. Returns (action, message)."""
    if not src.exists():
        return ("ERROR", f"missing source in repo: {src}")
    if dst.is_symlink():
        if dst.resolve() == src.resolve():
            return ("OK", "already linked")
        if not force:
            return ("CONFLICT", f"symlink to {dst.resolve()}")
        dst.unlink()
    elif dst.exists():
        # A real file or directory. Never merge; only replace
        # wholesale with explicit --force.
        if not force:
            return ("CONFLICT", f"existing {dst}")
        if dst.is_dir():
            shutil.rmtree(dst)
        else:
            dst.unlink()
    dst.parent.mkdir(parents=True, exist_ok=True)
    if copy or not _can_symlink():
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        return ("COPIED", str(dst))
    try:
        dst.symlink_to(src, target_is_directory=src.is_dir())
    except OSError:
        shutil.copytree(src, dst) if src.is_dir() else shutil.copy2(src, dst)
        return ("COPIED", str(dst))
    return ("LINKED", str(dst))


def _can_symlink():
    try:
        probe = Path(__import__("tempfile").mkdtemp()) / "probe"
        probe.symlink_to(REPO_ROOT)
        probe.unlink()
        probe.parent.rmdir()
        return True
    except OSError:
        return False


def remove(dst_root):
    """Remove only the exact pieces this installer creates."""
    failed = False
    for _, rel in PIECES:
        dst = dst_root / rel
        if dst.is_symlink():
            target = dst.resolve()
            if REPO_ROOT in target.parents or target == REPO_ROOT:
                dst.unlink()
                print(f"removed   {dst}")
            else:
                print(f"kept      {dst} -> {target} (not this repo)")
                failed = True
        elif dst.exists():
            print(f"kept      {dst} (not created by this installer)")
            failed = True
        else:
            print(f"absent    {dst}")
    return 1 if failed else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dest",
        default=str(Path.home() / ".config" / "opencode"),
        help="OpenCode config directory (default: ~/.config/opencode)",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="copy files instead of symlinking (for Windows)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace existing conflicting files at the target paths",
    )
    parser.add_argument(
        "--remove",
        action="store_true",
        help="uninstall the pieces this installer creates",
    )
    args = parser.parse_args()

    dest_root = Path(args.dest).expanduser()
    if args.remove:
        sys.exit(remove(dest_root))

    if not dest_root.exists():
        dest_root.mkdir(parents=True, exist_ok=True)

    exit_code = 0
    for src_rel, dst_rel in PIECES:
        action, message = link_or_copy(REPO_ROOT / src_rel, dest_root / dst_rel, args.copy, args.force)
        if action in ("OK", "LINKED", "COPIED"):
            print(f"{action:<8}  {src_rel} -> {dst_rel}")
        else:
            print(f"{action:<8}  {dst_rel}: {message}")
            if action == "CONFLICT":
                print(f"          rerun with --force to replace, or remove it manually")
            exit_code = 1
    if exit_code:
        print("completed with problems", file=sys.stderr)
    else:
        print(f"done. start `opencode` in any project and run /learn")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()