# Football Internal API

A high-performance, asynchronous RESTful API service built with **FastAPI**, **SQLAlchemy 2.0 (async)**, and **Pydantic v2** designed to power football analytics, internal tooling, and match prediction pipelines.

The service provides a centralized data-access layer for core football reference data—including **Countries**, **Competitions**, **Seasons**, **Venues**, **Teams**, **Season-Team Rosters**, and **Players**—backed by a relational **MySQL 8.0+** engine.

---

## Key Features & Architecture (2026 Standards)

- **Strict Layered Separation**:
  - `Routers` (`api/v1/routers/`): Thin HTTP endpoints handling serialization, rate limiting, and parameter parsing.
  - `Services` (`services/`): Business logic, multi-entity orchestration, and domain errors.
  - `Repositories` (`repositories/`): Data access with type-safe SQLAlchemy queries and dynamic query builders.
  - `Models` (`models/`): Modern SQLAlchemy 2.0 declarative models (`Mapped[...]`) with explicit relationship cascades and foreign keys.
  - `Schemas` (`schemas/`): Pydantic v2 DTOs with input validation, output filtering, and unified pagination envelopes.
- **Enterprise Security & Auth**:
  - Centralized `/api/v1` route grouping secured by constant-time `X-API-Key` authentication (`secrets.compare_digest`).
  - CORS middleware with configurable origin whitelists.
  - Security headers middleware (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, etc.).
  - Trusted host enforcement via `TrustedHostMiddleware`.
- **API Defense & Performance**:
  - **Rate Limiting**: Distributed/in-memory token bucket rate limiting via SlowAPI (`SlowAPIASGIMiddleware`), with automatic 429 JSON responses and `@limiter.exempt` probes.
  - **GZip Compression**: Automatic response payload compression for responses exceeding 1 KB.
  - **Dynamic Connection Pooling**: Configurable database pool (`DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_RECYCLE`, `DB_POOL_TIMEOUT`).
  - **Vault Secrets Integration**: Optional dynamic credential lookup via HashiCorp Vault (`hvac`).
- **Cloud-Native Observability**:
  - **Distributed Request Correlation**: Automatic `X-Request-ID` generation, context-var injection, and response echo.
  - **Structured Logging**: Unified JSON logs in production (`structlog` / stdlib) and formatted human-readable output in local/dev.
  - **Dual-Probe Health Monitoring**:
    - `GET /health/live`: Fast liveness probe that verifies process health without touching the database.
    - `GET /health/ready`: Readiness probe verifying real-time database connectivity (`SELECT 1`).
    - `GET /health`: Backward-compatible alias.
- **Resilient Error Architecture**:
  - Automatic database constraint mapping (`handle_integrity_error` converts MySQL 1062 duplicate keys and 1451/1452 foreign key errors into clean `409 ConflictError`).
  - Standardized JSON error response contract (`code`, `message`, `details`, `request_id`).

---

## Tech Stack

| Component | Technology |
|---|---|
| **Framework** | FastAPI 0.115+ / Starlette |
| **Server** | Uvicorn (ASGI) |
| **Database & ORM** | MySQL 8.0+, SQLAlchemy 2.0+ (async), `aiomysql` |
| **Validation & DTOs** | Pydantic v2 & `pydantic-settings` |
| **Secrets Management** | HashiCorp Vault (`hvac`) / `.env` environment cascades |
| **Rate Limiter** | SlowAPI (Token bucket) |
| **Logging** | Structlog + Python stdlib logging (`dictConfig`) |

---

## Project Structure

```
football_api/
├── .env                         # Environment selector (CONFIG_ENV=local|dev|prod)
├── .env.example                 # Environment configuration template
├── .env.local                   # Local machine secrets (git-ignored)
├── requirements.txt             # Locked Python dependencies
├── README.md                    # Service documentation & API guide
└── src/
    ├── main.py                  # ASGI app initialization, lifespan, middleware stack
    ├── api/
    │   └── v1/
    │       ├── __init__.py      # Versioned /api/v1 router with global security
    │       └── routers/         # Resource routers
    │           ├── countries.py
    │           ├── competitions.py
    │           ├── seasons.py
    │           ├── venues.py
    │           ├── teams.py
    │           ├── season_teams.py
    │           └── players.py
    ├── services/                # Business logic and integrity error handling
    ├── repositories/            # SQLAlchemy generic BaseRepository & specialized queries
    ├── models/                  # SQLAlchemy mapped entities & relationships
    ├── schemas/                 # Pydantic models (DTOs, FilterItem, PageResponse, etc.)
    ├── database/                # Engine lifecycle, sessionmaker, dependencies
    ├── configs/                 # Pydantic Settings, constants, Vault client, logging
    ├── core/                    # Domain exceptions, DB error handlers, API security
    └── middleware/              # Request logging, rate limiting, security headers
```

---

## Domain Entities & Endpoints

All business resources are versioned under `/api/v1` and protected with the `X-API-Key` header:

### 1. Countries (`/api/v1/countries`)
- `POST /` — Create country.
- `GET /` — Paginated list (`PageResponse[CountriesRead]`).
- `GET /by-name` — Look up by country name.
- `GET /by-code2` & `GET /by-code3` — Look up by ISO alpha-2 or alpha-3 codes.
- `GET /by-confederation` — Filter by continental confederation (UEFA, CONMEBOL, etc.).
- `GET /bulk` — Retrieve multiple countries by IDs.
- `GET /{country_id}` — Single country lookup.
- `POST /search` — Multi-operator dynamic filtering (`eq`, `in`, `like`, `gt`, `lt`, etc.).
- `PATCH /{country_id}` — Partial updates.
- `DELETE /{country_id}` — Deletion.

