"""Mirror a repository's learning notes to an optional vault folder.

Claude Code runs this hook as `vault_sync.py <mode>` with the event JSON on stdin:

- pull   (UserPromptSubmit): a `/vibe-wise:learn` prompt marks the session, then
                             copies vault -> repo.
- resume (SessionStart):     a marked session that is resumed copies vault -> repo.
- push   (SessionEnd):       copies repo -> vault when the session is marked, or when
                             this computer has synced the repo before (learning can
                             resume without the learn prompt).

The vault is the folder in the `vault_path` plugin option (for example an Obsidian
vault on Google Drive). Each repository gets `<vault>/<repo name>/`. A record of each
file's content at the last sync decides which side changed: a file is only overwritten
when its side hasn't changed since then. Files are never deleted. Every sync is logged;
nothing is printed, because stdout from these events is injected into Claude's context.
The hook never blocks the session and always exits 0.
"""

from datetime import datetime
from functools import partial
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile


LEARN_PROMPT = "/vibe-wise:learn"
MODES = ("pull", "resume", "push")
# The session id becomes a file name, so it must not be able to leave sessions/.
SESSION_ID = re.compile(r"[A-Za-z0-9_-]+")
# Prefix of in-progress copies; leftovers from a killed run must never spread.
TEMP_PREFIX = ".vault-sync-"


def write_log(path, mode, message):
    """Append one line to the sync log. A broken log must never break the session."""
    stamp = datetime.now().astimezone().isoformat(timespec="seconds")
    try:
        with path.open("a", encoding="utf-8") as stream:
            stream.write(f"{stamp} [{mode}] {message}\n")
    except (OSError, UnicodeError):
        pass


def is_learn_prompt(prompt):
    text = prompt.lstrip()
    if not text.startswith(LEARN_PROMPT):
        return False
    rest = text[len(LEARN_PROMPT):]
    # `/vibe-wise:learner` is a different command.
    return rest == "" or rest[0].isspace()


