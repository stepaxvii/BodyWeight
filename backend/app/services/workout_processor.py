"""
Workout completion processor - unified logic for processing completed workouts.

This module contains the core business logic for completing workouts:
- XP and coins calculation
- Streak updates
- Level progression
- Achievement checking
- Goal updates
- Notification creation
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Any
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import (
    User,
    WorkoutSession,
    WorkoutExercise,
    Exercise,
    UserExerciseProgress,
    Notification,
    UserGoal,
)
from app.services.xp_calculator import (
    calculate_xp,
    calculate_coins,
    get_level_from_xp,
    get_streak_multiplier,
)
from app.services.achievement_checker import check_achievements
from app.services.notifications import save_notification


@dataclass
class ExerciseSetData:
    """Data for a single exercise in a completed workout."""
    exercise_slug: str
    sets: List[int]  # Array of reps per set (or seconds for timed exercises)
    is_timed: bool = False


@dataclass
class WorkoutCompletionData:
    """DTO for workout completion data."""
    user_id: int
    started_at: datetime
    finished_at: datetime
    exercises: List[ExerciseSetData]
    workout_session_id: int | None = None  # If None, will create new session


@dataclass
class WorkoutCompletionResult:
    """Result of workout completion processing."""
    workout_session_id: int
    total_xp: int
    total_coins: int
    level_up: bool
    old_level: int
    new_level: int
    new_achievements: List[Dict[str, Any]]
    streak: int
    workout_summary: Dict[str, Any]


async def process_workout_completion(
    data: WorkoutCompletionData,
    session: AsyncSession,
) -> WorkoutCompletionResult:
    """
    Process a completed workout - unified function for all workout completion logic.

    This function handles:
    - Creating/updating workout session
    - Calculating XP and coins for each exercise
    - Updating user stats (XP, coins, level, streak)
    - Updating exercise progress
    - Checking and granting achievements
    - Updating user goals
    - Creating notifications

    Args:
        data: Workout completion data
        session: Database session

    Returns:
        WorkoutCompletionResult with all processing results
    """
    # 1. Get user
    user = await session.get(User, data.user_id)
    if not user:
        raise ValueError(f"User {data.user_id} not found")

    # 2. Check if first workout today
    today = date.today()
    is_first_today = user.last_workout_date != today

    # 3. Calculate streak multiplier
    streak_mult = get_streak_multiplier(user.current_streak)

    # 4. Create or get workout session
    if data.workout_session_id:
        workout = await session.get(WorkoutSession, data.workout_session_id)
        if not workout:
            raise ValueError(f"Workout session {data.workout_session_id} not found")
        workout.finished_at = data.finished_at
        workout.duration_seconds = int((data.finished_at - data.started_at).total_seconds())
        workout.status = "completed"
    else:
        workout = WorkoutSession(
            user_id=user.id,
            started_at=data.started_at,
            finished_at=data.finished_at,
            duration_seconds=int((data.finished_at - data.started_at).total_seconds()),
            streak_multiplier=streak_mult,
            status="completed",
            total_xp_earned=0,
            total_coins_earned=0,
            total_reps=0,
            total_duration_seconds=0,
        )
        session.add(workout)
        await session.flush()

    # 5. Process each exercise
    total_xp = 0
    total_coins = 0
    workout_exercises = []

    for ex_data in data.exercises:
        # Get exercise from DB
        exercise_result = await session.execute(
            select(Exercise).where(Exercise.slug == ex_data.exercise_slug)
        )
        exercise = exercise_result.scalar_one_or_none()

        if not exercise:
            continue  # Skip unknown exercises

        # Calculate totals
        total_value = sum(ex_data.sets)
        sets_count = len(ex_data.sets)

        if ex_data.is_timed:
            total_reps = 0
            total_duration = total_value
            xp_value = max(1, total_duration // 10)  # 10 sec = 1 rep equivalent
        else:
            total_reps = total_value
            total_duration = 0
            xp_value = total_reps

        # Calculate XP
        xp_earned = calculate_xp(
            base_xp=exercise.base_xp,
            difficulty=exercise.difficulty,
            reps=xp_value,
            streak_days=user.current_streak,
            is_first_today=is_first_today,
        )

        # Create workout exercise entry
        workout_exercise = WorkoutExercise(
            workout_session_id=workout.id,
            exercise_id=exercise.id,
            sets_completed=sets_count,
            total_reps=total_reps,
            total_duration_seconds=total_duration,
            xp_earned=xp_earned,
            coins_earned=0,
        )
        session.add(workout_exercise)
        workout_exercises.append(workout_exercise)

        # Update workout totals
        workout.total_xp_earned += xp_earned
        workout.total_reps += total_reps
        workout.total_duration_seconds += total_duration

        total_xp += xp_earned

        # Update user exercise progress
        progress_result = await session.execute(
            select(UserExerciseProgress)
            .where(UserExerciseProgress.user_id == user.id)
            .where(UserExerciseProgress.exercise_id == exercise.id)
        )
        progress = progress_result.scalar_one_or_none()

        best_set = max(ex_data.sets) if ex_data.sets else 0

        if progress:
            progress.total_reps_ever += total_reps
            progress.times_performed += 1
            if not ex_data.is_timed:
                progress.best_single_set = max(progress.best_single_set, best_set)
            progress.last_performed_at = data.finished_at

            if progress.total_reps_ever >= 100 and exercise.harder_exercise_id:
                progress.recommended_upgrade = True
        else:
            progress = UserExerciseProgress(
                user_id=user.id,
                exercise_id=exercise.id,
                total_reps_ever=total_reps,
                best_single_set=best_set if not ex_data.is_timed else 0,
                times_performed=1,
                last_performed_at=data.finished_at,
            )
            session.add(progress)

    # 6. Calculate coins
    workout_duration_minutes = workout.duration_seconds // 60 if workout.duration_seconds else 0
    coins_earned = calculate_coins(
        xp_earned=total_xp,
        streak_days=user.current_streak,
        workout_duration_minutes=workout_duration_minutes
    )
    workout.total_coins_earned = coins_earned
    total_coins = coins_earned

    # 7. Update user stats
    old_level = user.level
    user.total_xp += total_xp
    user.coins += coins_earned

    # 8. Update level
    new_level = get_level_from_xp(user.total_xp)
    user.level = new_level
    level_up = new_level > old_level

    # Award bonus coins for level up (5 coins per level gained)
    if level_up:
        levels_gained = new_level - old_level
        level_up_bonus = levels_gained * 5
        user.coins += level_up_bonus
        workout.total_coins_earned += level_up_bonus
        total_coins += level_up_bonus

    # 9. Update streak
    if user.last_workout_date is None:
        user.current_streak = 1
    elif user.last_workout_date == today - timedelta(days=1):
        user.current_streak += 1
    elif user.last_workout_date != today:
        user.current_streak = 1

    user.max_streak = max(user.max_streak, user.current_streak)
    user.last_workout_date = today

    await session.flush()

    # 10. Update user goals
    await _update_user_goals(user.id, data, workout, session)

    # 11. Check achievements
    new_achievements = await check_achievements(session, user)

    # Note: Coins and XP from achievements are already awarded in check_achievements()
    # We just track them in workout summary for display
    if new_achievements:
        bonus_coins = sum(a.get("coin_reward", 0) for a in new_achievements)
        # Add to workout total for display, but don't add to user.coins again
        # (already added in check_achievements)
        workout.total_coins_earned += bonus_coins
        total_coins += bonus_coins

    await session.flush()

    # 12. Create notifications
    if level_up:
        await save_notification(
            session=session,
            user_id=user.id,
            notification_type="level_up",
            title="Новый уровень!",
            message=f"Поздравляем! Ты достиг {new_level} уровня!",
        )

    for achievement in new_achievements:
        await save_notification(
            session=session,
            user_id=user.id,
            notification_type="achievement",
            title="Новое достижение!",
            message=f"Получено: {achievement.get('name_ru', achievement.get('name', 'Достижение'))}",
        )

    await session.flush()

    # 13. Prepare summary
    workout_summary = {
        "total_exercises": len(data.exercises),
        "total_reps": workout.total_reps,
        "total_sets": sum(len(ex.sets) for ex in data.exercises),
        "duration_minutes": workout_duration_minutes,
        "duration_seconds": workout.duration_seconds,
    }

    return WorkoutCompletionResult(
        workout_session_id=workout.id,
        total_xp=total_xp,
        total_coins=total_coins,
        level_up=level_up,
        old_level=old_level,
        new_level=new_level,
        new_achievements=new_achievements,
        streak=user.current_streak,
        workout_summary=workout_summary,
    )


async def _update_user_goals(
    user_id: int,
    data: WorkoutCompletionData,
    workout: WorkoutSession,
    session: AsyncSession,
) -> None:
    """Update user goals based on completed workout."""
    today = date.today()

    goals_result = await session.execute(
        select(UserGoal)
        .where(UserGoal.user_id == user_id)
        .where(UserGoal.completed == False)
        .where(UserGoal.end_date >= today)
    )
    active_goals = goals_result.scalars().all()

    for goal in active_goals:
        old_value = goal.current_value

        if goal.goal_type == "total_workouts":
            goal.current_value += 1
        elif goal.goal_type == "total_reps":
            goal.current_value += workout.total_reps
        elif goal.goal_type == "total_xp":
            goal.current_value += workout.total_xp_earned
        elif goal.goal_type == "workout_streak":
            user = await session.get(User, user_id)
            if user:
                goal.current_value = user.current_streak
        elif goal.goal_type.startswith("exercise_"):
            # Format: exercise_{slug}_{metric}
            parts = goal.goal_type.split("_", 2)
            if len(parts) >= 3:
                target_slug = parts[1]
                metric = parts[2] if len(parts) > 2 else "reps"

                for ex_data in data.exercises:
                    if ex_data.exercise_slug == target_slug:
                        if metric == "reps":
                            goal.current_value += sum(ex_data.sets)
                        elif metric == "sets":
                            goal.current_value += len(ex_data.sets)
                        elif metric == "times":
                            goal.current_value += 1
                        break

        # Check if goal completed
        if goal.current_value >= goal.target_value and not goal.completed:
            goal.completed = True
            goal.completed_at = data.finished_at

            # Create notification
            await save_notification(
                session=session,
                user_id=user_id,
                notification_type="goal_completed",
                title="Цель достигнута!",
                message=f"Цель выполнена: {goal.target_value} {goal.goal_type}",
            )

            # Award bonus coins
            user = await session.get(User, user_id)
            if user:
                bonus_goal_coins = 5
                user.coins += bonus_goal_coins
                workout.total_coins_earned += bonus_goal_coins

