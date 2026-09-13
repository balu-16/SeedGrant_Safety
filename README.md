# Smart Safety Tag

Personal-safety project: Expo / React Native client + FastAPI + PostgreSQL (Supabase) backend.

## Layout

- `client/` — Expo / React Native / TypeScript app (onboarding, auth, Home, Track, Guardians, Profile). See `client/README.md`.
- `server/` — FastAPI + PostgreSQL (Supabase) backend. See `server/README.md` for setup, migrations, and the API surface.
- `reference/` — original design reference images (unchanged).

Browser-test output (screenshots, traces) is generated under `client/test-results/`
and is git-ignored.

## Quick start

Frontend:

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

## Deploy (Render)

Root Directory: `server`. See `server/README.md` for build/start commands and env vars.
