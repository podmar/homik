# TIL — Today I Learned

> Living document — updated after each session via `/til`.
> Captures patterns, decisions, and gotchas from building homik.
> Every entry is grounded in real code in this repo.

---

## FastAPI Patterns

- **`APIRouter`** groups endpoints by domain. Registered in `main.py` with `app.include_router()`. No router needs to know about others.
- **`Depends()`** is dependency injection. FastAPI calls the function, gets the result, passes it to the handler. The handler declares what it needs; FastAPI wires it up.
- **`Annotated[Type, Depends(...)]`** is the modern DI pattern — bundles the type hint and the injection mechanism together. Pylance can resolve the type; FastAPI reads the `Depends`.
- **FastAPI caches dependencies per request.** If two handlers both depend on `get_session`, the session is created once. Same for `current_active_user`.
- **`status_code` on the decorator** sets the default response code. You can override it at runtime by injecting `Response` as a parameter and setting `response.status_code` in the body. Used in the POST /items upsert: 201 for new, 200 for existing.
- **Query parameters are implicit.** Any function parameter that isn't a path param, a Pydantic model, or a `Depends` is automatically treated as a query parameter.
- **`Query(ge=1)`** adds server-side validation to query params. FastAPI returns 422 automatically if validation fails — no manual check needed.
- **Router without prefix** (`APIRouter(tags=["batches"])`) is valid when your endpoints span multiple URL patterns. Batches use both `/items/{id}/batches` and `/batches/{id}`, so no single prefix fits.

---

## SQLModel & SQLAlchemy Patterns

- **`session.exec(select(Model).where(...))`** is SQLModel's query API. Think of `select(...)` as building the SQL statement; `session.exec()` runs it.
- **`session.get(Model, id)`** fetches by primary key. Checks the session identity cache before hitting the DB.
- **Write cycle:** `session.add(obj)` → `await session.commit()` → `await session.refresh(obj)`. The `refresh` is important — it reloads the row from the DB to get server-generated values like `id` and `created_at`.
- **`model_dump(exclude_unset=True)`** is the PATCH pattern. Pydantic tracks which fields were explicitly included in the request body. `exclude_unset=True` returns only those — fields the client didn't mention are left untouched on the ORM object.
- **`model_validate(orm_instance)`** converts an ORM object into a Pydantic schema. Used to go from table model → response schema, stripping fields like `household_id` that shouldn't be in the API response.
- **`col(Model.field)`** wraps a model attribute as a SQLAlchemy column expression. Needed for `.ilike()`, `.in_()`, `.desc()`, and `order_by()` — without it, Pyright sees Python types (`str`, `int`, `date`) and complains that those methods don't exist.
- **SQLModel's `AsyncSession` vs SQLAlchemy's.** SQLAlchemy's `AsyncSession` doesn't have `.exec()`. SQLModel's subclass (from `sqlmodel.ext.asyncio.session`) adds it. Configure the session factory with `async_sessionmaker(engine, class_=AsyncSession)` to get SQLModel sessions throughout.
- **Primary keys are `int | None` in SQLModel** before insertion. After `flush()` or `commit()` the PK is populated, but the type stays `int | None`. Use a `if pk is None: raise RuntimeError(...)` guard to narrow the type for Pyright.

---

## Security & Data Isolation

- **Every query must filter by `household_id`.** This is the most critical invariant in the codebase. A user must never see or modify another household's data.
- **Return 404 for wrong household, not 403.** Returning 403 would tell the caller "this ID exists but isn't yours" — which leaks information. 404 treats "not found" and "not yours" identically.
- **`household_id` is always set server-side.** It comes from `current_active_user`, never from the request body. The client has no say in which household an object belongs to.
- **`household_id` on Batch is denormalized.** It's copied from the Item so that every batch query can filter by household directly, without joining through items. This is a deliberate performance and isolation trade-off.
- **Guard `user.household_id is None` at the top of every endpoint.** The `User` model has `household_id: int | None` (nullable for future invite flow). Without the guard, a user with no household would get confusing 404s. With it, they get a clear 400. The guard also narrows the type for Pyright.
- **Household_id filter rule: parent verified immediately → no redundant filter on children.** If the parent was ownership-checked one line above, child queries scoped to that parent's FK are guaranteed to be in-household. Adding another filter is noise. Exception: if the household check is further up the call chain (e.g., the location was verified earlier but the batch queries come much later, as in `delete_location`), add `household_id` as a second gate — the chain is long enough to break.
- **Subqueries for filtering should also filter by `household_id`.** In `GET /items?location_id=X`, the subquery finding batches at that location also filters `Batch.household_id == user.household_id` — even though the outer query already filters items by household. Belt and braces.

---

## Python Type System

- **Pyright doesn't know about SQLAlchemy column instrumentation.** At the class level, `Item.name` looks like `str` to Pyright. `col(Item.name)` is the SQLModel-provided escape hatch that says "treat this as a column expression".
- **`assert` is banned in production code (ruff S101).** Python's `-O` flag strips `assert` statements, so they can't be relied on for safety checks. Use an explicit `if x is None: raise RuntimeError(...)` instead.
- **Type narrowing with `if x is None: raise`.** After `if user.household_id is None: raise HTTPException(...)`, Pyright knows `user.household_id` is `int` for the rest of the function. No need for a separate variable.
- **`int | None` is the modern Python union syntax** (Python 3.10+). Equivalent to `Optional[int]` from `typing`. SQLModel uses it for nullable fields and primary keys.

---

## Error Handling

