# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

**Homik** is a mobile-first household inventory PWA (React + Vite frontend, FastAPI + SQLModel backend, PostgreSQL via Neon). Users scan barcodes to track items in/out, browse inventory by location, and see what's expiring soon. Multi-user households are supported; all data is scoped to `household_id`.

The backend is the active build target. The frontend directory exists but is not yet scaffolded.

## Project context

This is a portfolio project built by a developer returning to the job market. Code will be read by hiring managers and senior developers.

- Follow FastAPI + SQLModel best practices for 2025/2026
- Keep it simple and focused — no over-engineering
- Prefer clarity over cleverness
- Every pattern used should be explainable in an interview
- Add comments where a pattern might be unfamiliar
- This is also a learning project — explain non-obvious decisions inline

## Backend commands

All backend commands run from `backend/` using `uv`:

```bash
# Install dependencies
uv sync

# Run dev server
uv run fastapi dev app/main.py

# Format
uv run ruff format .

# Lint
uv run ruff check .

# Type check
uv run pyright

# Run tests
uv run pytest

# Run a single test
uv run pytest tests/path/to/test_file.py::test_name
```

## Architecture

### Data model hierarchy

```
Household → User (many per household)
         → Location (e.g. Fridge, Cellar, Pantry — seeded on creation)
         → Category (e.g. Food, Cleaning — seeded on creation)
         → Item (what a product *is*; has barcode, brand, image_url, category)
              → Batch (one per unique location + expiry combo; holds quantity, location, expiry)
```

- **Item** = the product definition (name, barcode, brand, image_url from Open Food Facts, category, unit). No location — the same product can live in multiple places.
- **Batch** = one group of units sharing the same location and expiry date. A purchase split across two locations creates two batches.
- Expiry is stored as a full `date` field; the UI will show month + year only. Defaults to +12 months from today.
- `ShoppingListItem` model exists in v1 but has no UI — that's a v2 feature.

### Multi-household data isolation

Every query must be scoped to the current user's `household_id`. This is the most critical security invariant — a user must never see data from another household.

### External integration

Product lookup proxies through the backend to Open Food Facts (`GET /lookup/barcode/{barcode}`) to avoid browser CORS issues. No API key needed.

### Auth

FastAPI Users with JWT tokens. Registration creates both a new User and a new Household.

## Key conventions

- Python 3.13, async throughout (asyncpg driver for Postgres).
- Ruff enforces strict rules including mandatory type annotations (`ANN`) and no `print` statements (`T20`). Tests are exempt from annotations and security rules — see `pyproject.toml` for the full per-file ignore list.
- `asyncio_mode = "auto"` is set in pytest — no need to mark async tests explicitly.

### Datetime columns

All `datetime` fields must use `sa_column=sa.Column(sa.DateTime(timezone=True))` — asyncpg rejects timezone-aware datetimes in `TIMESTAMP WITHOUT TIME ZONE` columns. Always use `datetime.now(UTC)` (never `datetime.utcnow()`).

### Schema changes

No Alembic yet. Schema changes require dropping affected tables in the Neon console and restarting the server to recreate them. Add Alembic before any production data exists.

### SQLModel query conventions

**`col()` for column expressions:** When using `.ilike()`, `.in_()`, `.desc()`, or `order_by()` on a model attribute, wrap it with `col()` from `sqlmodel`. Without it, Pyright resolves the attribute as a Python type (`str`, `int`, `date`) and flags the SQL method as unknown.

```python
from sqlmodel import col, select

select(Item).where(col(Item.name).ilike(f"%{name}%"))
select(Item).where(col(Item.id).in_(subquery))
select(Batch).order_by(col(Batch.expiry_date))
```

**`AsyncSession` import:** Always import `AsyncSession` from `sqlmodel.ext.asyncio.session`, not from `sqlalchemy.ext.asyncio`. SQLAlchemy's version doesn't have `.exec()`. Also set `class_=AsyncSession` in `async_sessionmaker` so the session factory creates SQLModel sessions:

```python
from sqlmodel.ext.asyncio.session import AsyncSession
_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

### API endpoint conventions

**Household isolation:** Every query must filter by `user.household_id`. Return 404 for both "not found" and "wrong household" — never 403. Returning 403 leaks whether an ID exists.

**IntegrityError handling:** Let the DB enforce unique constraints rather than doing pre-check queries (race condition + extra round-trip). Catch `sqlalchemy.exc.IntegrityError` after `commit()`, call `session.rollback()`, and raise a 409. Do not attempt to introspect the underlying driver exception (`exc.orig.pgcode`, `isinstance(..., asyncpg.UniqueViolationError)`) — this is fragile across SQLAlchemy/asyncpg versions. Add a comment explaining why the broad catch is safe for that specific endpoint.

**Response schemas:** Never return raw table models — they expose `household_id` and other internals. Always return a `*Read` schema that explicitly lists the fields the client should see.

**PATCH pattern:** Use `data.model_dump(exclude_unset=True)` to only update fields explicitly sent in the request. This prevents overwriting existing values with `None` for fields the client didn't mention.

### fastapi-users imports

Import `SQLAlchemyUserDatabase` directly from `fastapi_users_db_sqlalchemy`, not `fastapi_users.db`. The re-export in `fastapi_users.db` uses a `try/except` block that Pylance cannot statically trace, causing false unknown-symbol errors.

## Developer workflow scripts

- `./scripts/create-pr.sh` — opens a PR from the current branch
- `./scripts/fetch-pr-comments.sh` — fetches open PR review comments into `docs/pr-comments.md`
- `/pr-description` — generates a PR description and saves to `docs/pr-description.md`
- `/review-comments` — works through `docs/pr-comments.md` one comment at a time
- `/til` — updates `docs/til.md` with learnings from the current session

## Developer environment

Host machine: Apple M4 MacBook (ARM64, no Rosetta). Package manager: Homebrew. Shell: zsh. `gh` CLI is installed on the host — not inside the Claude Code container.

## CI

A GitHub Actions workflow (`.github/workflows/claude-review.yml`) runs Claude Code review on every non-draft PR to `main`. It focuses on data isolation bugs, missing input validation, security issues, and learning-oriented feedback.
