# Custom Analytics Backend

A production-oriented FastAPI backend that powers a custom analytics dashboard, sitting between a PostgreSQL analytics warehouse and a Next.js frontend.

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-336791)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](#license)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Goals](#project-goals)
- [Authentication](#authentication)
- [Request Lifecycle](#request-lifecycle)
- [Project Structure](#project-structure)
- [API Design Philosophy](#api-design-philosophy)
- [Error Handling](#error-handling)
- [Getting Started](#getting-started)
- [Development Philosophy](#development-philosophy)
- [Roadmap](#roadmap)
- [License](#license)

---

## Overview

This service exposes authenticated REST APIs that deliver analytics data to a modern JavaScript frontend. The frontend never talks to the database directly — every dashboard component is backed by a dedicated API endpoint.

Event data originates from user interactions on a website, is collected by **RudderStack**, and is transformed into structured tables inside **PostgreSQL**. This backend's only data source is PostgreSQL; it never queries RudderStack directly, and RudderStack's only responsibility is ingestion.

The system is built in independent, replaceable layers — API routing, business logic, data access, authentication, and configuration — so each layer can evolve without breaking the others.

## Architecture

```
┌─────────┐     ┌─────────────┐     ┌──────────────┐     ┌──────────────────┐     ┌────────────────┐
│ Website │ ──▶ │ RudderStack │ ──▶ │  PostgreSQL  │ ──▶ │  FastAPI Backend  │ ──▶ │ Next.js Frontend│
└─────────┘     └─────────────┘     └──────────────┘     └──────────────────┘     └────────────────┘
```

**Boundaries are strict:**
- The frontend communicates only with FastAPI.
- FastAPI communicates only with PostgreSQL.
- RudderStack only writes events into PostgreSQL and is never queried directly.

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12+ |
| Framework | FastAPI |
| ASGI Server | Uvicorn |
| Database | PostgreSQL |
| DB Driver | psycopg (v3) |
| Auth | JSON Web Tokens (JWT) |
| Password Hashing | bcrypt (via Passlib) |
| Config Management | python-dotenv |
| Validation | Pydantic |
| Frontend | Next.js |
| Event Collection | RudderStack |
| API Style | REST, JSON |

## Project Goals

Rather than exposing raw database tables, every endpoint answers a specific business question. Each frontend visualization maps to one or more purpose-built endpoints, including:

- Dashboard summary
- Daily active users
- Revenue over time
- Retention analysis
- Conversion funnel
- Top products
- Top countries
- User journey
- Recent orders
- User analytics

## Authentication

All endpoints are protected via JWT, with a single public exception: the login endpoint.

**Flow:**

1. The client submits credentials to `/login`.
2. The backend validates the credentials.
3. On success, the backend issues a signed JWT.
4. The frontend stores the token and attaches it to every subsequent request:
   ```
   Authorization: Bearer <jwt_token>
   ```
5. FastAPI validates the token before executing any protected route's business logic.
6. An invalid or expired token short-circuits the request with `401 Unauthorized`.

## Request Lifecycle

Every request flows through the same set of layers in both directions:

```
Client
  → API Layer
    → Service Layer
      → Repository Layer
        → Database Connection
          → PostgreSQL
        ← Database Connection
      ← Repository Layer
    ← Service Layer
  ← API Layer
← JSON Response → Client
```

Each layer has exactly one responsibility, which keeps failures isolated and logic easy to trace.

## Project Structure

| Layer | Responsibility |
|---|---|
| **API** | Receives HTTP requests, returns HTTP responses |
| **Service** | Business logic and application-specific computation |
| **Repository** | SQL queries and database interaction |
| **Database** | Creates and manages PostgreSQL connections |
| **Auth** | Validates users and JWT tokens |
| **Schema** | Pydantic request/response models |
| **Core** | Shared configuration, constants, security settings |
| **Utils** | Reusable helper functions |

```
app/
├── api/            # Route definitions
├── services/       # Business logic
├── repositories/   # SQL / data access
├── db/             # Connection management
├── auth/           # JWT & user validation
├── schemas/        # Pydantic models
├── core/           # Config, constants, security
└── utils/          # Shared helpers
```

## API Design Philosophy

Endpoints are designed around business functionality, not database tables — the frontend requests a *dashboard summary*, not raw rows from underlying tables. Each endpoint returns exactly what its corresponding visualization needs, which:

- Minimizes payload size and unnecessary data transfer
- Simplifies frontend integration
- Hides internal schema and implementation details from consumers

## Error Handling

All errors are returned as JSON with a standard HTTP status code:

| Code | Meaning |
|---|---|
| `200 OK` | Successful request |
| `201 Created` | Resource successfully created |
| `400 Bad Request` | Invalid request parameters |
| `401 Unauthorized` | Authentication failed or token missing |
| `403 Forbidden` | Authenticated user lacks permission |
| `404 Not Found` | Requested resource does not exist |
| `422 Unprocessable Entity` | Validation failed |
| `500 Internal Server Error` | Unexpected server-side error |

## Getting Started

> Fill in project-specific commands as they're finalized — placeholders below follow the stack described above.

```bash
# Clone and enter the project
git clone <repo-url>
cd custom-analytics-backend

# Create and activate a virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Run the development server
uvicorn app.main:app --reload
```

## Development Philosophy

This backend is being built from first principles: each layer is implemented and understood individually before further abstraction is introduced. The API, service, authentication, and schema layers are designed to be completable **before** a live PostgreSQL database is connected — repositories may temporarily return mock or placeholder data during this phase.

Once real database credentials are available, only the repository layer requires modification; the rest of the application is unaffected.

## Roadmap

Planned enhancements that fit within the existing layered architecture without structural changes:

- [ ] Role-based authorization
- [ ] Redis caching
- [ ] Background jobs
- [ ] Asynchronous query execution
- [ ] Rate limiting
- [ ] API versioning
- [ ] Logging & monitoring
- [ ] Metrics collection
- [ ] OpenAPI customization
- [ ] Automated testing

## License

Specify a license (e.g., MIT) here.
