# Finance System

A production-grade backend for a finance dashboard, built with **FastAPI**, **SQLAlchemy 2.0 (async)**, **Pydantic v2**, and **SQLite**

---

## Architecture Overview

```
finance_system/
├── src/
│   ├── server.py              # Entry point — mounts the FastAPI app
│   ├── constants.py           # DB column lengths, validation limits
│   ├── enums/                 # UserRole, RecordType, RecordCategory
│   ├── config/                # Pydantic-Settings — reads from .env
│   ├── log/                   # Coloured dev logger / JSON prod logger
│   ├── clients/db/            # Async SQLAlchemy engine, session factory, Alembic runner
│   ├── models/                # SQLAlchemy ORM models (User, FinancialRecord)
│   ├── schemas/               # Pydantic v2 request/response schemas
│   ├── services/              # Business logic — all DB queries live here
│   ├── handlers/              # JWT dependency, global error handlers, app factory
│   ├── middleware/            # Request-logging + rate-limiter middleware
│   └── routes/                # FastAPI routers (auth, users, records, dashboard)
├── alembic/                   # Database migrations
└── tests/                     # Pytest async test suite
```

The layered design keeps **routes thin** (only HTTP concerns), **services pure** (only DB / business logic), and **schemas strict** (validation happens at the boundary).

---

## Data Models

### User
| Field | Type | Notes |
|---|---|---|
| id | BigInteger PK | Auto-increment |
| email | String(255) UNIQUE | Indexed |
| full_name | String(255) | |
| hashed_password | String(255) | bcrypt |
| role | String(50) | viewer / analyst / admin |
| is_active | Boolean | Soft-disable without deletion |
| created_at / updated_at | DateTime | UTC |

### FinancialRecord
| Field | Type | Notes |
|---|---|---|
| id | BigInteger PK | |
| created_by_id | FK → user.id | Indexed |
| amount | Numeric(15,2) | Always positive |
| type | String(50) | income \| expense |
| category | String(100) | Validated against type |
| record_date | Date | Indexed |
| notes | String(1000) | Optional |
| created_at / updated_at | DateTime | UTC |

---

## Roles & Access Control

| Endpoint | Viewer | Analyst | Admin |
|---|:---:|:---:|:---:|
| `POST /auth/register` | ✅ public | | |
| `POST /auth/login` | ✅ public | | |
| `GET /users/me` | ✅ | ✅ | ✅ |
| `GET /users` | ❌ | ❌ | ✅ |
| `POST /users` | ❌ | ❌ | ✅ |
| `PUT/DELETE /users/:id` | ❌ | ❌ | ✅ |
| `GET /records` | ✅ | ✅ | ✅ |
| `GET /records/:id` | ✅ | ✅ | ✅ |
| `POST /records` | ❌ | ❌ | ✅ |
| `PUT/DELETE /records/:id` | ❌ | ❌ | ✅ |
| `GET /dashboard/summary` | ✅ | ✅ | ✅ |
| `GET /dashboard/recent` | ✅ | ✅ | ✅ |
| `GET /dashboard/by-category` | ❌ | ✅ | ✅ |
| `GET /dashboard/trends` | ❌ | ✅ | ✅ |

Access control is enforced via FastAPI dependency injection in `handlers/auth_handlers.py`. The `require_role(*roles)` factory returns a typed dependency that validates the JWT-decoded role before the handler runs.

---

## API Reference

### Authentication
```
POST /api/v1/auth/register   — Create account (defaults to viewer role)
POST /api/v1/auth/login      — Returns JWT access token
```

### Users (Admin only except /me and own profile)
```
GET    /api/v1/users                  — List all users (filter: role, is_active)
POST   /api/v1/users                  — Create user with explicit role
GET    /api/v1/users/me               — Current user profile
GET    /api/v1/users/{id}             — Get user (admin or self)
PUT    /api/v1/users/{id}             — Update name, role, active status
DELETE /api/v1/users/{id}             — Delete user (cannot delete self)
```

