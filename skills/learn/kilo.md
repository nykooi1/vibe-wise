# VibeWise in Kilo Code

These notes adapt Claude Code tool and command names for the Kilo CLI and VS Code
extension. They don't change the learning behavior; follow SKILL.md and its guides
as written. AskUserQuestion becomes the `question` tool; the rest is unchanged.

- Commands: `/vibe-wise:learn` and `/vibe-wise:reset` are the same as in Claude Code.
- Paths: `${CLAUDE_PLUGIN_ROOT}` may not be expanded in Kilo. The command message
  provides the plugin's absolute root; use that path for the guides and helpers.
  Guides such as behavior.md sit beside SKILL.md.
- Files: use the Read and Glob tools as written. Check optional learner-state files
  with a conditional that succeeds when they're missing.
- Choices: AskUserQuestion becomes Kilo's `question` tool. Ask exactly one question
  with 2–4 short options and brief descriptions and no multi-select; use the native
  picker, not a printed imitation. If it's unavailable, ask one plain-text question.
  Open-ended reasoning questions stay in chat.
- Restoration: Kilo injects a VibeWise restore instruction at session start and again
  after compaction whenever `.vibe-wise/profile.md` is active. If context was
  compacted and you're unsure whether a decision is pending, search progress.md
  before acting. Do not infer that no decision is pending from an initial excerpt.
- Replies: present each checkpoint or question once, at the end of your reply, with
  its options beneath it. Don't restate it in a separate message, add a closing line
  after it, or quote these guides to the learner.
