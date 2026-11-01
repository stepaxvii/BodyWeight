# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Authored against the **`develop`** branch — the active integration branch. `main` is far behind and not representative.

## What this is

PixelFit (repo name: BodyWeight) — a Telegram Mini App fitness tracker with 8-bit / NES gamification. Monorepo:

- **`backend/`** — one Python codebase run as **two separate processes/containers** that share one database: a **FastAPI API** (`app.main:app`, uvicorn :8000) and an **aiogram Telegram bot** (`python -m app.bot.main`). They share state *only* through the DB — never in-memory.
- **`frontend/mini-app/`** — SvelteKit (Svelte 5, runes mode) compiled to a **static SPA** (adapter-static, no Node server in production).

Almost all user-facing text (UI copy, API descriptions, notifications, bot messages) is in **Russian**; keep that for new strings. Code/comments mix Russian and English.

## Commands

Backend commands run from `backend/`, frontend from `frontend/mini-app/`.

**Backend**
```bash
pip install -r requirements.txt          # (Docker image uses `uv pip install --system`)
alembic upgrade head                     # apply migrations — these are INCREMENTAL patches, not a from-scratch build (see note below)
python scripts/init_db.py                # seed categories/exercises/titles from app/data/*.json (run AFTER migrate; idempotent)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload   # API — this process ALSO runs the APScheduler jobs
python -m app.bot.main                   # the Telegram bot (separate process; does NOT run scheduled jobs)
alembic revision --autogenerate -m "..." # new migration; models auto-register via alembic/env.py
```

**Frontend**
```bash
npm ci
npm run dev        # Vite dev server on :3000, proxies /api -> localhost:8000
npm run check      # svelte-check — the ONLY automated gate in the whole repo
npm run build      # adapter-static output to build/ (SPA, fallback index.html)
```

**Docker / deploy** (see *Deployment topologies* — they differ in important ways)
```bash
docker compose up -d --build                       # root compose: SQLite + DEBUG=true, API(:8002)+bot only
docker compose -f deploy/docker-compose.yml up -d  # full stack: Postgres + nginx + frontend + API + bot
./deploy.sh                                        # the ACTUAL prod host flow (see below)
bash scripts/cleanup-server.sh                     # prune Docker + delete frontend node_modules/.svelte-kit/build (keeps ./data)
```

**Ops scripts** (run inside the API container)
```bash
docker exec bodyweight-api python scripts/announce_challenges.py [--dry-run|--no-push|--limit N]  # idempotent broadcast
docker compose exec backend python scripts/check_leaderboard_visible.py                           # DB diagnostic
```

**There are NO tests and NO CI** (no `.github/workflows`, no pytest). `npm run check` is the only automated check, and it covers the frontend only. The backend has zero automated coverage.

## The `/bodyweight` base path (load-bearing)

Everything is served under `/bodyweight`, hardwired in **four coupled places** — change one, change all four:
1. `frontend/mini-app/svelte.config.js` → `kit.paths.base = '/bodyweight'`
2. `frontend/mini-app/src/lib/api/client.ts` → `API_BASE = '/bodyweight/api'` (hardcoded; the `PUBLIC_*` vars in `.env.example` are **not read anywhere**)
3. nginx location blocks (`deploy/nginx-bodyweight.conf` and `deploy/nginx.conf`)
4. `src/lib/stores/workout.svelte.ts` → `loadActiveWorkout()` hand-builds a raw `fetch('/bodyweight/api/workouts/active')` that bypasses the client — a 4th hardcode to update too

In the SPA, **every internal link and static-asset URL must be prefixed with `base`** from `$app/paths` (e.g. `goto(\`${base}/challenges/${id}\`)`, `{base}/sprites/...`). Un-prefixed links work in `npm run dev` but 404 in the deployed Mini App. (Note: the start-param routes map at the top of `+layout.svelte` still holds un-prefixed paths like `'/friends'` — follow the `base`-prefixed form instead.)

## Frontend architecture

