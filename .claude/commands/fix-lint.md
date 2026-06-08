Read `docs/lint-report.md` and work through the lint issues one file at a time.

Before starting:
- If `docs/lint-report.md` doesn't exist or is empty, tell the user to run `./scripts/run-lint.sh` first (or their `run-lint` alias).
- Parse both sections (Ruff and Pyright). Group all issues by file — if the same file has both Ruff and Pyright issues, handle them together.
- Tell the user how many files have issues and what the breakdown is (Ruff / Pyright / both) before starting.

For each file with issues:
1. Show all the issues for that file at once (both Ruff and Pyright if applicable).
2. For each issue in the file:
   - Read the relevant code
   - Explain what the problem is and why it matters (one sentence)
   - Classify it: **clear error** (just fix it) or **design decision** (needs your call)
3. For clear errors: propose the fix and implement it — don't wait for confirmation.
4. For design decisions: explain the tradeoff, give a recommendation, and wait for the user to confirm before touching anything.
5. After fixing all issues in the file: summarize what was changed and what (if anything) was skipped and why.
6. Wait for the user to say they're ready before moving to the next file.

What counts as a design decision (confirm before fixing):
- Removing or changing a type annotation in a way that affects the public API
- Silencing a rule with `# noqa` or `# type: ignore`
- Restructuring logic to satisfy a check (not just renaming/reordering)
- Anything where multiple valid approaches exist and the choice has visible consequences

What counts as a clear error (fix without asking):
- Missing type annotation on a private or internal function
- Unused import
- Formatting / whitespace violation
- Shadowed variable name with an obvious fix
- `print` statement that should be removed
- Any issue where there is exactly one correct fix

Rules:
- Never batch changes across files.
- Do not commit. The user handles all commits.
- If a Pyright error and a Ruff error point at the same root cause, fix it once and note that it resolves both.
- If an issue appears to be a false positive (e.g. a Pyright unknown-symbol error caused by a bad re-export), say so explicitly and suggest adding a targeted `# type: ignore` with a comment explaining why.

When all files are done:
- List every file touched and what changed.
- List anything skipped and why.
- Remind the user to re-run `run-lint` to confirm the report is clean before committing.