def git_output(start, *args):
    """Run git in `start` and return its stdout; raise ValueError on any failure."""
    try:
        result = subprocess.run(
            ["git", "-C", start, *args], stdin=subprocess.DEVNULL,
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        raise ValueError(str(error))
    if result.returncode != 0:
        raise ValueError(result.stderr)
    return result.stdout.rstrip("\n")


def locate(start, vault):
    """Find the repo's local notes and vault folders without logging.

    Returns (toplevel, repo_name, local, remote); raises ValueError.
    """
    if not start:
        raise ValueError("empty start directory")
    toplevel = git_output(start, "rev-parse", "--show-toplevel")
    common = git_output(start, "rev-parse", "--path-format=absolute", "--git-common-dir")
    # A linked worktree's common dir is the main repository's .git, so every
    # worktree of a repository shares one vault folder.
    repo_name = Path(common).parent.name
    if not repo_name:
        raise ValueError("no repository name")
    local = Path(toplevel) / ".vibe-wise"
    legacy = Path(toplevel) / ".sensible-vibes"
    # Keep using legacy notes in place, but only when no new-style folder exists
    # (not even a symlink, which is refused later rather than silently bypassed).
    if not os.path.lexists(local) and os.path.lexists(legacy):
        local = legacy
    return toplevel, repo_name, local, vault / repo_name


def resolve(start, vault, log, failure):
    """Like locate, but log why the folders can't be used. Returns None then."""
    try:
        found = locate(start, vault)
    except ValueError:
        log(failure)
        return None
    _, _, local, remote = found
    if local.is_symlink() or remote.is_symlink():
        log(f"refusing symlinked state dir: {local} or {remote}")
        return None
    return found


def record_path(state, local):
    """Where the last-synced record of one local state directory lives."""
    key = hashlib.sha256(os.fsencode(os.path.abspath(local))).hexdigest()[:32]
    return state / "bases" / f"{key}.json"


def load_record(path, remote, log):
    """Return {relative path: content hash} as of the last sync with `remote`.

    None means there is no usable record: never synced, synced with another vault
    folder, or unreadable.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, NotADirectoryError):
        return None
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        log(f"ignoring unreadable sync record {path}: {error}")
        return None
    if not isinstance(data, dict) or not isinstance(data.get("files"), dict):
        log(f"ignoring unreadable sync record {path}")
        return None
    # A record for another vault folder says nothing about this one.
    if data.get("remote") != str(remote):
        return None
    return {key: value for key, value in data["files"].items() if isinstance(value, str)}


def save_record(path, remote, files, log):
    """Replace the record atomically; a failure only costs conflict detection."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=TEMP_PREFIX)
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as stream:
                json.dump({"remote": str(remote), "files": files}, stream, sort_keys=True)
            os.replace(temporary, path)
        except BaseException:
            try:
                os.unlink(temporary)
            except OSError:
                pass
            raise
    except OSError as error:
        log(f"could not save sync record {path}: {error}")


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(partial(stream.read, 65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def new_file_mode():
    """The mode a newly created regular file gets under the current umask."""
    # The umask can only be read by setting it, so restore it immediately.
    mask = os.umask(0)
    os.umask(mask)
    return 0o666 & ~mask


def usable_target(dst, relative):
    """Check that writing dst/relative can't escape dst or clobber a non-file."""
    current = dst
    for part in relative.parts[:-1]:
        current = current / part
        # A symlinked folder would redirect the write outside the state directory.
        if current.is_symlink() or (current.exists() and not current.is_dir()):
            return False
    target = dst / relative
    return not target.is_symlink() and (not target.exists() or target.is_file())


def copy_file(source, target):
    """Write via a temporary file so an interruption never leaves a partial note."""
    # Don't copy the source's mode: drvfs reports every vault file as 0o777.
    try:
        mode = stat.S_IMODE(os.lstat(target).st_mode)
    except FileNotFoundError:
        mode = new_file_mode()
    target.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=target.parent, prefix=TEMP_PREFIX)
    os.close(handle)
    try:
        shutil.copyfile(source, temporary)
        try:
            os.chmod(temporary, mode)
        except OSError:
            pass  # Synced drives may not support permission changes.
        os.replace(temporary, target)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def copy_notes(src, dst, base, log, kept_side):
    """Copy files from src to dst unless dst holds the only change since the last sync.

    `base` maps relative paths to content hashes as of the last sync; it is updated
    in place for every file that ends up the same on both sides.
    Returns (updated, kept_newer, conflicts).
    """
    dst.mkdir(parents=True, exist_ok=True)
    updated = kept_newer = conflicts = 0
    # os.walk doesn't follow symlinked directories, so those are never entered.
    for folder, _, names in os.walk(src):
        for name in names:
            source = Path(folder) / name
            if (name.lower() == "desktop.ini" or name.startswith(TEMP_PREFIX)
                    or source.is_symlink() or not source.is_file()):
                continue
            relative = source.relative_to(src)
            key = relative.as_posix()
            target = dst / relative
            if not usable_target(dst, relative):
                log(f"skipped {key}")
                continue
            # Compare content: Google Drive can't preserve modification times.
            source_hash = file_hash(source)
            target_hash = file_hash(target) if target.is_file() else None
            last = base.get(key)
            if source_hash == target_hash:
                base[key] = source_hash
            elif target_hash is None or last is None or target_hash == last:
                # Nothing to lose: dst lacks the file, was never synced, or is unchanged.
                copy_file(source, target)
                base[key] = source_hash
                updated += 1
            elif source_hash == last:
                # Only dst changed since the last sync (e.g. an unpushed session).
                kept_newer += 1
            else:
                # Leave the record alone so the conflict is reported until resolved.
                log(f"conflict {key}: changed on both sides since last sync; "
                    f"kept {kept_side} copy")
                conflicts += 1
    return updated, kept_newer, conflicts


def sync(mode, found, state, log, marker=None):
    """Copy in the direction `mode` implies. `marker` is written first when given."""
    toplevel, repo_name, local, remote = found
    pulling = mode != "push"
    src, dst = (remote, local) if pulling else (local, remote)
    verb = "pull" if pulling else "push"
    try:
        if marker is not None:
            marker.write_text(toplevel + "\n", encoding="utf-8")
        if not src.is_dir():
            log(f"no vault folder yet for {repo_name}, skipping pull" if pulling
                else f"no local state in {toplevel}, skipping push")
            return
        record = record_path(state, local)
        # Entries for files not seen this time are kept.
        files = load_record(record, remote, log) or {}
        try:
            counts = copy_notes(src, dst, files, log, "local" if pulling else "vault")
        finally:
            # Also after a partial failure: the files already copied are in sync.
            save_record(record, remote, files, log)
        log(f"{verb}ed {src} -> {dst} ({counts[0]} updated, {counts[1]} kept newer, "
            f"{counts[2]} conflicts)")
    except OSError as error:
        log(f"{verb} failed for {repo_name}: {error}")


def marked_toplevel(marker):
    """Read the repo path recorded when the session ran the learn prompt."""
    try:
        return marker.read_text(encoding="utf-8").splitlines()[0]
    except (OSError, UnicodeError, IndexError):
        return ""


def synced_before(cwd, vault, state, log):
    """Whether this computer has synced the repo containing `cwd` with this vault."""
    if not isinstance(cwd, str) or not os.path.isabs(cwd):
        return False
    try:
        _, _, local, remote = locate(cwd, vault)
    except ValueError:
        return False
    return load_record(record_path(state, local), remote, log) is not None


def vault_reachable(vault, log):
    if vault.is_absolute() and vault.is_dir():
        return True
    log(f"vault path does not exist: {vault}")
    return False


def run(mode):
    try:
        payload = json.loads(sys.stdin.read(65536))
    except (OSError, ValueError, RecursionError):
        return
    if not isinstance(payload, dict):
        return
    vault_option = os.environ.get("CLAUDE_PLUGIN_OPTION_VAULT_PATH", "").strip()
    data_option = os.environ.get("CLAUDE_PLUGIN_DATA", "").strip()
    # Without a vault the feature is off; without a data directory there's nowhere
    # to keep markers or the log. Either way, leave no trace.
    if not vault_option or not data_option:
        return
    state = Path(data_option) / "vault-sync"
    try:
        (state / "sessions").mkdir(parents=True, exist_ok=True)
    except OSError:
        return
    log = partial(write_log, state / "sync.log", mode)

    if mode not in MODES:
        log("unknown mode")
        return
    # Most prompts aren't the learn prompt; skip them before anything gets logged.
    if mode == "pull":
        prompt = payload.get("prompt")
        if not isinstance(prompt, str) or not is_learn_prompt(prompt):
            return
    session_id = payload.get("session_id")
    if not isinstance(session_id, str) or not SESSION_ID.fullmatch(session_id):
        log("invalid session_id")
        return
    marker = state / "sessions" / session_id
    vault = Path(os.path.expanduser(vault_option))

    if mode == "pull":
        cwd = payload.get("cwd")
        if not isinstance(cwd, str) or not os.path.isabs(cwd):
            log("cwd is not an absolute path")
            return
        if not vault_reachable(vault, log):
            return
        found = resolve(cwd, vault, log, "cwd is not a git repo")
        if found:
            sync(mode, found, state, log, marker)
        return

    if marker.is_file():
        start, failure = marked_toplevel(marker), "marked repo no longer resolvable"
    elif mode == "push" and synced_before(payload.get("cwd"), vault, state, log):
        # Learning resumes without the learn prompt, so a repo already synced on
        # this computer keeps pushing its notes.
        start, failure = payload["cwd"], "cwd is not a git repo"
    else:
        # Other sessions never ran the learn prompt and don't sync, so stay quiet
        # even when the vault is unreachable.
        return
    if not vault_reachable(vault, log):
        return
    found = resolve(start, vault, log, failure)
    if found:
        sync(mode, found, state, log)


def main():
    try:
        run(sys.argv[1] if len(sys.argv) > 1 else "")
    except Exception:
        # Syncing is a convenience and must never break or slow a session.
        pass


if __name__ == "__main__":
    main()
