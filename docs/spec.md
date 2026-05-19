# Homik — Project Specification
*Homik is a playful blend of "home" and "chomik" (Polish for hamster). English speakers hear the home root instantly; Polish speakers recognise the misspelled hamster and know the wordplay is intentional. Like a hamster stuffing its cheeks, Homik knows exactly what you've stashed away.*

---

## 1. Project Overview

A mobile-friendly web app for managing household inventory — food, cleaning products, and anything stored in hard-to-see places like a cellar. Designed for real daily use by multiple households. Built as a portfolio project with real users from day one.

**Core problem:** You can't see what's in the cellar. You forget what you have, what's running low, and what's about to expire.

**Core solution:** Scan items in and out, browse your inventory by location, and see what's expiring soon.

---

## 2. Version Roadmap

### v1 — Inventory App (this spec)
- Auth + household management
- Scan items in/out via barcode
- Inventory browsing + search
- Expiring soon view

### v2 — Agent Layer
- Weekly agent run: reasons over inventory
- Writes shopping list to DB
- Sends email summary (expiring items + low stock + recipe suggestions)
- Stock movement tracking
- OCR expiry date scanning

---

## 3. Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Frontend | React (Vite) PWA | Mobile-first, installable, camera access |
| Backend | FastAPI + SQLModel | Same stack as Crumbs |
| Database | PostgreSQL via Neon | Free tier, no inactivity pause |
| Auth | FastAPI Users | JWT tokens, registration, login, password reset |
| Barcode scanning | ZXing-js | Browser-based, works on mobile camera |
| Product lookup | Open Food Facts API | Free, good European product coverage |
| Package management | uv | Same as Crumbs |
| Linting | Ruff | Same as Crumbs |
| Frontend deployment | Vercel | Free tier |
| Backend deployment | Railway or Render | Free tier |

---

## 4. Data Model

### `Household`
| Field | Type | Notes |
|---|---|---|
| id | int | Primary key |
| name | str | e.g. "Marta & David's House" |
| created_at | datetime | |

### `User`
Managed by FastAPI Users.
| Field | Type | Notes |
|---|---|---|
| id | uuid | Primary key |
| email | str | Unique |
| hashed_password | str | |
| household_id | int | FK → Household |
| is_active | bool | |
| created_at | datetime | |

**Rules:**
- One user belongs to exactly one household
- One household has many users

### `Location`
| Field | Type | Notes |
|---|---|---|
| id | int | Primary key |
| household_id | int | FK → Household |
| name | str | e.g. "Cellar", "Fridge", "Pantry", "Kitchen" |

- Household-specific, fully editable
- Seeded with sensible defaults on household creation

### `Category`
| Field | Type | Notes |
|---|---|---|
| id | int | Primary key |
| household_id | int | FK → Household |
| name | str | e.g. "Food", "Cleaning", "Personal Care" |

- Household-specific, editable (rarely needed)
- Seeded with sensible defaults on household creation

### `Item`
The product — what something *is*, not how much you have.
| Field | Type | Notes |
|---|---|---|
| id | int | Primary key |
| household_id | int | FK → Household |
| name | str | |
| barcode | str | Optional, from scan |
| category_id | int | FK → Category |
| location_id | int | FK → Location, editable |
| unit | str | e.g. "pieces", "bottles", "kg" |
| notes | str | Optional |
| created_at | datetime | |
| updated_at | datetime | |

### `Batch`
One entry per purchase of an item. Holds quantity and expiry.
| Field | Type | Notes |
|---|---|---|
| id | int | Primary key |
| item_id | int | FK → Item |
| quantity | int | |
| expiry_date | date | Month + year precision, defaults to +12 months |
| created_at | datetime | |

**Why Batch exists:** The same product (e.g. pasta) can be bought multiple times with different expiry dates. Each purchase is a separate batch.

**Alert logic:** If total quantity across all batches for an item = 0 → flag for shopping list (v2).

### `ShoppingListItem` *(data model only in v1, feature in v2)*
| Field | Type | Notes |
|---|---|---|
| id | int | Primary key |
| household_id | int | FK → Household |
| item_id | int | FK → Item, optional |
| name | str | Fallback if no item_id |
| quantity_needed | int | |
| is_purchased | bool | |
| added_by | str | "agent" or "manual" |
| created_at | datetime | |

---

## 5. User Flows

