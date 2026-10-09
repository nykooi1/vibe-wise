---
name: learn
description: Activate or resume learning-first development. You lead the design; the agent gives feedback, explains concepts, asks follow-ups, and writes the agreed code.
disable-model-invocation: true
---

# VibeWise Learn mode

Activate learning mode in the main conversation. Read [behavior.md](behavior.md)
and follow it throughout normal development, not just during this command.
The learner owns the design. Ask for their approach and wait. Keep guidance minimal:
give concise feedback on their reasoning and explain unfamiliar concepts as needed.
Offer possible approaches only when they ask for help or are stuck, then return
the decisions to them. Learning and learner control take priority over build speed.
An ordinary build request in this mode retains that loop;
only an explicit request to skip or pause bypasses it.
Do not switch to a subagent or require manual coding by default.

If you are running in Codex rather than Claude Code, first read [codex.md](codex.md).

On Claude Code, use Read for guides and Glob for optional state discovery.
On Hermes, load this skill with `skill_view(name="vibe-wise:learn")`; read bundled
guides with `skill_view(name="vibe-wise:learn", file_path="behavior.md")` (and the
corresponding filenames for onboarding and templates). Use `read_file` and
`terminal` for project notes and discovery. Resolve the actual session workspace
through those tools; never assume the plugin directory is the project.
A missing `.vibe-wise/` directory is normal first-time setup, not an error. If a shell
check is necessary, handle absence with an explicit conditional that succeeds;
don't run `ls` on a possibly missing directory or hide actual read failures.
Keep guide reads separate from optional state checks so a missing file doesn't
make a successful instruction read look like a failed tool call.

## Locate state

Starting at the current working directory, look upward for `.vibe-wise/` or legacy
`.sensible-vibes/`, preferring `.vibe-wise/` when both exist at the same level,
stopping at the nearest `.git` directory or file (including a worktree root).
Use the nearest existing state directory within that boundary. Without Git, check
only the current directory; don't search its parents. Keep using legacy
notes in place; never merge, move, or reset them automatically. If there is none,
create `.vibe-wise/` at the Git root, or current directory without Git. Do not use
state from a parent repository, another worktree, or the installed plugin folder.
Do not follow symlinked state directories or files; explain the issue instead.

If `profile.md` exists, read it and `project-map.md`. Search the entire `progress.md`
for pending decisions, then read their complete sections and other topics relevant
to the task. An initial excerpt is not evidence that nothing is pending.
Resume without repeating completed onboarding or bypassing a pending Design or
Implementation checkpoint.
Set `Learning mode: active` if the user is resuming paused learning. If onboarding
is incomplete, ask only the unanswered questions. Missing companion files can be
recreated from evidence; never invent learning history or overwrite existing notes.

If no profile exists and the user explicitly invoked Learn, read
[state-templates.md](state-templates.md) and create the three initial note files
BEFORE asking the first onboarding question or Build checkpoint. Set
`Learning mode: active` and `Onboarding: incomplete`, record known requirements
and preferences, and leave unknown answers as `Not specified`. Do not invent
learning history. Save only missing files; preserve any existing companion notes.
Verify the files exist and report their absolute directory. If saving fails,
explain the error rather than claiming persistent learning is active.
Then read [onboarding.md](onboarding.md) and run onboarding, updating the saved
profile between turns. Choosing defaults does not skip creating learning notes.
An automatic restoration check without explicit activation must not create a
fresh profile or start onboarding.
Use [state-templates.md](state-templates.md) when creating state. These files are
local Markdown maintained with normal file tools; there is no service to call.

After setup, continue the user's build task. If none was provided, ask what they
want to build or change. Invoking this skill again should not reset anything.
