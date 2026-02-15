#!/usr/bin/env bash
# Очистка сервера от мусора после пересборок фронтенда и Docker.
# Запуск из корня репозитория: bash scripts/cleanup-server.sh
# Тома (./data с БД) не удаляются.

set -e

echo "=== 1. Docker: кэш сборки ==="
docker builder prune -f 2>/dev/null || true
echo ""

echo "=== 2. Docker: неиспользуемые образы и контейнеры ==="
docker image prune -a -f
docker container prune -f
echo ""

echo "=== 3. Docker: общий prune (сети, висячие образы) ==="
docker system prune -f
echo ""

echo "=== 4. Артефакты фронтенда на сервере ==="
if [ -d "frontend/mini-app" ]; then
  rm -rf frontend/mini-app/node_modules 2>/dev/null || true
  rm -rf frontend/mini-app/.svelte-kit   2>/dev/null || true
  rm -rf frontend/mini-app/build         2>/dev/null || true
  echo "Удалены node_modules, .svelte-kit, build"
else
  echo "frontend/mini-app не найден, пропуск"
fi
echo ""

echo "=== Использование диска Docker ==="
docker system df
