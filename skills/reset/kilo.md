# VibeWise Reset in Kilo Code

These notes adapt Claude Code tool and command names for the Kilo CLI and VS Code
extension. Follow SKILL.md as written otherwise. AskUserQuestion becomes the
`question` tool; the rest is unchanged.

- Paths: `${CLAUDE_PLUGIN_ROOT}` may not be expanded in Kilo. The command message
  provides the plugin's absolute root; run the helper from there:
  `<plugin root>/skills/reset/reset.py`, using its absolute path. The Learn guide is
  `<plugin root>/skills/learn/SKILL.md`.
- Commands: suggest `/vibe-wise:learn` where SKILL.md says `/vibe-wise:learn`.
- Choices: AskUserQuestion becomes Kilo's `question` tool. Ask header `Reset`, one
  question, single select, options **Cancel** (keep learning notes) and
  **Reset learning** (back up notes and restart onboarding). If it's unavailable,
  ask the same question in text. Then end your turn and wait for an explicit answer.
- Replies: ask the confirmation once, at the end of your reply. Don't add a closing
  line after it or quote these guides to the learner.
