Update `docs/spec.md` with decisions made during the current session.

Use `git diff main..HEAD`, recent commits, and the current conversation to find decisions worth recording.

**Rule of thumb:** If the decision is specific to homik's API or data model, it belongs here. If it's a pattern that would apply in any FastAPI project, it belongs in `/til`.

What counts: API contract choices (status codes, endpoint shape, error responses), data model decisions (field added/removed, constraint, denormalization), scope changes (v1/v2), deliberate behaviour that would surprise a reader of the spec (merge instead of reject, cascade in code not DB).

Where to put things:
- **Section 9 Key Decisions Log table** — high-level choice + one-sentence reason
- **Section 9 `### API Contract Decisions`** — implementation-level choices (endpoint behaviour, guard logic, merge vs reject)
- **Section 4 Data Model** — if a model field or constraint changed and the spec doesn't reflect it
- **Section 7 API Design** — if an endpoint signature changed

If nothing in the session qualifies, say so and stop — don't invent entries to justify running the skill.

Draft the additions and show them to the user before writing anything to the file. Wait for confirmation.

Sharpness rules:
- If it's already in the spec, skip it — don't restate
- Don't add exploratory ideas that weren't adopted
- One entry per decision. Decision + the one sharp reason it was made, nothing else.
