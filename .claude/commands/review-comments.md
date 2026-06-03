Work through the PR review comments in `docs/pr-comments.md` one at a time.

Before starting, tell the user to run `fetch-pr-comments` first if `docs/pr-comments.md` doesn't exist or looks empty.

Rules:
- One comment at a time. Never batch changes.
- For each comment:
  1. Explain what the reviewer is asking and why it matters — in plain language
  2. Give your assessment: is it a valid concern, a false positive, or wrong layer?
  3. Suggest the fix, or explain why no change is needed
  4. If a commit is needed, suggest a conventional commit message (e.g. `fix:`, `refactor:`)
  5. Wait — do not move to the next comment until the user confirms they are ready
- Do not make commits. The user handles all commits.
- Do not make multiple code changes at once, even if two comments are related.

When all comments are done:
- Remind the user to review `docs/pr-description.md` and update it if the changes warrant it
- Remind them to merge when ready

Then reflect on the review quality:
- List the changes that were genuinely valuable
- Flag any false positives or wrong-layer suggestions
- Note if the reviewer seems to be regressing (more noise than signal compared to previous PRs)
- Be specific — quote the comment if flagging a false positive
