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

echo "==> [1/4] git pull"
git pull --ff-only

echo "==> [2/4] build frontend (static -> frontend/mini-app/build, served by host nginx)"
( cd frontend/mini-app && npm install && npm run build )

echo "==> [3/4] rebuild + restart backend & bot (migrations run on container start)"
$DC up -d --build backend bot

echo "==> [4/4] status"
$DC ps

echo "==> done."
