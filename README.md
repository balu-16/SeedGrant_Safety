# Smart Safety Tag

Personal-safety project: Expo / React Native client + FastAPI + PostgreSQL (Supabase) backend.

## Layout

- `server/` — FastAPI + PostgreSQL (Supabase) backend. See `server/README.md` for setup, migrations, and the API surface.
- `reference/` — original design reference images (unchanged).

The Expo / React Native client lives in its own repo: **SmartSafetyTag-Client**.
Browser-test output (screenshots, traces) is generated under that repo's
`test-results/` directory and is git-ignored.

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
