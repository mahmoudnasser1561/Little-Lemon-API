# Little Lemon

A full-stack restaurant ordering platform: a Django REST API with real role-based
access control and a cache-aside layer, and a TypeScript monorepo serving two separate
frontends (a customer storefront and a staff ops console) against a shared, typed API
client and component library.

Role permissions, a cart-to-checkout-to-order lifecycle, versioned cache invalidation,
and a recent backend refactor that extracted checkout into its own Django app without
breaking a single one of the 175 existing tests.

This API is also the real workload running in
[**zero-trust-kubernetes-cluster**](https://github.com/mahmoudnasser1561/zero-trust-kubernetes-cluster):
a 15-node Kubernetes cluster with HA Postgres (CloudNativePG), HA Redis (Sentinel), and
zero-trust NetworkPolicy/RBAC, built as the production-infrastructure counterpart to this
repo.

## Architecture

```
Little-Lemon-API/
├── backend/                  Django REST API
│   ├── restaurant/           catalog, categories, users, roles
│   ├── cart/                 per-user cart
│   ├── checkout/             orders (extracted from restaurant; see commit history)
│   └── delivery_crew/        delivery assignment
│
├── frontend/                 npm workspaces monorepo
│   ├── apps/storefront/      customer-facing SPA (9 pages)
│   ├── apps/ops-console/     staff-facing SPA (3 pages, a separate deployable surface)
│   ├── packages/api-client/  typed fetch wrapper shared by both apps
│   └── packages/ui/          shared component library (8 components)
│
└── docker-compose.yml        Postgres + Redis + API + both frontends, one command
```

Two frontends instead of one SPA with hidden admin routes is a deliberate choice, not an
accident: it mirrors the backend's own role separation (`Manager`/`Delivery Crew` vs.
`Customer`) as two independently deployable surfaces, each pulling from the same shared
`api-client` and `ui` packages rather than duplicating fetch logic or buttons.

## Tech Stack

| | |
|---|---|
| **Backend** | Django 5.2, Django REST Framework, Djoser, django-filter |
| **Database** | PostgreSQL 16 (production/Docker), SQLite (local dev, zero setup) |
| **Cache** | Redis 7, cache-aside with versioned invalidation |
| **Frontend** | React 18, TypeScript, Vite, TanStack Query v5 |
| **Forms** | React Hook Form + Zod schema validation |
| **Styling** | Tailwind CSS |
| **Monorepo** | npm workspaces (2 apps, 2 shared packages) |
| **Infra** | Docker Compose (5 services, health-checked dependencies) |

## Backend

### Core Features

- Token-based authentication (`/api/api-token-auth/`) with DRF auth classes
- Role-based access control using Django groups (`Manager`, `Delivery Crew`)
- Menu items + categories APIs with full CRUD
- Cart workflow (`GET/POST/DELETE /api/cart/menu-items`) and checkout to orders
- Order lifecycle with assignment/status updates on `/api/orders/<id>`
- Pagination, search (`?search=`), ordering (`?ordering=price`/`-price`)
- Request throttling: `20/min` anonymous, `100/min` authenticated

### Role-Based Access Matrix

`Customer` means authenticated user with no group.

| Endpoint Group | Manager | Delivery Crew | Customer |
|---|---|---|---|
| `GET /api/categories/` | Yes | Yes | Yes |
| `POST /api/categories/` | Yes | No | No |
| `GET /api/menu-items/`, `GET /api/menu-items/<pk>` | Yes | Yes | Yes |
| `POST /api/menu-items/`, `PUT/PATCH/DELETE /api/menu-items/<pk>` | Yes (auth) | Yes (auth) | Yes (auth) |
| `GET/POST/DELETE /api/cart/menu-items` | Yes (own cart) | Yes (own cart) | Yes (own cart) |
| `GET /api/orders` | All orders | Assigned orders only | Own orders only |
| `POST /api/orders` | Yes | Yes | Yes |
| `GET /api/orders/<pk>` | Yes | Yes | Yes (auth) |
| `PUT/PATCH /api/orders/<pk>` | Yes | Yes | No (`Not Ok`) |
| Group management endpoints | Yes | No | No |

