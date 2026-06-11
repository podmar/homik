# Homik — Project Specification
*Homik is a playful blend of "home" and "chomik" (Polish for hamster). English speakers hear the home root instantly; Polish speakers recognise the misspelled hamster and know the wordplay is intentional. Like a hamster stuffing its cheeks, Homik knows exactly what you've stashed away.*

---

## 1. Project Overview

A mobile-friendly web app for managing household inventory — food, cleaning products, and anything stored in hard-to-see places like a cellar. Designed for real daily use by multiple households. Built as a portfolio project with real users from day one.

**Core problem:** You can't see what's in the cellar. You forget what you have, what's running low, and what's about to expire.

**Core solution:** Scan items in and out, browse your inventory by location, and see what's expiring soon.

---

## 2. Version Roadmap

### v1 — Backend (complete)
- Auth + household management
- CRUD for locations, categories, items, batches
- Barcode lookup proxy (Open Food Facts)
- Expiring soon view

### v1 — Frontend (in progress)
Intentionally a thin slice — get something working and user-friendly first, then add features based on real usage. Feature prioritisation happens after the first working version, not before.

Minimum to ship:
- Auth (register, login)
- Inventory list
- Item detail + batch list
- Scan flow (barcode → add batch)

Filters, search, and additional views are deferred until real usage shows what's needed. No v2 FE scope defined yet.

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
| brand | str | Optional, from Open Food Facts |
| image_url | str | Optional, from Open Food Facts |
| category_id | int | FK → Category |
| unit | str | e.g. "pieces", "bottles", "kg" |
| notes | str | Optional |
| created_at | datetime | |
| updated_at | datetime | |

**Note:** `location_id` is not on Item — location is tracked per Batch, since the same product can be stored in multiple places at once.

### `Batch`
One group of units sharing the same location and expiry date.
| Field | Type | Notes |
|---|---|---|
| id | int | Primary key |
| item_id | int | FK → Item |
| household_id | int | FK → Household — denormalized from Item for query isolation |
| location_id | int | FK → Location |
| quantity | int | Must be > 0 |
| expiry_date | date | Stored as full date; UI shows month + year only. Defaults to +12 months |
| created_at | datetime | |

**Why Batch exists:** The same product can be bought multiple times with different expiry dates, and/or stored across multiple locations. Each unique combination of item + location + expiry = one batch. This is enforced by a DB unique constraint on `(item_id, location_id, expiry_date)`.

**Merge on move:** When batches are moved to another location (via `DELETE /locations/{id}?move_to=`), if the target already has a batch for the same item + expiry date, the quantities are merged rather than creating a duplicate.

**Real-world example:** Buy 6 passatas → create two batches: `{quantity: 4, location: cellar, expiry: June 2027}` and `{quantity: 2, location: pantry, expiry: June 2027}`. Inventory view shows total = 6, broken down by location.

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
4. App queries Open Food Facts → prefills name, brand, image, category
5. **If existing product:** show current batches + quantities (grouped by location), user can add new batch or adjust existing
6. **If new product:** form shown with prefilled name/category, user enters quantity + unit, expiry defaults to current month + 12 months (month/year picker), all fields editable
7. **Split by location:** user can tap "Add another location" to create a second batch entry for the same purchase (e.g. 4 to cellar, 2 to pantry)
8. Save → written to DB

### Flow 2: Inventory view
1. List of all items with total quantity across all locations
2. Searchable/filterable by: name, location, expiry date
3. Tap item → detail view showing all batches (each with location, quantity, expiry)
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
- JWT tokens via FastAPI Users
- Protected endpoints require valid token
- All data queries scoped to `household_id` — users never see other households' data

### Invite flow (v2)

Registration forks into two paths depending on whether an invite token is present:

1. **No token** — creates a new `Household`, assigns it to the new user (current v1 behaviour)
2. **With token** — redeems the invite, assigns the existing `Household` to the new user instead

**Data model addition:** `HouseholdInvite` table

| Field | Type | Notes |
|---|---|---|
| id | int | Primary key |
| household_id | int | FK → Household |
| token | str | Unique, URL-safe random string |
| created_by | uuid | FK → User (who generated the invite) |
| expires_at | datetime | Short-lived — suggest 48 hours |
| used_at | datetime | Nullable; set on redemption to prevent reuse |

**Flow:**
1. Existing household member calls `POST /household/invite` → creates a `HouseholdInvite` row, returns a link containing the token
2. New user registers via `POST /auth/register` with the token in the request body
3. `on_after_register` hook in `UserManager` checks for the token: if valid and unexpired, sets `household_id` to the invite's household and marks `used_at`; otherwise creates a new household as normal

**Notes:**
- Tokens are single-use (`used_at` check prevents replay)
- Expired or already-used tokens fall back to creating a new household — or return a 400, TBD
- No email sending in v2; the link is shared manually (copy/paste or messaging app)
- `User.household_id` is already nullable in the current model, so no schema migration needed for the User table

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
- `GET /items` (supports search: `?name=`, `?location_id=`)
- `GET /items/{id}`
- `POST /items` — upsert: if a barcode is provided and already exists in the household, returns the existing item with HTTP 200 so the client can proceed to add a batch. Returns 201 for a new item.
- `PATCH /items/{id}`
- `DELETE /items/{id}` — cascades to all batches for that item

