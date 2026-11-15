# Football Internal API

Internal FastAPI service that exposes football reference data (starting with **countries**) over HTTP. It is built as an async, layered application with production-oriented configuration, structured logging, request correlation IDs, and a unified error response contract.

This README is the **entry point**: what the app is, how to run it, and where to find deeper documentation. For a full production walkthrough (request lifecycle, logging, exceptions, database, deployment), see:

| Document | Purpose |
|----------|---------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | How the application is structured and how a request flows through every layer |
| [docs/OPERATIONS.md](docs/OPERATIONS.md) | Environments, logging, errors, health checks, and production runbook |

---

## What this service does

- Serves read APIs for football **countries** (list, by id, by name/codes/confederation, bulk by ids).
- Talks to **MySQL** asynchronously via SQLAlchemy + `aiomysql`.
- Loads configuration from env files selected by `CONFIG_ENV` (`local` / `dev` / `prod`).
- Optionally loads DB credentials from **HashiCorp Vault** when `vault` is configured in settings.
- Emits **JSON logs in production** and human-readable logs otherwise.
- Attaches / echoes **`X-Request-ID`** on every request for distributed tracing and log correlation.
- Maps domain exceptions to a stable JSON error body (`code`, `message`, `details`, `request_id`).

---

## Tech stack

| Layer | Technology |
|-------|------------|
| API | FastAPI + Uvicorn |
| Validation / settings | Pydantic v2 + pydantic-settings |
| ORM / DB | SQLAlchemy 2.x async, MySQL (`mysql+aiomysql`) |
| Secrets (optional) | HashiCorp Vault (`hvac`) |
| Logging | stdlib `logging` + `dictConfig` (JSON in prod) |

---

## Project layout

```
football_api/
├── .env                 # selects environment (CONFIG_ENV=local|dev|prod)
├── .env.local           # local machine settings
├── .env.dev             # shared/dev settings
├── .env.prod            # production settings
├── requirements.txt     # Python dependencies (keep filled for deploys)
├── README.md
├── docs/
│   ├── ARCHITECTURE.md
│   └── OPERATIONS.md
└── src/
    ├── main.py                      # FastAPI app, lifespan, middleware, handlers
    ├── api/v1/routers/              # HTTP routes (thin)
    ├── services/                    # business rules; raises domain errors
    ├── repositories/                # SQLAlchemy data access
    ├── models/                      # ORM entities
    ├── schemas/                     # request/response DTOs + ErrorResponse
    ├── database/                    # engine, sessions, FastAPI DB dependency
    ├── configs/                     # settings, env loader, logging, Vault client
    ├── core/                        # domain exceptions + exception handlers
    └── middleware/                  # request ID + access logging
```

**Layering rule:** routers call services → services call repositories → repositories use the DB session. HTTP details (`status_code`, JSON shape) live in **handlers**, not in services.

---

## Quick start (local)

### 1. Prerequisites

- Python 3.11+ recommended
- MySQL reachable with a schema that contains `football_predictions.countries`
- A virtualenv (example path used in this repo: project-root `env/`)

### 2. Configure environment

Root selector (already typical):

```env
# .env
CONFIG_ENV=local
```

Then fill `.env.local` (see [docs/OPERATIONS.md](docs/OPERATIONS.md) for every variable):

```env
CONFIG_ENV=local
APP_NAME=football-internal-api
VERSION=1.0.0
DB_HOST=localhost
DB_PORT=3306
DB_USER=football
DB_PASSWORD=...
DB_NAME=local
LOG_LEVEL=DEBUG
DEBUG=true
```

How loading works:

1. `configs/env_loader.py` reads `.env` and takes `CONFIG_ENV`.
2. It resolves `.env.{CONFIG_ENV}` (e.g. `.env.local`).
3. `Settings` in `configs/config.py` loads that file via pydantic-settings.

### 3. Install dependencies

From `football_api/` (once `requirements.txt` is populated):

```bash
pip install -r requirements.txt
```

### 4. Run the API

```bash
cd football_api/src
python main.py
```

Or with Uvicorn explicitly:

