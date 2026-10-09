# Development

V1 uses Claude Code skills, Markdown instructions, one read-only Python hook,
and a small Python helper for confirmed learning resets.
There are no packages to install. Python 3.8+ is sufficient for the hook and tests.

## Local checks

```sh
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .claude-plugin/marketplace.json
claude plugin validate skills
python3 -B -m unittest discover -s tests -v
git diff --check
```

The tests execute the registered hook command with real JSON stdin in temporary
projects. They cover activation, restoration, partial onboarding, paused mode,
subdirectories, repository/worktree boundaries, missing/invalid files, symlinks,
constant-size restoration instructions as notes grow, and read-only behavior.
They do not prove that Claude follows the instructions or teaches well.
Rename coverage verifies that `.sensible-vibes/` notes restore without migration,
`.vibe-wise/` takes precedence at the same location, and legacy lookup preserves
repository boundaries, nearest-state selection, and symlink rejection.
Reset tests cover read-only preview, confirmed backup/reset, stale confirmation,
legacy and partial notes, nested projects, repeated backups, rejected symlinks,
backup/write failures, and restoring incomplete onboarding after reset.

## Hermes checks

The `.hermes-plugin/plugin.yaml` and `.hermes-plugin/__init__.py` files register
the shared Learn and Reset skills and a `pre_llm_call` restoration hook.
No additional Python dependencies are needed.
The hook has no authoritative workspace path, so it asks the agent to inspect its
own workspace instead of reading notes from the host process's working directory.
It does not read or write learner notes itself, and skips delegated child sessions.

```sh
hermes plugins doctor . --ci
python3 -B -m unittest discover -s tests -v
```

Run Plugin Doctor on the repository root, not `.hermes-plugin/` alone: its isolated
copy must include the shared skill files. Hermes discovers the manifest one level
below the installed repository. The adapter resolves guides relative to its own
location, independently of the session's working directory.

For local testing, copy the entire checkout to `$HERMES_HOME/plugins/vibe-wise` (default
`~/.hermes/plugins/vibe-wise`), enable `vibe-wise`, and restart Hermes. Run the
conversation checks below using `skill_view(name="vibe-wise:learn")` and
`skill_view(name="vibe-wise:reset")`; use Hermes's `clarify` picker or chat fallback.
Verify that explicit Learn creates all three notes before its first question, while
installation alone creates none. Also check restart, pause/resume, pending decisions,
compression, and reset cancellation/confirmation in a disposable project.

Initially loader-tested against Hermes checkout `0be2d562b0`; older versions without
`register_skill` are unsupported. Automated tests check registration and hook behavior,
not model compliance. The hook runs between turns, so it does not guarantee recovery
during mid-turn compression. In environments with `/tmp/.git`, run the test suite
with a non-repository `TMPDIR` so no-Git fixtures remain outside a Git boundary.

## Conversation smoke tests

Use an authenticated Claude Code session and temporary copies of projects.
Launch with `claude --plugin-dir /absolute/path/to/vibe-wise`.

For a manual walkthrough based on the playground notes app, see the
[Notion-style demo](demos/notion-dupe.md).

1. **Fresh project:** Run `/vibe-wise:learn`. Choose a new project, describe
   a small CLI, and accept preference defaults. Check that all three state files
   are created, the map separates proposed from implemented components, and no
   understanding is marked demonstrated without evidence. Choice questions must
   use native pickers with one question per screen; no questionnaire dump or
   failed shell check for a missing state directory.
2. **Existing unfamiliar repository:** Use a separate copy of a real repository.
   Choose the existing-repository flow. Confirm Claude reads actual entry points
   and configuration, gives an accurate short map before familiarity questions,
   asks whole-system versus focused scope, and doesn't invent a frontend/database.
3. **Checkpoint → implementation:** Ask for a meaningful feature, such as durable
   storage or retrying an external request. Confirm Claude asks one reasoning
   question under a title naming the decision, before suggesting its own solution
   or implementing the decision. Give a partial answer; check that
   it refines the answer, names the coding scope in an Implementation checkpoint,
   and offers Implement this step /
   Discuss. Select Discuss,
   ask for clarification or propose an alternative, and confirm it stays
   paused and updates the approach if needed. Select Implement this step;
   check it writes the code and records only evidenced learning. Restart while a
   confirmation is pending and confirm it preserves that pause.
4. **Skip and adaptation:** Say “I'm completely lost.” Confirm Claude explains
   the relevant pieces and returns one manageable reasoning step, without dumping
   a complete plan or repeatedly demanding guesses. Ask for an explanation or say “skip”; it should
   explain and proceed to a Design checkpoint without demanding another attempt. “Just
   implement it” should proceed. Make a trivial edit and confirm no checkpoint. After demonstrating
   a concept, check that later questions address new decisions rather than repeat it.