### Batches
- `GET /items/{id}/batches`
- `POST /items/{id}/batches` — `location_id` is optional; server defaults to last-used location for the household, then falls back to the first seeded location
- `POST /batches/{id}/adjust` — preferred endpoint for scan in/out. Accepts `{"delta": int}` (positive = add stock, negative = use stock). Returns 200 + updated batch if quantity > 0 after adjustment; returns 204 and deletes the batch if quantity reaches 0 or below.
- `PATCH /batches/{id}` — direct quantity/location/expiry override; use adjust for scan flows
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
| Expiry granularity | Stored as full date, displayed as month + year | Full date allows precise filtering and sorting; month/year display reduces friction for the user |
| Expiry default | +12 months from today | Zero friction for items where expiry doesn't matter |
| Expiry OCR | v2 | Adds complexity, not needed for v1 |
| Stock movements | v2 | Agent needs this to reason intelligently |
| Shopping list feature | v2 | More useful alongside agent |
| Alert threshold | Quantity = 0 | Simple, no configuration needed |
| Notifications | None in v1 | Filtered list in app; agent emails in v2 |
| Frontend | React PWA (Vite) | Known stack, mobile-friendly, installable |
| Barcode scanning | ZXing-js | Browser-based, no native app needed |
| Image upload | Not in v1 | Unnecessary complexity; image_url from OFF is sufficient |
| Multi-household user | One household per user | Simpler for v1; invite flow in v2 handles joining an existing household without changing this constraint |
| Location on Batch not Item | location_id on Batch | Same product can live in multiple locations (e.g. cellar + pantry); batch = unique combo of location + expiry |
| Location default | Last used location | Lowest friction for scanning session |
| brand + image_url on Item | Added in v1 | Single fields, zero complexity; brand disambiguates products; retrofitting requires migration |
| Expiry date source | Manual entry in v1, OCR in v2 | Standard consumer barcodes (EAN-13, UPC-A) encode only the product ID — no expiry date. The date must be read from the packaging. Manual entry with a +1 year default covers v1; OCR via camera is the v2 solution. |
| Past expiry dates | Allowed | No validation rejecting past `expiry_date` on batch creation — needed for initial inventory setup where users scan items already in the house. These batches appear immediately in the expiring-soon view. |
| Scan-out (deduction) flow | `POST /batches/{id}/adjust` | A dedicated adjust endpoint with a signed delta is simpler for the frontend than requiring it to calculate new quantity and branch between PATCH and DELETE. Auto-deletes the batch when quantity reaches zero. |

### API Contract Decisions

- **POST /items — upsert on barcode match.** Returns the existing item with HTTP 200 if a barcode already exists in the household; 201 for a new item. Client uses the status code: 200 = proceed to add a batch; 201 = fill out the new item form. Avoids a separate lookup-then-create round-trip.
- **`quantity > 0` enforced at two layers.** Pydantic `Field(gt=0)` returns a clean 422. DB `CheckConstraint("quantity > 0")` is the safety net if the API layer is bypassed.
- **Cascade delete on items — explicit in code, not DB.** `DELETE /items/{id}` manually deletes all batches first, then the item. N+1 queries accepted at household scale; a DB cascade would obscure the intent.
- **Merge on POST/PATCH collision instead of rejecting.** Both `POST /items/{id}/batches` and `PATCH /batches/{id}` merge quantities when `(item_id, location_id, expiry_date)` would collide. User intent is "add stock here" — a 409 forces the client to recover from something that isn't an error. Both endpoints return the surviving batch; PATCH may return a batch with a different `id` than the URL.
- **409 for FK-protected deletes.** Deleting a location that has batches, or a category that has items, returns 409. Data is not orphaned; the client gets a clear rejection signal.
- **`DELETE /locations/{id}?move_to={id}` — query param for cascading deletes.** One endpoint covers all cases: no batches → clean delete; has batches + no `move_to` → 409 with instructions; has batches + `move_to` → move then delete.
- **Cannot delete the last location.** Deleting the only location in a household is blocked with 409 — batches would have nowhere to move.
- **FE categorises inventory, not the backend.** `GET /items` returns all items; the frontend sorts into stocked / expiring soon / expired / out of stock from batch data it already has. No `expiry_before` filter on `GET /items` — don't add backend filters until a real screen proves it's needed. `GET /expiring` exists for the dedicated flat-list sorted by date.

---

## 10. Out of Scope for v1

- Push notifications
- Stock movement history
- OCR expiry date scanning
- Shopping list UI
- Agent / email summaries
- Recipe suggestions
- Image upload (image_url from Open Food Facts only)
- Multi-household per user
- Invite flow UI (backend design is specced in section 6, build in v2)

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

*Last updated: June 2026. Built with FastAPI + SQLModel + React PWA.*