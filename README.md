# Football Internal API

An asynchronous FastAPI service for football reference data, including countries,
competitions, seasons, venues, teams, season-team registrations, and players.
It uses SQLAlchemy 2 async sessions with MySQL and a separate privilege database
for authentication and authorization.

## Features

- FastAPI + Pydantic v2 + SQLAlchemy 2 async
- Separate MySQL data and access-control databases
- JWT bearer authentication and role-based data permissions
- Per-resource `data:read` and `data:write` permission checks
- SlowAPI rate limiting
- Structured request/authorization logging
- `X-Request-ID` propagation
- Liveness and database-ready health probes
- CORS, trusted-host, GZip, and security-header middleware
- JSON logs outside local development
- Optional Vault credential loading for the football database

## Runtime layout

```text
src/
  main.py                  # ASGI application and middleware stack
  api/v1/                   # API route modules
  services/                 # Business logic
  repositories/             # SQLAlchemy data access
  models/                   # Football data models
  models_priv/              # Access-control models
  repositories_priv/        # Access-control queries
  schemas/                  # Pydantic request/response models
  core/auth.py              # JWT and permission dependencies
  database/                 # Football database engine
  database_priv/            # Privilege database engine
  middleware/               # Request logging, rate limits, security headers
  configs/                  # Environment settings and logging
docs/
  ARCHITECTURE.md
  OPERATIONS.md
```

## Authentication

1. Log in with an employee username:

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"your_username"}'
```

2. Use the returned token as a bearer token:

```http
Authorization: Bearer <access_token>
X-Request-ID: optional-correlation-id
```

The login endpoint verifies that the employee exists and has an active role.
It does not verify a password: the current implementation is intended for an
internal/demo environment and should be hardened before external use.

Resource routes require one of these permissions:

| Operation | Permission |
|---|---|
| Reads | `data:read` |
| Creates, updates, deletes | `data:write` |

Roles and permission codes are resolved from the separate privilege database.

## API routes

Routers are currently mounted directly under their resource prefixes:

| Resource | Prefix | Main operations |
|---|---|---|
| Auth | `/auth` | `POST /auth/login` |
| Countries | `/countries` | Create, list, filter, search, update, delete |
| Competitions | `/competitions` | Create, list, filter, search, update, delete |
| Seasons | `/seasons` | Create, list, filter, search, update, delete |
| Venues | `/venues` | Create, list, filter, search, update, delete |
| Teams | `/teams` | Create, list, filter, search, update, delete |
| Season teams | `/season-teams` | Create, list, filter, update, delete |
| Players | `/players` | Create, list, filter, search, update, delete |

The generated Swagger UI lists each route, query parameter, and request schema.

Example authenticated requests:

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:8000/countries/?skip=0&limit=100"

curl -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -X POST http://127.0.0.1:8000/countries/ \
  -d '{"name":"England","code_alpha2":"EN","code_alpha3":"ENG","confederation":"UEFA"}'
```

## Health and documentation

| Endpoint | Purpose |
|---|---|
| `/health/live` | Process liveness; no database call |
| `/health/ready` | Football database readiness via `SELECT 1` |
| `/health` | Alias for `/health/ready` |
| `/docs` | Swagger UI, except in production |
| `/redoc` | ReDoc, except in production |
| `/openapi.json` | OpenAPI schema, except in production |

Health and documentation behavior are controlled by `CONFIG_ENV`.

## Configuration

Copy the environment template and replace placeholders:

```bash
cp .env.example .env.local
```

Set `.env` to select an environment file:

```env
CONFIG_ENV=local
```

Required settings include:

```env
APP_NAME=football-internal-api
VERSION=1.0.0
JWT_SECRET=change-this-secret

DB_HOST=localhost
DB_PORT=3306
DB_USER=football
DB_PASSWORD=change-this-password
DB_NAME=football_predictions

PRV_DB_HOST=localhost
PRV_DB_PORT=3306
PRV_DB_USER=access_reader
PRV_DB_PASSWORD=change-this-password
PRV_DB_NAME=access_control
```

Additional supported settings include:

```env
LOG_LEVEL=INFO
DEBUG=false
ALLOWED_ORIGINS=http://localhost:3000
TRUSTED_HOSTS=*
RATE_LIMIT_DEFAULT=200/minute
RATE_LIMIT_STORAGE_URI=memory://
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=1800
DB_POOL_TIMEOUT=30
DB_CONNECT_TIMEOUT=10
API_KEY=legacy-placeholder
API_KEY_NAME=X-API-Key
```

`ALLOWED_ORIGINS` and `TRUSTED_HOSTS` are parsed according to Pydantic settings
list parsing. In environment files, JSON-style lists such as
`["http://localhost:3000"]` are the safest portable form.

## Local setup

Prerequisites:

- Python 3.11+
- MySQL 8.0+ databases for football data and access control
- Required privilege tables/views for login and permission lookup

Install and run:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd src
python main.py
```

For direct Uvicorn startup:

```bash
cd src
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Responses

Most list endpoints return:

```json
{
  "items": [],
  "total": 0,
  "skip": 0,
  "limit": 100
}
```

Application and HTTP errors are converted to the project error contract:

```json
{
  "code": "not_found",
  "message": "Resource not found.",
  "details": null,
  "request_id": "uuid"
}
```

The request ID is accepted from `X-Request-ID`, generated when omitted, and
returned in both the response headers and structured logs.

## Further documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Operations](docs/OPERATIONS.md)