5. **Lifecycle:** Restart, resume, `/clear`, and `/compact`. Confirm preferences,
   the map, and mastered concepts survive without repeated onboarding. Pause
   learning, restart, and confirm it stays paused; invoke Learn to resume.
6. **Guided foundations:** With a beginner profile and a new project, check that
   essential capabilities are established and preserved when selecting a platform;
   stack, storage, and deployment must remain visible open decisions. Ask what an
   unfamiliar term means while answering a checkpoint. Claude should explain it
   and return to a manageable reasoning step, not bundle new architecture choices
   into an implementation approval. Use different projects to avoid overfitting.
   When labeling an explanation, use Concept for what something is or how it works,
   and Why this matters for its practical relevance to the project. Neither callout
   should introduce a mandatory quiz or confirmation, or require the other callout.
   A design-only Design checkpoint should offer Confirm and continue / Discuss. Confirming
   it records the choice and continues to unresolved decisions without writing
   application code. An Implementation checkpoint must name a concrete coding scope.
   When ready to code, it also confirms the design; don't require a separate
   Design checkpoint first. Several Build checkpoints may lead to one confirmation.
   Option descriptions should invite clarification and express readiness to proceed;
   choosing confirmation alone must not be recorded as demonstrated understanding.
   If Claude proposes additional implementation details, check that a concise list
   or Detail / Proposal / Why it matters table distinguishes them from learner
   decisions. Selecting Discuss should allow questions about individual items;
   unresolved consequential design choices still require learner reasoning.
7. **Preference versus reasoning:** Answer a checkpoint with a tentative preference
   and no rationale. Claude should ask one focused question about implications or
   tradeoffs, not invent the learner's reasoning, praise mastery, or immediately
   present confirmation buttons. Verify that this holds across different projects.
8. **Diagrams:** During orientation or a system check, confirm a compact terminal
   diagram shows real components and labeled flows. Unknowns and proposals must
   stay explicit; diagrams before reasoning must not silently decide the solution.
   All checkpoints use a divider, bold title, and blank lines around normal prose,
   rendered directly without cards, tables, or code fences. Questions may be detailed;
   don't force a short length or fixed width. Tables remain useful for comparisons
   and proposed additions. Every title keeps one leading `✦`
   and its full label in sentence case, followed by a colon, without emojis
   (for example, `✦ Build checkpoint: <description>`). Use native pickers for
   onboarding and confirmations, with no trailing paragraphs obscuring the response point.
   Reasoning questions should be open-ended in chat, not in a picker or its notes field.
9. **Clarification without steering:** Ask about an unfamiliar concept mid-decision.
   Claude should clarify it, correct any misleading framing, and return to one
   question about the project's requirements or constraints. It should not replace
   reasoning with a solution menu, bundle independent choices, or steer toward an
   architecture because it offers more learning opportunities.
10. **Learning first:** With default preferences, make an ordinary build request.
    Before any recommendation, solution menu, revealing diagram, dependency install,
    or application scaffold, Claude must ask for the learner's approach and wait.
    Answer, then check that refinement doesn't silently decide the next problem.
    Test unfamiliar concepts with neutral background, and familiar concepts with
    a new tradeoff: neither should remove the learner's turn to reason. Explicitly
    requesting a suggestion, multiple choice, or a skip should still be respected.

11. **Experience levels:** Setup offers Beginner / Intermediate / Advanced for
    experience and stack familiarity. Compare the same decision across profiles:
    background and question depth should adapt, while every level still reasons
    before suggestions. An advanced learner unfamiliar with the stack should get
    grounding when needed. Existing Some experience / Comfortable profiles should
    resume with intermediate guidance, without rewriting history or re-onboarding.
    Experience must not change the saved checkpoint frequency.

12. **Evaluation and concise confirmation:** Give a confident but flawed proposal;
    Claude should name the violated constraint rather than praise confidence.
    Give a sound proposal; it should explain why and combine feedback with a concise
    Design checkpoint, without redundant questions. Compare two viable approaches:
    tradeoffs should be tied to the project, not a claim of one correct answer.
    The checkpoint describes a proposal until confirmed and must not invent an
    unresolved issue. No code should be written before implementation approval.

13. **Reset:** In a temporary project with saved learning notes, invoke
    `/vibe-wise:reset`. Confirm it shows the absolute project and state paths and
    asks Cancel / Reset learning. Cancel must leave all files unchanged. Invoke
    again and confirm: original notes must exist in the reported backup, the
    active profile must be incomplete, and onboarding must ask fresh questions
    rather than reuse old preferences. Repeat with legacy notes and after restart.
    If notes change during confirmation, Claude must preview and confirm again.

