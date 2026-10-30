# Local state templates

Create only these three files in the chosen project's `.vibe-wise/`, or its existing
legacy `.sensible-vibes/` when resuming. Use the directory selected by SKILL.md.
Replace bracketed values with actual evidence or “Not specified.” Keep the two
status lines unformatted and near the top; the restoration hook reads them.
Do not replace existing state with a fresh template.

## profile.md

```markdown
# Learner Profile

Learning mode: active
Onboarding: complete

## Project
Situation: [New / Existing / Known]
Building: [project purpose]
Codebase familiarity: [answer]
Learning scope: [entire system / parts we touch / mixed]

## Experience
Overall programming: [Beginner / Intermediate / Advanced, or Not specified]
Stack familiarity: [per-technology levels if given; otherwise Not specified]

## Goals
Primary: [answer]
Capability goal: [optional answer]

## Preferences
Checkpoint frequency: Normal
Question style: Open-ended
Implementation style: AI writes code

## Strong Concepts
No demonstrated understanding recorded yet.

## Developing Concepts
None recorded yet.

## Revisit
None recorded yet.
```

## progress.md

```markdown
# Learning Progress

No learning events recorded yet.
```

As learning occurs, add a `## Topic` with concise bullets under Introduced,
Demonstrated understanding, and Needs reinforcement. Record reasoning evidence,
not quotations of a whole exchange. Product preferences establish requirements;
they aren't evidence of engineering understanding. Keep learner-proposed reasoning
distinct from concepts the AI explained. Consolidate repeated entries. Keep each
topic independently readable so it can be loaded without the whole file.
While waiting on a checkpoint, keep a short section headed exactly
`## Pending decision`, not in a topic, with the proposed approach and what reply is
awaited. Include the checkpoint's decision name and stage: awaiting reasoning,
choice confirmation, or implementation approval. Remove it once resolved: record
the outcome in the map as chosen or implemented, labeling approved additions as
the AI's, and any reasoning evidence in its topic. Don't move the pending text
into a topic; update entries the outcome supersedes. Record confirmed choices in
the map without claiming they are implemented. Keep any proposed coding scope explicit.
Confirmation covers only the proposal presented. Don't append unmentioned fields,
behaviors, rejected alternatives, or reasons to the chosen design. Mark unresolved
details unknown and the AI's suggestions proposed; never attribute them to the learner.

## project-map.md

```markdown
# Project Map

## Purpose
[What this software does.]

## Requirements
[User needs and constraints. These do not automatically settle technical choices.]

## Components
[Components, responsibilities, and supporting file paths.]

## Main Flow
[Compact text diagram with labeled arrows. Mark unknowns and distinguish proposed,
chosen, and implemented components. Reflect the learner's model refined together,
or verified existing code; don't fill missing relationships with assumed designs.]

## Data and Trust Boundaries
[Storage, ownership, auth, external services; unknown when unverified.]

## Build and Deployment
[Commands and configuration paths verified in the repository.]

## Unknowns
[Unresolved technical choices and what needs inspection, including relevant stack,
storage location/model, data structures, interfaces, and deployment choices.]
```
