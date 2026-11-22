# Architecture

This document describes the current request path, data flow, authentication,
database boundaries, middleware, and extension points for the Football Internal API.

## Component overview

```text
Client
  |
  | HTTP / Bearer JWT / X-Request-ID
  v
FastAPI application (src/main.py)
  |-- security headers
  |-- GZip
  |-- SlowAPI rate limiting
  |-- CORS
  |-- trusted hosts
  `-- request logging
       |
       v
api/v1 routers
       |-- JWT + permission dependencies
       |-- Pydantic input/output schemas
       v
services
       v
repositories
       v
SQLAlchemy async sessions
       |-- football_predictions database
       `-- access_control privilege database
```

The process has two engines:

- `Database` accesses football reference data.
- `PrivilegeDatabase` accesses employees, roles, permissions, and active
  privilege records.

## Application startup

`src/main.py`:

1. Loads settings through `get_settings()`.
2. Configures structlog based on the selected environment.
3. Creates the main FastAPI app.
4. Creates `Database` and `PrivilegeDatabase` during lifespan startup.
5. Registers middleware and exception handlers.
6. Includes the versioned router aggregate, which mounts resource routers.

On shutdown, both SQLAlchemy engines are disposed.

## Request lifecycle

### 1. Middleware

The request logging middleware:

- accepts `X-Request-ID` or generates a UUID;
- binds request ID, method, path, client IP, and later username to structlog;
- echoes the request ID in the response;
- logs completion or exception details; and
- excludes `/health`, `/health/live`, and `/health/ready` from access logs.

SlowAPI limits requests by remote address. The default is
`RATE_LIMIT_DEFAULT`, and resource routes use a `10/minute` decorator where
configured. Health endpoints are exempt.

### 2. Authentication

`POST /auth/login` accepts a username, looks up the employee in the privilege
database, and resolves active roles. The username and comma-separated primary
roles are encoded into an HS256 JWT with a two-hour default lifetime.

`core.auth.get_token_data` reads `Authorization: Bearer ...` and validates the
JWT signature and expiry.

The privilege database then resolves permission codes for the role:

```text
role_code -> role -> role_permissions -> permission_code
```

Routes call `require_permissions(["data:read"])` or
`require_permissions(["data:write"])`. Missing permissions produce a 403 and
an authorization-denied structured log entry.

This is an internal service boundary, not a password-authentication system:
the current login implementation locates an employee but does not hash or
verify a password.

### 3. Router

Routers own FastAPI HTTP concerns:

- route prefixes and tags;
- request and response models;
- permission dependencies;
- rate-limit decorators;
- dependency construction; and
- query/path parameter definitions.

Business SQL and domain rules belong in services and repositories rather than
directly in route functions.

### 4. Service

Services apply domain behavior and convert repository misses or constraint
failures into domain exceptions.

### 5. Repository

Repositories execute SQLAlchemy `select`, insert, update, and delete operations
through async sessions. The base repository provides pagination and dynamic
filter helpers used by specialized repositories.

### 6. Session

Each request receives an async session through its FastAPI dependency. Session
dependencies roll back on raised exceptions. Explicit repository commits are
used for writes.

## Database design

### Football database

The main engine is built from `DB_*` settings and can optionally load
credentials from HashiCorp Vault. It targets MySQL through `mysql+aiomysql`.

Core entities include:

- countries
- competitions
- seasons
- venues
- teams
- season-team registrations
- players

### Privilege database

The privilege engine is built from `PRV_*` settings. It is isolated from the
football database and stores:

- employees;
- roles;
- permissions;
- role-permission assignments;
- employee-role privileges;
- audit records.

## Health checks

| Endpoint | Behavior |
|---|---|
| `/health/live` | returns process OK without database access |
| `/health/ready` | executes `SELECT 1` against the main database |
| `/health` | compatibility alias for readiness |

The readiness endpoints return 503 with `{"status":"degraded","db":false}`
when the main database is unavailable.

## Error handling

Domain exceptions are mapped centrally to HTTP responses:

| Exception | Typical status | Code |
|---|---:|---|
| `NotFoundError` | 404 | `not_found` |
| `ConflictError` | 409 | `conflict` |
| `UnauthorizedError` | 401 | `unauthorized` |
| `ForbiddenError` | 403 | `forbidden` |

FastAPI validation errors, HTTP exceptions, rate-limit exceptions, and
unhandled exceptions are also converted to JSON by registered handlers.

## Security middleware

The application adds:

- CORS with `ALLOWED_ORIGINS`;
- trusted-host validation with `TRUSTED_HOSTS`;
- GZip for responses of at least 1000 bytes;
- security headers; and
- SlowAPI middleware.

Swagger, ReDoc, and OpenAPI are enabled outside `prod` and disabled by
`docs_enabled` in production.

## Configuration

Settings are loaded from the environment and the file selected by `CONFIG_ENV`.
Important groups are:

- application: `APP_NAME`, `VERSION`, `LOG_LEVEL`, `DEBUG`;
- JWT: `JWT_SECRET`;
- football database: `DB_*`;
- privilege database: `PRV_*`;
- HTTP: `ALLOWED_ORIGINS`, `TRUSTED_HOSTS`;
- rate limiting: `RATE_LIMIT_DEFAULT`, `RATE_LIMIT_STORAGE_URI`;
- pool: `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_RECYCLE`,
  `DB_POOL_TIMEOUT`, `DB_CONNECT_TIMEOUT`;
- optional `vault` settings supplied by settings configuration.

## Adding a resource

1. Create the SQLAlchemy model in `src/models/`.
2. Create Pydantic create/update/read/filter DTOs in `src/schemas/`.
3. Add a repository in `src/repositories/`.
4. Add service rules in `src/services/`.
5. Add thin routes in `src/api/v1/routers/`.
6. Attach `data:read` or `data:write` permission dependencies.
7. Include the router from `src/api/v1/__init__.py`.
8. Update README and operation documentation.

For public API versioning, mount this router aggregate under a prefix such as
`/api/v1`; the current router prefixes are resource-relative and have no
global `/api/v1` prefix.
