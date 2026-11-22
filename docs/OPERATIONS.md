# Operations runbook

Operational guidance for configuration, deployment, health checks, logging,
database connections, and troubleshooting.

For architecture and request flow, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Environments

| `CONFIG_ENV` | Env file | Typical use | JSON logs | Docs |
|---|---|---|---:|---:|
| `local` | `.env.local` | Developer machine | No | Enabled |
| `dev` | `.env.dev` | Shared environment | Yes | Enabled |
| `prod` | `.env.prod` | Production | Yes | Disabled |

`ENV_FILE` is selected from the top-level `.env` `CONFIG_ENV` value. Real
environment variables override values loaded from the selected env file.

## Configuration reference

| Variable | Required | Purpose |
|---|---:|---|
| `CONFIG_ENV` | Yes | `local`, `dev`, or `prod` |
| `APP_NAME` | Yes | OpenAPI title and application name |
| `VERSION` | No | OpenAPI/application version |
| `LOG_LEVEL` | No | Standard log level |
| `DEBUG` | No | Debug response detail; keep false in production |
| `JWT_SECRET` | Yes | HS256 signing and verification secret |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | Yes | Football database |
| `DB_CHARSET` | No | SQLAlchemy charset, default `utf8mb4` |
| `PRV_DB_HOST`, `PRV_DB_PORT`, `PRV_DB_USER`, `PRV_DB_PASSWORD`, `PRV_DB_NAME` | Yes | Privilege/access-control database |
| `ALLOWED_ORIGINS` | No | CORS origin allowlist |
| `TRUSTED_HOSTS` | No | Trusted host allowlist |
| `RATE_LIMIT_DEFAULT` | No | Default SlowAPI limit |
| `RATE_LIMIT_STORAGE_URI` | No | SlowAPI storage backend |
| `DB_POOL_SIZE`, `DB_MAX_OVERFLOW` | No | SQLAlchemy pool sizing |
| `DB_POOL_RECYCLE`, `DB_POOL_TIMEOUT`, `DB_CONNECT_TIMEOUT` | No | Pool and connection timeouts |
| `API_KEY`, `API_KEY_NAME` | No | Legacy configuration fields; resource auth currently uses JWT |

Example production baseline:

```env
CONFIG_ENV=prod
APP_NAME=football-internal-api
VERSION=1.0.0
LOG_LEVEL=INFO
DEBUG=false
JWT_SECRET=<platform-secret>

DB_HOST=<database-host>
DB_PORT=3306
DB_USER=<database-user>
DB_PASSWORD=<database-password>
DB_NAME=football_predictions

PRV_DB_HOST=<privilege-host>
PRV_DB_PORT=3306
PRV_DB_USER=<privilege-user>
PRV_DB_PASSWORD=<privilege-password>
PRV_DB_NAME=access_control

ALLOWED_ORIGINS=["https://internal.example"]
TRUSTED_HOSTS=["api.internal.example"]
RATE_LIMIT_DEFAULT=200/minute
RATE_LIMIT_STORAGE_URI=memory://
```

Never place real secrets in committed env files. Prefer platform environment
variables or Vault for the main database.

## Running

Development:

```bash
cd src
python main.py
```

Production-style Uvicorn:

```bash
cd src
uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 2 \
  --proxy-headers \
  --forwarded-allow-ips='*'
```

Do not enable reload or `DEBUG=true` in production. Size `--workers` together
with SQLAlchemy pool settings and MySQL `max_connections`; each process has
its own main and privilege database pool.

## Health probes

| Endpoint | Meaning | Recommended probe |
|---|---|---|
| `/health/live` | Process is serving HTTP | Kubernetes liveness |
| `/health/ready` | Main football database answered `SELECT 1` | Kubernetes readiness |
| `/health` | Backward-compatible readiness alias | Legacy monitor |

Health routes are exempt from rate limiting.

Readiness currently checks only the football database. The privilege database
is not checked by `/health/ready`; authentication-dependent failures may still
appear as privilege database or 500-class issues while this probe is healthy.

## Authentication operations

The login endpoint:

```http
POST /auth/login
Content-Type: application/json

{"username":"employee_name"}
```

The response contains a bearer JWT. Clients must send:

```http
Authorization: Bearer <token>
```

The JWT uses `JWT_SECRET`, includes `sub` and `role`, expires after two hours
by default, and is verified using HS256.