### Flow 1: Scan (add or deduct)
1. User taps **Scan** on home screen
2. Last used location is prefilled
3. Camera opens, user scans barcode (ZXing-js)
4. App queries Open Food Facts → prefills name, category
5. **If existing product:** show current batches + quantities, user can add new batch or adjust existing
6. **If new product:** form shown with prefilled name/category, user enters quantity + unit, expiry defaults to current month + 12 months (month/year picker), all fields editable
7. Save → written to DB

### Flow 2: Inventory view
1. List of all items with total quantity and location
2. Searchable/filterable by: name, location, expiry date
3. Tap item → detail view showing all batches
4. From detail: edit any field, adjust quantity per batch (+1 / -1 or type number)

### Flow 3: Expiring soon
- Filtered list of batches expiring within X days (exact threshold TBD — suggest 30 days)
- Passive view, no push notifications in v1
- Agent handles email alerts in v2

### Flow 4: Home screen
Two buttons only:
- **Scan** → Flow 1
- **Inventory** → Flow 2

Plus a nav link to **Expiring Soon**.

---

## 6. Auth + Household Management

- Registration creates a new user + new household
- Invite flow (v2): for now, household members are added manually via admin or shared invite link (simple implementation TBD)
- JWT tokens via FastAPI Users
- Protected endpoints require valid token
- All data queries scoped to `household_id` — users never see other households' data

---

## 7. API Design (high level)

### Auth
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`

### Household
- `GET /household/me`
- `PATCH /household/me`

### Locations
- `GET /locations`
- `POST /locations`
- `PATCH /locations/{id}`
- `DELETE /locations/{id}`

### Categories
- `GET /categories`
- `POST /categories`
- `PATCH /categories/{id}`
- `DELETE /categories/{id}`

### Items
- `GET /items` (supports search: name, location, expiry)
- `GET /items/{id}`
- `POST /items`
- `PATCH /items/{id}`
- `DELETE /items/{id}`

### Batches
- `GET /items/{id}/batches`
- `POST /items/{id}/batches`
- `PATCH /batches/{id}`
- `DELETE /batches/{id}`

### Expiry
- `GET /expiring?days=30` (returns batches expiring within N days)

### Barcode lookup (proxy to Open Food Facts)
- `GET /lookup/barcode/{barcode}`

---

## 8. External APIs

### Open Food Facts
- Free, no API key needed
- Endpoint: `https://world.openfoodfacts.org/api/v0/product/{barcode}.json`
- Returns: product name, brand, category, image URL
- Good coverage for European/German products
- Call from backend (proxy) to avoid CORS issues on frontend

---

## 9. Key Decisions Log

| Decision | Choice | Reason |
|---|---|---|
| App name | Homik | Wordplay: "home" for English speakers + misspelled "chomik" (hamster) for Polish speakers; pronounceable and memorable for both audiences |
| Database | Postgres via Neon | No inactivity pause, free tier, real-world standard |
| Auth | FastAPI Users | Educational, integrates with SQLModel, no black box |
| SQLite vs Postgres | Postgres | Multi-user, multi-household, multi-device |
| Expiry granularity | Month + year only | Reduces friction, good enough for pantry use |
| Expiry default | +12 months from today | Zero friction for items where expiry doesn't matter |
| Expiry OCR | v2 | Adds complexity, not needed for v1 |
| Stock movements | v2 | Agent needs this to reason intelligently |
| Shopping list feature | v2 | More useful alongside agent |
| Alert threshold | Quantity = 0 | Simple, no configuration needed |
| Notifications | None in v1 | Filtered list in app; agent emails in v2 |
| Frontend | React PWA (Vite) | Known stack, mobile-friendly, installable |
| Barcode scanning | ZXing-js | Browser-based, no native app needed |
| Image upload | Not in v1 | Unnecessary complexity |
| Multi-household user | One household per user | Simpler for v1 |
| Location default | Last used location | Lowest friction for scanning session |

---

## 10. Out of Scope for v1

- Push notifications
- Stock movement history
- OCR expiry date scanning
- Shopping list UI
- Agent / email summaries
- Recipe suggestions
- Image upload
- Multi-household per user
- Invite flow (manual household member addition for now)

---

## 11. Environment Setup

- Python 3.13 via pyenv
- uv for package management
- Ruff for linting/formatting
- Neon for Postgres (free tier)
- Vercel for frontend deployment
- Railway or Render for backend deployment
- ARM64 Mac M4, native setup (no Rosetta)

---

*Last updated: May 2026. Built with FastAPI + SQLModel + React PWA.*