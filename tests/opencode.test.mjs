// Exercise the OpenCode plugin's hooks in isolated new and existing projects.
// Run with: node --test "tests/*.test.mjs"

import assert from "node:assert/strict"
import fs from "node:fs"
import os from "node:os"
import path from "node:path"
import { beforeEach, afterEach, test } from "node:test"
import { fileURLToPath } from "node:url"

import plugin from "../opencode/vibe-wise.js"

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..")
const SESSION = "ses_main"

let temp
let project

beforeEach(() => {
  temp = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "vibe-wise-test-")))
  project = path.join(temp, "project with spaces")
  fs.mkdirSync(path.join(project, ".git"), { recursive: true })
})

afterEach(() => fs.rmSync(temp, { recursive: true, force: true }))

function state(dir = project, { mode = "active", onboarding = "complete", name = ".vibe-wise" } = {}) {
  const directory = path.join(dir, name)
  fs.mkdirSync(directory)
  fs.writeFileSync(
    path.join(directory, "profile.md"),
    `# Learner Profile\nLearning mode: ${mode}\nOnboarding: ${onboarding}\n` +
      "Checkpoint frequency: Light\nStrong concepts: HTTP request flow\n",
  )
  fs.writeFileSync(path.join(directory, "project-map.md"), "# Project Map\nCLI → service.py → SQLite\n")
  fs.writeFileSync(path.join(directory, "progress.md"), "# Learning Progress\n## Queues\nNeeds reinforcement: retries.\n")
  return directory
}

function fakeClient(sessions = {}) {
  const calls = []
  return {
    calls,
    session: {
      async get({ path: { id } }) {
        calls.push(id)
        if (sessions[id] instanceof Error) throw sessions[id]
        return { data: sessions[id] ?? { id } }
      },
    },
  }
}

function messages(sessionID = SESSION) {
  const user = (id, text) => ({
    info: { id, sessionID, role: "user" },
    parts: [{ id: `prt_${id}`, sessionID, messageID: id, type: "text", text }],
  })
  return [
    user("msg_1", "Add a notes command."),
    { info: { id: "msg_2", sessionID, role: "assistant" }, parts: [] },
    user("msg_3", "Keep going."),
  ]
}

async function hooks({ directory = project, client = fakeClient() } = {}) {
  return plugin.server({ client, directory, worktree: directory, project: {}, $: undefined })
}

/** Run the message transform and return the injected context, or undefined. */
async function restore(options = {}) {
  const output = { messages: options.messages ?? messages() }
  await (await hooks(options))["experimental.chat.messages.transform"]({}, output)
  const first = output.messages[0].parts[0]
  return first.synthetic ? first.text : undefined
}

test("exports only a V1 server plugin with an id", () => {
  assert.equal(plugin.id, "vibe-wise")
  assert.equal(typeof plugin.server, "function")
})

test("package version matches the Claude Code plugin manifest", () => {
  const pkg = JSON.parse(fs.readFileSync(path.join(ROOT, "package.json"), "utf8"))
  const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, ".claude-plugin/plugin.json"), "utf8"))
  assert.equal(pkg.version, manifest.version)
  assert.equal(path.resolve(ROOT, pkg.main), path.join(ROOT, "opencode", "vibe-wise.js"))
})

