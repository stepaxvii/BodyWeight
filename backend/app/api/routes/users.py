from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.api.deps import get_current_user
from app.db.database import get_session
from app.db.models import User

router = APIRouter(prefix="/users", tags=["users"])


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    level: int
    experience: int
    streak_days: int
    total_workouts: int
    total_reps: int
    total_time_seconds: int
    notifications_enabled: bool
    reminder_time: Optional[str]

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    notifications_enabled: Optional[bool] = None
    reminder_time: Optional[str] = None


class UserStats(BaseModel):
    level: int
    experience: int
    exp_to_next_level: int
    streak_days: int
    total_workouts: int
    total_reps: int
    total_time_seconds: int
    workouts_this_week: int
    reps_this_week: int


def calculate_exp_for_level(level: int) -> int:
    """Calculate total XP needed for a level."""
    return 100 * level * level


def calculate_level(exp: int) -> int:
    """Calculate level from total XP."""
    level = 1
    while calculate_exp_for_level(level) <= exp:
        level += 1
    return level - 1 if level > 1 else 1


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """Get current user info."""
    return user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update current user settings."""
    if data.notifications_enabled is not None:
        user.notifications_enabled = data.notifications_enabled
    if data.reminder_time is not None:
        user.reminder_time = data.reminder_time

    await session.commit()
    await session.refresh(user)
    return user


@router.get("/me/stats", response_model=UserStats)
async def get_my_stats(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get detailed user statistics."""
    from datetime import datetime, timedelta
    from sqlalchemy import func
    from app.db.models import Workout, WorkoutExercise

    week_ago = datetime.utcnow() - timedelta(days=7)

    # Count workouts this week
    result = await session.execute(
        select(func.count(Workout.id))
        .where(Workout.user_id == user.id)
        .where(Workout.started_at >= week_ago)
    )
    workouts_this_week = result.scalar() or 0

    # Count reps this week
    result = await session.execute(
        select(func.sum(WorkoutExercise.reps))
        .join(Workout)
        .where(Workout.user_id == user.id)
        .where(Workout.started_at >= week_ago)
    )
    reps_this_week = result.scalar() or 0

    current_level = calculate_level(user.experience)
    exp_for_current = calculate_exp_for_level(current_level)
    exp_for_next = calculate_exp_for_level(current_level + 1)

    return UserStats(
        level=current_level,
        experience=user.experience,
        exp_to_next_level=exp_for_next - user.experience,
        streak_days=user.streak_days,
        total_workouts=user.total_workouts,
        total_reps=user.total_reps,
        total_time_seconds=user.total_time_seconds,
        workouts_this_week=workouts_this_week,
        reps_this_week=reps_this_week,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get user by ID (for viewing friends)."""
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
