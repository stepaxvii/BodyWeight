from datetime import datetime, date, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.api.deps import AsyncSessionDep, CurrentUser
from app.db.models import (
    WorkoutSession,
    WorkoutExercise,
    Exercise,
    UserExerciseProgress,
    Notification,
)
from app.services.xp_calculator import (
    calculate_xp,
    calculate_coins,
    get_level_from_xp,
    get_streak_multiplier,
)
from app.services.achievement_checker import check_achievements

router = APIRouter()


class AddExerciseRequest(BaseModel):
    exercise_slug: str
    reps: int = 0  # For rep-based exercises
    duration_seconds: int = 0  # For time-based exercises
    sets: int = 1


class ExerciseSetData(BaseModel):
    """Data for a single exercise in a completed workout."""
    exercise_slug: str
    sets: List[int]  # Array of reps per set (or seconds for timed exercises)
    is_timed: bool = False


class CompleteWorkoutRequest(BaseModel):
    """Request body for completing a workout with all exercise data."""
    duration_seconds: int
    exercises: List[ExerciseSetData]


class WorkoutExerciseResponse(BaseModel):
    id: int
    exercise_id: int
    exercise_slug: str
    exercise_name: str
    exercise_name_ru: str
    is_timed: bool
    sets_completed: int
    total_reps: int
    total_duration_seconds: int
    xp_earned: int
    coins_earned: int

    class Config:
        from_attributes = True


class WorkoutResponse(BaseModel):
    id: int
    started_at: datetime
    finished_at: datetime | None
    duration_seconds: int | None
    total_xp_earned: int
    total_coins_earned: int
    total_reps: int
    total_duration_seconds: int
    streak_multiplier: float
    status: str
    exercises: List[WorkoutExerciseResponse] = []

    class Config:
        from_attributes = True


class WorkoutSummaryResponse(BaseModel):
    workout: WorkoutResponse
    new_achievements: List[dict] = []
    level_up: bool = False
    new_level: int | None = None


class TodayStatsResponse(BaseModel):
    workouts_count: int
    total_xp: int
    total_reps: int
    total_duration_seconds: int
    exercises_done: int


def _make_exercise_response(we: WorkoutExercise) -> WorkoutExerciseResponse:
    """Helper to create WorkoutExerciseResponse from WorkoutExercise model."""
    return WorkoutExerciseResponse(
        id=we.id,
        exercise_id=we.exercise_id,
        exercise_slug=we.exercise.slug,
        exercise_name=we.exercise.name,
        exercise_name_ru=we.exercise.name_ru,
        is_timed=we.exercise.is_timed,
        sets_completed=we.sets_completed,
        total_reps=we.total_reps,
        total_duration_seconds=we.total_duration_seconds,
        xp_earned=we.xp_earned,
        coins_earned=we.coins_earned,
    )


def _make_workout_response(workout: WorkoutSession) -> WorkoutResponse:
    """Helper to create WorkoutResponse from WorkoutSession model."""
    return WorkoutResponse(
        id=workout.id,
        started_at=workout.started_at,
        finished_at=workout.finished_at,
        duration_seconds=workout.duration_seconds,
        total_xp_earned=workout.total_xp_earned,
        total_coins_earned=workout.total_coins_earned,
        total_reps=workout.total_reps,
        total_duration_seconds=workout.total_duration_seconds,
        streak_multiplier=float(workout.streak_multiplier),
        status=workout.status,
        exercises=[_make_exercise_response(we) for we in workout.exercises],
    )