Rotate `JWT_SECRET` carefully: existing JWTs become invalid after rotation.

## Permission operations

Check the privilege database for:

- active employee role assignments;
- active roles;
- role-permission assignments;
- permission codes `data:read` and `data:write`.

Permission codes are resolved by username and role in the repository. Missing
permissions produce HTTP 403 and a `security.authorization_denied` warning.

## Rate limiting

- Limiter key: remote address.
- Default: `RATE_LIMIT_DEFAULT` (`200/minute` by default).
- Many resource routes also explicitly use `10/minute`.
- Storage default: `memory://`.
- Exceeded limit: HTTP 429 with `Retry-After: 60`.
- Health routes: exempt.

For multiple application processes, use a shared SlowAPI storage backend
instead of process-local memory. Otherwise each worker has an independent
counter.

## Logging

Outside `local`, setup uses JSON lines on stdout. Local and development logging
are text-oriented.

The request middleware adds:

- `request_id`;
- `method`;
- `path`;
- `client_ip`; and
- `username` after JWT authentication.

Authorization denials log role, required and missing permissions, method, path,
and request ID. Request completion and failures also include duration and status.

Never log passwords, JWT secrets, database passwords, or full sensitive bodies.
Search support incidents using `request_id`.

## Database operations

Both databases use `mysql+aiomysql`, pool pre-ping, and async sessions.

Main database:

- URL and pool settings come from `DB_*`.
- Optional Vault credentials replace configured values at startup.
- `ping()` executes `SELECT 1` with a short timeout.

Privilege database:

- URL and pool settings come from `PRV_*`.
- No startup ping or privilege schema migration is performed.
- Authentication and authorization requests fail if it is unavailable.

Keep database and application worker sizing aligned:

```text
required database connections approximately
worker count x (main pool + privilege pool)
```

## Security baseline

- Keep JWT secrets unique per environment.
- Keep `DEBUG=false` and disable docs in production.
- Restrict CORS origins and trusted hosts.
- Terminate TLS at an ingress or load balancer.
- Restrict network access to only trusted callers.
- Use least-privilege database accounts.
- Treat login as an internal/demo mechanism until password verification and
  credential protections are implemented.
- Map all writes to `data:write` and reads to `data:read`.

## Troubleshooting

### Application will not start

1. Confirm `.env` contains `CONFIG_ENV`.
2. Confirm `.env.local`, `.env.dev`, or `.env.prod` exists.
3. Confirm every required `APP`, `DB`, `PRV`, and `JWT` setting is present.
4. Check startup logs for missing settings or database URL construction errors.

### Readiness fails

1. Test network connectivity to `DB_HOST:DB_PORT`.
2. Verify `DB_USER` and `DB_PASSWORD`.
3. Verify `DB_NAME` and MySQL user grants.
4. Inspect `db_ping_failed` structured logs.

### Login or authorization fails

1. Verify the privilege database credentials and host.
2. Confirm employee and active role records exist.
3. Confirm role, role-permission, and permission rows exist.
4. Inspect the `security.authorization_denied` event.
5. Verify `JWT_SECRET` is the same across application processes.

### HTTP 401 or 403

| Condition | Typical cause |
|---|---|
| Missing/invalid bearer token | No/expired/incorrectly signed JWT |
| 403 missing permission | Role lacks `data:read` or `data:write` |
| Login 403 | Employee absent or no active role |

### HTTP 429

- Identify the client IP and route limit.
- Set `RATE_LIMIT_STORAGE_URI` to shared storage for multi-worker deployments.
- Adjust limits only after confirming expected traffic.

### Too many database connections

- Reduce worker count or pool size/overflow.
- Check MySQL connection usage.
- Confirm sessions are not held open by application code.

## Production checklist

- [ ] `CONFIG_ENV=prod`
- [ ] `DEBUG=false`
- [ ] JWT and database secrets injected securely
- [ ] `/docs`, `/redoc`, and `/openapi.json` disabled
- [ ] `ALLOWED_ORIGINS` and `TRUSTED_HOSTS` restricted
- [ ] TLS and network controls in place
- [ ] Both databases reachable
- [ ] Worker and pool sizes fit MySQL limits
- [ ] Shared rate-limit storage configured if needed
- [ ] Liveness uses `/health/live`
- [ ] Readiness uses `/health/ready`
- [ ] Log collector captures JSON stdout
- [ ] Alerting covers 5xx, 429, process crashes, and readiness failures
