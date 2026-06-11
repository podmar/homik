Use this when asking Claude to create or revise a skill file in `.claude/commands/`.

Paste into the conversation before describing the skill you want:

---

Write this as direct instructions to Claude, not a document. No headers. Imperative voice throughout ("do X", "skip if Y"). For each thing that could go wrong, name the failure mode explicitly rather than stating a virtue. Include: where to get inputs, confirm-before-write if it writes to a file, "if nothing qualifies say so and stop" if relevant, and pacing (iterative: wait after each item / single-output: gather → draft → confirm → write).