@router.get("/active", response_model=WorkoutResponse | None)
async def get_active_workout(
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """Get current active workout if exists."""
    result = await session.execute(
        select(WorkoutSession)
        .options(
            selectinload(WorkoutSession.exercises).selectinload(WorkoutExercise.exercise)
        )
        .where(WorkoutSession.user_id == user.id)
        .where(WorkoutSession.status == "active")
    )
    workout = result.scalar_one_or_none()

    if not workout:
        return None

    return _make_workout_response(workout)


@router.post("", response_model=WorkoutResponse, status_code=status.HTTP_201_CREATED)
async def start_workout(
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """Start a new workout session."""
    # Check if there's an active workout
    active_result = await session.execute(
        select(WorkoutSession)
        .where(WorkoutSession.user_id == user.id)
        .where(WorkoutSession.status == "active")
    )
    active_workout = active_result.scalar_one_or_none()

    if active_workout:
        # Auto-cancel old active workouts (older than 2 hours)
        hours_old = (datetime.utcnow() - active_workout.started_at).total_seconds() / 3600
        if hours_old > 2:
            active_workout.status = "cancelled"
            active_workout.finished_at = datetime.utcnow()
            await session.flush()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already have an active workout. Complete or cancel it first.",
            )

    # Calculate streak multiplier
    streak_mult = get_streak_multiplier(user.current_streak)

    workout = WorkoutSession(
        user_id=user.id,
        started_at=datetime.utcnow(),
        streak_multiplier=streak_mult,
        status="active",
    )
    session.add(workout)
    await session.flush()

    return WorkoutResponse(
        id=workout.id,
        started_at=workout.started_at,
        finished_at=None,
        duration_seconds=None,
        total_xp_earned=0,
        total_coins_earned=0,
        total_reps=0,
        total_duration_seconds=0,
        streak_multiplier=float(workout.streak_multiplier),
        status=workout.status,
        exercises=[],
    )


@router.get("/{workout_id}", response_model=WorkoutResponse)
async def get_workout(
    workout_id: int,
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """Get workout details."""
    result = await session.execute(
        select(WorkoutSession)
        .options(
            selectinload(WorkoutSession.exercises).selectinload(WorkoutExercise.exercise)
        )
        .where(WorkoutSession.id == workout_id)
        .where(WorkoutSession.user_id == user.id)
    )
    workout = result.scalar_one_or_none()

    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found",
        )

    return _make_workout_response(workout)


@router.put("/{workout_id}/exercise", response_model=WorkoutResponse)
async def add_exercise_to_workout(
    workout_id: int,
    request: AddExerciseRequest,
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """Add exercise to active workout."""
    import logging
    logging.info(f"[add_exercise] Received: slug={request.exercise_slug}, reps={request.reps}, duration={request.duration_seconds}, sets={request.sets}")

    # Get active workout
    result = await session.execute(
        select(WorkoutSession)
        .options(
            selectinload(WorkoutSession.exercises).selectinload(WorkoutExercise.exercise)
        )
        .where(WorkoutSession.id == workout_id)
        .where(WorkoutSession.user_id == user.id)
        .where(WorkoutSession.status == "active")
    )
    workout = result.scalar_one_or_none()

    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active workout not found",
        )

    # Get exercise
    exercise_result = await session.execute(
        select(Exercise).where(Exercise.slug == request.exercise_slug)
    )
    exercise = exercise_result.scalar_one_or_none()

    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found",
        )

    # Note: All exercises are available at any level (required_level is now just informational)

    # Check if this is first workout today
    today = date.today()
    is_first_today = user.last_workout_date != today

    # Handle time-based vs rep-based exercises
    is_timed = exercise.is_timed
    total_reps = 0
    total_duration = 0

    if is_timed:
        # For timed exercises, use duration_seconds
        total_duration = request.duration_seconds * request.sets
        # For XP calculation, treat 10 seconds as 1 "rep" equivalent
        xp_value = max(1, total_duration // 10)
    else:
        # For rep-based exercises
        total_reps = request.reps * request.sets
        xp_value = total_reps

    xp_earned = calculate_xp(
        base_xp=exercise.base_xp,
        difficulty=exercise.difficulty,
        reps=xp_value,
        streak_days=user.current_streak,
        is_first_today=is_first_today,
    )

    # Check if we have existing entry for this exercise in this workout
    existing_entry = None
    for we in workout.exercises:
        if we.exercise_id == exercise.id:
            existing_entry = we
            break

    if existing_entry:
        existing_entry.sets_completed += request.sets
        existing_entry.total_reps += total_reps
        existing_entry.total_duration_seconds += total_duration
        existing_entry.xp_earned += xp_earned
    else:
        workout_exercise = WorkoutExercise(
            workout_session_id=workout.id,
            exercise_id=exercise.id,
            sets_completed=request.sets,
            total_reps=total_reps,
            total_duration_seconds=total_duration,
            xp_earned=xp_earned,
            coins_earned=0,
        )
        session.add(workout_exercise)

    # Update workout totals
    workout.total_xp_earned += xp_earned
    workout.total_reps += total_reps
    workout.total_duration_seconds += total_duration

    # Update user exercise progress
    progress_result = await session.execute(
        select(UserExerciseProgress)
        .where(UserExerciseProgress.user_id == user.id)
        .where(UserExerciseProgress.exercise_id == exercise.id)
    )
    progress = progress_result.scalar_one_or_none()

    if progress:
        progress.total_reps_ever += total_reps
        progress.times_performed += 1
        if not is_timed:
            progress.best_single_set = max(progress.best_single_set, request.reps)
        progress.last_performed_at = datetime.utcnow()

        # Check if we should recommend upgrade
        if progress.total_reps_ever >= 100 and exercise.harder_exercise_id:
            progress.recommended_upgrade = True
    else:
        progress = UserExerciseProgress(
            user_id=user.id,
            exercise_id=exercise.id,
            total_reps_ever=total_reps,
            best_single_set=request.reps if not is_timed else 0,
            times_performed=1,
            last_performed_at=datetime.utcnow(),
        )
        session.add(progress)

    await session.flush()

    # Reload workout with exercises
    result = await session.execute(
        select(WorkoutSession)
        .options(
            selectinload(WorkoutSession.exercises).selectinload(WorkoutExercise.exercise)
        )
        .where(WorkoutSession.id == workout_id)
    )
    workout = result.scalar_one()

    return _make_workout_response(workout)


@router.post("/{workout_id}/complete", response_model=WorkoutSummaryResponse)
async def complete_workout(
    workout_id: int,
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """Complete a workout session."""
    result = await session.execute(
        select(WorkoutSession)
        .options(
            selectinload(WorkoutSession.exercises).selectinload(WorkoutExercise.exercise)
        )
        .where(WorkoutSession.id == workout_id)
        .where(WorkoutSession.user_id == user.id)
        .where(WorkoutSession.status == "active")
    )
    workout = result.scalar_one_or_none()

    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active workout not found",
        )

    if len(workout.exercises) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot complete workout with no exercises",
        )

    # Complete workout
    now = datetime.utcnow()
    workout.finished_at = now
    workout.duration_seconds = int((now - workout.started_at).total_seconds())
    workout.status = "completed"

    # Calculate coins (rare and valuable!)
    workout_duration_minutes = workout.duration_seconds // 60
    coins_earned = calculate_coins(
        xp_earned=workout.total_xp_earned,
        streak_days=user.current_streak,
        workout_duration_minutes=workout_duration_minutes
    )
    workout.total_coins_earned = coins_earned

    # Update user stats
    old_level = user.level
    user.total_xp += workout.total_xp_earned
    user.coins += coins_earned

    # Update level
    new_level = get_level_from_xp(user.total_xp)
    user.level = new_level
    level_up = new_level > old_level

    # Update streak
    today = date.today()
    if user.last_workout_date is None:
        user.current_streak = 1
    elif user.last_workout_date == today - timedelta(days=1):
        user.current_streak += 1
    elif user.last_workout_date != today:
        user.current_streak = 1

    user.max_streak = max(user.max_streak, user.current_streak)
    user.last_workout_date = today

    await session.flush()

    # Check achievements
    new_achievements = await check_achievements(session, user)

    # If there are new achievements, add bonus coins
    if new_achievements:
        bonus_coins = sum(a.get("coin_reward", 0) for a in new_achievements)
        workout.total_coins_earned += bonus_coins
        user.coins += bonus_coins

    # Create in-app notifications for level up and achievements
    if level_up:
        notification = Notification(
            user_id=user.id,
            notification_type="level_up",
            title="Новый уровень!",
            message=f"Поздравляем! Ты достиг {new_level} уровня!",
        )
        session.add(notification)

    for achievement in new_achievements:
        notification = Notification(
            user_id=user.id,
            notification_type="achievement",
            title="Новое достижение!",
            message=f"Получено: {achievement.get('name_ru', achievement.get('name', 'Достижение'))}",
        )
        session.add(notification)

    await session.flush()

    return WorkoutSummaryResponse(
        workout=_make_workout_response(workout),
        new_achievements=new_achievements,
        level_up=level_up,
        new_level=new_level if level_up else None,
    )


