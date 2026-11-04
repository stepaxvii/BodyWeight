#!/usr/bin/env bash
# One-command deploy on the Raspberry Pi (served by host Caddy at /bodyweight).
# The SvelteKit mini-app builds INSIDE Docker (the Pi has no Node), is written to
# backend/static, then published to the Caddy webroot. Backend + bot images are
# rebuilt; Alembic migrations run on backend container start.
#   Usage:  ./deploy.sh
set -euo pipefail
cd "$(dirname "$0")"

CADDY_ROOT="${CADDY_ROOT:-/srv/bodyweight}"

echo "==> [1/5] git pull"
git pull --ff-only

echo "==> [2/5] build mini-app in Docker -> backend/static"
docker build -t bw-frontend-build ./frontend/mini-app
docker run --rm -v "$PWD/backend/static:/out" bw-frontend-build
[ -f backend/static/index.html ] || { echo "ERROR: SPA build produced no index.html" >&2; exit 1; }

echo "==> [3/5] publish SPA to Caddy webroot ($CADDY_ROOT)"
sudo mkdir -p "$CADDY_ROOT"
sudo rsync -a --delete backend/static/ "$CADDY_ROOT"/
sudo chown -R caddy:caddy "$CADDY_ROOT" 2>/dev/null || true

echo "==> [4/5] rebuild + (re)start containers (xray+backend+bot via compose + override)"
docker compose up -d --build

echo "==> [5/5] status"
docker compose ps
echo "==> done. https://stepaproject.ru/bodyweight"
