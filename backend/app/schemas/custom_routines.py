"""Custom routine-related Pydantic schemas."""

from pydantic import BaseModel


class RoutineExerciseCreate(BaseModel):
    """Request schema for creating a routine exercise."""
    exercise_id: int
    target_reps: int | None = None
    target_duration: int | None = None
    rest_seconds: int = 30


class RoutineExerciseResponse(BaseModel):
    """Routine exercise response schema."""
    id: int
    exercise_id: int
    exercise_slug: str
    exercise_name_ru: str
    is_timed: bool
    sort_order: int
    target_reps: int | None
    target_duration: int | None
    rest_seconds: int

    class Config:
        from_attributes = True


class CustomRoutineCreate(BaseModel):
    """Request schema for creating a custom routine."""
    name: str
    description: str | None = None
    routine_type: str = "workout"  # morning, workout, stretch
    exercises: list[RoutineExerciseCreate] = []


class CustomRoutineUpdate(BaseModel):
    """Request schema for updating a custom routine."""
    name: str | None = None
    description: str | None = None
    routine_type: str | None = None
    exercises: list[RoutineExerciseCreate] | None = None


class CustomRoutineResponse(BaseModel):
    """Custom routine response schema."""
    id: int
    name: str
    description: str | None
    routine_type: str
    duration_minutes: int
    is_active: bool
    exercises: list[RoutineExerciseResponse]

    class Config:
        from_attributes = True


class CustomRoutineListItem(BaseModel):
    """Custom routine list item response schema."""
    id: int
    name: str
    routine_type: str
    duration_minutes: int
    exercises_count: int

    class Config:
        from_attributes = True
