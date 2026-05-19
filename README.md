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
chomik/
├── backend/     # FastAPI app
├── frontend/    # React PWA (coming soon)
├── docs/        # Spec and architecture notes
├── .github/     # Github workflows
└── .vscode/     # Shared editor settings
```

## Development

See [backend/README.md](backend/README.md) to run the API locally.
Frontend setup instructions coming once scaffolded.

## Status

🚧 Active development — v1 (inventory app) in progress.