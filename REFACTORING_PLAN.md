# 🔧 План Рефакторинга BodyWeight App

**Дата создания**: 30.12.2024
**Версия**: 1.0
**Статус**: К выполнению

---

## 📋 Содержание

1. [Обзор](#обзор)
2. [Метрики и Цели](#метрики-и-цели)
3. [Фаза 1: Критические Исправления](#фаза-1-критические-исправления)
4. [Фаза 2: Оптимизация Производительности](#фаза-2-оптимизация-производительности)
5. [Фаза 3: Улучшение Качества Кода](#фаза-3-улучшение-качества-кода)
6. [Фаза 4: Документация и Тестирование](#фаза-4-документация-и-тестирование)
7. [Риски и Митигация](#риски-и-митигация)
8. [Чеклист Выполнения](#чеклист-выполнения)

---

## Обзор

### Текущее Состояние Проекта

**Архитектура**:
- Frontend: SvelteKit + Svelte 5 + TypeScript
- Backend: FastAPI + SQLAlchemy + SQLite
- Bot: Aiogram 3.4

**Размер Кодовой Базы**:
- Backend: 38 файлов Python
- Frontend: 24 Svelte компонента, 14 TypeScript файлов
- Всего: ~15,000+ строк кода

**Основные Проблемы**:
1. ❌ Дублирование логики завершения тренировки (~400 строк)
2. ❌ Неработающий функционал целей (UserGoal)
3. ❌ Дублирование функций загрузки данных
4. ⚠️ Mock data в production коде
5. ⚠️ Отсутствие кэширования
6. ⚠️ N+1 запросы в некоторых эндпоинтах

---

## Метрики и Цели

### До Рефакторинга

| Метрика | Значение |
|---------|----------|
| Строк в workouts.py | 779 |
| API эндпоинтов для workout | 3 |
| Дублированных функций | 3+ |
| Mock data строк | ~150 |
| Кэшированных данных | 0 |
| N+1 запросов | 2+ места |
| Неиспользуемый код | ~500 строк |

### Целевые Показатели

| Метрика | Цель | Улучшение |
|---------|------|-----------|
| Строк в workouts.py | ~450 | -42% |
| API эндпоинтов для workout | 1 | -67% |
| Дублированных функций | 0 | -100% |
| Mock data строк | 0 (изоляция) | -100% |
| Кэшированных данных | 3+ типа | ✅ |
| N+1 запросов | 0 | ✅ |
| Неиспользуемый код | 0 | -100% |

---

## Фаза 1: Критические Исправления

**Длительность**: 3-5 дней
**Приоритет**: 🔴 КРИТИЧЕСКИЙ

### 1.1 Удаление Дублирования Workout Completion

**Проблема**: Два способа завершения тренировки с дублированием ~400 строк кода.

**Текущее Состояние**:
```python
# backend/app/api/routes/workouts.py

# Способ 1 (Legacy) - строки 233-508
@router.put("/{workout_id}/exercise")
async def add_exercise_to_workout(...)  # 140 строк

@router.post("/{workout_id}/complete")
async def complete_workout(...)  # 130 строк

# Способ 2 (Recommended) - строки 510-717
@router.post("/submit")
async def submit_workout(...)  # 200 строк
```

**План Действий**:

#### Шаг 1: Создать Общую Функцию Обработки
```python
# backend/app/services/workout_processor.py (НОВЫЙ ФАЙЛ)

from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import User, WorkoutSession, WorkoutExercise, Exercise
from app.services.xp_calculator import calculate_xp, calculate_coins
from app.services.achievement_checker import check_and_grant_achievements
from app.services.notification_service import create_notification

class WorkoutCompletionData:
    """DTO для данных завершения тренировки"""
    session_id: int
    user_id: int
    exercises: list[dict]  # {exercise_slug, reps, sets}
    started_at: datetime
    finished_at: datetime

async def process_workout_completion(
    data: WorkoutCompletionData,
    db: AsyncSession
) -> dict:
    """
    Общая функция обработки завершения тренировки.

    Возвращает:
        {
            "total_xp": int,
            "total_coins": int,
            "level_up": bool,
            "new_level": int,
            "new_achievements": list[str],
            "streak": int,
            "workout_summary": {...}
        }
    """

    # 1. Получить пользователя
    user = await db.get(User, data.user_id)

    # 2. Обновить streak
    streak_info = await _update_user_streak(user, data.finished_at.date(), db)

    # 3. Определить first_of_day_bonus
    first_bonus = await _is_first_workout_today(user.id, data.finished_at, db)

    # 4. Рассчитать XP и монеты для каждого упражнения
    total_xp = 0
    total_coins = 0
    workout_exercises = []

    for ex_data in data.exercises:
        exercise = await _get_exercise_by_slug(ex_data["exercise_slug"], db)

        xp_earned = calculate_xp(
            base_xp=exercise.base_xp,
            difficulty=exercise.difficulty,
            reps_or_duration=ex_data["reps"],
            streak_days=user.streak_days,
            first_of_day=first_bonus
        )

        coins_earned = calculate_coins(
            xp_earned=xp_earned,
            workout_duration_minutes=(data.finished_at - data.started_at).total_seconds() / 60
        )

        # Создать WorkoutExercise
        we = WorkoutExercise(
            workout_session_id=data.session_id,
            exercise_id=exercise.id,
            sets_completed=ex_data["sets"],
            total_reps=ex_data["reps"],
            xp_earned=xp_earned,
            coins_earned=coins_earned
        )
        db.add(we)
        workout_exercises.append(we)

        total_xp += xp_earned
        total_coins += coins_earned

        # Обновить прогресс упражнения
        await _update_exercise_progress(user.id, exercise.id, ex_data, db)

    # 5. Обновить пользователя
    old_level = user.level
    user.total_xp += total_xp
    user.coins += total_coins
    user.level = calculate_level_from_xp(user.total_xp)

    level_up = user.level > old_level

    # Бонус за level up
    if level_up:
        level_up_bonus = (user.level - old_level) * 5
        user.coins += level_up_bonus
        total_coins += level_up_bonus

    # 6. Обновить сессию тренировки
    session = await db.get(WorkoutSession, data.session_id)
    session.finished_at = data.finished_at
    session.total_xp_earned = total_xp
    session.total_coins_earned = total_coins
    session.streak_multiplier = streak_info["multiplier"]

    # 7. Проверить достижения
    new_achievements = await check_and_grant_achievements(user.id, db)

    # Добавить монеты за достижения
    for achievement_slug in new_achievements:
        achievement = await _get_achievement_data(achievement_slug)
        if achievement.get("coins_reward", 0) > 0:
            user.coins += achievement["coins_reward"]
            total_coins += achievement["coins_reward"]

    # 8. Обновить цели пользователя
    await _update_user_goals(user.id, data, db)

    # 9. Создать уведомления
    if level_up:
        await create_notification(
            user_id=user.id,
            notification_type="level_up",
            title=f"🎉 Уровень {user.level}!",
            message=f"Вы достигли уровня {user.level}! Получено {level_up_bonus} монет.",
            db=db
        )

    for achievement_slug in new_achievements:
        achievement = await _get_achievement_data(achievement_slug)
        await create_notification(
            user_id=user.id,
            notification_type="achievement_unlocked",
            title=f"🏆 {achievement['name_ru']}",
            message=achievement["description_ru"],
            db=db
        )

    await db.commit()

    return {
        "total_xp": total_xp,
        "total_coins": total_coins,
        "level_up": level_up,
        "old_level": old_level,
        "new_level": user.level,
        "new_achievements": new_achievements,
        "streak": user.streak_days,
        "streak_info": streak_info,
        "workout_summary": {
            "total_exercises": len(data.exercises),
            "total_reps": sum(ex["reps"] for ex in data.exercises),
            "total_sets": sum(ex["sets"] for ex in data.exercises),
            "duration_minutes": int((data.finished_at - data.started_at).total_seconds() / 60)
        }
    }


async def _update_user_streak(user: User, workout_date: date, db: AsyncSession) -> dict:
    """Обновление streak пользователя"""
    # Логика подсчёта streak...
    pass

async def _is_first_workout_today(user_id: int, workout_time: datetime, db: AsyncSession) -> bool:
    """Проверка, первая ли это тренировка сегодня"""
    # Логика проверки...
    pass

async def _get_exercise_by_slug(slug: str, db: AsyncSession) -> Exercise:
    """Получение упражнения по slug"""
    # Логика получения...
    pass

async def _update_exercise_progress(user_id: int, exercise_id: int, ex_data: dict, db: AsyncSession):
    """Обновление прогресса упражнения"""
    # Логика обновления UserExerciseProgress...
    pass

async def _update_user_goals(user_id: int, data: WorkoutCompletionData, db: AsyncSession):
    """Обновление целей пользователя"""
    # Логика обновления UserGoal.current_value...
    pass

async def _get_achievement_data(slug: str) -> dict:
    """Получение данных достижения"""
    # Загрузка из кэша...
    pass

def calculate_level_from_xp(total_xp: int) -> int:
    """Расчёт уровня из XP"""
    # Level = floor(sqrt(total_xp / 100)) + 1
    import math
    return int(math.sqrt(total_xp / 100)) + 1
```

#### Шаг 2: Упростить workouts.py
```python
# backend/app/api/routes/workouts.py (ПОСЛЕ РЕФАКТОРИНГА)

from app.services.workout_processor import process_workout_completion, WorkoutCompletionData

@router.post("/submit")
async def submit_workout(
    request: SubmitWorkoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Единственный эндпоинт для завершения тренировки.
    Принимает все данные сразу.
    """

    # 1. Создать сессию
    session = WorkoutSession(
        user_id=current_user.id,
        started_at=request.started_at,
        finished_at=request.finished_at
    )
    db.add(session)
    await db.flush()

    # 2. Подготовить данные
    completion_data = WorkoutCompletionData(
        session_id=session.id,
        user_id=current_user.id,
        exercises=request.exercises,
        started_at=request.started_at,
        finished_at=request.finished_at
    )

    # 3. Обработать через общую функцию
    result = await process_workout_completion(completion_data, db)

    # 4. Вернуть результат
    return SubmitWorkoutResponse(
        workout_session_id=session.id,
        **result
    )


# ❌ УДАЛИТЬ эти эндпоинты:
# @router.put("/{workout_id}/exercise")
# async def add_exercise_to_workout(...)

# @router.post("/{workout_id}/complete")
# async def complete_workout(...)
```

#### Шаг 3: Обновить Frontend
```typescript
// frontend/mini-app/src/lib/api/client.ts

// ❌ УДАЛИТЬ:
// async startWorkout()
// async addExerciseToWorkout()
// async completeWorkout()

// ✅ ОСТАВИТЬ только:
async submitWorkout(exercises: WorkoutExerciseInput[]): Promise<WorkoutResult> {
  const response = await this.fetch('/workouts/submit', {
    method: 'POST',
    body: JSON.stringify({
      started_at: this.workoutStartTime,
      finished_at: new Date().toISOString(),
      exercises: exercises
    })
  });
  return response.json();
}
```

**Результат**:
- ❌ Удалено: 2 эндпоинта + ~270 строк дублированного кода
- ✅ Создано: 1 универсальная функция обработки
- ✅ Упрощён workouts.py: 779 строк → ~450 строк

---

### 1.2 Реализация Обновления Целей (UserGoal)

**Проблема**: Поле `UserGoal.current_value` никогда не обновляется.

**План Действий**:

#### Шаг 1: Добавить Функцию Обновления Целей
```python
# backend/app/services/workout_processor.py

async def _update_user_goals(
    user_id: int,
    data: WorkoutCompletionData,
    db: AsyncSession
):
    """Обновление прогресса целей пользователя"""

    # Получить активные цели
    stmt = select(UserGoal).where(
        UserGoal.user_id == user_id,
        UserGoal.completed == False,
        UserGoal.end_date >= date.today()
    )
    result = await db.execute(stmt)
    goals = result.scalars().all()

    for goal in goals:
        old_value = goal.current_value

        if goal.goal_type == "total_workouts":
            goal.current_value += 1

        elif goal.goal_type == "total_reps":
            total_reps = sum(ex["reps"] for ex in data.exercises)
            goal.current_value += total_reps

        elif goal.goal_type == "total_xp":
            # XP будет рассчитан в основной функции
            # Здесь нужно передать total_xp
            pass

        elif goal.goal_type == "workout_streak":
            user = await db.get(User, user_id)
            goal.current_value = user.streak_days

        elif goal.goal_type.startswith("exercise_"):
            # Например: exercise_pushup-regular_reps
            parts = goal.goal_type.split("_")
            if len(parts) >= 3:
                exercise_slug = "_".join(parts[1:-1])
                metric = parts[-1]

                for ex_data in data.exercises:
                    if ex_data["exercise_slug"] == exercise_slug:
                        if metric == "reps":
                            goal.current_value += ex_data["reps"]
                        elif metric == "sets":
                            goal.current_value += ex_data["sets"]

        # Проверка завершения
        if goal.current_value >= goal.target_value and not goal.completed:
            goal.completed = True
            goal.completed_at = datetime.utcnow()

            # Создать уведомление
            await create_notification(
                user_id=user_id,
                notification_type="goal_completed",
                title=f"🎯 Цель достигнута!",
                message=f"Вы достигли цели: {goal.current_value}/{goal.target_value}",
                db=db
            )

            # Наградить монетами
            user = await db.get(User, user_id)
            bonus_coins = 10  # или зависит от сложности цели
            user.coins += bonus_coins
```

#### Шаг 2: Добавить Эндпоинт Прогресса Целей
```python
# backend/app/api/routes/goals.py

@router.get("/progress")
async def get_goals_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение прогресса по целям"""

    stmt = select(UserGoal).where(
        UserGoal.user_id == current_user.id
    ).order_by(UserGoal.completed.asc(), UserGoal.end_date.asc())

    result = await db.execute(stmt)
    goals = result.scalars().all()

    return [
        {
            "id": goal.id,
            "goal_type": goal.goal_type,
            "target_value": goal.target_value,
            "current_value": goal.current_value,
            "progress_percent": min(100, int(goal.current_value / goal.target_value * 100)),
            "completed": goal.completed,
            "completed_at": goal.completed_at,
            "end_date": goal.end_date,
            "days_remaining": (goal.end_date - date.today()).days
        }
        for goal in goals
    ]
```

**Результат**:
- ✅ Цели обновляются автоматически после каждой тренировки
- ✅ Пользователи получают уведомления о достижении целей
- ✅ Добавлен эндпоинт для отслеживания прогресса

---

### 1.3 Устранение Дублирования load_achievements()

**Проблема**: Функция определена в 2 местах.

**План Действий**:

```python
# backend/app/utils/achievement_loader.py (НОВЫЙ ФАЙЛ)

import json
from functools import lru_cache
from pathlib import Path
from typing import List, Dict

@lru_cache(maxsize=1)
def load_achievements() -> List[Dict]:
    """
    Загрузка достижений из JSON с кэшированием.
    Кэш сбрасывается при перезапуске приложения.
    """
    achievements_file = Path(__file__).parent.parent / "data" / "achievements.json"
    with open(achievements_file, "r", encoding="utf-8") as f:
        return json.load(f)

def get_achievement_by_slug(slug: str) -> Dict | None:
    """Получение достижения по slug"""
    achievements = load_achievements()
    return next((a for a in achievements if a["slug"] == slug), None)
```

```python
# backend/app/services/achievement_checker.py

# ❌ УДАЛИТЬ функцию load_achievements()
# ✅ ИМПОРТИРОВАТЬ:
from app.utils.achievement_loader import load_achievements, get_achievement_by_slug
```

```python
# backend/app/api/routes/achievements.py

# ❌ УДАЛИТЬ функцию load_achievements()
# ✅ ИМПОРТИРОВАТЬ:
from app.utils.achievement_loader import load_achievements, get_achievement_by_slug
```

**Результат**:
- ✅ Единая точка загрузки достижений
- ✅ Автоматическое кэширование через @lru_cache
- ✅ Упрощение поддержки

---

## Фаза 2: Оптимизация Производительности

**Длительность**: 2-3 дня
**Приоритет**: 🟡 ВЫСОКИЙ

### 2.1 Удаление/Изоляция Mock Data

**План Действий**:

```typescript
// frontend/mini-app/src/lib/api/mock-data.dev.ts (НОВЫЙ ФАЙЛ)

/**
 * Mock data для разработки без бэкенда.
 * Используется только в режиме DEV.
 */

export const MOCK_USER = { /* ... */ };
export const MOCK_CATEGORIES = [ /* ... */ ];
export const MOCK_EXERCISES = [ /* ... */ ];
// ...
```

```typescript
// frontend/mini-app/src/lib/api/client.ts

// ❌ УДАЛИТЬ все MOCK_* константы отсюда

// ✅ ДОБАВИТЬ:
import { MOCK_USER, MOCK_EXERCISES, /* ... */ } from './mock-data.dev';

class ApiClient {
  private useMockData = import.meta.env.DEV && import.meta.env.VITE_USE_MOCKS === 'true';

  async getExercises(): Promise<Exercise[]> {
    if (this.useMockData) {
      return MOCK_EXERCISES;
    }
    // реальный запрос...
  }
}
```

```bash
# .env.development
VITE_USE_MOCKS=false  # По умолчанию выключено
```

**Результат**:
- ✅ Mock data изолирован в отдельный файл
- ✅ Управление через env-переменную
- ✅ Не попадёт в production bundle
- ✅ -150 строк из основного client.ts

---

### 2.2 Исправление Расчёта XP на Frontend

**Проблема**: Локальный расчёт XP не совпадает с серверным.

**Решение 1 (Рекомендуется)**: Убрать локальный расчёт
```typescript
// frontend/mini-app/src/lib/stores/workout.svelte.ts

// ❌ УДАЛИТЬ:
// const totalXp = $derived.by(() => { /* сложный расчёт */ });

// ✅ ПОКАЗЫВАТЬ примерное значение:
const estimatedXp = $derived.by(() => {
  return selectedExercises.reduce((sum, ex) => {
    const data = exerciseData.get(ex.id);
    return sum + (ex.base_xp * ex.difficulty * (data?.sets.length || 1));
  }, 0);
});

// В UI:
// "Примерный XP: ~{estimatedXp}" с иконкой "?"
```

**Решение 2 (Альтернатива)**: Эндпоинт предпросмотра
```python
# backend/app/api/routes/workouts.py

@router.post("/preview")
async def preview_workout_xp(
    request: PreviewWorkoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Предварительный расчёт XP без сохранения тренировки"""

    total_xp = 0
    for ex in request.exercises:
        exercise = await get_exercise_by_slug(ex.exercise_slug, db)
        xp = calculate_xp(
            base_xp=exercise.base_xp,
            difficulty=exercise.difficulty,
            reps_or_duration=ex.reps,
            streak_days=current_user.streak_days,
            first_of_day=True  # предполагаем
        )
        total_xp += xp

    return {"estimated_xp": total_xp}
```

**Результат**:
- ✅ Пользователь видит точный или честный примерный XP
- ✅ Нет расхождений между frontend и backend
- ✅ Упрощение логики workout store

---

### 2.3 Устранение N+1 Запросов

**Проблема**: В `get_friends_leaderboard()` происходят N+1 запросы.

```python
# backend/app/api/routes/leaderboard.py

# ❌ БЫЛО:
@router.get("/friends")
async def get_friends_leaderboard(...):
    friendships = await db.execute(
        select(Friendship).where(...)
    )

    leaderboard = []
    for friendship in friendships.scalars():
        friend = await db.get(User, friendship.friend_id)  # ← N+1!
        leaderboard.append({...})

# ✅ СТАЛО:
@router.get("/friends")
async def get_friends_leaderboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Leaderboard среди друзей с оптимизированным запросом"""

    # Один JOIN запрос вместо N+1
    stmt = (
        select(User)
        .join(
            Friendship,
            (Friendship.friend_id == User.id) & (Friendship.user_id == current_user.id)
            | (Friendship.user_id == User.id) & (Friendship.friend_id == current_user.id)
        )
        .where(Friendship.status == "accepted")
        .order_by(User.total_xp.desc())
        .limit(50)
    )

    result = await db.execute(stmt)
    friends = result.scalars().all()

    # Добавить себя в список
    friends_with_me = [current_user] + list(friends)
    friends_with_me.sort(key=lambda u: u.total_xp, reverse=True)

    return [
        LeaderboardEntry(
            rank=idx + 1,
            user_id=user.id,
            telegram_id=user.telegram_id,
            username=user.username or "Пользователь",
            total_xp=user.total_xp,
            level=user.level,
            avatar_id=user.avatar_id,
            is_current_user=(user.id == current_user.id)
        )
        for idx, user in enumerate(friends_with_me)
    ]
```

**Результат**:
- ✅ 1 запрос вместо N+1
- ✅ Ускорение загрузки leaderboard в N раз

---

### 2.4 Добавление Кэширования

```python
# backend/app/utils/cache.py (НОВЫЙ ФАЙЛ)

from functools import lru_cache, wraps
from typing import Callable, Any
import time

def timed_cache(seconds: int = 300):
    """Decorator для кэширования с TTL"""
    def decorator(func: Callable) -> Callable:
        cache = {}
        cache_time = {}

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Создать ключ кэша
            cache_key = str(args) + str(kwargs)

            # Проверить наличие и срок действия
            if cache_key in cache:
                if time.time() - cache_time[cache_key] < seconds:
                    return cache[cache_key]

            # Выполнить функцию
            result = await func(*args, **kwargs)

            # Сохранить в кэш
            cache[cache_key] = result
            cache_time[cache_key] = time.time()

            return result

        return wrapper
    return decorator
```

```python
# backend/app/api/routes/exercises.py

from app.utils.cache import timed_cache

@router.get("")
@timed_cache(seconds=300)  # Кэш на 5 минут
async def get_exercises(
    db: AsyncSession = Depends(get_db)
):
    """Получение всех упражнений с кэшированием"""
    stmt = select(Exercise).order_by(Exercise.name)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/categories")
@timed_cache(seconds=600)  # Кэш на 10 минут
async def get_categories(
    db: AsyncSession = Depends(get_db)
):
    """Получение категорий с кэшированием"""
    stmt = select(ExerciseCategory).order_by(ExerciseCategory.sort_order)
    result = await db.execute(stmt)
    return result.scalars().all()
```

**Альтернатива (Redis)**:
```python
# backend/app/config.py
redis_url: str = "redis://localhost:6379"

# backend/app/main.py
from redis.asyncio import Redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.redis = Redis.from_url(settings.redis_url)
    yield
    # Shutdown
    await app.state.redis.close()

# backend/app/api/routes/exercises.py
@router.get("")
async def get_exercises(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    # Проверить кэш
    cached = await request.app.state.redis.get("exercises:all")
    if cached:
        return json.loads(cached)

    # Запрос к БД
    result = await db.execute(select(Exercise))
    exercises = result.scalars().all()

    # Сохранить в кэш на 5 минут
    await request.app.state.redis.setex(
        "exercises:all",
        300,
        json.dumps([ex.dict() for ex in exercises])
    )

    return exercises
```

**Результат**:
- ✅ Exercises кэшируются на 5 минут
- ✅ Categories кэшируются на 10 минут
- ✅ Achievements кэшируются навсегда (@lru_cache)
- ✅ Снижение нагрузки на БД

---

## Фаза 3: Улучшение Качества Кода

**Длительность**: 3-4 дня
**Приоритет**: 🟢 СРЕДНИЙ

### 3.1 Унификация Response Models

```python
# backend/app/schemas/user.py (НОВЫЙ ФАЙЛ)

from pydantic import BaseModel
from datetime import datetime

class UserBase(BaseModel):
    telegram_id: int
    username: str | None
    first_name: str | None
    last_name: str | None

class UserResponse(UserBase):
    id: int
    level: int
    total_xp: int
    coins: int
    streak_days: int
    avatar_id: int
    is_onboarded: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserStatsResponse(BaseModel):
    total_xp: int
    total_workouts: int
    total_reps: int
    total_time_minutes: int
    current_streak: int
    longest_streak: int
    level: int
    xp_to_next_level: int
    xp_progress_percent: float
    favorite_exercise: str | None
    favorite_category: str | None
```

```python
# backend/app/api/routes/auth.py
# ❌ УДАЛИТЬ: class UserResponse

# ✅ ИМПОРТИРОВАТЬ:
from app.schemas.user import UserResponse

# backend/app/api/routes/users.py
# ✅ ИСПОЛЬЗОВАТЬ ту же схему:
from app.schemas.user import UserResponse, UserStatsResponse
```

**Создать Единые Схемы**:
```
backend/app/schemas/
├── user.py          # UserResponse, UserStatsResponse, etc.
├── exercise.py      # ExerciseResponse, ExerciseCategoryResponse
├── workout.py       # WorkoutSessionResponse, SubmitWorkoutRequest, etc.
├── achievement.py   # AchievementResponse, UserAchievementResponse
├── leaderboard.py   # LeaderboardEntry
└── __init__.py
```

**Результат**:
- ✅ Единая точка определения схем
- ✅ Упрощение импортов
- ✅ Улучшение поддерживаемости

---

### 3.2 Синхронизация TypeScript Типов

```typescript
// frontend/mini-app/src/lib/types.ts

// ✅ СИНХРОНИЗИРОВАТЬ с backend/app/schemas/user.py
export interface UserStats {
  total_xp: number;
  total_workouts: number;
  total_reps: number;
  total_time_minutes: number;
  current_streak: number;
  longest_streak: number;
  level: number;
  xp_to_next_level: number;
  xp_progress_percent: number;
  favorite_exercise: string | null;
  favorite_category: string | null;
}
```

**Автоматическая Генерация (опционально)**:
```bash
# Установить openapi-typescript
npm install -D openapi-typescript

# Сгенерировать типы из OpenAPI схемы
npx openapi-typescript http://localhost:8000/openapi.json -o src/lib/api/schema.d.ts
```

```typescript
// frontend/mini-app/src/lib/api/client.ts
import type { paths } from './schema';

type GetExercisesResponse = paths['/api/exercises']['get']['responses']['200']['content']['application/json'];
```

**Результат**:
- ✅ 100% соответствие Frontend ↔ Backend типов
- ✅ Автоматическая синхронизация при изменении API

---

### 3.3 Добавление Пагинации

```python
# backend/app/api/routes/exercises.py

from fastapi import Query

@router.get("")
async def get_exercises(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Получение упражнений с пагинацией"""

    # Общее количество
    count_stmt = select(func.count()).select_from(Exercise)
    total = await db.scalar(count_stmt)

    # Постраничный запрос
    stmt = (
        select(Exercise)
        .order_by(Exercise.name)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    exercises = result.scalars().all()

    return {
        "items": exercises,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": skip + limit < total
    }
```

```python
# backend/app/api/routes/workouts.py

@router.get("/history")
async def get_workout_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """История тренировок с пагинацией"""

    count_stmt = (
        select(func.count())
        .select_from(WorkoutSession)
        .where(WorkoutSession.user_id == current_user.id)
    )
    total = await db.scalar(count_stmt)

    stmt = (
        select(WorkoutSession)
        .where(WorkoutSession.user_id == current_user.id)
        .order_by(WorkoutSession.finished_at.desc())
        .offset(skip)
        .limit(limit)
        .options(selectinload(WorkoutSession.exercises))
    )
    result = await db.execute(stmt)
    sessions = result.scalars().all()

    return {
        "items": sessions,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": skip + limit < total
    }
```

**Результат**:
- ✅ Снижение нагрузки на БД и сеть
- ✅ Быстрая загрузка больших списков
- ✅ Улучшение UX (infinite scroll)

---

### 3.4 Добавление Индексов БД

```python
# backend/alembic/versions/xxx_add_performance_indexes.py

def upgrade():
    # Индекс для запросов друзей по статусу
    op.create_index(
        'ix_friendship_user_status',
        'friendships',
        ['user_id', 'status']
    )

    # Индекс для истории тренировок
    op.create_index(
        'ix_workout_sessions_user_finished',
        'workout_sessions',
        ['user_id', 'finished_at']
    )

    # Индекс для поиска достижений пользователя
    op.create_index(
        'ix_user_achievements_user_unlocked',
        'user_achievements',
        ['user_id', 'unlocked_at']
    )

    # Индекс для целей пользователя
    op.create_index(
        'ix_user_goals_user_completed',
        'user_goals',
        ['user_id', 'completed', 'end_date']
    )

def downgrade():
    op.drop_index('ix_friendship_user_status')
    op.drop_index('ix_workout_sessions_user_finished')
    op.drop_index('ix_user_achievements_user_unlocked')
    op.drop_index('ix_user_goals_user_completed')
```

**Результат**:
- ✅ Ускорение частых запросов
- ✅ Улучшение производительности БД

---

### 3.5 Условное Логирование

```python
# backend/app/api/routes/leaderboard.py

# ❌ БЫЛО:
logger.warning(f"Found {len(top_users)} users")
logger.info(f"Processing user {user.id}")

# ✅ СТАЛО:
from app.config import settings

if settings.debug:
    logger.debug(f"Found {len(top_users)} users")
    logger.debug(f"Processing user {user.id}")

# Или использовать уровень logger:
logger.debug(f"Found {len(top_users)} users")  # Не будет в production
```

```python
# backend/app/config.py

class Settings(BaseSettings):
    debug: bool = False
    log_level: str = "INFO"  # DEBUG в dev, INFO в prod
```

```python
# backend/app/main.py

import logging

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

**Результат**:
- ✅ Чистые логи в production
- ✅ Детальные логи в development

---

## Фаза 4: Документация и Тестирование

**Длительность**: 2-3 дня
**Приоритет**: 🟢 СРЕДНИЙ

### 4.1 API Документация

```python
# backend/app/main.py

app = FastAPI(
    title="BodyWeight Fitness API",
    description="API для Telegram Mini App фитнес-трекера с геймификацией",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)
```

```python
# backend/app/api/routes/workouts.py

@router.post("/submit",
    summary="Завершить тренировку",
    description="""
    Единственный эндпоинт для завершения тренировки.

    Принимает все данные о тренировке сразу:
    - Время начала и окончания
    - Список упражнений с повторениями/подходами

    Автоматически:
    - Рассчитывает XP и монеты
    - Обновляет streak
    - Проверяет достижения
    - Обновляет цели
    - Создаёт уведомления
    """,
    response_description="Результаты тренировки с наградами",
    tags=["Workouts"]
)
async def submit_workout(...):
    ...
```

**Создать README для API**:
```markdown
# BodyWeight API

## Аутентификация

Все запросы требуют заголовок:
```
Authorization: tma <telegram_init_data>
```

## Основные Эндпоинты

### Тренировки

**POST /api/workouts/submit** - Завершить тренировку
```json
{
  "started_at": "2024-12-30T10:00:00Z",
  "finished_at": "2024-12-30T10:30:00Z",
  "exercises": [
    {
      "exercise_slug": "pushup-regular",
      "reps": 50,
      "sets": 3
    }
  ]
}
```

**Ответ**:
```json
{
  "workout_session_id": 123,
  "total_xp": 250,
  "total_coins": 2,
  "level_up": true,
  "new_level": 5,
  "new_achievements": ["first-workout"],
  "streak": 7
}
```

...
```

---

### 4.2 Unit Тесты

```python
# backend/tests/test_workout_processor.py

import pytest
from datetime import datetime, timedelta
from app.services.workout_processor import process_workout_completion, WorkoutCompletionData
from app.db.models import User, Exercise, WorkoutSession

@pytest.mark.asyncio
async def test_workout_completion_basic(db_session):
    """Тест базового завершения тренировки"""

    # Создать пользователя
    user = User(
        telegram_id=12345,
        username="testuser",
        level=1,
        total_xp=0,
        coins=0,
        streak_days=0
    )
    db_session.add(user)
    await db_session.flush()

    # Создать упражнение
    exercise = Exercise(
        slug="pushup-regular",
        name="Push-up",
        base_xp=10,
        difficulty=2
    )
    db_session.add(exercise)
    await db_session.flush()

    # Создать сессию
    session = WorkoutSession(
        user_id=user.id,
        started_at=datetime.utcnow() - timedelta(minutes=30)
    )
    db_session.add(session)
    await db_session.flush()

    # Подготовить данные
    data = WorkoutCompletionData(
        session_id=session.id,
        user_id=user.id,
        exercises=[
            {"exercise_slug": "pushup-regular", "reps": 20, "sets": 3}
        ],
        started_at=session.started_at,
        finished_at=datetime.utcnow()
    )

    # Выполнить обработку
    result = await process_workout_completion(data, db_session)

    # Проверить результаты
    assert result["total_xp"] > 0
    assert result["total_coins"] >= 0
    assert result["streak"] == 1

    # Проверить обновление пользователя
    await db_session.refresh(user)
    assert user.total_xp > 0
    assert user.level >= 1


@pytest.mark.asyncio
async def test_workout_goal_update(db_session):
    """Тест обновления целей после тренировки"""

    user = User(...)
    db_session.add(user)
    await db_session.flush()

    # Создать цель
    goal = UserGoal(
        user_id=user.id,
        goal_type="total_workouts",
        target_value=10,
        current_value=0,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30)
    )
    db_session.add(goal)
    await db_session.flush()

    # Завершить тренировку
    data = WorkoutCompletionData(...)
    result = await process_workout_completion(data, db_session)

    # Проверить обновление цели
    await db_session.refresh(goal)
    assert goal.current_value == 1
    assert goal.completed == False


@pytest.mark.asyncio
async def test_workout_level_up(db_session):
    """Тест повышения уровня"""

    user = User(
        total_xp=90,  # Близко к level 2 (требуется 100 XP)
        level=1
    )
    db_session.add(user)
    await db_session.flush()

    # Завершить тренировку с достаточным XP
    data = WorkoutCompletionData(...)
    result = await process_workout_completion(data, db_session)

    # Проверить level up
    assert result["level_up"] == True
    assert result["new_level"] == 2
    await db_session.refresh(user)
    assert user.level == 2
    assert user.coins > 0  # Получены бонусные монеты
```

**Результат**:
- ✅ Покрытие критичных функций тестами
- ✅ Уверенность в корректности рефакторинга
- ✅ Предотвращение регрессий

---

### 4.3 Проверка Неиспользуемых Компонентов

```bash
# Скрипт для поиска неиспользуемых компонентов
# frontend/scripts/find-unused-components.sh

#!/bin/bash

echo "Checking component usage..."

for file in frontend/mini-app/src/lib/components/*.svelte; do
    component=$(basename "$file" .svelte)

    # Поиск импортов компонента
    usage_count=$(grep -r "import.*$component" frontend/mini-app/src --include="*.svelte" --include="*.ts" | wc -l)

    if [ $usage_count -eq 0 ]; then
        echo "⚠️  UNUSED: $component"
    else
        echo "✅ USED ($usage_count): $component"
    fi
done
```

**Результат анализа**:
```
✅ USED (3): CustomRoutineEditor
✅ USED (2): CustomRoutineList
✅ USED (5): ExerciseCard
✅ USED (2): ExerciseInfoModal
✅ USED (1): FilterModal
✅ USED (1): OnboardingScreen
✅ USED (1): OnboardingSlides
⚠️  UNUSED: QuickExerciseModal  ← КАНДИДАТ НА УДАЛЕНИЕ
✅ USED (4): RoutinePlayer
✅ USED (1): UserProfileModal
```

**Действия**:
```bash
# Если компонент действительно не используется:
rm frontend/mini-app/src/lib/components/QuickExerciseModal.svelte
```

---

## Риски и Митигация

### Риск 1: Поломка Существующего Функционала

**Вероятность**: Средняя
**Влияние**: Высокое

**Митигация**:
1. ✅ Создать comprehensive тесты ПЕРЕД рефакторингом
2. ✅ Использовать feature flags для постепенного перехода
3. ✅ Сохранить старые эндпоинты как deprecated на 1-2 недели
4. ✅ Полное тестирование на staging окружении

```python
# Пример feature flag
from app.config import settings

@router.post("/submit")
async def submit_workout(...):
    if not settings.feature_new_workout_flow:
        raise HTTPException(503, "New workflow not enabled")
    ...

# Старые эндпоинты помечаем deprecated
@router.post("/{workout_id}/complete", deprecated=True)
async def complete_workout(...):
    logger.warning("Using deprecated endpoint /complete")
    ...
```

---

### Риск 2: Потеря Данных При Миграции БД

**Вероятность**: Низкая
**Влияние**: Критическое

**Митигация**:
1. ✅ Создать полный backup БД перед миграцией
2. ✅ Тестировать миграции на копии production данных
3. ✅ Использовать транзакции в alembic
4. ✅ Иметь rollback план

```bash
# Backup перед миграцией
sqlite3 database.db .dump > backup_$(date +%Y%m%d_%H%M%S).sql

# Тест миграции
alembic upgrade head --sql > migration.sql  # Проверить SQL
alembic upgrade head  # Применить

# Rollback в случае проблем
alembic downgrade -1
```

---

### Риск 3: Увеличение Времени Разработки

**Вероятность**: Высокая
**Влияние**: Среднее

**Митигация**:
1. ✅ Чёткое планирование и приоритизация (этот документ!)
2. ✅ Разбиение на small incremental changes
3. ✅ Параллельная работа над независимыми задачами
4. ✅ Ограничение scope - не добавлять новые фичи во время рефакторинга

---

### Риск 4: Несовместимость Frontend ↔ Backend

**Вероятность**: Средняя
**Влияние**: Высокое

**Митигация**:
1. ✅ Версионирование API (`/api/v1`, `/api/v2`)
2. ✅ Backwards compatibility период
3. ✅ Integration тесты Frontend + Backend
4. ✅ Автогенерация TypeScript типов из OpenAPI

```python
# Версионирование API
from fastapi import APIRouter

v1_router = APIRouter(prefix="/api/v1")
v2_router = APIRouter(prefix="/api/v2")

# v2 - новая логика
@v2_router.post("/workouts/submit")
async def submit_workout_v2(...):
    ...

# v1 - старая логика (deprecated)
@v1_router.post("/workouts")
async def create_workout_v1(...):
    ...
```

---

## Чеклист Выполнения

### Фаза 1: Критические Исправления ✅

- [ ] 1.1 Удалить дублирование workout completion
  - [ ] Создать `backend/app/services/workout_processor.py`
  - [ ] Реализовать `process_workout_completion()`
  - [ ] Упростить `workouts.py` до 1 эндпоинта
  - [ ] Удалить старые эндпоинты
  - [ ] Обновить frontend API client
  - [ ] Написать тесты
  - [ ] Протестировать на staging

- [ ] 1.2 Реализовать обновление UserGoal
  - [ ] Добавить `_update_user_goals()` в processor
  - [ ] Создать эндпоинт `/goals/progress`
  - [ ] Обновить frontend для отображения прогресса
  - [ ] Написать тесты

- [ ] 1.3 Устранить дублирование load_achievements()
  - [ ] Создать `backend/app/utils/achievement_loader.py`
  - [ ] Обновить импорты в achievement_checker.py
  - [ ] Обновить импорты в routes/achievements.py
  - [ ] Добавить @lru_cache

### Фаза 2: Оптимизация Производительности ✅

- [ ] 2.1 Изолировать Mock Data
  - [ ] Создать `frontend/mini-app/src/lib/api/mock-data.dev.ts`
  - [ ] Переместить все MOCK_* константы
  - [ ] Обновить client.ts с условным импортом
  - [ ] Добавить env переменную VITE_USE_MOCKS

- [ ] 2.2 Исправить расчёт XP на frontend
  - [ ] Удалить или пометить как estimated
  - [ ] ИЛИ создать `/workouts/preview` эндпоинт
  - [ ] Обновить UI с пояснениями

- [ ] 2.3 Устранить N+1 запросы
  - [ ] Оптимизировать `get_friends_leaderboard()`
  - [ ] Добавить JOIN запросы
  - [ ] Проверить другие эндпоинты

- [ ] 2.4 Добавить кэширование
  - [ ] Создать `backend/app/utils/cache.py`
  - [ ] Добавить @timed_cache для exercises
  - [ ] Добавить @timed_cache для categories
  - [ ] Проверить load_achievements кэш

### Фаза 3: Качество Кода ✅

- [ ] 3.1 Унифицировать Response Models
  - [ ] Создать `backend/app/schemas/`
  - [ ] Переместить все схемы
  - [ ] Обновить импорты

- [ ] 3.2 Синхронизировать TypeScript типы
  - [ ] Обновить `frontend/mini-app/src/lib/types.ts`
  - [ ] ИЛИ настроить автогенерацию из OpenAPI

- [ ] 3.3 Добавить пагинацию
  - [ ] `/exercises` с skip/limit
  - [ ] `/workouts/history` с skip/limit
  - [ ] `/achievements` с skip/limit
  - [ ] Обновить frontend для infinite scroll

- [ ] 3.4 Добавить индексы БД
  - [ ] Создать alembic миграцию
  - [ ] Добавить индексы на часто запрашиваемые поля
  - [ ] Применить миграцию

- [ ] 3.5 Условное логирование
  - [ ] Заменить logger.warning/info на logger.debug
  - [ ] Настроить уровни логирования

### Фаза 4: Документация ✅

- [ ] 4.1 API Документация
  - [ ] Добавить описания всех эндпоинтов
  - [ ] Создать README_API.md
  - [ ] Проверить Swagger UI

- [ ] 4.2 Unit Тесты
  - [ ] Тесты для workout_processor
  - [ ] Тесты для goal updates
  - [ ] Тесты для achievement checking
  - [ ] Покрытие > 70%

- [ ] 4.3 Проверить неиспользуемые компоненты
  - [ ] Запустить скрипт поиска
  - [ ] Удалить неиспользуемые

---

## Метрики Успеха

После завершения рефакторинга проект должен соответствовать:

| Критерий | Цель | Метод Проверки |
|----------|------|----------------|
| Строк кода в workouts.py | < 500 | `wc -l workouts.py` |
| Дублированного кода | 0% | Manual review |
| Покрытие тестами | > 70% | `pytest --cov` |
| Время ответа API | < 200ms | Load testing |
| Кэшированных ресурсов | 3+ | Check cache hits |
| N+1 запросов | 0 | SQL query logging |
| API версия | 2.0.0 | OpenAPI spec |
| Документация | 100% endpoints | Swagger UI |

---

## Заключение

Этот план рефакторинга рассчитан на **10-14 рабочих дней** (2-3 недели).

**Ожидаемые Результаты**:
- 🎯 -500 строк неиспользуемого кода
- 🚀 Улучшение производительности на 30-50%
- 🧹 Чистая и поддерживаемая кодовая база
- ✅ Полностью работающий функционал целей
- 📚 Полная документация API
- 🧪 Покрытие тестами > 70%

**Следующие Шаги**:
1. ✅ Утвердить план
2. 🔧 Создать feature branch `refactoring/phase-1`
3. 📝 Начать с Фазы 1, задача 1.1
4. 🔄 Code review после каждой задачи
5. 🚀 Deploy в staging после каждой фазы
6. ✨ Финальный релиз после Фазы 4

---

**Версия**: 1.0
**Дата**: 30.12.2024
**Автор**: Claude Code Review
**Статус**: ✅ Готов к выполнению
