import type { Plugin } from "@opencode-ai/plugin"

// OpenCode port of the Claude Code SessionStart hook (hooks/hooks.json).
// Runs the same read-only restore script and injects its additionalContext
// into the compaction prompt. Startup restore is handled by AGENTS.md,
// which is always in context. Edit the Python script, not this wrapper.
export const VibeWise: Plugin = async ({ directory }) => {
  // Resolve the script relative to this file, not the user's project,
  // so the plugin works when .opencode/ is symlinked or copied.
  const script = new URL("../../hooks/session_start.py", import.meta.url).pathname

  async function restore(): Promise<string | undefined> {
    // Same payload shape as the Claude Code hook event, sent on stdin.
    const payload = JSON.stringify({
      hook_event_name: "SessionStart",
      cwd: directory,
    })
    try {
      const proc = Bun.spawn(["python3", script], {
        cwd: directory,
        stdin: "pipe",
        stdout: "pipe",
        stderr: "pipe",
      })
      proc.stdin.write(payload)
      proc.stdin.end()
      const stdout = await new Response(proc.stdout).text()
      const exitCode = await proc.exited
      if (exitCode !== 0 || !stdout.trim()) return undefined
      return JSON.parse(stdout)?.hookSpecificOutput?.additionalContext
    } catch {
      // Learning must never block a coding session.
      return undefined
    }
  }

  return {
    "experimental.session.compacting": async (_input, output) => {
      const context = await restore()
      if (context) output.context.push(context)
    },
  }
}