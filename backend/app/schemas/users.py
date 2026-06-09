"""User-related Pydantic schemas."""

from datetime import date, time, datetime
from pydantic import BaseModel, model_validator


class UserResponse(BaseModel):
    """User profile response schema."""
    id: int
    telegram_id: int | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    has_password: bool = False
    avatar_id: str
    level: int
    total_xp: int
    coins: int
    current_streak: int
    max_streak: int
    streak_freezes: int = 0
    last_workout_date: date | None = None
    notification_time: time | None = None
    notifications_enabled: bool
    is_onboarded: bool
    leaderboard_visible: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @model_validator(mode="wrap")
    @classmethod
    def _compute_has_password(cls, values, handler):
        # If validating from ORM model, check password_hash attribute
        if hasattr(values, "password_hash"):
            result = handler(values)
            result.has_password = values.password_hash is not None
            return result
        return handler(values)


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
    streak_freezes: int = 0
    achievements_count: int
    coins: int
    this_week_workouts: int
    this_week_xp: int


class UpdateUserRequest(BaseModel):
    """Request schema for updating user profile."""
    avatar_id: str | None = None
    notification_time: time | None = None
    notifications_enabled: bool | None = None
    leaderboard_visible: bool | None = None


class CompleteOnboardingRequest(BaseModel):
    """Request body for completing onboarding (consent to show in leaderboard)."""
    leaderboard_consent: bool


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


class DayActivityResponse(BaseModel):
    """Activity data for a single day."""
    date: str  # ISO format: "2025-01-09"
    workouts: int  # Number of workouts completed
    total_xp: int  # Total XP earned from workouts (excluding achievements)


class UserActivityResponse(BaseModel):
    """User workout activity calendar data."""
    days: dict[str, DayActivityResponse]  # Map of date string to activity data
