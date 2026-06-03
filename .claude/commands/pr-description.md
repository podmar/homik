Write a PR description for the current branch and save it to `docs/pr-description.md`.

Use `git log main..HEAD` and `git diff main..HEAD` to understand what changed.

Rules:
- Do not list files changed — that's visible in the diff
- Focus on WHY, not WHAT
- Explain decisions that aren't obvious from the code
- Note anything a reviewer should pay attention to
- Keep it concise — one bullet per decision, one sharp reason per bullet
- End with a "What's next" line if there's a clear next step
- Use plain GitHub-flavoured markdown, no emoji
- Tone: professional, humble, clear

Sharpness rules:
- Don't restate the title in the opening summary — if the sentence adds nothing, cut it
- "What is in diff, is in diff" — never describe which files changed or say "this is reflected in X, Y, Z"
- No anecdote or backstory ("this bit us", "we discovered") — state the technical constraint directly
- Each bullet: decision + the one sharp reason it was made, nothing else
- Don't over-explain consequences that follow obviously from the constraint
- Cut filler: "zero complexity", "available to anyone", "particularly useful for"

Structure:
## <short title>
<1 sentence — only if it adds something the title doesn't>
### Decisions worth noting
### What's next
