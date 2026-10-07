# VibeWise

Learning-first Claude Code plugin. Claude Code layout in `skills/` and
`hooks/` is the source of truth. Do not move or rename those files.

## OpenCode compatibility

- `.opencode/skills/learn` and `.opencode/skills/reset` are symlinks to
  `../skills/<name>`. Edit skill content only under `skills/`.
- `.opencode/commands/*.md` are thin wrappers that load the matching skill.
  OpenCode takes command names from file names with no namespace separator,
  so they are `vibe-wise-learn.md` and `vibe-wise-reset.md` (`/vibe-wise-learn`,
  `/vibe-wise-reset`); the skills themselves stay named `learn`/`reset`.
- Skill scripts are plain Python 3 stdlib; run them with `python3`.
- Python helper entry points: `skills/reset/reset.py`,
  `hooks/session_start.py` (used by the Claude Code SessionStart hook).
- Tests: `python3 -m pytest tests/` (or `pytest tests/`).

## Learning context

If `.vibe-wise/profile.md` exists (or legacy `.sensible-vibes/`) and does not
say `Learning mode: paused`, restore learning context before coding: read
`profile.md` and `project-map.md`, search the whole `progress.md` for pending
decisions, then follow the `learn` skill. Missing state directory means
first-time setup; onboarding happens only through the `learn` skill.

## Conventions

- Skill frontmatter: keep to `name` and `description`; other hosts ignore
  unknown fields.
- Keep skill instructions path-agnostic (no `${CLAUDE_PLUGIN_ROOT}` in
  `skills/` markdown); resolve script paths relative to the skill directory.