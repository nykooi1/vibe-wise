<img src=".claude-plugin/icon.svg" alt="VibeWise brain with code brackets" width="96" height="96">

# VibeWise

**You build. AI writes.**

A Claude Code plugin that puts learning first and keeps you in control while AI writes the code you designed. Claude **asks for your approach first**, helps you examine tradeoffs, and explains unfamiliar concepts. You shape the design and decide when it's ready to implement. Claude writes the code, then explains what it changed and why.

For anyone who wants to learn as they build—whether you're an aspiring engineer, a junior developer, or an experienced engineer exploring an unfamiliar stack. Practice planning how the pieces fit together, anticipating failures, and checking the result while keeping ownership of the decisions.

## Get started

You need an up-to-date [Claude Code](https://code.claude.com/docs/en/setup) and
[Python 3](https://www.python.org/downloads/). VibeWise uses Python to restore
learning context and reset learning notes. No extra Python packages are needed.

Install from the built-in **Anthropic Directory**. In Claude Code, run:

```text
/plugin install vibe-wise@anthropic-plugin-directory
```

Choose an installation scope and confirm. No marketplace setup is needed.

Restart Claude Code in the project you want to work on, then run:

```text
/vibe-wise:learn
```

Setup asks one question at a time. Use the arrow keys and Enter for choices; pick **Use defaults** to skip preference setup. Then ask Claude to build something. Starting fresh or joining an unfamiliar repository both work. For an existing repository, Claude first inspects the code and sketches a small system map.

<details>
<summary>Alternative: install through GitHub</summary>

If Anthropic Directory isn't available in your Claude Code version, use the GitHub
marketplace. Choose one installation method; you don't need both.

Run these commands **one at a time** in Claude Code. First, add the marketplace:

```text
/plugin marketplace add nykooi1/vibe-wise
```

After it finishes, install the plugin:

```text
/plugin install vibe-wise@vibe-wise
```

Enable automatic updates through `/plugin` → **Marketplaces** → **vibe-wise** →
**Enable auto-update**. This is off by default for third-party marketplaces.
Restart Claude Code, then run `/vibe-wise:learn` in your project.

</details>

## What it feels like

You're building a Notion-style notes app: users sign in, create and edit private
notes, and organize them into folders. Here, you're working through how notes and
folders relate—and what should happen when someone deletes a folder.

This condensed example is adapted from a real learning session. Later implementation
steps are illustrative; intervening design discussions are omitted.

**You:**

```text
A note can be in several folders. Deleting a folder should delete its notes.
```

**Claude:**

```text
✦ Build checkpoint: Deleting a shared note

"Trip ideas" is in both Travel and Summer. Deleting it removes it from both.

When someone deletes Travel, what should happen to that note in Summer?
```

**You:**

```text
Keep it in Summer. If it has no folders left, keep the note outside any folder.
```

**Claude:**

```text
That separates deleting a folder from deleting a note.

✦ Build checkpoint: Connecting notes and folders

How would you represent which folders a note belongs to, without copying the note?
```

**You:**

```text
A links table with note_id and folder_id. Deleting a folder removes its links,
not the notes.
```

**Claude:**

```text
Each link records one membership. Several links can point to the same note;
a note with no links is unfiled.

notes ← folder links → folders

✦ Design checkpoint: Folder membership

Proposed: store notes once and track folder membership in a links table.
Deleting a folder removes its links and keeps the notes. This supports multiple
folders per note; loading a folder's notes needs a lookup through those links.

Confirming records this design. We still need to work through access rules
and technology choices before writing code.

❯ 1. Confirm and continue
     This approach makes sense to me; move to the next piece.
  2. Discuss
     Ask questions or clarify anything that doesn't make sense before deciding.
```

**You:**

```text
Confirm and continue.
```

*Later, after the remaining choices for this step are worked through...*

**Claude:**

```text
✦ Implementation checkpoint: Folder membership

I'll add the agreed tables and folder-deletion operation, then test that deleting
a folder preserves its notes and their membership in other folders.
This step builds storage behavior; the UI comes later.

❯ 1. Implement this step
     This approach makes sense to me; write the code for this step.
  2. Discuss
     Ask questions or clarify anything that doesn't make sense before deciding.
```

**You:**

```text
Implement this step.
```

*Claude writes the code and runs the tests.*

**Claude:**

```text
✦ Implementation report: Folder membership

- Added the schema migration: each membership references one note and one folder.
- Added folder deletion: removes the folder and its links, preserving note content.
- Added and ran tests for shared notes and notes left without a folder; both passed.
```

You don't need to know the answer already. Claude can explain unfamiliar concepts, sketch the relevant pieces, and help you tackle a smaller question. You stay involved in forming the plan. Answer in plain English; ask for more help or say “skip” whenever you want.

Describing what you want sets the requirements. Build Checkpoints ask you to work
out how it should function; a feature preference doesn't approve an architecture.

| Checkpoint | What happens |
| --- | --- |
| **Build** | You reason through how to approach the problem with Claude. |
| **Design** | Review the design. **Confirm and continue** records it and continues planning; no code yet. |
| **Implementation** | Review the specific code changes. **Implement this step** authorizes Claude to make them. |

These aren't three mandatory stops. When ready to code, the Implementation
checkpoint also confirms the design, skipping a separate Design checkpoint.
Both confirmations offer **Discuss** to ask questions, clarify anything confusing,
or explore alternatives before deciding.

When Claude proposes additional implementation details, it separates them from your
decisions in a short list or table explaining each addition and why it matters.
You can question or change any item before proceeding.

After implementation, Claude briefly explains what changed, how the key code works,
why it fits your decision, any tests it added or updated and what they cover, and
which checks ran with their results. Ask to dig deeper anywhere it's unclear.

Small diagrams help you trace data, understand relationships, and see how the system fits together.

## Make it yours

Experience changes the support you get, not your ownership of decisions:

| Level | Teaching approach |
| --- | --- |
| Beginner | Explain unfamiliar pieces, use diagrams, ask smaller reasoning questions. |
| Intermediate | Less introductory context; explore interactions and tradeoffs. |
| Advanced | Probe difficult constraints, failure modes, and design assumptions. |

Everyone reasons first. Claude adapts to what you demonstrate and how familiar you
are with the stack. Checkpoint frequency—Light, Normal, or Frequent—is separate.

- “Use fewer checkpoints.”
- “Focus on backend architecture.”
- “Use multiple-choice questions.”
- “Just implement this one.”
- “Pause learning.” Resume with `/vibe-wise:learn`.

Preferences, learning notes, and a project map live in `.vibe-wise/` in your project. Learning mode resumes in future sessions and after compaction. Add `.vibe-wise/` to your `.gitignore` to keep your notes out of Git; the plugin won't change it silently.

No extra account, backend, or telemetry. Saved notes are included in Claude's context, so your normal Claude Code data settings still apply.

To start learning this project from scratch, run `/vibe-wise:reset`. It shows the
project and asks **Cancel / Reset learning**. After confirmation, it backs up your
profile, progress, and project map inside the notes directory's `backups/` folder,
then restarts onboarding. Source code and other projects stay untouched. To change
your experience level or preferences, just tell Claude; no reset is needed.

## Updating

Open `/plugin` → **Installed**, select VibeWise, and choose **Update now**.
For automatic updates, open **Marketplaces**, select the source you installed from,
and enable auto-update if it's off.

To update a directory installation from your terminal:

```sh
claude plugin update vibe-wise@anthropic-plugin-directory
```

If you installed through the GitHub marketplace instead:

```sh
claude plugin marketplace update vibe-wise
claude plugin update vibe-wise@vibe-wise
```

Then restart Claude Code. Your project learning notes stay intact; no reset is needed.
Run `claude plugin list` to check the installed version.
[More about plugin updates](https://code.claude.com/docs/en/discover-plugins#keep-plugins-updated).

## OpenCode

VibeWise also works in [OpenCode](https://opencode.ai/docs/) (docs checked Oct 2026).
OpenCode has no plugin marketplace, so you install from this repository once and
the skills, commands, and hook wrapper become available in **every repo**.

You need [OpenCode](https://opencode.ai/docs/), [Python 3](https://www.python.org/downloads/)
on your `PATH`, and [Bun](https://bun.com) (OpenCode uses it to run the plugin).

1. Clone this repository anywhere and remember the path:

   ```sh
   git clone https://github.com/nykooi1/vibe-wise.git ~/tools/vibe-wise
   ```

2. Run the installer. It symlinks the skills, commands, and the compaction
   plugin into your OpenCode config so VibeWise works in every project:

   ```sh
   python3 ~/tools/vibe-wise/scripts/install-opencode.py
   ```

   Skills load through OpenCode's `skill` tool, `/vibe-wise-learn` and
   `/vibe-wise-reset` become slash commands, and `vibe-wise.ts` restores learning
   context when a session compacts. Re-running the installer is safe; it changes
   nothing when everything is already in place. Use `--dest <dir>` for a custom
   config location, `--copy` on Windows or where symlinks are unavailable,
   `--force` to replace conflicting files, and `--remove` to uninstall.

3. Start `opencode` in any project and run `/vibe-wise-learn`. First-time setup
   asks one question at a time, exactly like Claude Code. `/vibe-wise-reset`
   backs up the notes and restarts onboarding after confirmation.

<details>
<summary>Alternative: manual install</summary>

```sh
mkdir -p ~/.config/opencode/skills ~/.config/opencode/commands ~/.config/opencode/plugins
ln -s ~/tools/vibe-wise/skills/learn ~/.config/opencode/skills/learn
ln -s ~/tools/vibe-wise/skills/reset ~/.config/opencode/skills/reset
ln -s ~/tools/vibe-wise/.opencode/commands/vibe-wise-learn.md ~/.config/opencode/commands/vibe-wise-learn.md
ln -s ~/tools/vibe-wise/.opencode/commands/vibe-wise-reset.md ~/.config/opencode/commands/vibe-wise-reset.md
ln -s ~/tools/vibe-wise/.opencode/plugins/vibe-wise.ts ~/.config/opencode/plugins/vibe-wise.ts
```

On Windows, copy the files instead of symlinking; they resolve their own
paths from their real location, so copies keep working.

</details>

Notes live in `.vibe-wise/` in each project, shared with Claude Code — you can
switch hosts mid-project and the same notes load. Differences from Claude Code:

- The SessionStart hook has no OpenCode equivalent, so startup restore relies
  on rules in `AGENTS.md` (OpenCode reads it every session) and the `learn`
  skill itself; compaction restore is wrapped by the plugin.
- Skills' slash commands are OpenCode commands (`/vibe-wise-learn`,
  `/vibe-wise-reset`) instead of Claude Code namespaced commands
  (`/vibe-wise:learn`). OpenCode takes command names from file names and has
  no namespace separator, so they get a `vibe-wise-` prefix instead.
- The plugin runs `hooks/session_start.py` and injects its context only into
  compaction. If OpenCode's plugin API changes, the wrapper fails silently and
  learning still works — run `/vibe-wise-learn` to restore manually.

To update, `git pull` in your clone; symlinks follow.

## License

[MIT](LICENSE). You can use, modify, and share this software, including commercially. Keep the license notice with copies. The software comes without a warranty.