@router.delete("/{workout_id}")
async def cancel_workout(
    workout_id: int,
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """Cancel an active workout."""
    result = await session.execute(
        select(WorkoutSession)
        .where(WorkoutSession.id == workout_id)
        .where(WorkoutSession.user_id == user.id)
        .where(WorkoutSession.status == "active")
    )
    workout = result.scalar_one_or_none()

    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active workout not found",
        )

    workout.status = "cancelled"
    workout.finished_at = datetime.utcnow()

    return {"message": "Workout cancelled"}


@router.post("/submit", response_model=WorkoutSummaryResponse, status_code=status.HTTP_201_CREATED)
async def submit_workout(
    request: CompleteWorkoutRequest,
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """
    Submit a completed workout with all exercise data.
    This is the simplified endpoint - frontend sends all data at once.
    No need to create session first or track exercises during workout.
    """
    if len(request.exercises) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot submit workout with no exercises",
        )

    # Cancel any stale active workouts
    active_result = await session.execute(
        select(WorkoutSession)
        .where(WorkoutSession.user_id == user.id)
        .where(WorkoutSession.status == "active")
    )
    for old_workout in active_result.scalars().all():
        old_workout.status = "cancelled"
        old_workout.finished_at = datetime.utcnow()

    # Check if first workout today
    today = date.today()
    is_first_today = user.last_workout_date != today

    # Calculate streak multiplier
    streak_mult = get_streak_multiplier(user.current_streak)

    # Create workout session
    now = datetime.utcnow()
    workout = WorkoutSession(
        user_id=user.id,
        started_at=now - timedelta(seconds=request.duration_seconds),
        finished_at=now,
        duration_seconds=request.duration_seconds,
        streak_multiplier=streak_mult,
        status="completed",
        total_xp_earned=0,
        total_coins_earned=0,
        total_reps=0,
        total_duration_seconds=0,
    )
    session.add(workout)
    await session.flush()

    # Process each exercise
    for ex_data in request.exercises:
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

        # Update workout totals
        workout.total_xp_earned += xp_earned
        workout.total_reps += total_reps
        workout.total_duration_seconds += total_duration

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
            progress.last_performed_at = now

            if progress.total_reps_ever >= 100 and exercise.harder_exercise_id:
                progress.recommended_upgrade = True
        else:
            progress = UserExerciseProgress(
                user_id=user.id,
                exercise_id=exercise.id,
                total_reps_ever=total_reps,
                best_single_set=best_set if not ex_data.is_timed else 0,
                times_performed=1,
                last_performed_at=now,
            )
            session.add(progress)

    # Calculate coins
    workout_duration_minutes = request.duration_seconds // 60
    coins_earned = calculate_coins(
        xp_earned=workout.total_xp_earned,
        streak_days=user.current_streak,
        workout_duration_minutes=workout_duration_minutes
    )
    workout.total_coins_earned = coins_earned

    # Update user stats
    old_level = user.level
    user.total_xp += workout.total_xp_earned
    user.coins += coins_earned

    # Update level
    new_level = get_level_from_xp(user.total_xp)
    user.level = new_level
    level_up = new_level > old_level

    # Update streak
    if user.last_workout_date is None:
        user.current_streak = 1
    elif user.last_workout_date == today - timedelta(days=1):
        user.current_streak += 1
    elif user.last_workout_date != today:
        user.current_streak = 1

    user.max_streak = max(user.max_streak, user.current_streak)
    user.last_workout_date = today

    await session.flush()

    # Check achievements
    new_achievements = await check_achievements(session, user)

    # Add bonus coins for achievements
    if new_achievements:
        bonus_coins = sum(a.get("coin_reward", 0) for a in new_achievements)
        workout.total_coins_earned += bonus_coins
        user.coins += bonus_coins

    # Create in-app notifications for level up and achievements
    if level_up:
        notification = Notification(
            user_id=user.id,
            notification_type="level_up",
            title="Новый уровень!",
            message=f"Поздравляем! Ты достиг {new_level} уровня!",
        )
        session.add(notification)

    for achievement in new_achievements:
        notification = Notification(
            user_id=user.id,
            notification_type="achievement",
            title="Новое достижение!",
            message=f"Получено: {achievement.get('name_ru', achievement.get('name', 'Достижение'))}",
        )
        session.add(notification)

    await session.flush()

    # Reload workout with exercises
    result = await session.execute(
        select(WorkoutSession)
        .options(
            selectinload(WorkoutSession.exercises).selectinload(WorkoutExercise.exercise)
        )
        .where(WorkoutSession.id == workout.id)
    )
    workout = result.scalar_one()

    return WorkoutSummaryResponse(
        workout=_make_workout_response(workout),
        new_achievements=new_achievements,
        level_up=level_up,
        new_level=new_level if level_up else None,
    )


