<img src=".claude-plugin/icon.svg" alt="VibeWise brain with code brackets" width="96" height="96">

# VibeWise for Pi

**You build. AI writes.**

VibeWise is a learning-first coding workflow for [Pi](https://pi.dev) and Claude
Code. The coding agent asks for your approach first, helps you examine tradeoffs,
and explains unfamiliar concepts. You shape the design and decide when it is ready
to implement. The coding agent writes the agreed code, then explains what changed.

This repository is an unofficial Pi port of
[nykooi1/vibe-wise](https://github.com/nykooi1/vibe-wise). It keeps the upstream
Claude Code plugin and adds native Pi lifecycle support. Both hosts use the same
local `.vibe-wise/` project state.

For anyone who wants to learn as they build—whether you are an aspiring engineer,
a junior developer, or an experienced engineer exploring an unfamiliar stack.
Practice planning how the pieces fit together, anticipating failures, and checking
the result while keeping ownership of the decisions.

## Install for Pi

You need [Pi](https://pi.dev) and [Python 3](https://www.python.org/downloads/).
Python runs state resolution, session restoration, and the confirmed reset helper.
It needs no extra Python packages.

Install the public package from npm:

```sh
pi install npm:@yuritoledo/vibe-wise-pi
```

Start Pi in the project you want to work on, then run:

```text
/skill:learn
```

To start that project's learning state again from a confirmed backup, run:

```text
/skill:reset
```

## Install for Claude Code

The original Claude Code plugin remains available in this fork. Run these commands
one at a time in Claude Code:

```text
/plugin marketplace add yuritoledo/vibe-wise-pi
```

```text
/plugin install vibe-wise@vibe-wise
```

Restart Claude Code in the project you want to work on, then run:

```text
/vibe-wise:learn
```

For the upstream marketplace and release stream, use the
[original project](https://github.com/nykooi1/vibe-wise).

Setup asks one question at a time. Use the arrow keys and Enter for choices; pick
**Use defaults** to skip preference setup. Then ask the coding agent to build
something. Starting fresh or joining an unfamiliar repository both work. For an
existing repository, the coding agent first inspects the code and sketches a small
system map.

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

**Pi:**

```text
✦ Build checkpoint: Deleting a shared note

"Trip ideas" is in both Travel and Summer. Deleting it removes it from both.

When someone deletes Travel, what should happen to that note in Summer?
```

**You:**

```text
Keep it in Summer. If it has no folders left, keep the note outside any folder.
```

**Pi:**

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

**Pi:**

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

**Pi:**

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

*Pi writes the code and runs the tests.*

**Pi:**

```text
✦ Implementation report: Folder membership

- Added the schema migration: each membership references one note and one folder.
- Added folder deletion: removes the folder and its links, preserving note content.
- Added and ran tests for shared notes and notes left without a folder; both passed.
```

You don't need to know the answer already. Pi can explain unfamiliar concepts, sketch the relevant pieces, and help you tackle a smaller question. You stay involved in forming the plan. Answer in plain English; ask for more help or say “skip” whenever you want.

Describing what you want sets the requirements. Build Checkpoints ask you to work
out how it should function; a feature preference doesn't approve an architecture.

| Checkpoint | What happens |
| --- | --- |
| **Build** | You reason through how to approach the problem with Pi. |
| **Design** | Review the design. **Confirm and continue** records it and continues planning; no code yet. |
| **Implementation** | Review the specific code changes. **Implement this step** authorizes Pi to make them. |

These aren't three mandatory stops. When ready to code, the Implementation
checkpoint also confirms the design, skipping a separate Design checkpoint.
Both confirmations offer **Discuss** to ask questions, clarify anything confusing,
or explore alternatives before deciding.

When Pi proposes additional implementation details, it separates them from your
decisions in a short list or table explaining each addition and why it matters.
You can question or change any item before proceeding.

After implementation, Pi briefly explains what changed, how the key code works,
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

Everyone reasons first. Pi adapts to what you demonstrate and how familiar you
are with the stack. Checkpoint frequency—Light, Normal, or Frequent—is separate.

- “Use fewer checkpoints.”
- “Focus on backend architecture.”
- “Use multiple-choice questions.”
- “Just implement this one.”
- Run `/skill:learn-light` in Pi or `/vibe-wise:learn-light` in Claude Code for short
  guided questions. Say “stop Learn-light” to return to your previous workflow.
- “Pause learning.” Resume with `/skill:learn` in Pi or `/vibe-wise:learn` in Claude Code.

Learning notes use three scopes:

- Personal preferences and general experience: `~/.config/vibe-wise/profile.md`.
- Project onboarding and verified project map: `~/.config/vibe-wise/projects/<key>/`.
- Task progress and pending approvals: `.vibe-wise/progress.md` in each worktree.

An absolute `XDG_CONFIG_HOME` replaces `~/.config`. The key comes from Git's common
directory. Linked worktrees share onboarding; separate clones do not. A new
worktree restores project knowledge without importing another worktree's approvals.

Learning mode resumes in future sessions and after compaction. Existing local
profiles in `.vibe-wise/` or `.sensible-vibes/` keep their local behavior. VibeWise
does not move or merge them automatically. Add `.vibe-wise/` to your `.gitignore`
to keep task notes out of Git; VibeWise will not change it silently.

No extra account, backend, or telemetry. Saved notes enter the coding agent's context,
so the data settings of your selected model provider and host apply.

To start learning this project from scratch, run `/skill:reset` in Pi or
`/vibe-wise:reset` in Claude Code. It shows the project and asks **Cancel / Reset
learning**. After confirmation, it backs up and resets project onboarding, the
project map, and this worktree's progress. Shared project notes affect all linked
worktrees; global preferences and other worktrees' progress stay intact. With a
legacy local profile, reset backs up and clears that local profile, progress, and
map instead. Backups stay under the local notes directory's `backups/` folder.
Source code and other projects stay untouched. To change your experience level or
preferences, tell the coding agent; no reset is needed.

## Updating

Update the Pi package with:

```sh
pi update --extensions
```

Run `pi list` to check the installed package. Your project learning notes stay intact;
no reset is needed.

For Claude Code automatic updates, open `/plugin` → **Marketplaces** → **vibe-wise** →
**Enable auto-update**. To update manually, run:

```sh
claude plugin marketplace update vibe-wise
claude plugin update vibe-wise@vibe-wise
```

Restart Claude Code after an update. Run `claude plugin list` to check the installed
version. See the [Claude Code plugin update documentation](https://code.claude.com/docs/en/discover-plugins#keep-plugins-updated).

## License and attribution

This project is a derivative of [VibeWise](https://github.com/nykooi1/vibe-wise) by
Noah Kim. It remains available under the [MIT License](LICENSE). Keep the copyright
and license notice with copies. The software comes without a warranty.
