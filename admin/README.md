# Smart Safety Tag — Admin Portal

Web admin portal for the Smart Safety Tag platform. Plain **React 19 + Vite +
TypeScript** with the same hand-rolled design language as the mobile app
(`client/src/constants/theme.ts` tokens ported to CSS variables). Talks to the
**same** FastAPI backend as the mobile app — no separate server.

## Features

| Screen | What admins can do |
| --- | --- |
| Dashboard | KPIs (users, devices online, open emergencies, guardian links, push tokens), 30-day signup & emergency charts, recent incidents, health strip |
| Live SOS | Realtime emergency feed over WebSocket with optional alert sound; acknowledge/resolve inline |
| Users | Search/filter every account; full detail drawer (devices, guardians, emergencies, tokens, sessions); edit profile, disable/enable, force logout, one-time password reset, promote/demote admin, delete (typed confirmation) |
| Devices | All safety tags; battery/connection filters; rename, force offline, delete |
| Guardians | Every safety-circle link; force consent transitions (fixes stuck invites); delete |
| Emergencies | All incidents with status/trigger filters; detail view with map + status timeline; ack/resolve/cancel on behalf |
| Locations | Per-user trail on a real map (OpenStreetMap); latest fix; purge history (privacy) |
| Push & Broadcast | Inspect/delete a user's tokens; test push to one user or broadcast to all |
| Audit Log | Every admin mutation, filterable by action/target |
| System | Backend health, provider config, own session + sign-out |

## Getting started

```sh
npm install
npm run dev        # http://localhost:5173 — proxies /api to http://localhost:8000
```

Point the proxy elsewhere with `ADMIN_API_PROXY=http://host:port npm run dev`.

Sign in with an account whose `users.role` is `admin`. Promote the first admin
from the server side (there is no self-service path):

```sh
cd ../server
# either set ADMIN_EMAILS=email@example.com in .env (applied at startup)
uv run python -m app.bootstrap_admin email@example.com
```

## Environment

| Variable | Where | Purpose |
| --- | --- | --- |
| `VITE_API_URL` | admin build | Backend base URL (empty in dev → Vite proxy) |
| `ADMIN_API_PROXY` | admin dev | Proxy target override (default `http://localhost:8000`) |

## Build & deploy

```sh
npm run build      # outputs admin/dist (typechecks first)
```

`dist/` is a static bundle — deploy anywhere. A `vercel.json` SPA rewrite is
included; on Vercel set `VITE_API_URL` to the backend URL, then add the deployed
origin (e.g. `https://your-admin.vercel.app`) to the server's `CORS_ORIGINS`.

## Security model

- Admin-only routes are enforced server-side (`get_current_admin`): the role is
  read from the database on **every** request, so demotion or suspension takes
  effect immediately — the portal holds no special credentials.
- Every admin mutation writes an entry to `admin_audit_log` (viewable in the
  Audit Log screen).
- Access token stays in memory; the refresh token lives in `localStorage` and is
  rotated single-use by the backend, same flow as the mobile client.
- Destructive actions (delete user, purge locations, delete tag/link) require
  explicit confirmation modals.

## Project structure

```
admin/
├── vercel.json            # SPA rewrite for static hosting
└── src/
    ├── styles/theme.css   # design tokens + component styles (port of the app's theme)
    ├── api/               # fetch client w/ refresh rotation + typed endpoints
    ├── auth/              # session context (login, role check, restore, logout)
    ├── components/        # ui.tsx (design system), Layout, DataTable, MiniMap
    ├── hooks/             # useSosFeed — shared WebSocket feed for the whole app
    └── pages/             # one file per screen
```
