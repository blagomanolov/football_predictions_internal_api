# Operations & production runbook

Production-oriented documentation for running, configuring, observing, and troubleshooting the Football Internal API.

For design and request flow, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 1. Environments

| `CONFIG_ENV` | Env file | Typical use | Logging format | `DEBUG` |
|--------------|----------|-------------|----------------|---------|
| `local` | `.env.local` | Developer laptop | Plain text | `true` |
| `dev` | `.env.dev` | Shared / staging | Plain text | usually `true` or carefully controlled |
| `prod` | `.env.prod` | Production | **JSON (stdout)** | **`false` (mandatory)** |

### How env selection works

1. Process starts; `configs/env_loader.py` loads `football_api/.env`.
2. Reads `CONFIG_ENV` (default `local` if missing).
3. Requires `football_api/.env.{CONFIG_ENV}` to exist; otherwise raises `FileNotFoundError` at import time.
4. `Settings` binds variables from that file.

**Deploy tip:** in containers/K8s, prefer injecting real secrets as environment variables (or Vault) and keep `.env.prod` as a template of required keys — never commit real production passwords.

---

## 2. Configuration reference

| Env var | Settings field | Required | Notes |
|---------|----------------|----------|-------|
| `CONFIG_ENV` | `config_env` | yes (in `.env`) | `local` \| `dev` \| `prod` |
| `APP_NAME` | `app_name` | yes | OpenAPI title |
| `VERSION` | `version` | no (default `1.0.0`) | OpenAPI version |
| `LOG_LEVEL` | `log_level` | no (default `INFO`) | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `DEBUG` | `debug` | no (default `false`) | Controls 500 response verbosity |
| `DB_HOST` | `host` | yes | MySQL host |
| `DB_PORT` | `port` | no (default `3306`) | |
| `DB_USER` | `user` | yes* | *may be overridden by Vault |
| `DB_PASSWORD` | `password` | yes* | *may be overridden by Vault |
| `DB_NAME` | `database` | yes | Logical DB name in settings |
| `DB_CHARSET` | `db_charset` | no (default `utf8mb4`) | Passed as URL query |

Optional Vault configuration is supplied via the `vault` settings object (not a single env string) — see Architecture §7.

### Production `.env.prod` baseline

```env
CONFIG_ENV=prod
APP_NAME=football-internal-api
VERSION=1.0.0
LOG_LEVEL=INFO
DEBUG=false
DB_HOST=...
DB_PORT=3306
DB_USER=...
DB_PASSWORD=...
DB_NAME=...
```

---

## 3. Process management (how to run in production)

### Do

```bash
cd football_api/src
uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 2 \
  --proxy-headers \
  --forwarded-allow-ips='*'
```

Notes:

- **No `--reload` in production** (reload is for local only; `python main.py` currently enables reload — use Uvicorn CLI for prod).
- `--workers` > 1 = multiple processes; each has its own DB pool. Size workers × `pool_size` against MySQL `max_connections`.
- Behind a reverse proxy / ALB / Ingress, enable proxy headers so client IP / scheme are correct if you later log them.
- Prefer a supervisor (systemd, Docker, Kubernetes) that restarts on non-zero exit.

### Don’t

- Run with `DEBUG=true` in prod.
- Expose Uvicorn directly to the public internet without TLS termination and auth at the edge (this is an **internal** API).
- Rely on `python main.py` as the production entrypoint while it hardcodes `reload=True` and `127.0.0.1`.

### Container sketch

