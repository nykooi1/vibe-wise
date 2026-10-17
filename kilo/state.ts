/**
 * Read-only learning-state lookup for the Kilo plugin.
 *
 * This ports the lookup rules in `hooks/session_start.py` (`git_root`,
 * `state_directory`, `profile_is_active`) so the plugin can decide whether to
 * restore learning context. The Python hook is the reference implementation;
 * keep the two in sync. Nothing here writes to disk.
 */

import {
  closeSync,
  existsSync,
  lstatSync,
  openSync,
  readSync,
  realpathSync,
} from "node:fs"
import { dirname, join, relative, resolve, sep } from "node:path"

const STATE_NAMES = [".vibe-wise", ".sensible-vibes"]
const CHUNK_SIZE = 64 * 1024
const MAX_LINE = 1024 * 1024
const LINE_BREAK = /\r\n|\r|\n/

// Python's str.isspace() / re `\s` whitespace set for str patterns (which
// excludes U+FEFF, unlike JavaScript's `\s` and String.prototype.trim()).
const PAUSED =
  /^Learning mode:[\t\n\v\f\r\u001c-\u001f \u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]*paused[\t\n\v\f\r\u001c-\u001f \u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]*$/i
const PY_WHITESPACE =
  /[\t\n\v\f\r\u001c-\u001f \u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]/

/** True when the line is blank under Python's `str.strip()` semantics. */
function isBlankPython(line: string): boolean {
  for (const ch of line) {
    if (!PY_WHITESPACE.test(ch)) return false
  }
  return true
}

function lstatOrNull(path: string) {
  try {
    return lstatSync(path)
  } catch {
    return null
  }
}

/** Nearest repository or worktree root (a `.git` directory or file). */
export function gitRoot(cwd: string): string | null {
  let directory = resolve(cwd)
  for (;;) {
    // Python uses Path.exists(), which follows symlinks: a dangling `.git`
    // symlink is not a repository root, so keep climbing.
    if (existsSync(join(directory, ".git"))) return directory
    const parent = dirname(directory)
    if (parent === directory) return null
    directory = parent
  }
}

/**
 * Nearest notes directory without crossing a Git project boundary.
 *
 * Within Git, a source subdirectory still finds the project's notes. Without
 * Git there is no project boundary, so only the starting folder counts:
 * searching upward could adopt notes from an unrelated parent folder.
 */
export function stateDirectory(cwd: string): string | null {
  const start = resolve(cwd)
  const root = gitRoot(start)

  let candidates: string[]
  if (root === null) {
    candidates = [start]
  } else {
    const depth = relative(root, start).split(sep).filter(Boolean).length + 1
    candidates = []
    let directory = start
    for (let i = 0; i < depth; i++) {
      candidates.push(directory)
      const parent = dirname(directory)
      if (parent === directory) break
      directory = parent
    }
  }

  for (const directory of candidates) {
    // Prefer the new name at the nearest location; keep legacy notes in place.
    for (const name of STATE_NAMES) {
      const state = join(directory, name)
      const stats = lstatOrNull(state)
      if (stats === null) continue
      // Stop even if this candidate is invalid. Falling back to a parent could
      // silently load a different project's learner profile. A symlinked or
      // non-directory state is rejected (a broken symlink still counts as present).
      if (stats.isDirectory() && !stats.isSymbolicLink()) return state
      return null
    }
  }
  return null
}

/**
 * Check activation without copying learner notes anywhere.
 *
 * Streams the file in bounded chunks with a strict UTF-8 decoder, mirroring the
 * reference hook: invalid text isn't evidence of active learning, and a very
 * large `profile.md` cannot force an unbounded allocation. A paused marker can
 * appear after a long profile, so the whole file is scanned. Older profiles may
 * lack an explicit mode; their non-blank content preserves restoration behavior.
 */
export function profileIsActive(path: string): boolean {
  let fd: number
  try {
    const stats = lstatSync(path)
    // Missing, symlinked, or non-regular files are not evidence of active learning.
    if (!stats.isFile()) return false
    fd = openSync(path, "r")
  } catch {
    return false
  }

  // ignoreBOM keeps a leading U+FEFF, matching Python's `open(encoding="utf-8")`.
  const decoder = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true })
  const buffer = Buffer.allocUnsafe(CHUNK_SIZE)
  let carry = ""
  let hasContent = false

  try {
    for (;;) {
      const read = readSync(fd, buffer, 0, CHUNK_SIZE, null)
      if (read === 0) break
      carry += decoder.decode(buffer.subarray(0, read), { stream: true })
      const lines = carry.split(LINE_BREAK)
      carry = lines.pop() ?? ""
      // An unterminated line longer than MAX_LINE is content; drop it so a
      // single huge line cannot grow `carry` without bound.
      if (carry.length > MAX_LINE) {
        hasContent = true
        carry = ""
      }
      for (const line of lines) {
        if (!isBlankPython(line)) hasContent = true
        if (PAUSED.test(line)) return false
      }
    }
    // Flush any trailing partial line and any buffered decoder state.
    carry += decoder.decode()
    if (!isBlankPython(carry)) hasContent = true
    if (PAUSED.test(carry)) return false
    return hasContent
  } catch {
    // Unreadable, truncated, or invalid text isn't evidence of active learning.
    return false
  } finally {
    try {
      closeSync(fd)
    } catch {
      // Ignore close failures.
    }
  }
}

/**
 * The active learning-state directory for a working directory, or null.
 *
 * Resolves symlinks first, matching the reference callers (`session_start.py`
 * and `reset.py` resolve the working directory before lookup) so restore and
 * reset agree when the project is opened through a symlink.
 */
export function activeStateDirectory(cwd: string): string | null {
  let start = cwd
  try {
    start = realpathSync(cwd)
  } catch {
    // Fall back to the given path if it cannot be resolved.
  }
  const state = stateDirectory(start)
  if (state === null) return null
  if (!profileIsActive(join(state, "profile.md"))) return null
  return state
}