14. **Requirements versus design:** Give a product requirement without proposing
    a mechanism. Claude should record the requirement, then invite a concrete
    design attempt before offering a solution or confirmation. It must not count
    the requirement as demonstrated engineering understanding. Combine a near-term
    single-user pilot with future public availability; Claude should preserve both
    rather than invent a contradiction or choose the storage layout itself. Ask
    for grounding: the response should clarify concepts and return an open design
    step, not give the complete design and quiz the learner on recalling it.
    Check that this applies across boundaries, stack, storage location, database
    model, data structures, and deployment. Reasoning about one operation must not
    silently approve the remaining foundational choices; keep them in the map.
    Ask for a model of components, entities, relationships, and flows. Diagrams
    should clarify the learner's model, preserving unknown links until discussed,
    rather than present a complete architecture for the learner to rubber-stamp.
    After clarifying desired behavior and edge cases, check the handoff to technical
    design: Claude must invite the learner's representation before supplying its
    own structure, including through an explanatory diagram.
15. **Implementation report:** After an approved step, Claude should explain the
    changed files, important code mechanics, connection to the learner's design,
    any tests added or updated and what they cover, and actual verification results.
    Distinguish tests written from checks run; unrun checks must be explicit.
    Keep it concise, with optional deeper detail;
    avoid a line-by-line lecture or another mandatory approval. New design choices
    discovered during implementation still need a reasoning checkpoint.
    Feedback should be factual and specific, with no personal praise, hype, or
    congratulatory filler. Corrections should be direct without belittling.
16. **Coherent reasoning and faithful confirmation:** Offer a rough component list
    before the overall flow is understood. Claude should invite the learner to
    connect responsibilities and flows rather than immediately start a chain of
    implementation-detail questions. When the learner is stuck, explain the missing
    concept directly and return to a meaningful decision, without hints that funnel
    them toward a predetermined answer. Confirm a narrowly worded proposal, then
    inspect the notes: unmentioned fields, lifecycle behavior, alternatives, and
    rationale must remain unresolved, not appear as agreed design or learner reasoning.

Do not commit `.vibe-wise/` or test transcripts. The plugin recommends an
ignore rule during onboarding, but changes `.gitignore` only after telling the
user and receiving their instruction to make the edit.

## Design and official references

Verified against current first-party documentation on 2026-09-28:

