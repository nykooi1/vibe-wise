import { afterEach, describe, expect, test } from "bun:test"
import { mkdirSync, mkdtempSync, rmSync, symlinkSync, writeFileSync } from "node:fs"
import { tmpdir } from "node:os"
import { join } from "node:path"
import {
  activeStateDirectory,
  gitRoot,
  profileIsActive,
  stateDirectory,
} from "./state.ts"

const made: string[] = []

function scratch(): string {
  const dir = mkdtempSync(join(tmpdir(), "vibewise-kilo-"))
  made.push(dir)
  return dir
}

function dir(...parts: string[]): string {
  const path = join(...parts)
  mkdirSync(path, { recursive: true })
  return path
}

function file(path: string, body: string): string {
  mkdirSync(join(path, ".."), { recursive: true })
  writeFileSync(path, body)
  return path
}

function gitRootAt(path: string): string {
  mkdirSync(join(path, ".git"), { recursive: true })
  return path
}

afterEach(() => {
  while (made.length) rmSync(made.pop()!, { recursive: true, force: true })
})

describe("gitRoot", () => {
  test("finds the nearest .git directory", () => {
    const root = gitRootAt(dir(scratch(), "repo"))
    const sub = dir(root, "src", "deep")
    expect(gitRoot(sub)).toBe(root)
  })

  test("finds a .git file (worktree)", () => {
    const root = scratch()
    file(join(root, ".git"), "gitdir: /elsewhere\n")
    expect(gitRoot(dir(root, "src"))).toBe(root)
  })

  test("a dangling .git symlink is not a repository root", () => {
    const repo = gitRootAt(scratch())
    const sub = dir(repo, "sub")
    symlinkSync(join(repo, "missing"), join(sub, ".git"), "dir")
    expect(gitRoot(sub)).toBe(repo)
  })

  test("returns null without a repository", () => {
    expect(gitRoot(dir(scratch(), "plain"))).toBeNull()
  })
})

describe("stateDirectory", () => {
  test("without git, finds state in the starting folder", () => {
    const cwd = scratch()
    const state = dir(cwd, ".vibe-wise")
    expect(stateDirectory(cwd)).toBe(state)
  })

  test("without git, does not search parent folders", () => {
    const parent = scratch()
    dir(parent, ".vibe-wise")
    const cwd = dir(parent, "project")
    expect(stateDirectory(cwd)).toBeNull()
  })

  test("with git, a subdirectory finds the project state", () => {
    const root = gitRootAt(scratch())
    const state = dir(root, ".vibe-wise")
    const sub = dir(root, "src", "deep")
    expect(stateDirectory(sub)).toBe(state)
  })

  test("prefers .vibe-wise over .sensible-vibes at the same level", () => {
    const root = gitRootAt(scratch())
    const preferred = dir(root, ".vibe-wise")
    dir(root, ".sensible-vibes")
    expect(stateDirectory(root)).toBe(preferred)
  })

  test("keeps legacy .sensible-vibes in place", () => {
    const root = gitRootAt(scratch())
    const legacy = dir(root, ".sensible-vibes")
    expect(stateDirectory(root)).toBe(legacy)
  })

  test("does not cross the git boundary", () => {
    const outer = scratch()
    dir(outer, ".vibe-wise")
    const root = gitRootAt(dir(outer, "repo"))
    const sub = dir(root, "src")
    expect(stateDirectory(sub)).toBeNull()
  })

  test("rejects a symlinked state directory", () => {
    const root = gitRootAt(scratch())
    const real = dir(root, "real-notes")
    symlinkSync(real, join(root, ".vibe-wise"), "dir")
    expect(stateDirectory(root)).toBeNull()
  })

  test("rejects a broken symlink", () => {
    const root = gitRootAt(scratch())
    symlinkSync(join(root, "missing"), join(root, ".vibe-wise"), "dir")
    expect(stateDirectory(root)).toBeNull()
  })

  test("rejects a state path that is a regular file", () => {
    const root = gitRootAt(scratch())
    file(join(root, ".vibe-wise"), "not a directory\n")
    expect(stateDirectory(root)).toBeNull()
  })

  test("returns null when no state exists", () => {
    const root = gitRootAt(scratch())
    expect(stateDirectory(root)).toBeNull()
  })

  test("finds state past a dangling .git symlink, like the reset helper", () => {
    const repo = gitRootAt(scratch())
    const state = dir(repo, ".vibe-wise")
    const sub = dir(repo, "sub")
    symlinkSync(join(repo, "missing"), join(sub, ".git"), "dir")
    expect(stateDirectory(sub)).toBe(state)
  })
})

