"""Workout-related Pydantic schemas."""

from datetime import datetime
from pydantic import BaseModel


class ExerciseSetData(BaseModel):
    """Data for a single exercise in a completed workout."""
    exercise_slug: str
    sets: list[int]  # Array of reps per set (or seconds for timed exercises)
    is_timed: bool = False


class CompleteWorkoutRequest(BaseModel):
    """Request body for completing a workout with all exercise data."""
    duration_seconds: int
    exercises: list[ExerciseSetData]


class WorkoutExerciseResponse(BaseModel):
    """Response schema for a single exercise in a workout."""
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
    """Response schema for a workout session."""
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
    exercises: list[WorkoutExerciseResponse] = []

    class Config:
        from_attributes = True


class WorkoutSummaryResponse(BaseModel):
    """Response schema for workout completion summary."""
    workout: WorkoutResponse
    new_achievements: list[dict] = []
    level_up: bool = False
    new_level: int | None = None


class TodayStatsResponse(BaseModel):
    """Response schema for today's workout statistics."""
    workouts_count: int
    total_xp: int
    total_reps: int
    total_duration_seconds: int
    exercises_done: int
