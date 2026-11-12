---
name: learn-light
description: Use concise guided questions to explore an unfamiliar topic while keeping the user's decisions in their hands.
disable-model-invocation: true
---

# Learn-light

Use this guidance when the user invokes Learn-light or another skill explicitly
references this file. It does not activate or pause Learn mode, change saved
preferences, or grant permission to implement. Respect the active skill's approval
requirements. Explain that the user can say “stop Learn-light” at any time to return
to the previous workflow; stop asking these questions when they do.

Ask up to five short questions, one at a time, adapting each to the current task:
what they know or assume; what is unclear; relevant constraints; the decision or
next step they need; and how much explanation would help. Skip answers already known.
Use the host's structured-question tool for choices where available and obey its
question and option limits. Provide a way to describe the answer in their own words;
use the host's native free-text option when available, or accept free text in chat.
Allow “I'm not sure—explain the key concept first” instead of requiring an answer.
Explain the concept, then revisit a question only if a decision still needs it.

Use the answers to give concise, relevant guidance and tradeoffs. The user keeps
ownership of consequential decisions. Treat choices as prompts for judgment, not
proof of understanding or approval to make changes.