### Financial Records
```
GET    /api/v1/records                — List records (filter: type, category, date_from, date_to, search, page, page_size)
POST   /api/v1/records                — Create record [Admin]
GET    /api/v1/records/{id}           — Get single record
PUT    /api/v1/records/{id}           — Update record [Admin]
DELETE /api/v1/records/{id}           — Soft-delete record (sets is_deleted=true) [Admin]
```

### Dashboard
```
GET /api/v1/dashboard/summary         — Total income, expenses, net balance, counts
GET /api/v1/dashboard/recent          — Latest N records (default 10, max 50)
GET /api/v1/dashboard/by-category     — Totals grouped by category [Analyst+]
GET /api/v1/dashboard/trends          — Monthly income/expense over last N months [Analyst+]
```

### System
```
GET /health   — Health check (no auth)
```

---

## Local Setup

### Prerequisites
- Python 3.11+
- [Poetry](https://python-poetry.org/) — `pip install poetry`

### Steps

```bash
# 1. Install dependencies
cd finance_system
poetry install

# 2. Configure environment
cp .env.example .env
# Edit .env if needed — SQLite requires no further setup

# 3. Run migrations (auto-runs on startup, but can run manually)
cd finance_system
PYTHONPATH=src poetry run alembic upgrade head

# 4. Start the server
PYTHONPATH=src poetry run python src/server.py
```

Server starts at `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.

On first startup with no users, the admin seed account is created automatically using the credentials in `.env`:
- **Email:** `admin@example.com`
- **Password:** `Admin@12345`

### Docker

```bash
docker build -t finance-system .
docker run -p 8000:8000 --env-file .env finance-system
```

---

## Running Tests

```bash
cd finance_system
PYTHONPATH=src poetry run pytest -v
```

Tests use an **in-memory SQLite database** — no setup needed. Each test gets a fresh transaction via fixture-level cleanup.

---

## Design Decisions & Tradeoffs

### Database
- **SQLite + aiosqlite** is the default for zero-configuration local development. The entire stack uses SQLAlchemy 2.0 abstractions, so swapping to PostgreSQL (asyncpg) only requires changing two env vars: `DB_DRIVER` and the connection fields.
- `render_as_batch=True` in Alembic env enables ALTER TABLE support on SQLite (SQLite does not support native column alterations).

### Authentication
- **JWT (HS256)** tokens carry `sub` (user ID) and `role` claims. Role is re-read from the DB on each request to respect real-time deactivation/role changes — the JWT role is only used as a fast-path hint.
- Passwords are hashed with **bcrypt** via passlib.

### Access Control
- Role enforcement is centralised in `handlers/auth_handlers.py` via `require_role(*roles)`. Routes declare their access requirement as a single Depends — no scattered `if user.role != ...` checks inside handlers.

### Validation
- All input is validated at schema boundary with Pydantic v2. Cross-field rules (e.g. category must match type) use `@model_validator(mode="after")`.
- Error responses include a structured `errors` list with field path and message.

### Dashboard
- Summary and category breakdown use single-query SQL aggregations for efficiency.
- Monthly trends aggregate in Python after a single date-range scan — portable across SQLite and PostgreSQL without driver-specific date functions.

### Logging
- Development: coloured, human-readable output with request ID prefix.
- Production (`ENVIRONMENT=production`): structured JSON, request ID on every log line.
- A `ContextVar` threads the request ID through the async call stack without explicit propagation.

### Soft Delete
- `DELETE /records/{id}` sets `is_deleted = true` rather than removing the row. All read queries, dashboard aggregations, and trend calculations silently exclude deleted records. The data is preserved for audit purposes and can be restored by an admin directly via DB if needed.

### Search
- `GET /records?search=<term>` does a case-insensitive `ILIKE` match across the `notes` and `category` columns. The search term is combined with all other filters (type, category, date range, pagination) in a single query.

### Rate Limiting
- Powered by **slowapi** (a FastAPI-native wrapper around limits). Auth endpoints are throttled per client IP:
  - `POST /auth/login` — 10 requests/minute
  - `POST /auth/register` — 20 requests/minute
- Exceeding the limit returns `429 Too Many Requests` with a `Retry-After: 60` header.

### Admin Seeding
- On first startup with an empty `user` table, the server auto-creates an admin account from `.env` config. This avoids a chicken-and-egg problem where no admin exists to create the first admin.
