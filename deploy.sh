#!/usr/bin/env bash
#
# One-command deploy: rebuild the SvelteKit frontend (static) AND the backend
# Docker image, then (re)start the containers. DB migrations are applied
# automatically inside the backend container on start (alembic upgrade head),
# so there is no separate migration step here.
#
# Usage (on the server):  bash deploy.sh   (or ./deploy.sh once it's +x)
#
set -euo pipefail

# Always operate from the repo root (where docker-compose.yml lives).
cd "$(dirname "$0")"

echo "==> [1/4] git pull"
git pull --ff-only

echo "==> [2/4] build frontend (static -> frontend/mini-app/build, served by host nginx)"
( cd frontend/mini-app && npm install && npm run build )

echo "==> [3/4] rebuild + restart backend & bot (migrations run on container start)"
docker compose up -d --build backend bot

echo "==> [4/4] status"
docker compose ps

echo "==> done."
