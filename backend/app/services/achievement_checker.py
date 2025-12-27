import json
from datetime import datetime
from pathlib import Path
from typing import List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, UserAchievement, WorkoutSession, UserExerciseProgress


def load_achievements() -> dict:
    """Load achievements definitions from JSON file."""
    achievements_path = Path(__file__).parent.parent / "data" / "achievements.json"
    if achievements_path.exists():
        with open(achievements_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"achievements": []}


async def check_achievements(
    session: AsyncSession,
    user: User,
) -> List[dict]:
    """
    Check and unlock achievements for a user.

    Returns list of newly unlocked achievements.
    """
    achievements_data = load_achievements()
    newly_unlocked = []

    # Get already unlocked achievements
    result = await session.execute(
        select(UserAchievement.achievement_slug)
        .where(UserAchievement.user_id == user.id)
    )
    unlocked_slugs = set(row[0] for row in result.fetchall())

    for achievement in achievements_data.get("achievements", []):
        slug = achievement["slug"]

        # Skip if already unlocked
        if slug in unlocked_slugs:
            continue

        # Check condition
        condition = achievement.get("condition", {})
        condition_type = condition.get("type")
        condition_value = condition.get("value", 0)

        unlocked = False

        if condition_type == "total_workouts":
            count_result = await session.execute(
                select(func.count(WorkoutSession.id))
                .where(WorkoutSession.user_id == user.id)
                .where(WorkoutSession.status == "completed")
            )
            count = count_result.scalar() or 0
            unlocked = count >= condition_value

        elif condition_type == "streak":
            unlocked = user.current_streak >= condition_value

        elif condition_type == "level":
            unlocked = user.level >= condition_value

        elif condition_type == "total_xp":
            unlocked = user.total_xp >= condition_value

        elif condition_type == "exercise_reps":
            # Count total reps for matching exercises
            exercise_pattern = condition.get("exercise", "")
            if exercise_pattern.endswith("*"):
                # Wildcard match
                prefix = exercise_pattern[:-1]
                reps_result = await session.execute(
                    select(func.sum(UserExerciseProgress.total_reps_ever))
                    .join(UserExerciseProgress.exercise)
                    .where(UserExerciseProgress.user_id == user.id)
                    .where(UserExerciseProgress.exercise.has(slug=prefix))  # Simplified
                )
            else:
                reps_result = await session.execute(
                    select(func.sum(UserExerciseProgress.total_reps_ever))
                    .join(UserExerciseProgress.exercise)
                    .where(UserExerciseProgress.user_id == user.id)
                    .where(UserExerciseProgress.exercise.has(slug=exercise_pattern))
                )
            total_reps = reps_result.scalar() or 0
            unlocked = total_reps >= condition_value

        elif condition_type == "time_of_day":
            # Check if last workout was before/after specific time
            before_time = condition.get("before")
            after_time = condition.get("after")

            last_workout_result = await session.execute(
                select(WorkoutSession)
                .where(WorkoutSession.user_id == user.id)
                .where(WorkoutSession.status == "completed")
                .order_by(WorkoutSession.finished_at.desc())
                .limit(1)
            )
            last_workout = last_workout_result.scalar_one_or_none()

            if last_workout and last_workout.finished_at:
                workout_time = last_workout.finished_at.time()
                if before_time:
                    target_time = datetime.strptime(before_time, "%H:%M").time()
                    unlocked = workout_time < target_time
                elif after_time:
                    target_time = datetime.strptime(after_time, "%H:%M").time()
                    unlocked = workout_time > target_time

        if unlocked:
            # Create achievement record
            user_achievement = UserAchievement(
                user_id=user.id,
                achievement_slug=slug,
            )
            session.add(user_achievement)

            # Award XP and coins
            xp_reward = achievement.get("xp_reward", 0)
            coin_reward = achievement.get("coin_reward", 0)
            user.total_xp += xp_reward
            user.coins += coin_reward

            newly_unlocked.append(achievement)

    return newly_unlocked
