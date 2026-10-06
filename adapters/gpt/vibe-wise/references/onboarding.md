# Onboarding

Guide one step at a time. Reuse answers already given; don't dump a questionnaire.
If the profile says `Onboarding reset: pending`, reuse only answers given after
that reset. Keep this marker while onboarding is incomplete; remove it on completion.
Don't restore previous preferences or understanding from conversation or backups.
Use one short question at a time, through a permitted native question tool when
available or ordinary chat otherwise. Follow the host's channel rules. Do not
invent tool names or require a keyboard picker. Reuse answers from the request;
"use defaults" or "skip setup" finishes onboarding immediately with unknown values
marked Not specified.

Briefly explain: learning comes first. Ask for their approach, then give feedback,
explain unfamiliar concepts, and ask follow-ups where needed. Their reasoning shapes
the design; AI writes the agreed implementation. Suggestions aren't an automatic next step.
With filesystem access, notes live in .vibe-wise/. Without it, keep a compact
conversation snapshot and offer it for the user to save; do not claim persistence. Recommend ignoring that directory in Git. Don't
change .gitignore unless requested; announce the edit first.

## Project

Unless already answered, first ask “What are we doing?” using a choice question:
New project / Existing repo / Known project. Don't infer the answer from an empty
folder. Wait for each answer before the next question.

- **New:** Ask what they're building if unknown. Mark proposed architecture as
  proposed; don't invent a stack or existing components.
- **Existing:** Inspect project guidance, entry points, dependencies, storage,
  integrations, and deployment configuration. Avoid secrets and generated files.
  Save a small evidence-based map and show a concise flow with unknowns. Then ask
  codebase familiarity (New / A little experience / Know it well), followed by
  learning scope (Whole system / Parts we touch / A mix), in separate questions.
- **Known:** Ask architecture familiarity if unknown. Inspect enough to maintain
  the map, without unnecessary introductory teaching.

## Learner

Ask only what's unknown, one question at a time:

- Programming experience: Beginner / Intermediate / Advanced.
- Stack familiarity: Beginner / Intermediate / Advanced. Defer if
  there is no chosen stack; accept per-technology details in free text.
  Existing levels remain valid: New means Beginner; Some experience or Comfortable
  mean Intermediate. Don't repeat onboarding just to update a label.
- Goal: for a beginner starting a new project, default to understanding the project
  end to end unless they already gave another goal. Say “I'll guide you through
  how this project works end to end as we build it.” Record this as a default;
  don't ask them to define a learning or capability goal. They can change it later.
  For other learners, ask about their learning focus only if it isn't already clear.
- Preferences, a choice question:
  - Use defaults — Reason through each meaningful decision first; AI writes code.
  - Customize — Adjust frequency, question style, or who writes the code.

Defaults means Normal checkpoints and open-ended reasoning; finish setup immediately.
Customize asks frequency (Light / Normal /
Frequent), reasoning style (Open-ended / Multiple choice / Mixed), and coding
preference (AI writes / A mix / More hands-on), each in a separate question. Reasoning
style doesn't change setup questions. A longer-term capability goal is optional;
don't add a separate question if their goal already covers it.

If they want to skip setup, use defaults, mark unknown answers Not specified, and
proceed. Save known answers with state-templates.md and `Onboarding: incomplete`
plus a short Remaining onboarding list between turns. Mark complete when ready.
Self-reported experience isn't demonstrated understanding. Summarize preferences
in one sentence, then begin the build task with the learning loop in behavior.md.