- **Static SPA, client-only.** `routes/+layout.ts` sets `prerender=true` + `ssr=false` globally. Never assume a server runtime, cookies, or request headers; guard browser APIs. Dynamic/param routes **must** ship a `+page.ts` with `prerender=false` (that's why `boss`, `challenges`, `challenges/[id]`, `challenges/new` each have one) — otherwise adapter-static's `strict:true` build fails trying to prerender them.
- **Auth/onboarding gate lives only in `+layout.svelte`.** Page components may assume the user is authenticated and onboarded; children aren't rendered until `userStore.isAuthenticated && userStore.isOnboarded`.
- **Svelte 5 runes "class-singleton" stores** in `src/lib/stores/*.svelte.ts`: one class with `$state` fields, derived values as plain `get` accessors (not `$derived` fields), exported as a single `new` singleton (`userStore`, `workoutStore`, `exercisesStore`, `favoritesStore`, `telegram`, `sound`). Read `store.field` directly in components — there is no `writable()`/`$store` syntax. **Map/Set state must be replaced wholesale** (`new Map(x)`, `new Set(x)`) to stay reactive.
- **All HTTP goes through the `api` singleton** (`src/lib/api/client.ts`): auto-selects `tma <initData>` vs `Bearer <jwt>`, 10s AbortController timeout + one retry; only `getAllExercises()`/`getAllAchievements()` auto-paginate — other list methods return a single page. (Lone exception: `workoutStore.loadActiveWorkout()` hand-builds a fetch — a known inconsistency, Telegram-auth only.)
- **Two CSS token systems coexist** in `src/app.css`: the "Neo 2026" tokens (`--bg/--accent/--gold/--line/...`) and legacy `--pixel-*` names aliased on top of them. `src/lib/styles/hud.css` is a className-based HUD kit (not components). Both are imported once, in `+layout.svelte`. A global `* { text-transform: none !important }` kills all CSS uppercasing — author copy in its final case.
- **Fonts:** Pixel Operator (self-hosted TTF) — ⚠️ **Latin-only, NO Cyrillic glyphs in any release**: all Russian text in the SPA silently falls back to the generic `monospace` stack. Silkscreen (Google Fonts CDN) is **digits-only, no Cyrillic** — never use it as a Cyrillic fallback. The backend share-card renderer bundles **Pixelify Sans** (OFL, full Cyrillic) in `backend/app/assets/fonts/` for Russian strings.
- UI primitives are imported from the `$lib/components/ui` barrel (`PixelButton`, `PixelCard`, `PixelIcon`, `PixelTabs`, `CountUp`, …). Not everything is exported from it: `Banner`/`Diff` live *inside* `ui/` but aren't in `ui/index.ts`, and `BossBar`/`TitlePicker` live in `components/` root — import all four by full path.
- **`src/lib/utils/xp.ts` must stay identical to backend `xp_calculator.py`**, and challenge reward tiers / streak-freeze constants are duplicated in challenge/profile screens with "must mirror backend" comments. Change one side → UI silently diverges from server truth.

## Backend architecture

- **FastAPI wiring:** `main.py` builds the app and mounts a single `api_router` (prefix `/api`) defined in `app/api/__init__.py`, which mounts all feature routers under sub-prefixes (the one source of truth for URL prefixes). The lifespan starts the scheduler, and **only when `DEBUG=true`** seeds data. Swagger/ReDoc/OpenAPI are **DEBUG-gated** — no API docs in production. The backend serves only `/api/*` and `/health`; the SPA is always served by nginx.
- **Dual auth, one dependency.** `get_current_user` (`app/api/deps.py`, exposed as the `CurrentUser` type alias) resolves `Authorization: Bearer <jwt>` (HS256) **or** `tma <initData>` (Telegram HMAC-SHA256, 24h freshness). In DEBUG, `tma debug_<telegram_id>` bypasses HMAC. The dependency only *reads* the user — brand-new Telegram users must first hit `POST /api/auth/validate` (which creates them). Web auth adds email/username/password (salted SHA-256, 30-day JWT) and a Telegram↔web account **link + merge** flow (`/auth/link-telegram` → bot DM → `/auth/confirm-link/{token}`), backed by an **in-memory** `_pending_links` dict (single-process assumption).
- **DB layer** (`app/db/database.py`): async SQLAlchemy 2.0 (`Mapped`/`mapped_column`), one `Base`, one async engine from `settings.database_url`. **SQLite (aiosqlite) in dev, Postgres (asyncpg) in prod — chosen purely by `DATABASE_URL`.** The session dependency **auto-commits on clean return / rolls back on exception**, so most routes only `flush()`; `boss`/`challenges`/`custom_routines` are the exceptions that `commit()` explicitly and `rollback()`+raise 400 on service-layer `ValueError`.
  - **Schema changes go through Alembic, never `create_all()`** (a `main.py` comment forbids it). ⚠️ But the migration chain is **incremental, not from-scratch**: revision `001` opens with `ALTER TABLE users …`, so it patches a base schema that predates the chain — the core tables (`users`, `exercises`, `workout_sessions`, …) are created by *no* migration, so `alembic upgrade head` on a brand-new empty DB fails at `001`. (Only later feature tables like `monthly_bosses`/`challenges` have `create_table` migrations.) `alembic/env.py` overrides `alembic.ini`'s placeholder URL with `settings.database_url` and imports `app.db.models` so autogenerate sees every model — add every new model to `app/db/models/__init__.py`.
  - Use **`BooleanCoerce`** (`db/types.py`) for boolean columns with a string `server_default` — SQLite stores `'false'` as a truthy string (see `User.leaderboard_visible`, fixed by migration 007).
- **Content is JSON-sourced** from `backend/app/data/`:
  - **Upserted into the DB** by `data_loader.init_data`: `categories.json`, `exercises/*.json`, and 5 hardcoded title `ShopItem`s. Re-seeding **overwrites** seeded exercise fields from JSON (JSON is the source of truth). `gif_url` is **derived** as `/sprites/exercises/{slug}.svg` — never put it in JSON.
  - **Served directly from JSON** (no DB table): `routines/*.json`, `achievements.json`. (`messages.json` exists but is **dead** — not read anywhere; notification copy is hardcoded in `services/notifications.py`.)
  - **Hybrid:** `bosses.json` is a 12-month template catalog; the boss service materializes one `monthly_bosses` row per month on demand.
  - To **add an exercise**: append to the right `data/exercises/<category>.json` (`slug`, `category`, `name`/`name_ru`, `difficulty`, `base_xp`, `required_level`, `equipment`, `is_timed`, `tags`, optional `easier`/`harder`), then re-seed. To **add a boss/achievement**: edit the JSON; no migration needed.

### Workout completion = the domain hub

`POST /api/workouts/submit` is the single completion endpoint (older per-set endpoints removed; idempotent via `client_request_id` — duplicate submissions are not double-recorded). It funnels through `services/workout_processor.py:process_workout_completion`, which in one transaction: computes **per-exercise XP**, updates `UserExerciseProgress` + personal records, computes coins, bumps `user.total_xp/coins/level` (+5 coins/level-up), **advances the streak**, deals **monthly-boss damage**, records **challenge progress**, updates goals, unlocks **achievements** (self-awarding XP/coins), and emits in-app + Telegram notifications. Boss/challenge hooks are wrapped in try/except and must stay best-effort.

Where the numbers live — edit the right file:
- **`services/xp_calculator.py`** — all core formulas: `XP = total_reps × (base_xp × 0.3) × streak_mult`, floored (XP is proportional to *total* reps, independent of set split; **difficulty is baked into `base_xp`, there is no separate difficulty multiplier**; timed exercises convert at 10s = 1 rep). Coins (scarce: +1 if session XP≥500, +min(streak//7,4), +1 if ≥45min). Level curve `100·(level-1)²`. Streak multiplier ramps 1.0→1.5 over 7 days. Cycling and walking are special-cased (own formulas; `cycling`/`walking` slugs need extra fields).
- **`services/streak.py`** — streak-freeze economy (500 coins, max 2). ⚠️ The forward streak *increment* lives in `workout_processor`; the overnight *reset/bridge* lives here — changing streak rules means editing **both**.
- **`services/boss.py`** (boss damage = workout XP 1:1, no cap; reward tiers), **`services/challenges.py`** (reward tiers, TTLs, per-day AND-completion), **`services/activity_norm.py`** (default 1400 XP/day target for calendar coloring).

### Scheduler & bot

- **APScheduler runs ONLY in the FastAPI process** (`services/scheduler.py`, started in the lifespan) — 6 jobs: hourly reminders, daily inactivity (12:00 server-local), streak-freeze `00:01 UTC`, boss finalize+spawn `00:05`, challenge lifecycle `00:10` (order matters), admin stats digest `05:00 UTC`. ⚠️ Assumes a **single API instance** — two replicas double-fire jobs. Also, boss/challenge lifecycle work also runs **lazily on read**, so a server that slept past month-end still catches up.
- **Admin digest** (`services/admin_stats.py`): aggregates yesterday's product stats (new users, DAU, workouts, XP/sets/reps, top exercises, challenge joins, freezes burned, referral rewards, ~boss damage) **plus audience health** (promo-reachable = has `telegram_id` and `bot_blocked=False`; blocked count) and sends a Russian HTML message to `ADMIN_TELEGRAM_ID` (`settings.admin_telegram_id`; unset = feature off). Same digest on demand via the admin-only `/digest` bot command. The admin also gets **real-time best-effort notices** (no PII, just counts) on each new registration (`notify_admin_new_user` fired at every user-creation site) and each bot block.
- **Block tracking:** `User.bot_blocked` is set by the bot's `handlers/chat_member.py` `my_chat_member` handler (block → `kicked`, unblock → `member`) and defensively by `notifications._send` on a 403. `notifications.py` routes every push through one `_send()` helper (403 = user blocked → INFO + record; other failures = `.exception()` with traceback).
- **Logging** (`app/logging_config.py:setup_logging`): both processes call it; reads `settings.log_level` (bot no longer hardcodes INFO) and quiets noisy libs (aiogram/apscheduler/httpx). Plain-text to stdout, no structured logging / request IDs.
- ⚠️ **UTC/local time mix:** the forward streak increment, goals, and activity-norm use `date.today()` (server-local), while boss/challenge lifecycle and the overnight streak-freeze job use `datetime.utcnow()` — even the streak feature straddles both clocks (increment local in `workout_processor.py`, reset/bridge UTC in `streak.py`). Real footgun for day-boundary correctness.
- **Bot** (`app/bot/main.py`): aiogram long-polling, three routers — `handlers/admin.py` (admin-only `/digest`, registered first), `handlers/chat_member.py` (`my_chat_member` → `User.bot_blocked`), and `handlers/start.py` (everything else), HTML parse mode, public commands registered in `on_startup`. Shares the DB via `async_session_maker` directly. Telegram pushes from the API process use a *separate* lazily-created `Bot` in `services/notifications.py`.

## Deployment topologies (they disagree — know which one is live)

1. **`docker-compose.yml`** (root): simple/dev — SQLite, `DEBUG=true`, API published on `127.0.0.1:8002`, bot. No nginx/frontend/Postgres. **This is the compose file `deploy.sh` actually drives in prod** for backend+bot.
2. **`deploy/docker-compose.yml`**: full stack — Postgres 15 + containerized nginx + frontend (sirv) + API + bot, `DEBUG=false`. The `systemd` unit targets this one.
3. **`./deploy.sh`** (the real host flow on stepaproject.ru): `git pull --ff-only` → build the SPA on the host (`npm ci && npm run build`, with a stale-build guard) → `docker compose up -d --build backend bot` (root compose). **Migrations/seed run inside the API container on start** (`alembic upgrade head && python scripts/init_db.py && uvicorn …`) — there is no separate migrate step. **HOST nginx** (`deploy/nginx-bodyweight.conf`) serves the SPA from `build/` and proxies `/bodyweight/api` → backend.

⚠️ Known inconsistencies on the server to reconcile: root compose publishes `:8002` but `deploy/nginx-bodyweight.conf` proxies `:8000`; the systemd unit points at the `deploy/` stack while `deploy.sh` uses the root stack. Root `.env` needs `BOT_TOKEN/SECRET_KEY/MINI_APP_URL` (+ optional `ADMIN_TELEGRAM_ID` for the daily digest); `deploy/.env` additionally needs `DB_PASSWORD`. Shell scripts are pinned to LF (`.gitattributes`). `PERFORMANCE_REVIEW.md` (Russian, 2026-06-21) catalogs still-open N+1 queries, missing indexes, and frontend fetch waterfalls with a P0/P1/P2 plan.

## API surface

Routers mount under `/api` (`app/api/__init__.py`): `auth`, `users`, `exercises`, `workouts`, `achievements`, `leaderboard`, `friends`, `goals`, `shop`, `custom-routines`, `notifications`, `boss`, `challenges`. Each has a matching schema module in `app/schemas/` and models in `app/db/models/`. Unauthenticated: `auth` (`validate`/`register`/`login`/`confirm-link`) and three `exercises` GETs — `/categories`, `/routines/all`, `/routines/{slug}`. Everything else takes `CurrentUser`.

**Leaderboard is friends-weekly only:** the single `GET /api/leaderboard` returns the current user + accepted friends ranked by XP earned since Monday 00:00 UTC (zero-XP friends included via outerjoin). The old global / global-weekly / friends-all-time endpoints are gone. `User.leaderboard_visible` still gates who appears (ORM default is now `True` for new users; the settings toggle and old opt-outs are respected).
