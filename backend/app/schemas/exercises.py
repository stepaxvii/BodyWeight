"""Exercise-related Pydantic schemas."""

from pydantic import BaseModel


class CategoryResponse(BaseModel):
    """Exercise category response schema."""
    id: int
    slug: str
    name: str
    name_ru: str
    icon: str | None
    color: str | None
    sort_order: int
    exercises_count: int = 0

    class Config:
        from_attributes = True


class ExerciseResponse(BaseModel):
    """Exercise response schema."""
    id: int
    slug: str
    name: str
    name_ru: str
    description: str | None
    description_ru: str | None
    tags: list[str] = []
    difficulty: int
    base_xp: int
    required_level: int
    equipment: str = "none"  # none, pullup-bar, dip-bars
    is_timed: bool = False  # True for time-based exercises (planks, stretches)
    gif_url: str | None
    thumbnail_url: str | None
    category_slug: str
    easier_exercise_slug: str | None = None
    harder_exercise_slug: str | None = None
    is_favorite: bool = False

    class Config:
        from_attributes = True


class ExerciseProgressResponse(BaseModel):
    """User progress for a specific exercise."""
    total_reps_ever: int
    best_single_set: int
    times_performed: int
    recommended_upgrade: bool


class ExerciseWithProgressResponse(ExerciseResponse):
    """Exercise response with user progress."""
    user_progress: ExerciseProgressResponse | None = None


class RoutineExerciseResponse(BaseModel):
    """Exercise in a routine response schema."""
    exercise_slug: str
    exercise_name: str
    exercise_name_ru: str
    target_reps: int | None
    target_duration: int | None
    rest_seconds: int
    order: int


class RoutineResponse(BaseModel):
    """Routine response schema."""
    slug: str
    name: str
    description: str | None
    exercises: list[RoutineExerciseResponse]
    estimated_duration_minutes: int


class FavoriteResponse(BaseModel):
    """Favorite exercise toggle response."""
    exercise_slug: str
    is_favorite: bool
