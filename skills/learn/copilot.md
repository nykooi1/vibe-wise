# VibeWise in GitHub Copilot

Follow SKILL.md and behavior.md as written. These notes adapt only host names,
paths, and interaction mechanisms.

- Slash command: `/learn` is the installed VibeWise learning skill.
- Reset: use `/reset` where the guide says `/vibe-wise:reset`.
- Paths: plugin guides are read through the normal workspace and skill file tools.
- Choices: use Copilot's native question or confirmation UI when available.
  If it is unavailable, ask one plain-text question with explicit options,
  end the turn, and wait for an answer.
- Restoration: sessionStart hooks add context from the active `.vibe-wise/`
  profile. After a resume or clear, read the complete pending sections rather
  than assuming context was preserved by the conversation alone.