test("config hook registers learn and reset commands", async () => {
  const config = {}
  await (await hooks()).config(config)
  assert.deepEqual(Object.keys(config.command).sort(), ["vibe-wise:learn", "vibe-wise:reset"])
  const learn = config.command["vibe-wise:learn"]
  assert.match(learn.description, /learning-first development/)
  assert.doesNotMatch(learn.template, /^---/)
  assert.match(learn.template, /# VibeWise Learn mode/)
  for (const name of ["behavior.md", "onboarding.md", "state-templates.md"]) {
    assert.ok(learn.template.includes(`<vibe-wise-guide file="${name}">`), name)
  }
  assert.match(learn.template, /`question` tool/)
})

test("guides-included note comes before any instruction to read a guide", async () => {
  // A model that reads top-down otherwise searches the disk for behavior.md and can
  // load another installed copy, which also triggers an OpenCode permission prompt.
  const config = {}
  await (await hooks()).config(config)
  state()
  const texts = { ...Object.fromEntries(Object.entries(config.command).map(([k, v]) => [k, v.template])), restore: await restore() }
  for (const [name, text] of Object.entries(texts)) {
    const note = text.indexOf("Don't search for these files")
    assert.ok(note >= 0, name)
    for (const read of [/Read \[behavior\.md\]/, /Read `[^`]*SKILL\.md`/]) {
      const at = text.search(read)
      if (at >= 0) assert.ok(note < at, `${name}: ${read}`)
    }
  }
})

test("reset command points at the installed helper", async () => {
  const config = {}
  await (await hooks()).config(config)
  const reset = config.command["vibe-wise:reset"].template
  assert.doesNotMatch(reset, /CLAUDE_PLUGIN_ROOT/)
  const helper = `${ROOT.replaceAll("\\", "/")}/skills/reset/reset.py`
  assert.ok(reset.includes(`python3 "${helper}"`), reset)
  assert.ok(fs.existsSync(helper))
})

test("command templates avoid OpenCode's template syntax", async () => {
  // OpenCode replaces $1/$ARGUMENTS, runs !`shell` blocks, and attaches @files in
  // command templates. The guides must reach the model unchanged.
  const config = {}
  await (await hooks()).config(config)
  for (const [name, { template }] of Object.entries(config.command)) {
    assert.doesNotMatch(template, /\$\d|\$ARGUMENTS/, name)
    assert.doesNotMatch(template, /!`/, name)
    assert.doesNotMatch(template, /(?<![\w`])@\.?[^\s`,.]/, name)
  }
})

test("user-defined commands take precedence", async () => {
  const mine = { template: "my learn" }
  const config = { command: { "vibe-wise:learn": mine } }
  await (await hooks()).config(config)
  assert.equal(config.command["vibe-wise:learn"], mine)
  assert.ok(config.command["vibe-wise:reset"])
})

test("fresh project is inactive and nothing is injected", async () => {
  assert.equal(await restore(), undefined)
  assert.deepEqual(fs.readdirSync(project), [".git"])
})

test("active project restores into the first user message only", async () => {
  const notes = state()
  const output = { messages: messages() }
  await (await hooks())["experimental.chat.messages.transform"]({}, output)
  const [first, , last] = output.messages
  assert.equal(first.parts.length, 2)
  assert.equal(last.parts.length, 1)
  const context = first.parts[0]
  assert.equal(context.type, "text")
  assert.equal(context.synthetic, true)
  assert.equal(context.messageID, "msg_1")
  assert.notEqual(context.id, first.parts[1].id)
  assert.ok(context.text.includes(`State directory: ${notes}`))
  assert.match(context.text, /Restarting or compacting is not approval/)
  assert.ok(context.text.includes('<vibe-wise-guide file="behavior.md">'))
  // Instructions point to notes instead of copying them.
  assert.doesNotMatch(context.text, /HTTP request flow|SQLite|retries/)
})

test("restoration is not injected twice", async () => {
  state()
  const output = { messages: messages() }
  const transform = (await hooks())["experimental.chat.messages.transform"]
  await transform({}, output)
  await transform({}, output)
  assert.equal(output.messages[0].parts.length, 2)
})

test("onboarding guide is included until onboarding is complete", async () => {
  const notes = state(project, { onboarding: "incomplete" })
  assert.ok((await restore()).includes('<vibe-wise-guide file="onboarding.md">'))
  // Without a status line, the guide is included rather than withheld.
  fs.writeFileSync(path.join(notes, "profile.md"), "# Learner Profile\nLearning mode: active\n")
  assert.ok((await restore()).includes('<vibe-wise-guide file="onboarding.md">'))
  fs.rmSync(notes, { recursive: true })
  state()
  assert.ok(!(await restore()).includes('<vibe-wise-guide file="onboarding.md">'))
})

test("existing repo restores from a nested working directory", async () => {
  const notes = state()
  const nested = path.join(project, "src", "app")
  fs.mkdirSync(nested, { recursive: true })
  assert.ok((await restore({ directory: nested })).includes(`State directory: ${notes}`))
})

test("legacy notes restore and new notes win at the same location", async () => {
  const legacy = state(project, { name: ".sensible-vibes" })
  assert.ok((await restore()).includes(`State directory: ${legacy}`))
  const current = state()
  assert.ok((await restore()).includes(`State directory: ${current}`))
})

test("nested repository and worktree do not borrow a parent profile", async () => {
  state()
  const nestedRepo = path.join(project, "vendor", "child")
  fs.mkdirSync(path.join(nestedRepo, ".git"), { recursive: true })
  assert.equal(await restore({ directory: nestedRepo }), undefined)
  const worktree = path.join(project, "worktree")
  fs.mkdirSync(worktree)
  fs.writeFileSync(path.join(worktree, ".git"), "gitdir: elsewhere\n")
  assert.equal(await restore({ directory: worktree }), undefined)
})

test("an invalid nearer state does not fall back to a parent", async () => {
  state()
  const nested = path.join(project, "pkg")
  fs.mkdirSync(nested)
  fs.writeFileSync(path.join(nested, ".vibe-wise"), "not a directory")
  assert.equal(await restore({ directory: nested }), undefined)
})

test("paused, empty, unreadable, and legacy-mode profiles", async () => {
  const notes = state(project, { mode: "paused" })
  assert.equal(await restore(), undefined)

  const profile = path.join(notes, "profile.md")
  fs.writeFileSync(profile, "# Learner Profile\n" + "Strong concepts: x\n".repeat(5000) + "Learning mode: paused\n")
  assert.equal(await restore(), undefined)

  fs.writeFileSync(profile, "  \n\n")
  assert.equal(await restore(), undefined)

  fs.writeFileSync(profile, Buffer.from([0xff, 0xfe, 0x00]))
  assert.equal(await restore(), undefined)

  fs.writeFileSync(profile, "# Learner Profile\nCheckpoint frequency: Normal\n")
  assert.ok(await restore())
})

test("symlinked state or profile is not read", async (t) => {
  const outside = state(path.join(temp))
  try {
    fs.symlinkSync(outside, path.join(project, ".vibe-wise"), "dir")
  } catch {
    t.skip("symlinks unavailable")
    return
  }
  assert.equal(await restore(), undefined)
  fs.unlinkSync(path.join(project, ".vibe-wise"))
  const notes = path.join(project, ".vibe-wise")
  fs.mkdirSync(notes)
  fs.symlinkSync(path.join(outside, "profile.md"), path.join(notes, "profile.md"))
  assert.equal(await restore(), undefined)
})

test("subagent sessions are skipped and lookups are cached", async () => {
  state()
  const client = fakeClient({ ses_child: { id: "ses_child", parentID: SESSION } })
  const transform = (await hooks({ client }))["experimental.chat.messages.transform"]
  for (let i = 0; i < 2; i++) {
    const output = { messages: messages("ses_child") }
    await transform({}, output)
    assert.equal(output.messages[0].parts.length, 1)
  }
  assert.deepEqual(client.calls, ["ses_child"])
})

test("failed session lookup still restores the main session", async () => {
  state()
  const client = fakeClient({ [SESSION]: new Error("server unavailable") })
  assert.ok(await restore({ client }))
})

test("malformed inputs are ignored", async () => {
  state()
  const transform = (await hooks())["experimental.chat.messages.transform"]
  await transform({}, { messages: [] })
  await transform({}, { messages: [{ info: { role: "user" }, parts: [] }] })
  assert.equal(await restore({ directory: "relative/path" }), undefined)
  assert.equal(await restore({ directory: path.join(temp, "missing") }), undefined)
})

test("restoration never changes learner notes", async () => {
  const notes = state()
  const before = Object.fromEntries(fs.readdirSync(notes).map((f) => [f, fs.readFileSync(path.join(notes, f), "utf8")]))
  await restore()
  const after = Object.fromEntries(fs.readdirSync(notes).map((f) => [f, fs.readFileSync(path.join(notes, f), "utf8")]))
  assert.deepEqual(after, before)
})
