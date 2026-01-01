# Исправление проблемы с миграциями

## Проблема 1: duplicate column name: is_onboarded

База данных уже содержит колонки из старых миграций, но Alembic не знает об этом.

## Проблема 2: table user_avatar_purchases already exists

Таблица `user_avatar_purchases` уже существует в базе данных (создана вручную или другим способом).

## Решение

Если таблица `user_avatar_purchases` уже существует, нужно просто пометить миграцию как уже применённую:

### Решение: Пометить миграцию как уже применённую

Если таблица `user_avatar_purchases` уже существует, просто пометите миграцию как применённую:

```bash
# В Docker - пометить как head (включая новую миграцию)
docker compose exec backend alembic stamp head

# Или напрямую
cd backend
alembic stamp head
```

Это сообщит Alembic, что все миграции (включая новую `67aca3c3bf83`) уже применены.

### Проверка

После пометки проверьте:

```bash
# Текущая версия
docker compose exec backend alembic current

# Должна быть: 67aca3c3bf83
```

### Если таблица НЕ существует

Если таблица не существует, но возникла ошибка, можно изменить миграцию, чтобы она проверяла существование таблицы перед созданием (см. ниже).

## Проверка

После применения проверьте:

```bash
# Текущая версия
docker compose exec backend alembic current

# Должна быть: 67aca3c3bf83 (или 005_update_achievement_slugs если только пометили)
```

## Если проблема остаётся

Если после `stamp` всё равно возникают ошибки, можно проверить структуру базы:

```bash
# Подключиться к SQLite
docker compose exec backend sqlite3 /path/to/database.db

# Проверить таблицу alembic_version
SELECT * FROM alembic_version;

# Проверить структуру users
.schema users
```