describe("profileIsActive", () => {
  test("active content is restored", () => {
    const path = file(join(scratch(), "profile.md"), "# Learner Profile\nLearning mode: active\n")
    expect(profileIsActive(path)).toBe(true)
  })

  test("a paused profile is not restored", () => {
    const path = file(join(scratch(), "profile.md"), "Learning mode: paused\n")
    expect(profileIsActive(path)).toBe(false)
  })

  test("paused detection is case-insensitive and tolerates trailing space", () => {
    const path = file(join(scratch(), "profile.md"), "learning mode:\tPaused   \n")
    expect(profileIsActive(path)).toBe(false)
  })

  test("a paused marker after long content still stops restoration", () => {
    const body = "x".repeat(80_000) + "\n" + "Learning mode: paused\n"
    const path = file(join(scratch(), "profile.md"), body)
    expect(profileIsActive(path)).toBe(false)
  })

  test("a large active profile is restored across chunk boundaries", () => {
    const body = "line of notes\n".repeat(20_000) + "Learning mode: active\n"
    const path = file(join(scratch(), "profile.md"), body)
    expect(profileIsActive(path)).toBe(true)
  })

  test("invalid UTF-8 is not restored", () => {
    const path = join(scratch(), "profile.md")
    writeFileSync(
      path,
      Buffer.concat([
        Buffer.from("Learning mode: active\n"),
        Buffer.from([0xff, 0xfe, 0x0a]),
      ]),
    )
    expect(profileIsActive(path)).toBe(false)
  })

  test("CR-only line endings still detect a paused marker", () => {
    const path = join(scratch(), "profile.md")
    writeFileSync(
      path,
      Buffer.from("Learning mode: active\rLearning mode: paused\r"),
    )
    expect(profileIsActive(path)).toBe(false)
  })

  test("keeps a leading BOM like the reference, so a pause marker after it stays active", () => {
    const path = join(scratch(), "profile.md")
    writeFileSync(
      path,
      Buffer.concat([
        Buffer.from([0xef, 0xbb, 0xbf]),
        Buffer.from("Learning mode: paused\n"),
      ]),
    )
    expect(profileIsActive(path)).toBe(true)
  })

  test("a NEL-only file is blank like the reference", () => {
    const path = join(scratch(), "profile.md")
    writeFileSync(path, Buffer.from([0xc2, 0x85]))
    expect(profileIsActive(path)).toBe(false)
  })

  test("a very long unterminated line is bounded and treated as content", () => {
    const path = file(join(scratch(), "profile.md"), "a".repeat(2 * 1024 * 1024))
    expect(profileIsActive(path)).toBe(true)
  })

  test("older profiles without a mode are restored when non-blank", () => {
    const path = file(join(scratch(), "profile.md"), "Legacy notes only.\n")
    expect(profileIsActive(path)).toBe(true)
  })

  test("blank content is not restored", () => {
    const path = file(join(scratch(), "profile.md"), "   \n\n")
    expect(profileIsActive(path)).toBe(false)
  })

  test("a missing file is not restored", () => {
    expect(profileIsActive(join(scratch(), "profile.md"))).toBe(false)
  })

  test("a symlinked profile is not restored", () => {
    const root = scratch()
    const real = file(join(root, "real.md"), "Learning mode: active\n")
    const link = join(root, "profile.md")
    symlinkSync(real, link)
    expect(profileIsActive(link)).toBe(false)
  })

  test("a directory is not restored", () => {
    expect(profileIsActive(dir(scratch(), "profile.md"))).toBe(false)
  })
})

describe("activeStateDirectory", () => {
  test("returns the state only when the profile is active", () => {
    const root = gitRootAt(scratch())
    const state = dir(root, ".vibe-wise")
    file(join(state, "profile.md"), "Learning mode: active\n")
    expect(activeStateDirectory(root)).toBe(state)
  })

  test("returns null for a paused profile", () => {
    const root = gitRootAt(scratch())
    const state = dir(root, ".vibe-wise")
    file(join(state, "profile.md"), "Learning mode: paused\n")
    expect(activeStateDirectory(root)).toBeNull()
  })

  test("returns null without state", () => {
    expect(activeStateDirectory(gitRootAt(scratch()))).toBeNull()
  })

  test("resolves a symlinked project directory like the reset helper", () => {
    const repo = gitRootAt(scratch())
    const state = dir(repo, ".vibe-wise")
    file(join(state, "profile.md"), "Learning mode: active\n")
    const sub = dir(repo, "sub")
    const link = join(scratch(), "link")
    symlinkSync(sub, link, "dir")
    expect(activeStateDirectory(link)).toBe(state)
  })
})
