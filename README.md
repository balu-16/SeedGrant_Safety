# Smart Safety Tag

Personal-safety project: Expo / React Native client + FastAPI + PostgreSQL (Supabase) backend + React admin portal.

## Layout

- `client/` — Expo / React Native / TypeScript app (onboarding, auth, Home, Track, Guardians, Profile). See `client/README.md`.
- `server/` — FastAPI + PostgreSQL (Supabase) backend, shared by the app and the admin portal. See `server/README.md` for setup, migrations, and the API surface.
- `admin/` — React + Vite web admin portal (same design language as the app). See `admin/README.md`.
- `reference/` — original design reference images (unchanged).

Browser-test output (screenshots, traces) is generated under `client/test-results/`
and is git-ignored.

## Quick start

Frontend (mobile app):

```sh
cd client
npm install
npx expo start
```

Backend:

```sh
cd server
uv sync
cp .env.example .env   # then fill in DATABASE_URL + JWT_SECRET
uv run python -m app.db.migrate
uv run uvicorn app.main:app --reload   # http://127.0.0.1:8000
```

Admin portal (web):

```sh
cd admin
npm install
npm run dev   # http://localhost:5173, proxies /api to localhost:8000
```

## Admin portal

- Same backend, same database — the portal adds `/api/admin/*` routes guarded by a
  `role` column on `users` (fail-closed, checked per request).
- First admin: set `ADMIN_EMAILS=email@example.com` on the server (promoted at
  startup), or run `uv run python -m app.bootstrap_admin email@example.com` once.
- Features: dashboard KPIs + charts, live SOS monitor (WebSocket), full user
  control (disable / force-logout / reset-password / promote / delete), device and
  guardian management, emergency timelines on a map, location history + purge,
  push broadcasts, and a complete audit log.
- Deploy: static build (`admin/dist`) — e.g. Vercel (config included). Set
  `VITE_API_URL` to the backend URL and add the portal origin to the server's
  `CORS_ORIGINS`.

## Deploy (Render)

Root Directory: `server`. See `server/README.md` for build/start commands and env vars.
