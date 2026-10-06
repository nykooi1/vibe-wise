# /learn — VibeWise learning mode (Cursor port)

Activate or resume learning-first development. You lead the design; the agent
gives feedback, explains concepts, asks follow-ups, and writes the agreed code.

1. **Locate state** from the workspace root: `.vibe-wise/`, else legacy
   `.sensible-vibes/` (keep in place, never merge). Stop at `.git`. If none,
   create `.vibe-wise/` at the workspace root.
2. **Resume:** read `profile.md` + `project-map.md`, scan all of `progress.md`
   for pending decisions. Never repeat onboarding or bypass a pending checkpoint.
   Set `Learning mode: active` when resuming a pause.
3. **Fresh start:** run onboarding one question at a time in plain text
   (project → experience → preferences; "Use defaults" skips to Normal
   checkpoints, open-ended reasoning, AI writes code). Templates:
   `../../../../skills/learn/state-templates.md`.
4. Continue the build task in the learning loop (checkpoints above). Invoking
   `/learn` again resumes — it never resets. Reset lives in `reset.md`.

Full behavior: `../../../../skills/learn/behavior.md`. Onboarding flow:
`../../../../skills/learn/onboarding.md`.
