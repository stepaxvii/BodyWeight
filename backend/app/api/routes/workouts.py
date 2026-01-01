from datetime import datetime, date, timedelta
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import AsyncSessionDep, CurrentUser
from app.db.models import (
    WorkoutSession,
    WorkoutExercise,
)
from app.services.xp_calculator import (
    get_streak_multiplier,
)
from app.services.workout_processor import (
    process_workout_completion,
    WorkoutCompletionData,
    ExerciseSetData as ProcessorExerciseSetData,
)
from app.schemas import (
    CompleteWorkoutRequest,
    WorkoutExerciseResponse,
    WorkoutResponse,
    WorkoutSummaryResponse,
    TodayStatsResponse,
)

router = APIRouter()


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


# DEPRECATED: Old endpoints removed in favor of /submit
# Use POST /workouts/submit instead


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
    This is the unified endpoint - frontend sends all data at once.
    Uses workout_processor for all business logic.
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

    # Prepare data for processor
    now = datetime.utcnow()
    completion_data = WorkoutCompletionData(
        user_id=user.id,
        started_at=now - timedelta(seconds=request.duration_seconds),
        finished_at=now,
        exercises=[
            ProcessorExerciseSetData(
                exercise_slug=ex.exercise_slug,
                sets=ex.sets,
                is_timed=ex.is_timed,
            )
            for ex in request.exercises
        ],
    )

    # Process workout through unified processor
    result = await process_workout_completion(completion_data, session)

    # Reload workout with exercises for response
    workout_result = await session.execute(
        select(WorkoutSession)
        .options(
            selectinload(WorkoutSession.exercises).selectinload(WorkoutExercise.exercise)
        )
        .where(WorkoutSession.id == result.workout_session_id)
    )
    workout = workout_result.scalar_one()

    return WorkoutSummaryResponse(
        workout=_make_workout_response(workout),
        new_achievements=result.new_achievements,
        level_up=result.level_up,
        new_level=result.new_level if result.level_up else None,
    )


@router.get("/history", response_model=list[WorkoutResponse])
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
