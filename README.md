# 🐹 homik

A mobile-friendly household inventory app — scan items in and out, browse by location, see what's expiring soon. Built for real daily use by multiple households.

> *homik* blends "home" with "chomik" (Polish for hamster 🐹).

Built with production practices in mind — the interesting part is the reasoning behind the decisions, not the feature list.

## What's interesting technically

- **Batch model** — the same product can live in multiple locations with different expiry dates. A `Batch` represents one unique combination of item + location + expiry, enforced by a DB constraint. Moving batches between locations merges quantities rather than creating duplicates.
- **Multi-tenant isolation** — every query is scoped to `household_id`. The API returns 404 for both "not found" and "wrong household" — never 403, which would leak whether an ID exists.
- **Intentionally thin v1** — no features added until real usage shows they're needed. The frontend categorises inventory client-side from data it already has, rather than adding backend filters speculatively.

For the full decision log: [`docs/spec.md`](docs/spec.md) — [`docs/til.md`](docs/til.md)

## Development workflow

This project uses Claude Code for PR reviews. Claude runs in an isolated container and commits are made manually, which keeps the developer in control of what lands and makes the changes a genuine learning exercise.

The loop looks like this:

1. `./scripts/run-lint.sh` — runs Ruff and Pyright, writes results to `docs/lint-report.md`
2. `/fix-lint` (Claude Code skill) — works through lint issues one file at a time, auto-fixing clear errors and confirming design decisions
3. `./scripts/run-tests.sh` — runs the test suite, writes results to `docs/test-report.txt`
4. `/fix-test` (Claude Code skill) — works through test failures one at a time, diagnosing root cause before applying any fix
5. `/pr-description` (Claude Code skill) — drafts the PR description
6. `./scripts/create-pr.sh` — opens a PR from the current branch
7. CI runs an automated Claude review (`.github/workflows/claude-review.yml`)
8. `./scripts/fetch-pr-comments.sh` — pulls review comments into `docs/pr-comments.md`
9. `/review-comments` (Claude Code skill) — works through each comment interactively, one at a time

## Stack

| Layer    | Tech                        |
|----------|-----------------------------|
| Frontend | React + Vite (PWA)          |
| Backend  | FastAPI + SQLModel          |
| Database | PostgreSQL via Neon          |
| Auth     | FastAPI Users (JWT)         |
| Scanning | ZXing-js (browser camera)   |
| Products | Open Food Facts API         |

## Project structure

```
homik/
├── backend/     # FastAPI app
├── frontend/    # React PWA (coming soon)
├── docs/        # Spec and architecture notes
├── scripts/     # Developer workflow scripts
├── .claude/     # Claude Code commands and settings
├── .github/     # Github workflows
└── .vscode/     # Shared editor settings
```

## Development

See [backend/README.md](backend/README.md) to run the API locally.
Frontend setup instructions coming once scaffolded.

## Running tests

Tests run against a local Postgres container. You'll need Docker installed and the daemon running. The container binds to port 5432.

```bash
./scripts/run-tests.sh   # starts the container if needed, then runs the full suite
```

The container stays running after the script finishes — useful when iterating on tests. Stop it when you're done for the day:

```bash
docker compose down
```

