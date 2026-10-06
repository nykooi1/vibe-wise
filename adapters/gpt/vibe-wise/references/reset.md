# Reset local learning notes

Only reset at the user's explicit request. Source code and other projects are out
of scope. If there is no filesystem, explain that reset only clears the active
learning snapshot, not the chat transcript or the platform's stored memory.

1. Preview with `python "<skill directory>/scripts/reset.py" --cwd "<absolute project directory>"`.
   On an error, stop. If no notes exist, report that and offer normal onboarding.
2. Show the exact project, files, and backup destination. If the user's existing
   request already explicitly covers resetting these notes with a backup, proceed.
   Otherwise ask whether to reset those notes and wait; silence is not consent.
3. Run the same command with `--confirm "<preview confirmation token>"`. Safely
   quote actual paths and token; never run placeholders. If the target changed,
   preview again and establish consent for any changed scope before retrying.
4. Only on success, report the backup path and restart onboarding. Discard old
   learning preferences and pending decisions; do not restore them from backups.
   On partial failure, report the error and backup location; inspect active notes
   before proceeding. Never improvise deletion commands or remove backups.
