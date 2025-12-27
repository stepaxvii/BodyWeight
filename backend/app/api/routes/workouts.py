from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional, List

from app.api.deps import get_current_user
from app.db.database import get_session
from app.db.models import User, Workout, WorkoutExercise, Exercise

router = APIRouter(prefix="/workouts", tags=["workouts"])


class ExerciseEntry(BaseModel):
    exercise_id: int
    sets: int = 1
    reps: Optional[int] = None
    duration_seconds: Optional[int] = None


class WorkoutCreate(BaseModel):
    exercises: List[ExerciseEntry]
    notes: Optional[str] = None


class WorkoutExerciseResponse(BaseModel):
    id: int
    exercise_id: int
    exercise_name: str
    exercise_icon: str
    sets: int
    reps: Optional[int]
    duration_seconds: Optional[int]
    is_personal_record: bool
    exp_earned: int


class WorkoutResponse(BaseModel):
    id: int
    started_at: datetime
    finished_at: Optional[datetime]
    notes: Optional[str]
    total_exp: int
    exercises: List[WorkoutExerciseResponse]


class WorkoutSummary(BaseModel):
    id: int
    started_at: datetime
    exercises_count: int
    total_reps: int
    total_time: int
    total_exp: int


def calculate_level(exp: int) -> int:
    """Calculate level from total XP."""
    level = 1
    while 100 * level * level <= exp:
        level += 1
    return level - 1 if level > 1 else 1


@router.post("/", response_model=dict)
async def create_workout(
    data: WorkoutCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new workout."""
    if not data.exercises:
        raise HTTPException(status_code=400, detail="No exercises provided")

    workout = Workout(
        user_id=user.id,
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
        notes=data.notes,
    )
    session.add(workout)
    await session.flush()

    total_exp = 0
    total_reps = 0
    total_time = 0
    new_records = []

    for entry in data.exercises:
        # Get exercise
        result = await session.execute(
            select(Exercise).where(Exercise.id == entry.exercise_id)
        )
        exercise = result.scalar_one_or_none()

        if not exercise:
            raise HTTPException(status_code=400, detail=f"Exercise {entry.exercise_id} not found")

        # Calculate XP
        if entry.reps:
            exp = entry.reps * entry.sets * exercise.exp_per_rep
            total_reps += entry.reps * entry.sets
        elif entry.duration_seconds:
            exp = entry.duration_seconds * exercise.exp_per_second
            total_time += entry.duration_seconds
        else:
            exp = 0

        # Check for personal record
        is_record = False
        if entry.reps:
            result = await session.execute(
                select(func.max(WorkoutExercise.reps))
                .join(Workout)
                .where(Workout.user_id == user.id)
                .where(WorkoutExercise.exercise_id == entry.exercise_id)
            )
            max_reps = result.scalar() or 0
            if entry.reps > max_reps:
                is_record = True
                new_records.append({
                    "exercise": exercise.name,
                    "value": entry.reps,
                    "type": "reps"
                })
        elif entry.duration_seconds:
            result = await session.execute(
                select(func.max(WorkoutExercise.duration_seconds))
                .join(Workout)
                .where(Workout.user_id == user.id)
                .where(WorkoutExercise.exercise_id == entry.exercise_id)
            )
            max_time = result.scalar() or 0
            if entry.duration_seconds > max_time:
                is_record = True
                new_records.append({
                    "exercise": exercise.name,
                    "value": entry.duration_seconds,
                    "type": "time"
                })

        workout_exercise = WorkoutExercise(
            workout_id=workout.id,
            exercise_id=entry.exercise_id,
            sets=entry.sets,
            reps=entry.reps,
            duration_seconds=entry.duration_seconds,
            is_personal_record=is_record,
            exp_earned=exp,
        )
        session.add(workout_exercise)
        total_exp += exp

    workout.total_exp = total_exp

    # Update user stats
    old_level = calculate_level(user.experience)
    user.experience += total_exp
    user.total_workouts += 1
    user.total_reps += total_reps
    user.total_time_seconds += total_time
    new_level = calculate_level(user.experience)

    # Update streak
    today = datetime.utcnow().date()
    if user.last_workout_date:
        last_date = user.last_workout_date.date()
        if last_date == today - timedelta(days=1):
            user.streak_days += 1
        elif last_date != today:
            user.streak_days = 1
    else:
        user.streak_days = 1

    user.last_workout_date = datetime.utcnow()
    user.level = new_level

    await session.commit()

    return {
        "workout_id": workout.id,
        "total_exp": total_exp,
        "total_reps": total_reps,
        "total_time": total_time,
        "new_level": new_level,
        "level_up": new_level > old_level,
        "streak_days": user.streak_days,
        "new_records": new_records,
    }


@router.get("/", response_model=List[WorkoutSummary])
async def get_workouts(
    limit: int = 20,
    offset: int = 0,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get user's workout history."""
    result = await session.execute(
        select(Workout)
        .where(Workout.user_id == user.id)
        .order_by(Workout.started_at.desc())
        .offset(offset)
        .limit(limit)
        .options(selectinload(Workout.exercises))
    )
    workouts = result.scalars().all()

    return [
        WorkoutSummary(
            id=w.id,
            started_at=w.started_at,
            exercises_count=len(w.exercises),
            total_reps=sum(e.reps or 0 for e in w.exercises),
            total_time=sum(e.duration_seconds or 0 for e in w.exercises),
            total_exp=w.total_exp,
        )
        for w in workouts
    ]


@router.get("/{workout_id}", response_model=WorkoutResponse)
async def get_workout(
    workout_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get workout details."""
    result = await session.execute(
        select(Workout)
        .where(Workout.id == workout_id)
        .where(Workout.user_id == user.id)
        .options(selectinload(Workout.exercises).selectinload(WorkoutExercise.exercise))
    )
    workout = result.scalar_one_or_none()

    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    return WorkoutResponse(
        id=workout.id,
        started_at=workout.started_at,
        finished_at=workout.finished_at,
        notes=workout.notes,
        total_exp=workout.total_exp,
        exercises=[
            WorkoutExerciseResponse(
                id=e.id,
                exercise_id=e.exercise_id,
                exercise_name=e.exercise.name,
                exercise_icon=e.exercise.icon,
                sets=e.sets,
                reps=e.reps,
                duration_seconds=e.duration_seconds,
                is_personal_record=e.is_personal_record,
                exp_earned=e.exp_earned,
            )
            for e in workout.exercises
        ],
    )


@router.get("/stats/weekly")
async def get_weekly_stats(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get weekly workout statistics."""
    week_ago = datetime.utcnow() - timedelta(days=7)

    result = await session.execute(
        select(Workout)
        .where(Workout.user_id == user.id)
        .where(Workout.started_at >= week_ago)
        .options(selectinload(Workout.exercises))
    )
    workouts = result.scalars().all()

    # Stats per day
    days = {}
    for i in range(7):
        day = (datetime.utcnow() - timedelta(days=i)).date()
        days[day.isoformat()] = {"workouts": 0, "reps": 0, "exp": 0}

    for w in workouts:
        day = w.started_at.date().isoformat()
        if day in days:
            days[day]["workouts"] += 1
            days[day]["reps"] += sum(e.reps or 0 for e in w.exercises)
            days[day]["exp"] += w.total_exp

    return {
        "total_workouts": len(workouts),
        "total_reps": sum(sum(e.reps or 0 for e in w.exercises) for w in workouts),
        "total_exp": sum(w.total_exp for w in workouts),
        "days": days,
    }
