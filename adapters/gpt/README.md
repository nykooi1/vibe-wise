# VibeWise for GPT

An independent MIT-licensed adaptation of [nykooi1/vibe-wise](https://github.com/nykooi1/vibe-wise),
based on commit `1135f4ae8205da78404a71e85f567d5911da4e4d`.
You design; the assistant teaches, challenges assumptions, implements agreed code,
and explains verified results. The original copyright and license are retained.

## Codex

Copy the `vibe-wise` folder into your Codex skills directory, normally
`~/.codex/skills` (or `$CODEX_HOME/skills` if configured). This package includes
SKILL.md and agents/openai.yaml. Start a new chat after installation if the skill
is not yet discoverable. Invoke:

```text
$vibe-wise Help me build a notes app and understand its design. Use defaults.
```

Other examples:

```text
$vibe-wise Resume learning this repository.
Use fewer checkpoints and focus on backend architecture.
Just implement this one.
Pause learning.
Reset VibeWise learning notes for this project, keeping a backup.
```

The three project notes are `.vibe-wise/profile.md`, `progress.md`, and
`project-map.md`. Existing `.sensible-vibes` notes can be used in place.
Python 3 is needed for the bundled context and reset helpers, with no third-party
packages. Python 3.12+ detects Windows junctions as well as symbolic links.
If Python is unavailable, the skill describes manual read-only discovery; reset
requires the helper. No telemetry or network calls are made by these helpers.

## Other GPT chats or agent hosts

Use `GPT-INSTRUCTIONS.md` as a reusable chat prompt or as instructions in a host
that lets you configure an assistant. It contains the teaching workflow in one
file, without Codex tool names or plugin dependencies. No specific GPT model is
hard-coded. The host determines tool access and persistence: text-only chats can
teach and propose code, but cannot inspect your local repository or run tests.
Save the offered learning snapshot and supply it in a later chat to resume.

## Cross-session restoration

There is no automatic lifecycle hook in this adaptation. Invoke `$vibe-wise` to
reload project notes. If you want project guidance to request restoration, you
can add this optional text to your AGENTS.md yourself:

> When this project's VibeWise profile is active, load the installed vibe-wise
> skill before development and restore its project notes. Respect paused mode,
> pending decisions, repository boundaries, and current user instructions. If
> the skill is unavailable, report that instead of guessing its workflow.

Installing the skill does not edit AGENTS.md or .gitignore. Consider excluding
`.vibe-wise/` from version control if you do not want to share learning notes.

## Verification

```text
python -B -m unittest discover -s adapters/gpt/tests -v
```

Run this command from the repository root. Tests cover project boundaries, legacy notes, pause detection, read-only discovery,
stale reset tokens, backups, and reset failures. They verify helper behavior;
they do not establish teaching quality across GPT models. The package does not
make model API calls or require an API key.