### Data Model

- `Category`: `slug`, `title`
- `MenuItem`: `title`, `price`, `featured`, `category`, `image`
- `Cart`: `user`, `menuitem`, `quantity`, `unit_price`, `price`; unique per `(user, menuitem)`
- `Order` / `OrderItem` (in `checkout/`): order line items created from cart at checkout; unique per `(order, menuitem)`

### Caching

A cache-aside layer sits in front of Postgres for the public catalog only: `GET /api/menu-items/`
(including every `?search=`/`?ordering=`/`?page=` combination) and `GET /api/categories/`. Cart
and orders are intentionally not cached: they're per-user, mutate on nearly every request, and
are already cheap single-user-scoped queries.

- **Read path**: a request checks Redis first. On a hit, the cached response is returned as-is; on
  a miss, it falls through to Postgres and the result is cached before responding.
- **Every cached response carries `X-Cache: HIT` or `X-Cache: MISS`**, so the behavior is directly
  observable with `curl -i`.
- **Invalidation is versioned, not scanned.** List caches are keyed as `...:v{N}:{query-hash}`. Any
  menu item write bumps the menu-list version, instantly orphaning every previously cached page
  (they expire on their own TTL, nothing is scanned or deleted). A category write bumps both the
  category-list and menu-list versions, since menu item responses embed a category snapshot.
- **TTLs are a safety net on top of invalidation**, not the primary mechanism: they catch writes
  made outside the API (Django admin, a shell). Default 5 minutes, configurable per cache.
- **Redis is a performance layer, not a source of truth.** `IGNORE_EXCEPTIONS` means an
  unreachable Redis degrades every cached endpoint to "always miss" and serves straight from
  Postgres; it never turns into a 500.
- Without `REDIS_HOST` set (local Pipenv runs, tests), `CACHES` falls back to Django's in-process
  `LocMemCache` automatically, no extra setup needed to run tests or `runserver` locally.

See `backend/restaurant/caching.py` for the implementation.

### Testing

```
Ran 175 tests in 4.023s
OK (expected failures=8)
```

Tests live next to the code they cover (`restaurant/tests/`, `cart/tests/`,
`delivery_crew/tests/`, `checkout/tests/`) and share helpers in `LittleLemonAPI/testing.py`.
They run against a separate in-memory test database and never touch `db.sqlite3`.

Tests marked `@known_bug('B..')` describe the desired behavior of a bug or feature that's
still open; they're tracked as expected failures in the suite rather than silently
skipped or deleted. Fix one and the runner reports an "unexpected success"; remove the
decorator and it becomes a normal regression test. `SHOW_KNOWN_BUGS=1` runs them as
normal tests so you can see exactly why they currently fail.

```bash
cd backend
pipenv run python manage.py test              # whole suite
pipenv run python manage.py test cart          # one app
pipenv run python manage.py test -v 2          # verbose, list every test
```

## Frontend

### `apps/storefront`: the customer app

Nine pages covering the full ordering journey: browse the menu, view an item, manage the
cart, check out, sign up / log in, view profile, and view order history / order detail.

- **Server state via TanStack Query**: cache invalidation, background refetch, and
  loading/error states handled declaratively instead of hand-rolled `useEffect` fetch
  logic.
- **Forms via React Hook Form + Zod**: schema-validated forms (login, sign-up, checkout)
  with type inference flowing from the same Zod schema used to validate.
- **Route guards** (`RequireAuth.tsx`) gate cart/checkout/profile/orders behind a real
  authenticated-session check, not just hidden nav links.

### `apps/ops-console`: the staff app

A genuinely separate SPA for `Manager`/`Delivery Crew` users: menu item management and
category management, not admin routes bolted onto the customer app behind a role check.
Same shared `api-client`/`ui` packages, same auth token mechanism, its own route guard
(`RequireStaffAuth.tsx`) and its own Vite dev server (`:5174`, vs. the storefront's
`:5173`).

### Shared packages

