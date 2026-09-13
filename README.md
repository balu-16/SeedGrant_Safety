# Smart Safety Tag

Personal-safety project: Expo / React Native client + FastAPI + PostgreSQL (Supabase) backend.

## Layout

- `client/` — Expo / React Native app. See `client/README.md` for setup and checks.
- `server/` — FastAPI + PostgreSQL (Supabase) backend. See `server/README.md` for setup, migrations, and the API surface.
- `reference/` — original design reference images (unchanged).
- `artifacts/` — browser-test screenshots (generated, ignored by git).

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