```bash
cd football_api/src
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

- Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- Interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- OpenAPI JSON: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## HTTP API (current)

Base path for countries: `/countries`  
(Health is at `/health`, outside the resource router.)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness: `{"status":"ok"}` |
| `GET` | `/countries/` | Paginated list (`skip`, `limit`) |
| `GET` | `/countries/{country_id}` | Single country by id |
| `GET` | `/countries/bulk?ids=1&ids=2` | Many countries by ids |
| `GET` | `/countries/by-name?names=England` | Filter by `name` |
| `GET` | `/countries/by-code2?codes=EN` | Filter by `code_alpha2` |
| `GET` | `/countries/by-code3?codes=ENG` | Filter by `code_alpha3` |
| `GET` | `/countries/by-confederation?confederations=UEFA` | Filter by confederation |

**Success response shape** (example `CountriesRead`):

```json
{
  "id": 1,
  "name": "England",
  "code_alpha2": "EN",
  "code_alpha3": "ENG",
  "confederation": "UEFA",
  "flag_url": null,
  "created_at": "...",
  "updated_at": "..."
}
```

**Error response shape** (all handled failures):

```json
{
  "code": "not_found",
  "message": "Countries not found.",
  "details": null,
  "request_id": "a1b2c3d4-...."
}
```

| HTTP | `code` | When |
|------|--------|------|
| 404 | `not_found` | Domain `NotFoundError` (e.g. missing country) |
| 422 | `validation_error` | Bad query/body (Pydantic) |
| 4xx/5xx | `http_error` | Starlette/FastAPI `HTTPException` |
| 500 | `internal_error` | Unhandled exception (message sanitized when `DEBUG=false`) |

Every response includes header **`X-Request-ID`**. Clients may send their own; otherwise the server generates a UUID.

---

## How a request works (short version)

```
Client
  → RequestContextMiddleware   (assign/echo X-Request-ID, access log, timing)
  → Router (api/v1/routers)
  → Depends(get_db_session)    (async session from app.state.database)
  → Service                    (business rules; may raise NotFoundError / AppError)
  → Repository                 (SQLAlchemy queries)
  → MySQL
  ← Pydantic response_model
  ← OR exception handler → ErrorResponse JSON
```

On startup (`lifespan` in `main.py`), the app builds a `Database` engine and stores it on `app.state.database`. On shutdown it disposes the engine.

Full narrative: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Configuration highlights

| Variable | Role |
|----------|------|
| `CONFIG_ENV` | Which env file to load: `local`, `dev`, `prod` |
| `APP_NAME` / `VERSION` | OpenAPI title/version |
| `LOG_LEVEL` | Root/handler level (`DEBUG`, `INFO`, …) |
| `DEBUG` | If `true`, 500 responses may include exception text; **must be `false` in prod** |
| `DB_*` | MySQL connection parameters |
| `vault` (settings) | Optional Vault block for credential injection |

In **prod** (`CONFIG_ENV=prod`), logs are **one JSON object per line** on stdout for CloudWatch / ELK / Loki collectors. Elsewhere logs are plain text with `[req=<request_id>]`.

---

## Production checklist (summary)

Before deploying:

1. Set `CONFIG_ENV=prod`, `DEBUG=false`, `LOG_LEVEL=INFO` (or higher).
2. Provide real `DB_*` (or Vault) secrets via the platform — do not commit secrets.
3. Run under a process manager (e.g. `uvicorn main:app --host 0.0.0.0 --port 8000 --workers N`) **without** `--reload`.
4. Scrape `/health` for liveness; ship stdout logs to your aggregator.
5. Confirm clients propagate or accept `X-Request-ID`.

Details and runbook: [docs/OPERATIONS.md](docs/OPERATIONS.md).

---

## Development conventions

- **Do not** raise `HTTPException` from services. Raise `AppError` subclasses from `core/exceptions.py`; handlers in `core/exception_handlers.py` map them to HTTP.
- Keep routers thin: parse input, call service, return DTOs.
- Put SQL only in repositories.
- Never log passwords, tokens, or full Vault payloads.

---

## License / ownership

Internal service — not intended as a public API unless explicitly exposed behind your gateway and auth layer.
