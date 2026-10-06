# /reset — VibeWise reset (Cursor port)

Back up this project's learning notes and restart onboarding after
confirmation. Does not touch code. Paths below are relative to this repo's
`ports/cursor/` directory; replace `<project dir>` with the workspace root.

1. Preview (read-only) — replace the placeholder, never pass it literally:
   ```sh
   python3 "../../../../skills/reset/reset.py" --cwd "<project dir>"
   ```
   No notes reported → nothing to reset; suggest `/learn`.
2. Show the project + state paths, what resets, and that originals land in
   that state's `backups/`. Ask **Cancel** vs **Reset learning** in plain text
   and wait. Invocation alone is not confirmation.
3. Only after **Reset learning**:
   ```sh
   python3 "../../../../skills/reset/reset.py" --cwd "<original cwd>" --confirm "<confirmation>"
   ```
   If the target changed, preview again. Report the backup path on success;
   never claim success on failure. Then resume `/learn` fresh.
