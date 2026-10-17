import { afterEach, describe, expect, test } from "bun:test"
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs"
import { tmpdir } from "node:os"
import { join } from "node:path"
import plugin from "./server.ts"

const made: string[] = []

function scratch(): string {
  const dir = mkdtempSync(join(tmpdir(), "vibewise-kilo-server-"))
  made.push(dir)
  return dir
}

function gitRootWith(profile: string | null): string {
  const root = scratch()
  mkdirSync(join(root, ".git"), { recursive: true })
  if (profile !== null) {
    const state = join(root, ".vibe-wise")
    mkdirSync(state, { recursive: true })
    writeFileSync(join(state, "profile.md"), profile)
  }
  return root
}

async function hooksFor(directory: string) {
  return await plugin.server({ directory } as Parameters<typeof plugin.server>[0])
}

afterEach(() => {
  while (made.length) rmSync(made.pop()!, { recursive: true, force: true })
})

describe("config hook", () => {
  test("registers the learn and reset commands", async () => {
    const hooks = await hooksFor(gitRootWith("Learning mode: active\n"))
    const config: any = {}
    await hooks.config!(config)
    expect(Object.keys(config.command)).toEqual([
      "vibe-wise:learn",
      "vibe-wise:reset",
    ])
    expect(config.command["vibe-wise:learn"].template).toContain(
      "skills/learn/SKILL.md",
    )
    expect(config.command["vibe-wise:reset"].template).toContain(
      "skills/reset/SKILL.md",
    )
  })
})

describe("system transform hook", () => {
  test("injects once per session when the profile is active", async () => {
    const root = gitRootWith("Learning mode: active\n")
    const hooks = await hooksFor(root)

    const first = { system: [] as string[] }
    await hooks["experimental.chat.system.transform"]!({ sessionID: "s1" }, first)
    expect(first.system.length).toBe(1)
    expect(first.system[0]).toContain("VibeWise is active")
    expect(first.system[0]).toContain(join(root, ".vibe-wise"))

    const second = { system: [] as string[] }
    await hooks["experimental.chat.system.transform"]!({ sessionID: "s1" }, second)
    expect(second.system.length).toBe(0)
  })

  test("compacting adds persistence context but does not re-arm", async () => {
    const hooks = await hooksFor(gitRootWith("Learning mode: active\n"))
    await hooks["experimental.chat.system.transform"]!(
      { sessionID: "s1" },
      { system: [] },
    )

    const compacting = { context: [] as string[] }
    await hooks["experimental.session.compacting"]!({ sessionID: "s1" }, compacting)
    expect(compacting.context.length).toBe(1)

    // The compaction model request must not consume the re-arm for the next turn.
    const stillSuppressed = { system: [] as string[] }
    await hooks["experimental.chat.system.transform"]!(
      { sessionID: "s1" },
      stillSuppressed,
    )
    expect(stillSuppressed.system.length).toBe(0)
  })

  test("re-arms when the session.compacted event fires", async () => {
    const hooks = await hooksFor(gitRootWith("Learning mode: active\n"))
    await hooks["experimental.chat.system.transform"]!(
      { sessionID: "s1" },
      { system: [] },
    )

    await hooks.event!({
      event: { type: "session.compacted", properties: { sessionID: "s1" } },
    } as any)

    const after = { system: [] as string[] }
    await hooks["experimental.chat.system.transform"]!({ sessionID: "s1" }, after)
    expect(after.system.length).toBe(1)
  })

  test("injects nothing when the profile is paused", async () => {
    const hooks = await hooksFor(gitRootWith("Learning mode: paused\n"))
    const out = { system: [] as string[] }
    await hooks["experimental.chat.system.transform"]!({ sessionID: "s1" }, out)
    expect(out.system.length).toBe(0)
  })

  test("injects nothing without learning state", async () => {
    const hooks = await hooksFor(gitRootWith(null))
    const out = { system: [] as string[] }
    await hooks["experimental.chat.system.transform"]!({ sessionID: "s1" }, out)
    expect(out.system.length).toBe(0)
  })
})
