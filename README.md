# 🐹 homik

A mobile-friendly web app for managing household inventory —
food, cleaning products, and anything stored in hard-to-see
places like a cellar.

> *homik* blends "home" with "chomik" (Polish for hamster 🐹).

## What it does

- Scan items in and out via barcode
- Browse inventory by location (fridge, cellar, pantry…)
- See what's expiring soon
- Multi-user household support

## Development workflow

This project uses Claude Code for PR reviews. Claude runs in an isolated container and commits are made manually, which keeps the developer in control of what lands and makes the changes a genuine learning exercise.

The loop looks like this:

1. `/pr-description` (Claude Code skill) — drafts the PR description
2. `./scripts/create-pr.sh` — opens a PR from the current branch
3. CI runs an automated Claude review (`.github/workflows/claude-review.yml`)
4. `./scripts/fetch-pr-comments.sh` — pulls review comments into `docs/pr-comments.md`
5. `/review-comments` (Claude Code skill) — works through each comment interactively, one at a time

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

## Status

🚧 Active development — v1 (inventory app) in progress.