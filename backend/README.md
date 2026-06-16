# homik — Backend

FastAPI backend for the homik household inventory app.

## Requirements

- Python 3.13 (via pyenv)
- [uv](https://github.com/astral-sh/uv) for package management
- A [Neon](https://neon.tech) PostgreSQL database

## Setup

```bash
# Install dependencies
uv sync

# Copy environment variables
cp .env.example .env
# Fill in DATABASE_URL and SECRET_KEY in .env

# Run the development server
uv run fastapi dev app/main.py
```

## Environment variables

| Variable                    | Description                        |
|-----------------------------|------------------------------------|
| `DATABASE_URL`              | Neon PostgreSQL connection string  |
| `TEST_DATABASE_URL`         | Separate Neon database for tests — must differ from `DATABASE_URL` (tests truncate all tables) |
| `SECRET_KEY`                | JWT signing secret                 |
| `ALGORITHM`                 | JWT algorithm (default: HS256)     |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime (default: 30)     |
| `ENVIRONMENT`               | `development` or `production`      |
| `FRONTEND_URL`              | Frontend origin for CORS           |
| `OFF_BASE_URL`              | Open Food Facts API base URL       |

## Linting and formatting

```bash
# Format
uv run ruff format .

# Lint
uv run ruff check .

# Type check
uv run pyright
```

## Tests

```bash
# Run tests (from project root — writes output to docs/test-report.txt)
./scripts/run-tests.sh

# Or run directly from backend/
uv run pytest
```

Use `/fix-test` in Claude Code to work through any failures.