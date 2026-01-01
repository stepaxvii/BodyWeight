"""User-related Pydantic schemas."""

from datetime import date, time, datetime
from pydantic import BaseModel


class UserResponse(BaseModel):
    """User profile response schema."""
    id: int
    telegram_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    avatar_id: str
    level: int
    total_xp: int
    coins: int
    current_streak: int
    max_streak: int
    last_workout_date: date | None
    notification_time: time | None
    notifications_enabled: bool
    is_onboarded: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    """User statistics response schema."""
    total_workouts: int
    total_xp: int
    total_reps: int
    total_time_minutes: int
    current_level: int
    xp_for_next_level: int
    xp_progress_percent: float
    current_streak: int
    max_streak: int
    achievements_count: int
    coins: int
    this_week_workouts: int
    this_week_xp: int


class UpdateUserRequest(BaseModel):
    """Request schema for updating user profile."""
    avatar_id: str | None = None
    notification_time: time | None = None
    notifications_enabled: bool | None = None


class UserProfileResponse(BaseModel):
    """Public user profile with achievements."""
    id: int
    username: str | None
    first_name: str | None
    avatar_id: str
    level: int
    total_xp: int
    coins: int
    current_streak: int
    achievements: list[str]  # List of unlocked achievement slugs
    is_friend: bool
    # Current user sent request to this user
    friend_request_sent: bool = False
    # This user sent request to current user
    friend_request_received: bool = False
    # Friendship ID for accept/decline actions
    friendship_id: int | None = None
