# Smart Safety Tag

Monorepo for the Smart Safety Tag personal-safety project.

## Layout

- `client/` — Expo / React Native / TypeScript frontend (onboarding, auth, Home, Track, Guardians, Profile). See `client/README.md` for the full run guide and demo walkthrough.
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