```dockerfile
# illustrative — adapt to your base image / user / secrets story
WORKDIR /app/football_api
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
WORKDIR /app/football_api/src
ENV CONFIG_ENV=prod
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

Ensure `.env` / `.env.prod` (or equivalent env injection) is available at the path expected by `env_loader` (`football_api/` two levels above `configs/`).

---

## 4. Health, readiness, and probes

| Endpoint | Current behavior | Use as |
|----------|------------------|--------|
| `GET /health` | Returns `{"status":"ok"}` if the process can serve HTTP | **Liveness** |

**Gap (document so ops are not surprised):** `/health` does **not** check MySQL. A process can be “alive” while the DB is down; those requests will fail with `500` / `internal_error` and appear in logs.

Recommended future addition:

- `GET /ready` — runs a cheap `SELECT 1` (or pool checkout) and returns 503 if DB is unavailable → use as **readiness** probe.

---

## 5. Logging in production

### What you get

When `CONFIG_ENV=prod`, each log line is a JSON object on **stdout**, for example:

```json
{
  "ts": "2026-10-25T04:00:00.123456+00:00",
  "level": "INFO",
  "logger": "app.access",
  "message": "method=GET path=/countries/1 status=200 duration_ms=12.4",
  "request_id": "3f2c8a1e-...."
}
```

On errors, `exc_info` may be present with a traceback.

### Correlation

1. Client may send `X-Request-ID: <uuid-or-trace-id>`.
2. Middleware stores it in a context var and echoes it on the response.
3. Logging filter injects `request_id` into log records.
4. Error JSON body also includes `request_id`.

**Support workflow:** ask the caller for `X-Request-ID` (or copy it from the response) → search logs for that id → see access line + any `AppError` / stack traces for the same request.

### Log levels guidance

| Level | Use |
|-------|-----|
| `DEBUG` | Local investigation only |
| `INFO` | Access logs, lifecycle, normal ops (default prod) |
| `WARNING` | Expected domain failures worth alerting on (`AppError`) |
| `ERROR` / exception logs | Unhandled failures, DB session failures |

SQLAlchemy engine logger is capped at **WARNING** to avoid flooding collectors with SQL.

### Sensitive data policy

Never log:

- DB passwords, Vault tokens, Authorization headers
- Full request bodies that may contain PII unless explicitly approved
- Raw exception strings that might embed connection URLs with credentials

---

## 6. Error contract (client & on-call)

Stable body:

```json
{
  "code": "string",
  "message": "string",
  "details": null,
  "request_id": "string"
}
```

| HTTP | `code` | Typical cause | On-call action |
|------|--------|---------------|----------------|
| 404 | `not_found` | Missing resource | Usually client/data; not an outage |
| 422 | `validation_error` | Bad query/body | Client bug; `details` has Pydantic errors |
| 4xx | `http_error` | Explicit HTTPException | Inspect message |
| 401/403 | `unauthorized` / `forbidden` | Future auth usage | Auth config / caller credentials |
| 409 | `conflict` | Future write conflicts | Data state |
| 500 | `internal_error` | Bug, DB down, misconfig | **Page / investigate logs by `request_id`** |

With `DEBUG=false`, the 500 `message` is always `"Internal server error"`. The real exception is only in logs.

---

## 7. Database operations notes

- Driver: `mysql+aiomysql`
- ORM schema name on countries: `football_predictions`
- Pool: `pool_size=10`, `max_overflow=20`, `pool_recycle=1800`, `pool_pre_ping=True`
- Session errors roll back and re-raise; they surface as `internal_error` unless mapped earlier

### Credentials

| Mode | Behavior |
|------|----------|
| Direct | Uses `DB_USER` / `DB_PASSWORD` / `DB_HOST` from env |
| Vault catalogue | Metadata + creds path → updates host/user/password at startup |
| Vault creds_path | Updates user/password at startup |

Vault failures at startup prevent the app from becoming healthy — that is intentional (fail closed).

---

## 8. Middleware & headers

| Header | Direction | Behavior |
|--------|-----------|----------|
| `X-Request-ID` | Request | Optional; if absent, server generates UUID |
| `X-Request-ID` | Response | Always set to the id used for this request |

Gateways should forward `X-Request-ID` end-to-end when chaining internal services.

---

## 9. Production checklist

Before first prod traffic:

- [ ] `CONFIG_ENV=prod`
- [ ] `DEBUG=false`
- [ ] `LOG_LEVEL=INFO` (or `WARNING` if intentionally quieter)
- [ ] Secrets not in git; injected by platform or Vault
- [ ] `requirements.txt` (or lockfile) pinned and installed in the image
- [ ] Uvicorn run without `--reload`, bound to `0.0.0.0` (or mesh sidecar)
- [ ] Workers sized vs MySQL `max_connections`
- [ ] Liveness probe → `/health`
- [ ] Log shipper collects **stdout** JSON
- [ ] Alert on rate of `internal_error` / 5xx and on process crash loops
- [ ] Network policy: only trusted callers can reach the service
- [ ] Confirm OpenAPI `/docs` is disabled or restricted in prod if policy requires (FastAPI serves docs by default — lock down at gateway if needed)

---

## 10. Troubleshooting playbook

### App won’t start — `FileNotFoundError: Environment file not found`

- `.env` sets `CONFIG_ENV=prod` but `.env.prod` is missing in the image/workdir.
- Fix: ship the file or change how `env_loader` resolves paths for your platform.

### App starts but every request is 500

1. Grab `request_id` from response.
2. Find matching log line + `exc_info`.
3. Common causes: wrong DB host/creds, schema `football_predictions` missing, MySQL not reachable from the pod/host.

### 404 `not_found` for a country that “should” exist

- Confirm id/filter values and DB content.
- Filters are exact matches on the column (`name`, `code_alpha2`, …).

### Logs missing `request_id`

- Ensure middleware is registered (`main.py`).
- Ensure `RequestIdFilter` is attached to handlers (done in `main.py` after `dictConfig`).
- For JSON, field appears only when the attribute is set on the record.

### Too many DB connections

- Lower Uvicorn `--workers` or SQLAlchemy `pool_size` / `max_overflow`.
- Check for connection leaks (sessions not closed — dependency should always close via context manager).

---

## 11. Security baseline (internal API)

| Control | Status / recommendation |
|---------|-------------------------|
| TLS | Terminate at load balancer / ingress |
| AuthN | Not in-app yet — enforce at gateway (JWT, mTLS, VPN, IP allowlist) |
| AuthZ | Use `ForbiddenError` / `UnauthorizedError` when you add in-app checks |
| Docs exposure | Restrict `/docs`, `/redoc`, `/openapi.json` in prod if required |
| Error leakage | Keep `DEBUG=false` |
| Secrets | Env injection or Vault; rotate credentials; no secrets in logs |

---

## 12. Dependency hygiene

`requirements.txt` at `football_api/requirements.txt` must list runtime packages for reproducible deploys. After installing into a clean venv:

```bash
pip freeze > requirements.txt
```

Or maintain a curated pin list (FastAPI, Uvicorn, SQLAlchemy, aiomysql, pydantic-settings, python-dotenv, hvac, StrEnum, …). Prefer a lock strategy your team already uses (pip-tools, Poetry, uv).

---

## Related documents

- [ARCHITECTURE.md](ARCHITECTURE.md) — deep dive on request flow and layers
- [../README.md](../README.md) — quick start and API overview
