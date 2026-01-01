# Руководство по применению миграций

## Миграция: `67aca3c3bf83_add_user_avatar_purchases_table`

Эта миграция создаёт таблицу `user_avatar_purchases` для отслеживания покупок аватаров пользователями.

### Что делает миграция

- Создаёт таблицу `user_avatar_purchases` с полями:
  - `id` (primary key)
  - `user_id` (foreign key к `users.id`)
  - `avatar_id` (string, ID аватара)
  - `purchased_at` (datetime, время покупки)
- Создаёт уникальное ограничение на `(user_id, avatar_id)` - один аватар можно купить один раз
- Создаёт индекс на `user_id` для быстрого поиска покупок пользователя

---

## Применение миграции на сервере

### Вариант 1: Через Docker Compose (рекомендуется)

Если проект запущен через Docker Compose:

```bash
# Перейти в директорию проекта
cd /path/to/BodyWeight

# Применить миграции
docker compose exec backend alembic upgrade head
```

### Вариант 2: Напрямую на сервере

Если backend запущен напрямую (не в Docker):

```bash
# Перейти в директорию backend
cd /path/to/BodyWeight/backend

# Активировать виртуальное окружение (если используется)
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Применить миграции
alembic upgrade head
```

### Вариант 3: Через SSH на удалённом сервере

```bash
# Подключиться к серверу
ssh user@your-server.com

# Перейти в директорию проекта
cd /path/to/BodyWeight

# Если используется Docker
docker compose exec backend alembic upgrade head

# Или напрямую
cd backend
source venv/bin/activate
alembic upgrade head
```

---

## Проверка применения миграции

### Проверить текущую версию миграций

```bash
# В Docker
docker compose exec backend alembic current

# Напрямую
cd backend
alembic current
```

Должна быть версия: `67aca3c3bf83`

### Проверить таблицу в базе данных

```bash
# Подключиться к PostgreSQL
docker compose exec db psql -U your_user -d your_database

# Или напрямую
psql -U your_user -d your_database

# Проверить наличие таблицы
\dt user_avatar_purchases

# Посмотреть структуру таблицы
\d user_avatar_purchases
```

---

## Откат миграции (если нужно)

Если нужно откатить миграцию:

```bash
# Откатить на одну версию назад
docker compose exec backend alembic downgrade -1

# Или напрямую
cd backend
alembic downgrade -1
```

---

## Важные замечания

1. **Резервное копирование**: Перед применением миграции на production рекомендуется сделать бэкап базы данных:
   ```bash
   docker compose exec db pg_dump -U your_user your_database > backup.sql
   ```

2. **Проверка на dev**: Всегда сначала применяйте миграцию на dev/staging окружении.

3. **Мониторинг**: После применения миграции проверьте логи приложения на наличие ошибок.

---

## Структура таблицы после миграции

```sql
CREATE TABLE user_avatar_purchases (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    avatar_id VARCHAR(50) NOT NULL,
    purchased_at TIMESTAMP DEFAULT now(),
    UNIQUE (user_id, avatar_id)
);

CREATE INDEX ix_user_avatar_purchases_user_id ON user_avatar_purchases(user_id);
```