- **`IntegrityError`** is the SQLAlchemy exception for any DB constraint violation — unique constraints, FK violations, NOT NULL violations, check constraints. It's not specific to one type.
- **Broad `IntegrityError` catch is acceptable** when other causes are ruled out by design: if `household_id` is server-set (no FK violation), `name` is Pydantic-validated (no NOT NULL violation), and there are no check constraints — the only possible cause is the unique constraint.
- **Don't introspect the driver exception.** Checking `exc.orig.pgcode` (psycopg2 convention) or `isinstance(exc.orig, asyncpg.UniqueViolationError)` is fragile across SQLAlchemy/asyncpg versions. A well-commented broad catch is more honest.
- **Always `session.rollback()` before raising** after a failed commit. SQLAlchemy async sessions don't auto-rollback; leaving the session in a failed state causes subsequent operations to fail.
- **`raise X from None`** explicitly suppresses the exception chain. Right when you're intentionally translating a low-level error (DB constraint) into an API error (HTTP 409) and don't want DB internals in the traceback.
- **`raise X from exc`** preserves the chain. Right when you want the original error context to be visible (e.g., wrapping a network error in a 502).
- **Ruff B904** enforces that `raise` inside `except` blocks must have `from err` or `from None`. Without it, the implicit chaining is ambiguous.

---

## Developer Tooling

- **`set -uo pipefail` without `-e` for lint scripts.** `-e` exits immediately on any non-zero exit code, which would kill the script before capturing lint output — lint failures are the expected case. Drop `-e` and capture output with `|| true` so both tools always run regardless of result.
- **`uv run` via a subshell, not a direct binary path.** Running `(cd backend && uv run ruff check .)` ensures `uv` resolves the correct project virtualenv without hardcoding `.venv/bin/ruff` or assuming anything about PATH. Works identically on any machine with `uv` installed.
- **`gh pr edit --body "$(cat docs/pr-description.md)"`** updates the PR description from a local file. Combine with a shell function (not an alias) so the `$()` expands at call time, not at definition time: `update-pr() { gh pr edit --body "$(cat docs/pr-description.md)"; }` in `~/.zshrc`.
- **Shell functions vs aliases for subshell expansion.** A plain `alias` expands `$()` when the alias is defined, capturing the value at shell startup. A function re-evaluates `$()` every time it's called — necessary whenever the substitution reads a file that changes between calls.
- **Claude Code skill design: classify before acting.** The `/fix-lint` skill explicitly separates "clear errors" (auto-fix: unused imports, missing annotations on private functions, print statements) from "design decisions" (wait for confirmation: `# type: ignore`, public API type changes, logic restructuring). Without this, a skill would either be too timid (ask about everything) or too aggressive (silently change semantics). The classification is defined in the skill file itself so the behaviour is predictable and auditable.

---

## Session Log

### 2026-06-08 — Lint workflow tooling (PR: feat/lint-workflow)

Built: `scripts/run-lint.sh` (Ruff + Pyright → `docs/lint-report.md`) and `/fix-lint` Claude Code skill.

Key decisions:
- `set -uo pipefail` without `-e` — lint exit codes must be captured, not abort the script
- `uv run` via subshell — no PATH assumptions, correct virtualenv always used
- `/fix-lint` skill classifies issues as "clear error" or "design decision" before acting — prevents silent semantic changes
- `docs/lint-report.md` gitignored — same pattern as `pr-comments.md` / `pr-description.md`

---

### 2026-06-09 — PR review pass on CRUD endpoints (PR: feat/crud-endpoints)

Built: worked through 8 automated review comments; applied 4 fixes, skipped 4 false positives.

Key decisions:
- Batch POST and PATCH merge quantities on `(item_id, location_id, expiry_date)` collision — 409 was wrong UX
- `household_id` filter rule established: parent verified immediately → no redundant child filter; longer chain → add filter
- `delete_location` batch queries were missing `household_id` — genuine isolation gap fixed
- Stale "scan-out v1 = no adjust endpoint" TIL entry removed (endpoint was already built)
- `gh pr edit --body "$(cat ...)"` + shell function pattern documented

---

### 2026-06-08 — CRUD refinements (PR: feat/pr-review-comments)

Built: location delete with move/merge flow, batch adjust endpoint, unique constraint on batches, spec + docs updates.

Key decisions:
- `DELETE /locations/{id}?move_to=` — query param pattern for cascading deletes
- Batch merge on move — quantities combined when target already has same (item, expiry)
- `(item_id, location_id, expiry_date)` unique constraint added to Batch model (requires table drop in Neon)
- `POST /batches/{id}/adjust` with delta — replaces PATCH+DELETE client branching
- `new_quantity < 0` → 422 (over-removal error); `== 0` → 204 (batch deleted)
- `expiry_before` filter removed from `GET /items` — FE categorises client-side
- FE v1 defined as intentionally thin slice; feature prioritisation deferred

---

### 2026-06-05 — CRUD endpoints (PR: feat/pr-review-comments)

Built: Location, Category, Item, Batch CRUD + barcode lookup proxy (`GET /lookup/barcode/{barcode}` → Open Food Facts).

Key decisions made:
- IntegrityError broad catch pattern agreed and documented
- `household_id` None guard added to all endpoints (fixes type errors + weak spot)
- `col()` introduced to fix Pyright column expression errors
- SQLModel `AsyncSession` swap in `database.py` to expose `.exec()`
- `from None` added to all `raise HTTPException` inside `except` blocks (B904)
- `assert` replaced with `if ... raise RuntimeError` (S101)
- `days` param in `/expiring` bounded with `Query(ge=1)`
- PATCH `IntegrityError` handling added to locations and categories (bug: was missing)

Errors fixed: 16 Pyright errors, 7 ruff errors.
