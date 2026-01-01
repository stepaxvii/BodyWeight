"""Goal-related Pydantic schemas."""

from datetime import date, datetime
from pydantic import BaseModel


class CreateGoalRequest(BaseModel):
    """Request schema for creating a goal."""
    goal_type: str  # weekly_workouts, daily_xp, weekly_xp
    target_value: int
    duration_days: int = 7  # Default to weekly


class GoalResponse(BaseModel):
    """Goal response schema."""
    id: int
    goal_type: str
    target_value: int
    current_value: int
    start_date: date
    end_date: date
    completed: bool
    completed_at: datetime | None
    progress_percent: float

    class Config:
        from_attributes = True
