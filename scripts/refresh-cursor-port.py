#!/usr/bin/env python3
"""Refresh the Cursor port's vendored guides from the canonical sources.

The port is copied out of this repository, so it carries byte-identical copies
of the guides and the reset helper. Run this after changing any of them, or
pass --check to report stale copies without writing.
"""

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
PORT = ROOT / "ports/cursor"

# Canonical source in this repository -> copy inside the port's .cursor tree.
VENDORED = {
    "hooks/session_start.py": ".cursor/vibe-wise/hooks/session_start.py",
    "skills/learn/SKILL.md": ".cursor/vibe-wise/skills/learn/SKILL.md",
    "skills/learn/behavior.md": ".cursor/vibe-wise/skills/learn/behavior.md",
    "skills/learn/onboarding.md": ".cursor/vibe-wise/skills/learn/onboarding.md",
    "skills/learn/state-templates.md": ".cursor/vibe-wise/skills/learn/state-templates.md",
    "skills/reset/reset.py": ".cursor/vibe-wise/skills/reset/reset.py",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report stale copies and exit 1 instead of writing them",
    )
    args = parser.parse_args()

    stale = []
    for source, destination in VENDORED.items():
        expected = (ROOT / source).read_bytes()
        target = PORT / destination
        try:
            current = target.read_bytes()
        except FileNotFoundError:
            current = None
        if current == expected:
            print(f"ok      {destination}")
            continue
        stale.append(destination)
        print(f"{'stale  ' if args.check else 'updated'} {destination}")
        if not args.check:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(expected)

    if stale and args.check:
        print(
            f"{len(stale)} vendored file(s) out of date; "
            "run python3 scripts/refresh-cursor-port.py",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
