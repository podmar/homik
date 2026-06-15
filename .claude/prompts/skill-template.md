Use this when asking Claude to create or revise a skill file in `.claude/commands/`.

Paste into the conversation before describing the skill you want:

---

Write this as direct instructions to Claude, not a document. No headers. Imperative voice throughout ("do X", "skip if Y"). For each thing that could go wrong, name the failure mode explicitly rather than stating a virtue. Include: where to get inputs, confirm-before-write if it writes to a file, "if nothing qualifies say so and stop" if relevant, and pacing (iterative: wait after each item / single-output: gather → draft → confirm → write).

Do not add a self-review step for quality or correctness — Claude is anchored to what it just produced and will tend to confirm rather than critique. For those, end the skill by telling the user they can send a follow-up message (e.g. "check this for X" or "/code-review"). A self-check step is fine for completeness against a concrete checklist (e.g. "confirm every failure was either fixed or explicitly skipped").
