# Performance Review — BodyWeight

> Ревью проекта с фокусом на медленную загрузку данных.
> Дата: 2026-06-21

---

## Содержание

1. [Краткое резюме](#краткое-резюме)
2. [Бэкенд: API и БД](#бэкенд-api-и-бд)
3. [Фронтенд: загрузка данных](#фронтенд-загрузка-данных)
4. [Кэширование](#кэширование)
5. [Приоритетный план исправлений](#приоритетный-план-исправлений)

---

## Краткое резюме

Основные причины медленной загрузки:

1. **Водопадные запросы** — страницы загружают данные последовательно вместо параллельного
2. **N+1 запросы к БД** — циклы с отдельными запросами на каждую итерацию
3. **Отсутствие кэширования** — данные читаются с диска/БД при каждом запросе без кэша
4. **Загрузка всех данных** — некоторые страницы загружают ВСЕ упражнения, потом фильтруют в JS
5. **Отсутствующие индексы** — запросы по foreign key без индексов

---

## Бэкенд: API и БД

### Критично: N+1 запросы

#### 1. `get_today_stats()` — ленивая загрузка exercises в цикле
**Файл:** `backend/app/api/routes/workouts.py:416-433`

```python
workouts = workouts_result.scalars().all()  # ← без selectinload!
for w in workouts:
    for we in w.exercises:  # ← N+1 lazy load на каждую тренировку!
```

**Исправление:** Добавить `selectinload(WorkoutSession.exercises)` в запрос.

#### 2. `workout_processor` — запросы внутри цикла упражнений
**Файл:** `backend/app/services/workout_processor.py:180-183, 273-278`

Внутри `for ex_data in data.exercises` — 2 запроса на каждое упражнение:
- `select(Exercise).where(Exercise.slug == ...)`
- `select(UserExerciseProgress).where(...)`

При 10 упражнениях = 20 лишних запросов. Нужно batch-загружать.

#### 3. `_calc_running_completion()` в цикле участников
**Файл:** `backend/app/api/routes/challenges.py:430-438`

Для каждого участника вызывается функция с 1-2 запросами. При P участниках = O(P) запросов.

#### 4. `_calc_running_completion()` в цикле активных челленджей
**Файл:** `backend/app/api/routes/challenges.py:250-253`

Для каждого активного челленджа — отдельный запрос.

#### 5. `achievement_checker` — запросы на каждое условие
**Файл:** `backend/app/services/achievement_checker.py:29-118`

На каждое условие достижения — отдельный запрос. При ~20 достижениях = 10-15 запросов после каждой тренировки.

#### 6. `boss.py: get_user_rank()` — загружает ВСЕ вклады
**Файл:** `backend/app/services/boss.py:318-331`

Загружает все записи `BossContribution` в память, потом считает ранг в Python. Нужен `COUNT(*) + 1`.

#### 7. `boss.py: get_boss_history` — вызывает `get_user_rank` в цикле на 12 боссов
**Файл:** `backend/app/api/routes/boss.py:191-195`

12 полных сканирований таблицы.

#### 8. `_notify_friends_about_workout` — запрос на каждого друга
**Файл:** `backend/app/services/workout_processor.py:512-573`

Для каждого друга — индивидуальный запрос уведомления. При 10 друзьях = 10 запросов.

---

### Критично: Отсутствующие индексы

| Таблица | Поле | Файл |
|---------|------|------|
| `WorkoutExercise` | `exercise_id` | `workout.py:40` |
| `UserExerciseProgress` | `user_id`, `exercise_id` | `user_exercise.py:16-17` |
| `UserGoal` | `user_id` | `goal.py:15` |
| `UserPurchase` | `user_id` | `shop.py:31` |
| `WorkoutSession` | `status` (лучше составной `(user_id, status)`) | `workout.py:27` |
| `Exercise` | `category_id` | `exercise.py:29` |

**Высокоценный составной индекс:** `WorkoutSession(user_id, status, started_at)` — используется в `get_current_user_stats`, `get_today_stats`, `get_workout_history`.

---

### Высоко: Синхронное чтение файлов в async обработчиках

**Файл:** `backend/app/services/data_loader.py:13-17, 37-46`

```python
def load_json(filename: str) -> dict | list:
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)  # ← блокирует event loop!
```

Вызывается из async-маршрутов `get_routines`, `get_routine` на КАЖДОМ запросе. Нужно либо кэшировать, либо использовать `aiofiles`.

---

### Высоко: Лишняя загрузка данных

#### `get_exercises()` — загружает ВСЕ упражнения, фильтрует в Python
**Файл:** `backend/app/api/routes/exercises.py:114-134, 147-168`

Запрос тянет все записи из БД, потом фильтрует по tags/favorites в Python. `total` считается как `len(filtered)` после фильтрации. Нужно перенести фильтрацию в SQL.

#### `get_categories()` — загружает ВСЕ упражнения ради подсчёта
**Файл:** `backend/app/api/routes/exercises.py:51-55`

Использует `selectinload(ExerciseCategory.exercises)` чтобы посчитать `len([e for e in cat.exercises if e.is_active])`. SQL `COUNT` подзапрос был бы эффективнее.

---

### Средне: Паттерны в БД

#### Автокоммит на каждом запросе
**Файл:** `backend/app/db/database.py:24-33`

```python
async def get_async_session():
    async with async_session_maker() as session:
        yield session
        await session.commit()  # ← коммит даже на GET-запросах
```

#### Двойной коммит
Многие маршруты вызывают `session.commit()` явно + dependency коммитает снова:
- `challenges.py:187, 276, 355, 476`
- `exercises.py:464, 472`
- `notifications.py:65, 82`

#### Lazy loading без защиты
Все связи в моделях используют lazy loading по умолчанию. Нет `lazy="raise"` или `lazy="noload"` как защита от случайных N+1.

---

### Средне: Отсутствие пагинации

| Endpoint | Файл |
|----------|------|
| `list_challenges` | `challenges.py:157-277` |
| `get_friends` | `friends.py:14-54` |
| `get_shop_items` | `shop.py:11-56` |
| `get_goals` | `goals.py:12-48` |
| `search_users` | `friends.py:331-376` |
| `get_global_leaderboard` | `leaderboard.py:33-80` (нет skip) |

---

### Низко: Broadcast уведомления — индивидуальные INSERT'ы

**Файл:** `backend/app/services/boss.py:106-119, 210-242`

При новом боссе — `session.add()` + `session.flush()` для КАЖДОГО пользователя. При 1000 пользователях = 1000 вставок. Нужен `bulk_insert_mappings`.

---

## Фронтенд: загрузка данных

### Критично: Водопадные запросы на страницах

#### Главная страница — 5 последовательных/полупоследовательных запросов
**Файл:** `src/routes/+page.svelte:22-43`

```
1. userStore.loadStats()              ← последовательный
2. api.getUnreadNotificationCount()   ← после #1
3. api.getUserActivity(currentYear)   ← параллельно с #4
4. api.getUserActivity(prevYear)      ← параллельно с #3
5. BossBar: api.getCurrentBoss()      ← отдельный onMount
```

Запросы 1, 2, 3/4, 5 независимы — все можно запустить параллельно.

#### Страница тренировки — 4-стадийный водопад
**Файл:** `src/routes/workout/+page.svelte:324-402`

```
Стадия 1: [categories, routines, customRoutines]  ← параллельно (хорошо)
Стадия 2: [activeWorkout, favorites]              ← после стадии 1
Стадия 3: loadExercises()                         ← после стадии 2
Стадия 4: api.getAllExercises()                   ← после стадии 3 (!!!)
```

Стадия 4 загружает ВСЕ упражнения (последовательная пагинация!) ради "Программы дня".

**Дополнительно:** `favorites.svelte.ts:168-181` — при переключении на вкладку "Избранное" вызывается `api.getAllExercises()` ЕЩЁ РАЗ.

#### Страница профиля — 4 последовательных запроса
**Файл:** `src/routes/profile/+page.svelte:42-62`

```
1. userStore.loadStats()           ← последовательный
2. api.getAllAchievements()        ← после #1 (многостраничная!)
3. api.getUserActivity()           ← после #2
4. api.getUserRecords()            ← после #3
```

Запросы 2, 3, 4 независимы — можно параллельно.

---

### Высоко: API клиент без retry/timeout

**Файл:** `src/lib/api/client.ts:76-113`

```typescript
async request<T>(path, options) {
    const response = await fetch(url, { ... }); // ← нет retry, нет timeout
}
```

Нет `AbortController`, нет retry при сетевых ошибках, нет дедупликации запросов.

---

### Высоко: `getAllExercises()` — последовательная пагинация

**Файл:** `src/lib/api/client.ts:215-229`

```typescript
while (hasMore) {
    const response = await api.getExercises(undefined, { skip, limit: 100 });
    allExercises.push(...response.items);
    // ← каждый запрос ждёт завершения предыдущего
}
```

При 500 упражнениях = 5 последовательных HTTP-запросов. Можно либо распараллелить, либо сделать бэкенд-эндпоинт без пагинации.

---

### Высоко: `exercisesStore` — polling для дедупликации

**Файл:** `src/lib/stores/exercises.svelte.ts:44-51`

```typescript
return new Promise((resolve) => {
    const checkLoaded = setInterval(() => {
        if (!this._loading) {
            clearInterval(checkLoaded);
            resolve(this._exercises);
        }
    }, 100); // ← polling каждые 100мс вместо Promise
});
```

Нужно использовать паттерн с shared Promise.

---

### Высоко: Блокирующий auth gate

**Файл:** `src/routes/+layout.svelte:43-70, 110`

Приложение показывает полный спиннер пока не завершится аутентификация. Нет skeleton UI или оптимистичного рендера.

---

### Средне: Лишний запрос `getCurrentUser` на leaderboard

**Файл:** `src/routes/leaderboard/+page.svelte:43-52`

```typescript
const [, u] = await Promise.all([
    loadLeaderboard(),
    api.getCurrentUser().catch(() => null), // ← данные уже в userStore!
]);
```

---

### Средне: Challenge detail рефетчится при каждом visibility change

**Файл:** `src/routes/challenges/[id]/+page.svelte:46-51`

Каждый раз когда пользователь возвращается к приложению — полный рефетч без условных запросов (ETag/If-None-Match).

---

## Кэширование

### Бэкенд

| Что | Кэшировано? | Файл |
|-----|-------------|------|
| `get_categories` | Да, 600 сек | `exercises.py:49` |
| `get_routines` | **Нет** | `exercises.py:376` |
| `get_routine` (one) | **Нет** | `exercises.py:405` |
| `get_exercises` | **Нет** | `exercises.py:114` |
| `get_global_leaderboard` | **Нет** | `leaderboard.py:33` |
| `get_weekly_leaderboard` | **Нет** | `leaderboard.py:82` |
| `get_current_boss` | **Нет** | `boss.py:145` |
| JSON файлы (routines, exercises) | **Нет** — читаются с диска на каждый запрос | `data_loader.py:37-46` |

**Проблема:** `timed_cache` не thread-safe, нет max-size, не multi-process safe (`backend/app/utils/cache.py:14-75`).

### Фронтенд

| Что | Кэшировано? | TTL |
|-----|-------------|-----|
| `exercises_cache` (localStorage) | Да, но **без проверки свежести** | Нет |
| `cache_user` | Да, без TTL | Нет |
| `cache_user_stats` | Да, без TTL | Нет |
| `cache_favorites` | Да, без TTL | Нет |
| `cache_categories/routines/custom` | Да, без TTL | Нет |

**Все localStorage кэши** используются ТОЛЬКО как offline fallback. Нет cache-first стратегии.

---

## Приоритетный план исправлений

### P0 — Немедленно (большой эффект)

1. **Параллельные запросы на фронтенде**
   - Главная: объединить все 5 запросов в `Promise.all`
   - Тренировка: вынести стадию 4 ("Программа дня") в неблокирующий фоновой запрос
   - Профиль: объединить achievements + activity + records в `Promise.all`
   - Убрать лишний `getAllExercises()` при открытии вкладки "Избранное"

2. **Индексы в БД**
   - `WorkoutExercise.exercise_id`
   - `UserExerciseProgress(user_id, exercise_id)`
   - `WorkoutSession(user_id, status, started_at)` — составной
   - `UserGoal.user_id`, `UserPurchase.user_id`

3. **Кэширование JSON данных на бэкенде**
   - `load_all_routines()` и `load_all_exercises()` кэшировать после первого чтения
   - Они читаются с диска при КАЖДОМ запросе

4. **Убрать N+1 в `get_today_stats()`**
   - Добавить `selectinload(WorkoutSession.exercises)`

### P1 — Скоро (заметный эффект)

5. **Batch-загрузка в `workout_processor`**
   - Собрать все `slug` упражнений, сделать 1 запрос вместо N

6. **Фильтрация упражнений в SQL** вместо Python
   - `get_exercises()` должен фильтровать по tags/equipment/difficulty на уровне БД

7. **Retry + timeout в API клиенте**
   - Минимум: retry 1 раз при сетевой ошибке
   - Timeout 10 сек на запрос

8. **Promise-based дедупликация** вместо setInterval в `exercisesStore`

9. **Убрать double commit** в маршрутах

### P2 — Позже (оптимизации)

10. Cache-first стратегия на фронтенде (показать кэш, обновить фоном)
11. Пагинация для challenges, friends, shop, goals
12. Batch inserts для broadcast уведомлений
13. SQLite WAL mode
14. `precompress: true` в svelte.config.js
15. Lazy loading для изображений бейджей
