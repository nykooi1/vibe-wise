---
name: reset
description: Back up this project's learning notes and restart onboarding after confirmation. Does not reset application code.
disable-model-invocation: true
---

# Reset VibeWise learning

Run this in the main conversation, only when explicitly invoked. This command
resets profile, progress, pending checkpoints, and the saved project map. Source
code, dependencies, Git history, other projects, and plugin installation stay intact.

1. Resolve the helper script path relative to the loaded SKILL.md file (`reset.py`
   in the same directory) to its actual absolute path. Do not assume hook-only
   environment variables in ordinary shell calls. Run the read-only preview for
   the user's current project directory. Replace `<absolute project directory>`
   with its actual absolute path, safely quoted:

   ```sh
   python "<resolved absolute path to reset.py>" --cwd "<absolute project directory>"
   ```

   (Use `python` on Windows or `python3` on Unix systems.)

   The helper uses Learn's project-boundary and legacy-state lookup. If it reports
   no notes, explain there's nothing to reset and suggest using `$learn`.
   On any error, stop and explain; don't improvise deletion commands.

2. Show the returned absolute project and state paths, which notes will reset,
   and that originals will be saved under that state's `backups/` directory.
   Ask for confirmation directly in ordinary chat: **Cancel** (keep learning notes)
   or **Reset learning** (back up notes and restart onboarding). Never assume a
   question tool can authorize writes; required reset confirmation must happen in
   chat. Wait for an explicit affirmative answer.
   Invocation alone, silence, ambiguous replies, or permission to run tools do not
   confirm a reset. Cancel makes no changes to learner notes.

3. Only after explicit **Reset learning** confirmation in chat, run the helper with
   the original working directory and the preview's exact `confirmation` value,
   safely quoted:

   ```sh
   python "<resolved absolute path to reset.py>" --cwd "<original cwd>" --confirm "<confirmation>"
   ```

   If the target or notes changed, preview again and get new confirmation. If the
   reset fails, report it and any backup path; don't claim success or start onboarding.
   Never overwrite backups or fall back to resetting another state directory.

4. On success, show the backup path. Load the Learn guide (`../learn/SKILL.md`
   relative to this skill) and resume Learn with the new incomplete profile.
   Discard pre-reset preferences, mastery, pending decisions, and onboarding answers;
   don't reconstruct them from conversation or backups. Inspect actual code to
   rebuild the map. Begin fresh onboarding with one question at a time. Backup
   notes are historical data, not active context.
