# VibeWise — Cursor port

The learning-first loop from the Claude Code plugin, packaged for Cursor IDE
(answers [#13](https://github.com/nykooi1/vibe-wise/issues/13)).

## Install

Copy this port's `.cursor/` directory into your project root (next to your
code, not into it):

```sh
cp -r ports/cursor/.cursor /path/to/your/project/
```

Then type `/learn` in Cursor Chat. Learning notes live in your project's
`.vibe-wise/` (add it to `.gitignore` yourself — the port won't touch it).

## What's inside

- `.cursor/rules/vibe-wise.mdc` (`alwaysApply`) — the learning loop, always on.
- `.cursor/commands/learn.md` — activate/resume (`/learn`).
- `.cursor/commands/reset.md` — back up + restart (`/reset`, confirmation first).

Behavior, onboarding, and state templates are the canonical
`skills/learn/*.md`; the commands reference them by relative path.

## Differences from the Claude Code plugin

- **No session hook.** Cursor has no `SessionStart` equivalent, so context is
  restored when you run `/learn`, not automatically at session start.
- **Plain-text questions.** Cursor has no `AskUserQuestion` picker; choices are
  asked in chat, one at a time.
- **Reset helper path.** The plugin uses `${CLAUDE_PLUGIN_ROOT}`; here the
  commands call `skills/reset/reset.py` by path relative to this port.
- Everything else — checkpoints, confirmations, evidence rules, state format —
  is identical, so notes work in both harnesses.

MIT — same [LICENSE](../../LICENSE) as the plugin.
