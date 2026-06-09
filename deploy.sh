#!/usr/bin/env bash
#
# One-command deploy for the Ubuntu server: rebuild the SvelteKit frontend
# (static) AND the backend Docker image, then (re)start the containers.
# DB migrations run automatically inside the backend container on start
# (alembic upgrade head), so there is no separate migration step here.
#
# Prerequisites on the server: git, Node.js + npm, Docker Engine, and Docker
# Compose (v2 plugin "docker compose" or legacy "docker-compose").
#
# Usage:  ./deploy.sh        (or:  bash deploy.sh)
#
set -euo pipefail

# Always operate from the repo root (where docker-compose.yml lives).
cd "$(dirname "$0")"

# Pick whichever Docker Compose is installed (v2 plugin preferred).
if docker compose version >/dev/null 2>&1; then
	DC="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
	DC="docker-compose"
else
	echo "ERROR: Docker Compose not found (need 'docker compose' or 'docker-compose')." >&2
	exit 1
fi

BUILD_DIR="frontend/mini-app/build"

echo "==> [1/5] git pull"
git pull --ff-only

echo "==> [2/5] build frontend (static -> $BUILD_DIR, served by host nginx)"
# Marker to prove the build actually (re)wrote its output during THIS run.
marker="$(mktemp)"
( cd frontend/mini-app && npm install && npm run build )

echo "==> [3/5] verify frontend build"
if [ ! -f "$BUILD_DIR/index.html" ]; then
	echo "ERROR: frontend build failed — $BUILD_DIR/index.html not found." >&2
	rm -f "$marker"
	exit 1
fi
if [ ! "$BUILD_DIR/index.html" -nt "$marker" ]; then
	echo "ERROR: $BUILD_DIR/index.html was not rebuilt this run (stale output)." >&2
	rm -f "$marker"
	exit 1
fi
rm -f "$marker"
file_count=$(find "$BUILD_DIR" -type f | wc -l)
echo "    OK: frontend rebuilt — ${file_count} files, index.html $(stat -c '%y' "$BUILD_DIR/index.html")"

echo "==> [4/5] rebuild + restart backend & bot (migrations run on container start)"
$DC up -d --build backend bot

echo "==> [5/5] status"
$DC ps

echo "==> done. Frontend built OK and containers are up."