### 2. Competitions (`/api/v1/competitions`)
- `POST /` — Create competition.
- `GET /` — Paginated list (`PageResponse[CompetitionsRead]`).
- `GET /by-name` & `GET /by-code` — Query by competition name or acronym (e.g., `EPL`, `UCL`).
- `GET /by-type` — Filter by competition format (`domestic_league`, `domestic_cup`, `continental_cup`, `international`).
- `GET /by-country` — Enriched results returning competition with its associated `country_name`.
- `GET /{competition_id}` & `POST /search` & `PATCH` & `DELETE`.

### 3. Seasons (`/api/v1/seasons`)
- `POST /` — Create season record with unique `(competition_id, name)` constraint.
- `GET /` — Paginated list (`PageResponse[SeasonsRead]`).
- `GET /by-name` — Lookup by season name (e.g., `2024/2025`).
- `GET /by-country` — Enriched results returning `(Seasons, competition_name, country_name)`.
- `GET /{season_id}` & `POST /search` & `PATCH` & `DELETE`.

### 4. Venues / Stadiums (`/api/v1/venues`)
- `POST /` — Create venue with pitch dimensions, surface type, and geo-coordinates.
- `GET /` — Paginated list (`PageResponse[VenuesRead]`).
- `GET /by-name` & `GET /by-city` — Filter by stadium name or city.
- `GET /by-country` — Enriched lookup returning venue with country name.
- `GET /{venue_id}` & `POST /search` & `PATCH` & `DELETE`.

### 5. Teams (`/api/v1/teams`)
- `POST /` — Create team with country and home venue links.
- `GET /` — Paginated list (`PageResponse[TeamsRead]`).
- `GET /by-name` & `GET /by-code` — Filter by team name or code (e.g. `ARS`, `MCI`).
- `GET /by-country` & `GET /by-venue` — Lookups enriched with parent relation details.
- `GET /{team_id}` & `POST /search` & `PATCH` & `DELETE`.

### 6. Season Teams / Rosters (`/api/v1/season-teams`)
- `POST /` — Register a team into a competition season.
- `GET /` — Paginated roster list.
- `GET /by-team` — Enriched retrieval returning season names and team names.
- `GET /{season_team_id}` & `DELETE /{season_team_id}`.

### 7. Players (`/api/v1/players`)
- `POST /` — Create player with detailed positions, preferred foot, and market values. **Supports specifying nationality either by `nationality_country_id` or by human-readable `country_name`**.
- `GET /` — Paginated list (`PageResponse[PlayersRead]`).
- `GET /by-name` — Query by common name (e.g. `Rodri`, `Saka`).
- `GET /by-country` — Filter players by nationality name.
- `GET /{player_id}` & `POST /search` & `PATCH` & `DELETE`.

---

## Standardized Responses

### 1. Paginated Envelope (`PageResponse[T]`)
Used by all listing and dynamic search endpoints:
```json
{
  "items": [
    {
      "id": 1,
      "name": "England",
      "code_alpha2": "EN",
      "code_alpha3": "ENG",
      "confederation": "UEFA",
      "flag_url": null,
      "created_at": "2026-10-18T09:30:00"
    }
  ],
  "total": 54,
  "skip": 0,
  "limit": 1
}
```

### 2. Error Response Contract (`ErrorResponse`)
Returned consistently for all 4xx and 5xx exceptions:
```json
{
  "code": "conflict",
  "message": "Country already exists with this code_alpha2.",
  "details": {
    "duplicate_key": "code_alpha2",
    "value": "EN"
  },
  "request_id": "4a18d184-b258-45e3-9990-23a57960fc03"
}
```

---

## Local Setup & Quickstart

### 1. Prerequisites
- Python 3.11+ (Python 3.12 recommended)
- MySQL 8.0+ running with the `football_predictions` schema loaded

### 2. Configure Environment
Create `.env.local` using `.env.example` as a reference:
```bash
cp .env.example .env.local
```

Ensure `.env` selects local mode:
```env
CONFIG_ENV=local
```

Key variables in `.env.local`:
```env
CONFIG_ENV=local
APP_NAME=football-internal-api
VERSION=1.0.0
API_KEY=your-secret-internal-key-here

DB_HOST=localhost
DB_PORT=3306
DB_USER=football
DB_PASSWORD=YourStrongPasswordHere!
DB_NAME=football_predictions
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=1800

LOG_LEVEL=DEBUG
DEBUG=true
```

### 3. Install Dependencies
```bash
source /path/to/virtualenv/bin/activate
pip install -r requirements.txt
```

### 4. Run the Service
From `football_api/src`:
```bash
python main.py
```
Or via Uvicorn directly:
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

---

## API Documentation & Testing

- **Interactive Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
  - Click **Authorize 🔓** in the top-right corner.
  - Enter your `API_KEY` (e.g. `your-secret-internal-key-here`) and click **Authorize**.
  - All subsequent "Try it out" requests will automatically include the required `X-API-Key` header.
- **Alternative ReDoc UI**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Raw OpenAPI Schema**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)
- **Liveness Probe**: [http://127.0.0.1:8000/health/live](http://127.0.0.1:8000/health/live)
- **Readiness Probe**: [http://127.0.0.1:8000/health/ready](http://127.0.0.1:8000/health/ready)

*(Note: In production environments where `CONFIG_ENV=prod`, docs endpoints are automatically disabled for security.)*
