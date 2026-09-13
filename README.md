# Smart Safety Tag — Server

Backend for the Smart Safety Tag personal-safety project (FastAPI + PostgreSQL on Supabase).

The Expo / React Native client lives in a separate repo: **SmartSafetyTag-Client**.

## Layout

- `server/` — FastAPI + PostgreSQL (Supabase) backend. See `server/README.md` for setup, migrations, and the API surface.
- `reference/` — original design reference images (unchanged).
- `artifacts/` — browser-test screenshots (generated, ignored by git).

## Quick start

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
