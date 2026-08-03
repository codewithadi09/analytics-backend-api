# OneCX Analytics Backend

A production-oriented FastAPI backend powering a custom analytics dashboard for [OneCX](https://one-cx.com), a B2B customer-experience consultancy. The backend sits between a PostgreSQL warehouse populated by real RudderStack behavioral event data and a React (Vite + Tailwind) frontend, exposing purpose-built REST endpoints for eight real analytics domains, plus a self-contained internal auth/admin system.

[![Python](https://img.shields.io/badge/Python-3.14%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.140%2B-009688)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-336791)](https://www.postgresql.org/)
[![SQLite](https://img.shields.io/badge/SQLite-app%20data-003B57)](https://www.sqlite.org/)
[![Redis](https://img.shields.io/badge/Redis-cache%20%2B%20sessions-DC382D)](https://redis.io/)
[![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey)](#license)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Data Model — Two Separate Databases](#data-model--two-separate-databases)
- [Authentication & Authorization](#authentication--authorization)
- [Request Lifecycle](#request-lifecycle)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [API Design Philosophy](#api-design-philosophy)
- [Error Handling](#error-handling)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Windows-Specific Notes](#windows-specific-notes)
- [Development Philosophy](#development-philosophy)
- [Known Limitations & Roadmap](#known-limitations--roadmap)
- [License](#license)

---

## Overview

This service exposes authenticated REST APIs that deliver real analytics data to a React dashboard. The frontend never queries any database directly — every visualization is backed by a dedicated, purpose-built API endpoint.

Event data originates from visitor interactions on the OneCX website (page views, clicks, form activity), is collected by **RudderStack**, and lands in a PostgreSQL schema (`rudder_schema`) as 44 tables. This backend's analytics data source is exclusively that schema, accessed **read-only** — the application never writes to it, and RudderStack's only responsibility is ingestion.

A second, entirely separate concern — the application's own user accounts (for internal dashboard access, not analytics subjects) — lives in a local **SQLite** database, deliberately kept apart from the analytics warehouse. See [Data Model](#data-model--two-separate-databases) below for why this separation matters.

The system was originally scaffolded against fake e-commerce mock data (Phases 1–11) to learn the architecture from first principles, then fully rebuilt (Phase 12 onward) against real behavioral data once database access was granted, and most recently extended with a complete internal authentication system replacing an initial mock auth layer.

## Architecture

```
┌─────────┐     ┌─────────────┐     ┌────────────────┐     ┌──────────────────┐     ┌──────────────┐
│ Website │ ──▶ │ RudderStack │ ──▶ │  PostgreSQL     │ ──▶ │  FastAPI Backend  │ ──▶ │ React Frontend│
└─────────┘     └─────────────┘     │  (rudder_schema)│     └──────────────────┘     │ (Vite +       │
                                     └────────────────┘              │                │  Tailwind)    │
                                                                      │                └──────────────┘
                                                              ┌───────┴────────┐
                                                              │                │
                                                        ┌─────▼─────┐   ┌──────▼──────┐
                                                        │  SQLite    │   │    Redis    │
                                                        │ (app users)│   │ (cache,     │
                                                        └────────────┘   │  rate limit,│
                                                                         │  sessions)  │
                                                                         └─────────────┘
```

**Boundaries are strict:**
- The frontend communicates only with FastAPI.
- FastAPI's analytics queries touch only `rudder_schema` in PostgreSQL, and only via `SELECT` — this app has no write access there and needs none.
- FastAPI's own operational data (user accounts) lives only in SQLite, entirely separate from the analytics warehouse.
- RudderStack only writes events into PostgreSQL and is never queried directly by this backend.
- Redis backs caching, rate limiting, and revocable session tokens — never the source of truth for any of the three data domains above.

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.14 |
| Framework | FastAPI |
| ASGI Server | Uvicorn |
| Analytics database | PostgreSQL 18 (`rudder_schema`, read-only) |
| Analytics DB driver | psycopg (v3), `psycopg[pool]` — raw parameterized SQL, no ORM |
| App database | SQLite (`aiosqlite`), WAL mode |
| Cache / sessions / rate limiting | Redis (`redis.asyncio`) |
| Auth | JSON Web Tokens (`python-jose`), access + revocable refresh tokens |
| Password hashing | bcrypt, called directly (not via Passlib) |
| Config management | `pydantic-settings`, `.env` |
| Validation | Pydantic v2 |
| Frontend | React + Vite + Tailwind CSS v4 |
| Event collection | RudderStack |
| API style | REST, JSON |

## Data Model — Two Separate Databases

This project deliberately maintains **two independent databases with different connection modules, different drivers, and different write permissions.** Conflating them was identified early on as a design risk and avoided throughout:

| | PostgreSQL (`rudder_schema`) | SQLite (`app_data.db`) |
|---|---|---|
| **Contains** | Real RudderStack behavioral events — page views, clicks, form activity, identities | This app's own operational data — user accounts, password hashes, roles |
| **Access level** | Read-only (`SELECT` only; no `CREATE`/`INSERT` grant) | Full read/write — this app owns this database |
| **Connection module** | `app/database/connection.py` (async connection pool) | `app/database/app_connection.py` (single shared connection, WAL mode) |
| **Who is a "user" here** | Anonymous website visitors, identified only by `anonymous_id` (and resolved email/name post-conversion) | Internal dashboard operators (superadmin + members) |

Reaching for the wrong one of these for a given piece of data is treated as a design bug, not a style preference.

## Authentication & Authorization

This is an **internal tool with no public self-signup.** Access is provisioned exclusively by a superadmin.

- **Bootstrap superadmin:** credentials (`SUPERADMIN_USERNAME`, `SUPERADMIN_PASSWORD`) come from `.env` and are seeded into SQLite once, automatically, on first startup — safe to leave in place on every subsequent boot (no-op if the account already exists).
- **Username/password only** — there is no email anywhere in the auth system. Members are provisioned by the superadmin with just a username and a password.
- **No self-service password recovery.** If a member forgets their password, the superadmin resets it directly via an admin endpoint — there is no "forgot password" email flow, consistent with there being no email field at all.
- **Two permission levels, not a role framework:** a single `is_superadmin` boolean flag distinguishes "can manage other accounts" from "can't." A broader multi-role system was explicitly deferred.
- **Tokens:** a 30-minute JWT **access token** is paired with a 30-day, **revocable, rotating refresh token**. The refresh token is tracked server-side in Redis (one active refresh token per user at a time); each use rotates it (old one destroyed, new one issued), and a password change immediately revokes it. This means a stolen refresh token can be invalidated on demand, not just left to expire naturally.
- **Stateless authorization:** the JWT embeds `user_id` and `is_superadmin` as claims at issuance, so every protected route knows the caller's identity and permission level without a database lookup on every request. The tradeoff: a permission change takes effect within the token's 30-minute lifetime, not instantly — an accepted cost for keeping every protected request fast.

**Flow:**

1. The client submits `{username, password}` to `POST /auth/login`.
2. On success, the backend issues `{access_token, refresh_token}`.
3. The frontend attaches the access token to every request: `Authorization: Bearer <access_token>`.
4. When the access token expires, the frontend silently trades the refresh token for a new pair via `POST /auth/refresh`, without prompting for a password.
5. An invalid, expired, or revoked access token short-circuits the request with `401 Unauthorized`; a non-superadmin calling an admin-only route gets `403 Forbidden`.

## Request Lifecycle

Every request flows through the same layered path in both directions, regardless of which database it ultimately reaches:

```
Client
  → API Layer          (FastAPI routes, request/response validation)
    → Service Layer     (business logic, caching decisions)
      → Repository Layer (raw SQL / SQLite queries)
        → Database Connection
          → PostgreSQL (rudder_schema)  or  SQLite (app_data.db)
        ← Database Connection
      ← Repository Layer
    ← Service Layer
  ← API Layer
← JSON Response → Client
```

Each layer has exactly one responsibility, which keeps failures isolated and logic easy to trace — a rule enforced consistently across all eight analytics domains and the auth/admin layer alike.

## Project Structure

| Layer | Responsibility |
|---|---|
| **api/** | Route definitions — receives HTTP requests, returns HTTP responses |
| **services/** | Business logic, caching decisions, cross-repository orchestration |
| **repositories/** | Raw SQL (Postgres) or SQLite queries — the only layer that touches a database directly |
| **database/** | Connection management — `connection.py` (Postgres pool) and `app_connection.py` (SQLite) are entirely separate modules |
| **auth/** | JWT issuance/verification, FastAPI dependencies (`get_current_user`, `require_rate_limit`, `require_admin`) |
| **schemas/** | Pydantic request/response models, one file per domain |
| **core/** | Configuration, shared constants, low-level security primitives |
| **utils/** | Middleware — request logging, security headers |

```
app/
├── main.py                    # FastAPI app factory, middleware, startup/shutdown lifecycle
├── api/                       # Route definitions
│   ├── auth.py                 # login, refresh, change-own-password
│   ├── admin.py                 # superadmin-only user management
│   ├── filters.py
│   ├── traffic.py
│   ├── interactions.py
│   ├── navigation.py
│   ├── journey.py               # visitor selector + cross-session detail
│   ├── engagement.py
│   ├── conversion.py
│   ├── form_dropoff.py
│   └── dropoff_explorer.py
├── services/                  # Business logic + caching
├── repositories/               # SQL / SQLite data access
├── database/
│   ├── connection.py            # PostgreSQL async pool (rudder_schema, read-only)
│   └── app_connection.py        # SQLite connection (app's own user data)
├── auth/
│   ├── jwt.py                   # token issuance/verification, Redis-backed revocation
│   └── dependencies.py          # get_current_user, require_rate_limit, require_admin
├── core/
│   ├── config.py                # pydantic-settings, loads .env
│   ├── constants.py              # real event/table names, funnel steps, Redis key prefixes
│   ├── security.py               # bcrypt hashing, JWT encode/decode primitives
│   └── redis_client.py
├── schemas/                    # Pydantic models, one file per domain
└── utils/
    ├── request_logging.py
    └── security_headers.py
```

## API Reference

All protected endpoints require `Authorization: Bearer <access_token>`. Errors are always shaped `{"detail": {"message": "...", "code": "SOME_CODE"}}`.

### Auth — `/auth`

| Method & Path | Auth | Description |
|---|---|---|
| `POST /auth/login` | Public | `{username, password}` → access + refresh tokens |
| `POST /auth/refresh` | Requires valid refresh token | Trades a refresh token for a new access + refresh pair (rotating) |
| `PATCH /auth/me/password` | Any logged-in user | Change your own password (requires current password) |

### Admin — `/admin` (superadmin only, `403` otherwise)

| Method & Path | Description |
|---|---|
| `POST /admin/users` | Create a new member (username + password only) |
| `PATCH /admin/users/{username}/password` | Reset a specific member's password |
| `GET /admin/users` | List all accounts (never includes password hashes) |

### Filters — `/filters`

| Method & Path | Description |
|---|---|
| `GET /filters` | Funnel steps, known event names, traffic sources, and overall date range — populates dashboard filter controls |

### Analytics Domains

| Domain | Endpoints |
|---|---|
| **Traffic & Overview** | `GET /traffic/overview` |
| **Interactions / Click Analytics** | `GET /interactions/leaderboard`, `GET /interactions/events` |
| **Navigation Path Analysis** | `GET /navigation/overview` |
| **User Journey** | `GET /journey/visitors` (searchable selector), `GET /journey/{anonymous_id}` (cross-session detail, `sort_order` only — no date-range filter here by design) |
| **Services & Content Engagement** | `GET /engagement/overview` |
| **Conversion Funnel** | `GET /conversion/funnel` — the core lead-generation metric |
| **Form Field Drop-off** | `GET /form-dropoff/overview` |
| **Drop-off Explorer** | `GET /dropoff-explorer/summary`, `GET /dropoff-explorer/visitors` |

### System

| Method & Path | Description |
|---|---|
| `GET /health` | Liveness/readiness check — reports Redis and PostgreSQL connectivity |
| `GET /docs` | Interactive OpenAPI (Swagger) documentation |

## API Design Philosophy

Endpoints are designed around business questions, not database tables — the frontend requests a *traffic overview* or a *conversion funnel*, never raw rows from an underlying table. Each endpoint returns exactly what its corresponding dashboard panel needs, which:

- Minimizes payload size and unnecessary data transfer
- Simplifies frontend integration
- Hides internal schema details (including the 44-table RudderStack schema and its inconsistencies) from consumers entirely

## Error Handling

Every error is returned as JSON with a standard HTTP status code and a consistent `{message, code}` shape, enforced globally via a shared exception handler in `main.py`:

| Code | Meaning |
|---|---|
| `200 OK` | Successful request |
| `201 Created` | Resource successfully created |
| `400 Bad Request` | Invalid request parameters (e.g. unknown funnel step, out-of-order step pair) |
| `401 Unauthorized` | Authentication failed, missing, expired, or revoked token |
| `403 Forbidden` | Authenticated but lacking the required permission (non-superadmin on an admin route) |
| `404 Not Found` | Requested resource does not exist (e.g. no journey for a given visitor) |
| `422 Unprocessable Entity` | Request body/query failed schema validation |
| `429 Too Many Requests` | Rate limit exceeded |
| `500 Internal Server Error` | Unexpected server-side error (generic message in production; real exception included only when `DEBUG=true`) |

## Getting Started

**Prerequisites:** Python 3.14+, Docker Desktop (for Redis), and SSH access to the remote PostgreSQL server.

```powershell
# Clone and enter the project
git clone https://github.com/codewithadi09/analytics-backend-api.git
cd analytics-backend-api

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
copy .env.example .env
# then edit .env with real values -- see Environment Variables below
```

**Start Redis** (in its own terminal, left running):

```powershell
docker start analytics-redis
# first time only, if the container doesn't exist yet:
# docker run -d --name analytics-redis -p 6379:6379 redis:7-alpine
```

**Open the SSH tunnel to PostgreSQL** (in its own dedicated terminal, left running — do not close):

```powershell
ssh -i "path\to\your\private_key" -N -L 5433:127.0.0.1:5432 root@<remote-host>
```

**Run the development server:**

```powershell
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API documentation, or `http://localhost:8000/health` to confirm Redis and PostgreSQL connectivity.

## Environment Variables

All configuration is loaded exclusively through `app/core/config.py` — no other module reads `os.environ` directly. Required variables in `.env` (never committed):

| Variable | Purpose |
|---|---|
| `JWT_SECRET_KEY` | Signs access/refresh tokens — must not be a placeholder value; the app refuses to start otherwise |
| `DATABASE_URL` | PostgreSQL connection string, via the SSH tunnel (`127.0.0.1:5433`, **not** `localhost` — see Windows notes) |
| `REDIS_URL` | Redis connection string |
| `SQLITE_DB_PATH` | Path to the app's own SQLite database file (default `app_data.db`) |
| `SUPERADMIN_USERNAME` / `SUPERADMIN_PASSWORD` | Bootstrap superadmin credentials, seeded on first startup — also rejected if left as an obvious placeholder |
| `ALLOWED_ORIGINS` | CORS allow-list for the frontend's origin |
| `LOGIN_RATE_LIMIT_PER_MINUTE` | Stricter rate limit specifically on auth endpoints |

## Windows-Specific Notes

Two platform-specific issues were identified and permanently fixed during development, both centralized so they don't need to be remembered per-script:

- **`psycopg`'s async mode requires a Selector event loop**, incompatible with Windows' default Proactor loop. Fixed once, centrally, in `app/database/connection.py` (`asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())`) — applies automatically to anything that imports the database connection module.
- **SSH tunnel target must be `127.0.0.1`, never `localhost`.** Windows can resolve `localhost` to the IPv6 loopback (`::1`), which doesn't match the tunnel's IPv4 binding, causing silent connection failures. Always tunnel to `127.0.0.1:5432`, and set `DATABASE_URL` to `127.0.0.1:5433` accordingly.

## Development Philosophy

This backend was built incrementally, one domain at a time, with each layer (schema → repository → service → API route) sanity-checked and live-HTTP-tested before moving to the next — never batching multiple untested layers together. Real bugs were found and fixed this way rather than papered over, including:

- A double-counting bug in engagement tracking (RudderStack's `page_engaged` event fires once per milestone crossed, not once per visit — fixed via `COUNT(DISTINCT ...)` visit deduplication).
- A cross-session timestamp-pairing bug in form field fill-time calculations (pairing events across unrelated sessions produced nonsensical multi-hour "fill times" — fixed by scoping the pairing to a single session).
- A route-ordering bug class avoided proactively: literal paths (e.g. `/journey/visitors`) are always registered before parameterized paths (e.g. `/journey/{anonymous_id}`) in the same router, since FastAPI matches routes in registration order.

The mock e-commerce data layer the project was originally scaffolded against (Phases 1–11) has been fully removed — every domain described in this document is built against real RudderStack data or the app's own real SQLite-backed accounts, with no remaining placeholder/mock logic anywhere in the codebase.

## Known Limitations & Roadmap

**Explicitly out of scope, by deliberate decision, not oversight:**
- Traffic Source Attribution — RudderStack's campaign-context columns are unpopulated in the current data; not worth building against effectively-empty fields.
- Behavioral Lead Scoring — too few real conversions exist yet to calibrate a scoring model meaningfully.
- A multi-tier role system beyond superadmin/member — deferred until a concrete need arises.

**Real, planned next work:**
- [ ] Date-range filtering across the remaining analytics domains (Journey's detail view is a deliberate, permanent exception — sort order only)
- [ ] Cross-domain metrics (conversion by device/platform, new-vs-returning visitor conversion rate, navigation paths among converters specifically)
- [ ] Time-series trend views (daily-bucketed traffic/engagement/conversion, rather than single aggregate totals)
- [ ] `GET /admin/users` consumers in the frontend (list view exists; UI not yet built)
- [ ] Automated test suite (a `tests/` directory exists but is not yet populated — all verification to date has been manual sanity checks plus live HTTP testing)

## License

MIT License

Copyright (c) 2026 Aditya Karmakar

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.