- [Plugin creation](https://code.claude.com/docs/en/plugins/create): standard
  component directories and `--plugin-dir` for local loading.
- [Skills](https://code.claude.com/docs/en/skills): the command is
  `/vibe-wise:learn`. Explicit invocation starts onboarding; the hook restores
  behavior in later sessions only where a learner profile already exists.
- [Hooks](https://code.claude.com/docs/en/hooks): `SessionStart` sources include
  `startup`, `resume`, `clear`, `compact`, and `fork`. The hook emits a small
  `hookSpecificOutput.additionalContext` pointing to the Learn guide and selected
  state directory. It checks the profile for paused mode without a prefix cutoff,
  but injects no learner-note excerpts or partial topic index. Claude must read the
  profile/map, search all of progress for pending decisions, and read the complete
  pending sections plus relevant topics before continuing. Hook output does not
  grow with learning history; Claude's subsequent file reads still consume context.
- [Marketplace creation](https://code.claude.com/docs/en/plugin-marketplaces):
  the small catalog points to this repository's plugin root. The GitHub install
  instructions work after these files are published to the remote repository.
- [Anthropic's learning-output-style plugin](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/learning-output-style):
  inspected its SessionStart configuration and context injection. VibeWise
  supplies its own reasoning-first instructions and leaves implementation to AI.

No `PreCompact` hook is needed: it doesn't provide an opportunity for Claude to
save learning notes through `additionalContext`. Save notes at meaningful events
and restore them through `SessionStart` with source `compact`. Unsaved reasoning
can still be lost if a session ends before Claude writes it; the hook doesn't
infer progress from transcripts. State writes are performed by Claude using
normal permissions, so denied writes should be reported rather than called saved.

Keep V1 local and terminal-native. No backend, analytics, accounts, separate LLM
calls, scoring engine, or custom UI. Saved context is processed by Claude Code
under the user's existing data settings.

## V1 verification

Tested on 2026-09-28 with Claude Code 2.1.240:

- Plugin, marketplace, and skill validation passed; installation in an isolated
  local marketplace configuration succeeded.
- All 16 hook tests passed, including simulated compact/clear/resume events.
- Live Claude sessions completed fresh-project onboarding and orientation of an
  unfamiliar copy of this repository. A new session restored saved preferences.
- The fresh-project session asked about persistence, reviewed the learner's JSON
  storage proposal, waited through clarification (the choice was initially named
  Ask a question; now Discuss), then wrote
  the CLI after Implement. Its five generated CLI/storage tests passed locally.

Those initial live tests used print mode with file tools and covered the plain-text
choice fallback. For 0.1.1, additional checks on Claude Code 2.1.284 verified the
native first-question picker and Enter selection in an interactive terminal.
The following prompt asked only for the project description. A separate beginner
conversation kept foundational choices open, asked a named checkpoint, and returned
to that checkpoint after explaining unfamiliar concepts, without implementing.

For 0.1.2, a live design-review check offered Use this choice / Discuss first and
explicitly described recording the choice and moving to the next decision without
writing code. This check used print mode's text fallback.

For 0.1.4, a tentative preference with no rationale triggered a follow-up question
instead of confirmation buttons or application code. The first run omitted its
checkpoint heading; after clarifying that follow-ups keep a heading, the repeat
used a named checkpoint. These checks establish that the interaction paused, not
that a complete session will consistently teach good engineering judgment.

All 16 hook tests still pass. The actual `/compact` command still needs an
interactive smoke test. Checkpoint quality remains model-dependent; these examples
verify observed behavior, not a guarantee for every conversation.

For 0.1.9, a live print-mode session with default preferences paused an ordinary
build request before suggesting a stack or writing application code. Its initial
scope question bundled multiple details; the instructions now explicitly limit
requirements gathering to one focused question too. After scope confirmation,
“I'm completely lost” received an incomplete end-to-end diagram and a plain-English
question about the missing flow. Claude left language, storage, and indexing open,
and changed only learning notes. This verifies the observed grounding behavior;
the revised requirements-question pacing still needs a fresh-session check.

For 0.1.13, the VibeWise rename passes all 21 hook tests and plugin, marketplace,
and skill validation. New notes use `.vibe-wise/`; existing `.sensible-vibes/`
notes remain in place and are restored by the renamed plugin.

For 0.1.14, reset uses a read-only preview and an explicit confirmation before
calling the helper with that snapshot's token. Backups stay inside the selected
state directory so its existing ignore rule applies. Only the three learning
notes are replaced. A replacement failure may leave a partial reset; the helper
reports failure and the backup path, and the skill stops instead of onboarding.
All 35 tests and plugin, marketplace, and skill validation pass.
A live print-mode smoke test verified the text confirmation fallback: preview
changed no notes, explicit Reset learning backed up all three originals, and
Claude asked the first onboarding question without carrying forward old preferences.
The fixture's source file stayed unchanged. Reset's native picker still needs an
interactive check; the existing Learn picker was verified in earlier testing.

For 0.1.15, print-mode checks during prompt revision kept a public-access
requirement separate from architecture approval and reflected a learner-proposed
data model without choosing the remaining stack or storage. Grounding responses
were still too expansive, motivating the shorter behavior instructions.
A final check with the shortened prompt implemented an explicitly approved
write-then-replace file update, verified successful saves and preservation of the
original after a serialization failure, and explained the code and its connection
to the learner's decision. The report used three top-level bullets but expanded
them into nested detail: brevity remains inconsistent. These checks exercise
individual interactions, not a guarantee of teaching quality across a full session.

For 0.1.17, the behavior guide was rewritten around learner-owned design and direct
concept teaching rather than a fixed question sequence. Final print-mode checks
asked the learner to assign responsibilities across their proposed system and
saved a narrowly confirmed design without inventing fields, lifecycle rules, or
rationale. When the learner said they had been guessing, Claude reopened the
decision and explained the concept directly. That explanation remained lengthy
and ended with a comprehension question; consistent pacing and avoiding unnecessary
quizzes still need real-session evaluation. All 35 automated tests and plugin/skill
validation pass; these do not measure teaching quality.

For 0.1.20, a print-mode photo-organizer check clarified shared edits and album
deletion behavior. Claude recorded requirements, asked the learner how to represent
the data, and waited without supplying a linking structure or writing application
code. This checks one requirements-to-design handoff, not consistent behavior
throughout a conversation. All 35 tests and plugin/skill validation pass.

For 0.1.21, restoration uses a small instruction message pointing to source files,
with no truncated notes or partial progress index. All 37 tests pass, including
large histories and a paused status beyond the old profile cutoff. Plugin,
marketplace, and skill validation pass. A live print-mode startup check read the
Learn/behavior guides and saved notes, found a pending implementation decision
over 40,000 characters into progress, and resumed its confirmation without writing
application code. The source fixture stayed unchanged. Compaction events remain
covered at the hook level; an actual interactive `/compact` check is still pending.
