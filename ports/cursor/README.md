# VibeWise — Cursor port

The learning-first loop from the Claude Code plugin, packaged for Cursor IDE
(the Cursor request in [#13](https://github.com/nykooi1/vibe-wise/issues/13),
following the `ports/<harness>/` shape proposed in
[#18](https://github.com/nykooi1/vibe-wise/issues/18)).

## Install

Copy this port's `.cursor/` directory into your project root (next to your
code, not into it):

```sh
cp -r ports/cursor/.cursor /path/to/your/project/
```

Then type `/learn` in Cursor Chat. Learning notes live in your project's
`.vibe-wise/` (add it to `.gitignore` yourself — the port won't touch it).
Python 3 is needed only for `/reset`.

## What's inside

- `.cursor/rules/vibe-wise.mdc` (`alwaysApply`) — the learning loop, always on.
- `.cursor/commands/learn.md` — activate/resume (`/learn`).
- `.cursor/commands/reset.md` — back up + restart (`/reset`, confirmation first).
- `.cursor/vibe-wise/` — copies of the canonical `skills/learn/*.md`,
  `skills/reset/reset.py`, and the `hooks/session_start.py` helper that
  `reset.py` imports. The port carries its own copies because the `.cursor/`
  directory is copied out of this repository; commands and rules read them
  from the project root.

## Differences from the Claude Code plugin

- **No session hook.** Cursor has no `SessionStart` equivalent, so context is
  restored when you run `/learn`, not automatically at session start.
- **Plain-text questions.** Cursor has no `AskUserQuestion` picker; choices are
  asked in chat, one at a time.
- **Reset helper path.** The plugin uses `${CLAUDE_PLUGIN_ROOT}`; here `/reset`
  runs `.cursor/vibe-wise/skills/reset/reset.py` from the project root.
- **Vendored guides.** Behavior, onboarding, state templates, and the reset
  helper are byte-identical copies of the canonical files at this commit. The
  copied tree cannot reach back into this repository, so the port carries them
  rather than linking. Re-copy `.cursor/` after `git pull` to pick up guide
  changes; existing notes are untouched.
- Everything else — checkpoints, confirmations, evidence rules, state format —
  is identical, so notes work in both harnesses.

`tests/test_cursor_port.py` keeps the copies in sync with the canonical files
and checks that the copied tree resolves and runs from a project root itself.

MIT — same [LICENSE](../../LICENSE) as the plugin.