@router.get("/history", response_model=List[WorkoutResponse])
async def get_workout_history(
    session: AsyncSessionDep,
    user: CurrentUser,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Get user's workout history."""
    result = await session.execute(
        select(WorkoutSession)
        .options(
            selectinload(WorkoutSession.exercises).selectinload(WorkoutExercise.exercise)
        )
        .where(WorkoutSession.user_id == user.id)
        .where(WorkoutSession.status == "completed")
        .order_by(WorkoutSession.finished_at.desc())
        .limit(limit)
        .offset(offset)
    )
    workouts = result.scalars().all()
    return [_make_workout_response(w) for w in workouts]


@router.get("/today", response_model=TodayStatsResponse)
async def get_today_stats(
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """Get today's workout statistics."""
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    # Count today's completed workouts
    workouts_result = await session.execute(
        select(WorkoutSession)
        .where(WorkoutSession.user_id == user.id)
        .where(WorkoutSession.status == "completed")
        .where(WorkoutSession.finished_at >= today_start)
        .where(WorkoutSession.finished_at <= today_end)
    )
    workouts = workouts_result.scalars().all()

    total_xp = sum(w.total_xp_earned for w in workouts)
    total_reps = sum(w.total_reps for w in workouts)
    total_duration = sum(w.total_duration_seconds for w in workouts)

    # Count unique exercises
    exercise_ids = set()
    for w in workouts:
        for we in w.exercises:
            exercise_ids.add(we.exercise_id)

    return TodayStatsResponse(
        workouts_count=len(workouts),
        total_xp=total_xp,
        total_reps=total_reps,
        total_duration_seconds=total_duration,
        exercises_done=len(exercise_ids),
    )
