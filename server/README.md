# Smart Safety Tag — V0 Backend (`server/`)

FastAPI + asyncpg + PostgreSQL (Supabase) backend for the Smart Safety Tag personal-safety project.
REST for everything; WebSocket only for real-time event fan-out (`emergency-created`,
`emergency-updated`). The ESP32 tag talks to the phone over BLE —
never to this backend over WebSockets. No frontend code lives here.

## Stack

Python 3.12+, FastAPI, `uvicorn[standard]`, asyncpg (parameterized SQL, no ORM),
pydantic-settings, PyJWT, pwdlib (Argon2), email-validator. Dev: pytest, pytest-asyncio,
httpx, ruff, mypy. Managed entirely with `uv` (never `pip`).

## Setup (exact commands, run from `server/`)

```bash
cd server
uv sync                  # reproduce exact env from pyproject.toml + uv.lock
cp .env.example .env     # then fill in DATABASE_URL + JWT_SECRET
```

Configure `.env` (all env-driven, nothing hardcoded):

```text
DATABASE_URL=postgresql://postgres.PROJECT:PASSWORD@aws-0-<region>.pooler.supabase.com:5432/postgres
DB_SSLMODE=require
JWT_SECRET=<long random, min 32 chars>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=["*"]
ENV=development
# Admin portal bootstrap: comma-separated emails promoted to admin at startup
ADMIN_EMAILS=
# Push delivery: mock (default, log-only) or fcm (direct FCM HTTP v1)
PUSH_PROVIDER=fcm
FCM_PROJECT_ID=<firebase project id>
FCM_CREDENTIALS_PATH=./fcm-service-account.json
FCM_DRY_RUN=false
```

Run migrations (idempotent via `schema_migrations`, safe to re-run):

```bash
uv run python -m app.db.migrate
```

Start the API:

```bash
uv run uvicorn app.main:app --reload   # http://127.0.0.1:8000
```

Verify: `GET /api/health` (no DB), `GET /api/ready` (needs DB; 503 otherwise),
Swagger at `/docs`.

### Admin portal bootstrap

The web admin portal (`../admin/`) consumes `/api/admin/*`, which requires
`users.role = 'admin'`. Promote accounts with `ADMIN_EMAILS` (comma-separated,
applied at startup) or one-off:

```bash
uv run python -m app.bootstrap_admin email@example.com
```

## Tests (isolated — never touch Supabase)

```bash
uv run pytest            # 39 tests, in-memory fake repos, no live DB
uv run ruff check . && uv run ruff format --check .
uv run mypy app
```

## API surface (all under `/api`)

| Area | Endpoints |
|---|---|
| health | `GET /api/health`, `GET /api/ready` |
| auth | `POST /api/auth/register|login|refresh|logout|logout-all` |
| users | `GET/PATCH /api/users/me` |
| devices | `POST/GET /api/devices`, `GET/PATCH /api/devices/{id}`, `POST /{id}/pair|unpair`, `GET /{id}/status` |
| guardians | `POST /api/guardians/invite`, `GET /api/guardians`, `GET /api/guardians/protecting`, `PATCH /{id}/status`, `DELETE /{id}` |
| locations | `POST /api/locations`, `GET /api/locations/latest?user_id=`, `GET /api/locations/history?user_id=&limit=&offset=` |
| emergencies | `POST/GET /api/emergencies`, `GET /api/emergencies/{id}`, `PATCH /{id}/status`, `POST /{id}/resolve|cancel` |
| push-tokens | `POST/GET/DELETE /api/push-tokens` (DELETE takes `?token=<raw>`) |
| admin | `GET /api/admin/stats|health|users|devices|guardians|emergencies|locations|push-tokens|audit`, `PATCH/DELETE /api/admin/...`, `POST /api/admin/users/{id}/disable|enable|force-logout|reset-password|promote|demote`, `POST /api/admin/emergencies/{id}/ack|resolve|cancel`, `POST /api/admin/push/send` — **role=admin, fully audited** |
| ws | `WS /api/ws?token=<access_jwt>` (auth at handshake, multi-socket per user; admins also receive every emergency event) |

Auth: Argon2 passwords, short access JWT + rotating server-stored refresh tokens
(`sub/type/iat/exp/jti` claims; cross-type tokens rejected with 401). Refresh
rotation is single-use — a concurrent reuse of the same refresh token gets 401.
Rate limits (per client IP, in-memory): register 5/min, login 10/min, refresh
60/min, SOS create 10/min → `429 rate_limited`.
Authorization: owner-only by default; accepted guardians get read (locations,
emergencies) and may ack/resolve. Guardian consent is enforced: only the invited
guardian can accept an invite (owner may reject/remove); guardians discover
pending invites via `GET /api/guardians/protecting?include_pending=true`, and
invites sent to an email before that account existed are linked automatically
at registration. All transitions validated in services.

Quick manual check:

```bash
curl -s http://127.0.0.1:8000/api/health
TOKEN=$(curl -s -X POST :8000/api/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"you@x.com","password":"..."}' | python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])")
curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/api/users/me
```

## Layout

`app/core` (config/logging/exceptions/security/deps), `app/db` (pool/migrate),
`app/{auth,users,devices,guardians,locations,emergencies,push_tokens}` (router→service→repository),
`app/notifications` (provider protocol + mock; `fcm.py` implements direct FCM
HTTP v1 delivery with OAuth2 service-account auth, high-priority SOS channel,
and dead-token pruning),
`app/websocket` (manager + authenticated route), `app/api` (aggregation + health),
`migrations/*.sql`, `tests/` (fake repos, ASGI client).

## Notes for later phases

- Supabase URL arrives separately: set `DATABASE_URL`, run migrate, no code changes.
- BLE/GPS stay client-side; backend accepts `device_id`, `source`, and push tokens
  (hashed for lookup + raw token stored for FCM delivery — added in migration 007).
- Emergency create is transactional (`emergencies` + `emergency_events`); push
  fan-out runs as a background task after the response; WS/notify are best-effort.
- Startup fails closed in production-like `ENV` values when `JWT_SECRET` is still
  the insecure default; CORS credentials are only enabled for explicit origin lists.
- Deploy (Render): Root Directory `server`, build `uv sync`, start
  `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`, run
  `uv run python -m app.db.migrate` as a release/one-off job. Set env vars
  (DATABASE_URL, JWT_SECRET, CORS_ORIGINS, PUSH_PROVIDER, FCM_*) in the dashboard.