- **`packages/api-client`**: the one place that knows how to talk to the Django API,
  base URL, auth header injection, JSON handling, a typed `ApiError` with status + body,
  and a settable `onUnauthorized` hook so a 401 anywhere triggers the same sign-out
  behavior app-wide. Every resource module (`menu.ts`, `cart.ts`, `orders.ts`,
  `categories.ts`, `auth.ts`) goes through one `request<T>()` function rather than
  scattering `fetch` calls. `localStorage` access is wrapped in `try/catch` everywhere:
  private browsing or blocked storage degrades to "signed out," it never throws.
- **`packages/ui`**: 8 shared components (`Button`, `Card`, `Input`, `FormField`,
  `Badge`, `Chip`, `Pagination`, `Stepper`) consumed by both apps, so a button doesn't
  have two slightly different implementations across the storefront and ops console.

### Dev-mode networking, done properly

Requests are relative (`/api/...`), not absolute: Vite's dev server proxies them to the
real backend, same-origin, no CORS configuration needed anywhere. The proxy target is
environment-aware: `http://localhost:8000` for `npm run dev` on the host, overridden to
`http://api:8000` inside `docker-compose` (the frontend container's own `localhost` isn't
the API container). The same relative-path pattern holds in production behind an
ingress: the ingress routes `/api` to the backend service, same-origin from the
browser's point of view either way.

### What's not here yet

No frontend unit/e2e tests. Type safety currently comes from TypeScript's own compiler
(`tsc -b --noEmit`), not a test suite. Worth being direct about that rather than
implying otherwise.

## Running with Docker

```bash
cp backend/.env.example backend/.env
# edit backend/.env: set POSTGRES_PASSWORD and SECRET_KEY to real values
# generate a SECRET_KEY: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

docker compose up
```

One command brings up all five services (Postgres, Redis, the API, and both frontends)
with health-checked startup ordering (the API waits for Postgres/Redis to actually be
ready, not just "started"). Migrations run automatically.

| Service | URL |
|---|---|
| API | http://localhost:8000 |
| Storefront | http://localhost:5173 |
| Ops console | http://localhost:5174 |

Both frontends run Vite's dev server with hot reload; the source is bind-mounted in, so
editing on the host reflects live in the running containers. To bring up just the
backend: `docker compose up db redis api`.

Since there's no public manager signup endpoint by design, create one inside the running
container:

```bash
docker compose exec api python manage.py create_user --role manager --username boss --email boss@example.com
```

## Local Setup, No Docker

Backend on SQLite (zero setup):

```bash
cd backend
pipenv install
pipenv run python manage.py migrate
pipenv run python manage.py createsuperuser
pipenv run python manage.py runserver
```

Frontend, either app:

```bash
cd frontend
npm install
npm run dev:storefront      # :5173
npm run dev:ops-console     # :5174
```

## Environment Variables

All optional: every one has a fallback that keeps local/test runs working with zero setup.

- `SECRET_KEY`: falls back to a hardcoded dev value if unset.
- `DEBUG`: defaults to `True` locally; `docker-compose.yml` sets `False`.
- `ALLOWED_HOSTS`: comma-separated; defaults to `[]`.
- `POSTGRES_DB`/`USER`/`PASSWORD`/`HOST`/`PORT`: set → Postgres; unset → `db.sqlite3`.
- `REDIS_HOST`/`PORT`/`PASSWORD`/`DB`: set → Redis cache; unset → in-process `LocMemCache`.
- `CACHE_TTL_MENU_LIST`/`CACHE_TTL_MENU_ITEM`/`CACHE_TTL_CATEGORY_LIST`: seconds, default `300`.
- `VITE_API_BASE_URL`: frontend override for pointing at a deployed API with no dev proxy in front.
- `VITE_PROXY_TARGET`: frontend dev-proxy target; `docker-compose` sets this to `http://api:8000`.

## Roadmap

- Fix Djoser user-create serializer to include the password flow
- Tighten object-level permissions for order detail/update
- Frontend unit/e2e test coverage
- Production (static build + nginx) image for the frontend, alongside the current dev-mode one
