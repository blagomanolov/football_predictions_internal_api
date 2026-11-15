# Architecture

This document explains **how the Football Internal API works end-to-end**: process bootstrap, request lifecycle, layered responsibilities, database sessions, configuration, and how cross-cutting concerns (logging, request IDs, exceptions) plug in.

Audience: developers and platform engineers who need to extend or operate the service safely.

---

## 1. Goals of this design

| Goal | How it is achieved |
|------|--------------------|
| Clear separation of concerns | Routers → services → repositories → models |
| Safe HTTP error contract | Domain exceptions + global handlers → `ErrorResponse` |
| Observable requests | `X-Request-ID` + access logs + structured logs in prod |
| Environment isolation | `.env` selector + `.env.{local\|dev\|prod}` |
| Async I/O | FastAPI + async SQLAlchemy + `aiomysql` |
| Optional secrets management | Vault client wired into `Database` when configured |

---

## 2. High-level component diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         main.py (ASGI app)                       │
│  • dictConfig(logging)                                           │
│  • lifespan → Database on app.state                               │
│  • RequestContextMiddleware                                      │
│  • register_exception_handlers()                                 │
│  • include_router(countries)                                     │
└───────────────┬─────────────────────────────┬───────────────────┘
                │                             │
                ▼                             ▼
     api/v1/routers/*                  middleware/request_context.py
     (HTTP only)                       (request_id, access log)
                │
                ▼
          services/*                   core/exceptions.py
          (rules; AppError)  ───────►  core/exception_handlers.py
                │                      schemas/errors.py
                ▼
       repositories/*                  database/dependencies.py
                │                      database/database.py
                ▼
            models/*  ──SQL──►  MySQL (schema football_predictions)
                │
                ▼
            schemas/*  (Pydantic DTOs for API I/O)
```

Configuration and logging live under `configs/` and are applied once at import/startup time in `main.py`.

---

## 3. Application bootstrap (`src/main.py`)

Startup order matters. The current sequence is:

### 3.1 Load settings

```text
get_settings()
  → env_loader.load_base_env()
      → read football_api/.env  (CONFIG_ENV)
      → return path to .env.{CONFIG_ENV}
  → pydantic Settings loads that file
```

`get_settings()` is `@lru_cache`’d so settings are a singleton for the process lifetime.

### 3.2 Configure logging

```text
build_logging_config(LOG_LEVEL, CONFIG_ENV)
  → dictConfig(...)
  → attach RequestIdFilter to handlers
```

- If `CONFIG_ENV=prod` → **JSON** lines via `JsonFormatter`.
- Otherwise → **plain text** with `req=%(request_id)s`.

### 3.3 Create FastAPI app with lifespan

On **startup**:

1. Instantiate `Database(**settings.model_dump())`.
2. Optionally pull credentials from Vault if `vault` is present.
3. Build async engine + session factory.
4. Store instance on `app.state.database`.

On **shutdown**:

1. `await database.engine.dispose()` — release connection pool cleanly.

### 3.4 Register cross-cutting behavior

1. `app.add_middleware(RequestContextMiddleware)`
2. `register_exception_handlers(app)`
3. Mount routes (`/health`, `/countries/...`)

Uvicorn then serves the ASGI `app` object.

---

## 4. Request lifecycle (detailed)

Take `GET /countries/42` as an example.

### Step A — Middleware (`middleware/request_context.py`)

1. Read `X-Request-ID` from the incoming request, or generate a UUID.
2. Store it in a `ContextVar` (`request_id_ctx`) so any code/logging in this request can see it.
3. Call the next ASGI layer (`call_next`).
4. On the way out:
   - Set response header `X-Request-ID`.
   - Log an **access line**: method, path, status, duration_ms (logger `app.access`).
5. If an exception escapes the route before a response exists, log with `logger.exception` and re-raise so exception handlers can still produce a JSON body.

`RequestIdFilter` copies `request_id_ctx` onto every `LogRecord` as `record.request_id`, so formatters can emit it without callers passing `extra=` everywhere.

### Step B — Router (`api/v1/routers/countries.py`)

The router is intentionally thin:

1. FastAPI parses path/query and validates types.
2. `Depends(get_service)` builds:
   - DB session via `get_db_session`
   - `CountriesRepository(session)`
   - `CountriesService(repo)`
3. Handler calls `await service.get(country_id)`.
4. Return value is validated/serialized as `CountriesRead` (`response_model`).

Routers should **not** contain SQL or business branching beyond HTTP wiring.

### Step C — Service (`services/countries.py`)

Business rules live here. Example:

```text
obj = await repository.get(id)
if not obj:
    raise NotFoundError("Countries not found.")
return CountriesRead.model_validate(obj)
```

Important production rule:

- Services raise **`AppError` subclasses** (`NotFoundError`, `ConflictError`, …).
- Services do **not** import FastAPI `HTTPException`.
- That keeps the domain testable and reusable outside HTTP.

### Step D — Repository (`repositories/`)

`BaseRepository` implements generic async queries (`get`, `get_many_by_ids`, `get_many_by_field`, `list`).  
`CountriesRepository` specializes the model (`Countries`).

Repositories:

- Own SQLAlchemy `select` / execute.
- Return ORM entities (or collections), not HTTP responses.
- Do not catch-and-swallow DB errors; let them bubble to handlers (session layer still rolls back).

### Step E — Database session (`database/`)

`get_db_session` (FastAPI dependency):

```text
request.app.state.database  →  database.get_session()  →  yield AsyncSession
```

Inside `Database.get_session()`:

- Opens a session from the pool.
- On exception: `rollback()`, logs with `logger.exception`, re-raises.
- Session is closed by the async context manager when the request finishes.

Engine settings (prod-relevant):

| Setting | Value | Why |
|---------|-------|-----|
| `pool_pre_ping` | `True` | Detect dead connections before use |
| `pool_size` | `10` | Baseline concurrent connections |
| `max_overflow` | `20` | Burst headroom |
| `pool_recycle` | `1800` | Avoid MySQL “wait_timeout” stale sockets |
| `echo` | `False` | Do not print SQL to logs by default |

ORM table: `football_predictions.countries` (`models/countries.py`).

### Step F — Success path

Pydantic serializes the DTO → JSON → client. Middleware access log records status (e.g. 200).

### Step G — Error path

If anything raises:

| Exception type | Handler | HTTP | `code` |
|----------------|---------|------|--------|
| `AppError` / subclasses | `app_error_handler` | `exc.status_code` | `exc.code` (e.g. `not_found`) |
| `RequestValidationError` | `validation_exception_handler` | 422 | `validation_error` |
| `HTTPException` / Starlette HTTP | `http_exception_handler` | given | `http_error` |
| Any other `Exception` | `unhandled_exception_handler` | 500 | `internal_error` |

All of them return the same schema (`schemas/errors.py`):

```json
{
  "code": "...",
  "message": "...",
  "details": null,
  "request_id": "..."
}
```

For unhandled errors:

- `DEBUG=true` → message may include exception text; `details` may include type name.
- `DEBUG=false` (required in production) → generic `"Internal server error"`; no stack in the body. Stack still goes to **logs** via `logger.exception`.

---

## 5. Domain exception model (`core/exceptions.py`)

```text
AppError (base)
├── NotFoundError      → 404 / not_found
├── ConflictError      → 409 / conflict
├── UnauthorizedError  → 401 / unauthorized
└── ForbiddenError     → 403 / forbidden
```

Each carries:

- `message` — human-readable
- `code` — machine-stable string for clients/alerts
- `status_code` — HTTP mapping (applied only in the handler)
- `details` — optional structured context (never put secrets here)

**How to add a new domain error**

1. Subclass `AppError` (or reuse an existing subclass).
2. Raise it from a service when the rule fails.
3. No router/handler change needed — `AppError` handler already covers subclasses.

---

## 6. Logging architecture (`configs/logging_config.py`)

### Formatters

| Env | Formatter | Output |
|-----|-----------|--------|
| `prod` | `JsonFormatter` | One JSON object per line on stdout |
| `local` / `dev` | `standard` | Text: `time [LEVEL] logger [req=...]: message` |

### JSON fields (production)

| Field | Meaning |
|-------|---------|
| `ts` | UTC ISO-8601 timestamp |
| `level` | `INFO`, `WARNING`, `ERROR`, … |
| `logger` | Logger name |
| `message` | Rendered message |
| `request_id` | Correlation id when present |
| `exc_info` | Formatted traceback when logging an exception |

### Loggers configured

| Logger | Role |
|--------|------|
| root (`""`) | Application default |
| `uvicorn.access` / `uvicorn.error` | Server access/error |
| `sqlalchemy.engine` | Forced to **WARNING** to avoid SQL floods in prod |
| `app.access` | Custom access log from middleware |

**Operational rule:** collect **stdout**. Do not write secrets. Prefer `logger.exception` only at boundaries where you need a traceback (handlers, DB session, middleware).

---

## 7. Configuration architecture

### Files

| File | Role |
|------|------|
| `.env` | Only (or mainly) `CONFIG_ENV=...` |
| `.env.local` | Developer machine |
| `.env.dev` | Shared non-prod |
| `.env.prod` | Production values / placeholders filled by deploy system |

### Settings object (`configs/config.py`)

Important fields:

- App: `config_env`, `app_name`, `version`, `log_level`, `debug`
- DB: `host`, `port`, `user`, `password`, `database`, `db_charset`
- Optional: `vault` dict for HashiCorp integration

Aliases map env vars (`DB_HOST`, `LOG_LEVEL`, …) onto Python attributes.

### Vault path (optional)

If `settings.vault` is set, `Database` prefers Vault over static password:

1. Build `VaultClient` from `vault.client_config`.
2. Either:
   - **catalogue** mode: read KV metadata → then dynamic/static creds path; update host/user/password, or
   - **creds_path** mode: read username/password from a path; update user/password.
3. Otherwise raise `RuntimeError` (unknown Vault strategy).

This runs at **startup**, not per request.

---

## 8. API versioning note

Source code lives under `api/v1/`, but routers are currently mounted at `/countries` (no `/api/v1` URL prefix yet). When you expose the service publicly or to many consumers, prefer:

```python
app.include_router(countries.router, prefix="/api/v1")
```

and keep future breaking changes under `/api/v2`.

---

## 9. Extending the application (checklist)

To add a new resource (example: `leagues`):

1. `models/leagues.py` — ORM table
2. `schemas/leagues.py` — Create/Update/Read DTOs
3. `repositories/leagues.py` — extend `BaseRepository` if needed
4. `services/leagues.py` — rules; raise `AppError` subtypes
5. `api/v1/routers/leagues.py` — thin routes + `Depends`
6. `main.py` — `app.include_router(leagues.router)`
7. Document endpoints in README / OpenAPI descriptions

Do **not** bypass the service layer from routers for “just a quick query” — that is how error contracts and logging diverge over time.

---

## 10. Known intentional boundaries (current codebase)

- Countries API is **read-oriented** (create/update schemas exist; write routes are not mounted yet).
- AuthN/AuthZ is not implemented in-app — place the service behind a gateway / mTLS / IAM as required.
- `requirements.txt` should be kept filled (`pip freeze` or a locked file) for reproducible deploys.
- Health check is a simple process liveness probe; it does **not** yet verify MySQL connectivity (add a separate `/ready` if you need readiness).

---

## Related documents

- [OPERATIONS.md](OPERATIONS.md) — env vars, runbook, logging/error ops, production checklist
- [../README.md](../README.md) — quick start and API table
