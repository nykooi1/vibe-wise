# VibeWise Reset in Codex

These notes adapt Claude Code tool and command names for Codex. Follow SKILL.md
as written otherwise.

- Paths: `${CLAUDE_PLUGIN_ROOT}` is not expanded in Codex. Run `reset.py` from
  this file's directory, using its absolute path. The Learn guide is
  `../learn/SKILL.md` relative to this file.
- Commands: suggest `$vibe-wise:learn` where SKILL.md says `/vibe-wise:learn`.
- Choices: AskUserQuestion doesn't exist here. If a native question tool such as
  `request_user_input` is available, use it with the same options; otherwise ask
  the same question in text. Then end your turn and wait for an explicit answer.
- Replies: ask the confirmation once, at the end of your reply. Don't add a
  closing line after it or quote these guides to the user.
