# TIL — Today I Learned

Update `docs/til.md` with learnings from the current session.

## Steps

1. Read `docs/til.md` to understand what's already there.

2. Review recent work — look at the git diff, recent commits, and the current conversation to identify:
   - New patterns or concepts introduced
   - Errors that were hit and why they happened
   - Design decisions made and the reasoning
   - Gotchas or non-obvious behaviour

3. Add new content to the appropriate sections. Rules:
   - **Don't duplicate.** If a concept is already covered, skip it or add a sub-point only if it adds something new.
   - **Add to existing sections** rather than creating new ones unless it's genuinely new territory.
   - **One concept per bullet.** Keep entries concise — a sentence or two max.
   - **Ground it in the codebase.** Reference the actual file/pattern when helpful.

4. Add a new entry to the **Session Log** at the bottom:
   - Today's date
   - What was built (one line)
   - Key decisions or errors fixed (bullet list)

5. Show the user a summary of what was added — list the section and the new bullet(s) so they can review and ask for changes before accepting.

## What to look for

**Patterns worth capturing:**
- New language or framework features used
- Query patterns, ORM tricks, async gotchas
- Security decisions (auth, isolation, validation)
- Type system gotchas

**Errors worth capturing:**
- Type errors and why they happened
- Linter rule violations and what they mean
- Runtime errors hit during testing

**Design decisions worth capturing:**
- Any time we chose between two approaches and had a reason
- Any time a simpler approach was rejected
- API contract decisions (status codes, field names, optional vs required)
- Wording decisions on error messages (yes, those count)

## Important

Keep the tone clear and direct — write as if explaining to a senior developer.
Do not add fluff, do not pad entries, do not repeat things already covered.
This is a learning log, not a changelog — capture the *why*, not just the *what*.
