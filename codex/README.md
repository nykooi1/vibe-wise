# VibeWise for Codex

Mindful pair programming that keeps you in the driver's seat.

You lead the design; Codex gives feedback, explains concepts, asks follow-up questions, and writes the agreed code.

## Requirements

- [Codex CLI](https://github.com/openai/codex)
- Python 3 (`python` on Windows, `python3` on Unix) — no third-party Python packages required.

## Installation

### 1. Add the marketplace

Add from GitHub:

```sh
codex plugin marketplace add nykooi1/vibe-wise
```

Or for local development from the repository root:

```sh
codex plugin marketplace add .
```

To verify the marketplace is registered:

```sh
codex plugin marketplace list
```

### 2. Install the plugin

Install `vibe-wise` from the marketplace:

```sh
codex plugin add vibe-wise@vibe-wise
```

Verify installation:

```sh
codex plugin list
```

### 3. Review and trust the hook

VibeWise registers a `SessionStart` hook (`codex/hooks/hooks.json`) that restores learning context at session start and after compaction. In Codex, hooks from newly installed plugins remain untrusted until user review.

Open `/hooks` in Codex, inspect the VibeWise hook:

```text
python "${PLUGIN_ROOT}/hooks/session_start.py"
```

Approve and trust the hook for your workspace.

## Usage

### Start learning

In your project directory, launch Codex and invoke the Learn skill:

```text
$learn
```

Onboarding guides you through setting your goals and checkpoint preferences one question at a time. Then describe what you want to build; Codex will invite your design approach before writing any code.

### Reset learning notes

To back up existing learning notes and restart onboarding from scratch:

```text
$reset
```

The command generates a preview with a snapshot confirmation token. Confirm in chat to create a timestamped backup in `.vibe-wise/backups/` and reset only learning notes. Your project code and Git history are never modified.
