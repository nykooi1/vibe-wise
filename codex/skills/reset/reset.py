"""Preview by default; reset only a confirmed snapshot of local learning notes."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile


sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hooks"))
from session_start import state_directory


FRESH = {
    "profile.md": (
        "# Learner Profile\n\nLearning mode: active\nOnboarding: incomplete\n"
        "Onboarding reset: pending\n\n"
        "Remaining onboarding: Project situation, experience, stack familiarity, "
        "goals, and preferences.\n"
    ),
    "progress.md": "# Learning Progress\n\nNo learning events recorded yet.\n",
    "project-map.md": "# Project Map\n\nNot mapped yet. Inspect the current project.\n",
}


def snapshot(cwd):
    state = state_directory(cwd)
    if state is None:
        return None, {}, None
    notes = {}
    for name in FRESH:
        path = state / name
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError:
            continue
        if not stat.S_ISREG(mode):
            raise ValueError("Refusing to reset non-regular note: " + str(path))
        notes[name] = path.read_bytes()
    # Include identity, missing files, and content so confirmation cannot drift
    # to another project or silently discard notes updated by another session.
    digest = hashlib.sha256(str(state).encode())
    for name in FRESH:
        data = notes.get(name)
        digest.update(json.dumps([name, None if data is None else data.hex()]).encode())
    return state, notes, digest.hexdigest()


def reset(cwd, confirmation=None):
    cwd = Path(cwd)
    if not cwd.is_absolute() or not cwd.is_dir():
        raise ValueError("Use an existing absolute project working directory.")
    cwd = cwd.resolve()
    state, notes, fingerprint = snapshot(cwd)
    if confirmation is not None and (not notes or confirmation != fingerprint):
        raise ValueError("Target or notes changed. Preview and confirm again; nothing reset.")
    if not notes:
        return {"status": "no_notes", "cwd": str(cwd)}
    result = {
        "status": "preview", "project": str(state.parent), "state": str(state),
        "files": list(notes), "backup_parent": str(state / "backups"),
        "confirmation": fingerprint,
    }
    if confirmation is None:
        return result

    backup_parent = state / "backups"
    if backup_parent.is_symlink() or (backup_parent.exists() and not backup_parent.is_dir()):
        raise ValueError("Backup path must be a real directory; nothing reset.")
    backup_parent.mkdir(mode=0o700, exist_ok=True)
    prefix = datetime.now(timezone.utc).strftime("reset-%Y%m%dT%H%M%SZ-")
    backup = Path(tempfile.mkdtemp(prefix=prefix, dir=backup_parent))
    try:
        # Finish all backups and prepare replacements before touching active notes.
        for name, data in notes.items():
            (backup / name).write_bytes(data)
        for name, text in FRESH.items():
            (backup / (".new-" + name)).write_text(text, encoding="utf-8")
        if snapshot(cwd)[2] != fingerprint:
            raise ValueError("Notes changed during backup; active notes were not reset.")
        for name in FRESH:
            os.replace(backup / (".new-" + name), state / name)
    except (OSError, ValueError) as error:
        raise ValueError(
            "Reset did not complete. Backup location: {}. "
            "Check active notes before continuing. {}".format(backup, error)
        ) from error
    return {"status": "reset", "project": str(state.parent),
            "state": str(state), "backup": str(backup)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--confirm", help="Snapshot token from a preview; only after user confirmation")
    args = parser.parse_args()
    try:
        result = reset(args.cwd, args.confirm)
    except (OSError, ValueError) as error:
        print(json.dumps({"status": "error", "message": str(error)}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
