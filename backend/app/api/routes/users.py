from datetime import date, time
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func

from app.api.deps import AsyncSessionDep, CurrentUser
from app.db.models import User, WorkoutSession, UserAchievement
from app.services.xp_calculator import xp_for_level, get_level_from_xp

router = APIRouter()


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    photo_url: str | None
    level: int
    total_xp: int
    coins: int
    current_streak: int
    max_streak: int
    last_workout_date: date | None
    notification_time: time | None
    notifications_enabled: bool

    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    total_workouts: int
    total_xp: int
    total_reps: int
    current_level: int
    xp_for_next_level: int
    xp_progress_percent: float
    current_streak: int
    max_streak: int
    achievements_count: int
    coins: int


class UpdateUserRequest(BaseModel):
    notification_time: time | None = None
    notifications_enabled: bool | None = None


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(user: CurrentUser):
    """Get current user's profile."""
    return UserResponse.model_validate(user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user: CurrentUser,
    request: UpdateUserRequest,
    session: AsyncSessionDep,
):
    """Update current user's settings."""
    if request.notification_time is not None:
        user.notification_time = request.notification_time
    if request.notifications_enabled is not None:
        user.notifications_enabled = request.notifications_enabled

    await session.flush()
    return UserResponse.model_validate(user)


@router.get("/me/stats", response_model=UserStatsResponse)
async def get_current_user_stats(
    user: CurrentUser,
    session: AsyncSessionDep,
):
    """Get detailed statistics for current user."""
    # Total workouts
    workouts_result = await session.execute(
        select(func.count(WorkoutSession.id))
        .where(WorkoutSession.user_id == user.id)
        .where(WorkoutSession.status == "completed")
    )
    total_workouts = workouts_result.scalar() or 0

    # Total reps
    reps_result = await session.execute(
        select(func.sum(WorkoutSession.total_reps))
        .where(WorkoutSession.user_id == user.id)
        .where(WorkoutSession.status == "completed")
    )
    total_reps = reps_result.scalar() or 0

    # Achievements count
    achievements_result = await session.execute(
        select(func.count(UserAchievement.id))
        .where(UserAchievement.user_id == user.id)
    )
    achievements_count = achievements_result.scalar() or 0

    # Level progress
    current_level = user.level
    current_level_xp = xp_for_level(current_level)
    next_level_xp = xp_for_level(current_level + 1)
    xp_in_current_level = user.total_xp - current_level_xp
    xp_needed_for_level = next_level_xp - current_level_xp
    xp_progress_percent = (xp_in_current_level / xp_needed_for_level) * 100 if xp_needed_for_level > 0 else 0

    return UserStatsResponse(
        total_workouts=total_workouts,
        total_xp=user.total_xp,
        total_reps=total_reps,
        current_level=current_level,
        xp_for_next_level=next_level_xp,
        xp_progress_percent=min(xp_progress_percent, 100),
        current_streak=user.current_streak,
        max_streak=user.max_streak,
        achievements_count=achievements_count,
        coins=user.coins,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    session: AsyncSessionDep,
    current_user: CurrentUser,  # Require auth to view profiles
):
    """Get user profile by ID (public info only)."""
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse.model_validate(user)
