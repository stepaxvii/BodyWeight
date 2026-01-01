from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import AsyncSessionDep, CurrentUser
from app.db.models import (
    Exercise,
    ExerciseCategory,
    UserExerciseProgress,
    UserFavoriteExercise
)
from app.services.data_loader import load_all_routines
from app.utils.cache import timed_cache

router = APIRouter()


class CategoryResponse(BaseModel):
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
    total_reps_ever: int
    best_single_set: int
    times_performed: int
    recommended_upgrade: bool


class ExerciseWithProgressResponse(ExerciseResponse):
    user_progress: ExerciseProgressResponse | None = None


@router.get("/categories", response_model=list[CategoryResponse])
@timed_cache(seconds=600)  # Cache for 10 minutes
async def get_categories(session: AsyncSessionDep):
    """Get all exercise categories with caching."""
    result = await session.execute(
        select(ExerciseCategory)
        .options(selectinload(ExerciseCategory.exercises))
        .order_by(ExerciseCategory.sort_order)
    )
    categories = result.scalars().all()

    return [
        CategoryResponse(
            id=cat.id,
            slug=cat.slug,
            name=cat.name,
            name_ru=cat.name_ru,
            icon=cat.icon,
            color=cat.color,
            sort_order=cat.sort_order,
            exercises_count=len([e for e in cat.exercises if e.is_active]),
        )
        for cat in categories
    ]


@router.get("", response_model=list[ExerciseResponse])
async def get_exercises(
    session: AsyncSessionDep,
    user: CurrentUser,
    category: str | None = Query(None, description="Filter by category slug"),
    tags: str | None = Query(None, description="Filter by tags (comma-separated)"),
    difficulty: int | None = Query(None, ge=1, le=5, description="Filter by difficulty"),
    max_level: int | None = Query(None, description="Filter exercises up to required level"),
    favorites_only: bool = Query(False, description="Show only favorite exercises"),
):
    """Get all exercises with optional filters and caching."""
    query = (
        select(Exercise)
        .options(selectinload(Exercise.category))
        .where(Exercise.is_active is True)
    )

    if category:
        query = query.join(Exercise.category).where(ExerciseCategory.slug == category)

    if difficulty:
        query = query.where(Exercise.difficulty == difficulty)

    if max_level:
        query = query.where(Exercise.required_level <= max_level)

    query = query.order_by(Exercise.name_ru)

    result = await session.execute(query)
    exercises = result.scalars().all()

    # Get user's favorite exercise IDs
    favorites_result = await session.execute(
        select(UserFavoriteExercise.exercise_id)
        .where(UserFavoriteExercise.user_id == user.id)
    )
    favorite_ids = set(favorites_result.scalars().all())

    # Parse tags filter
    tag_filter = set(tags.split(",")) if tags else None

    response = []
    for ex in exercises:
        is_favorite = ex.id in favorite_ids

        # Filter by favorites if requested
        if favorites_only and not is_favorite:
            continue

        # Filter by tags if provided
        if tag_filter:
            ex_tags = set(ex.tags or [])
            if not tag_filter.intersection(ex_tags):
                continue

        ex_response = ExerciseResponse(
            id=ex.id,
            slug=ex.slug,
            name=ex.name,
            name_ru=ex.name_ru,
            description=ex.description,
            description_ru=ex.description_ru,
            tags=ex.tags or [],
            difficulty=ex.difficulty,
            base_xp=ex.base_xp,
            required_level=ex.required_level,
            equipment=ex.equipment,
            is_timed=ex.is_timed,
            gif_url=ex.gif_url,
            thumbnail_url=ex.thumbnail_url,
            category_slug=ex.category.slug if ex.category else "",
            is_favorite=is_favorite,
        )
        response.append(ex_response)

    return response


@router.get("/{slug}", response_model=ExerciseWithProgressResponse)
async def get_exercise(
    slug: str,
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """Get exercise details with user progress."""
    result = await session.execute(
        select(Exercise)
        .options(
            selectinload(Exercise.category),
            selectinload(Exercise.easier_exercise),
            selectinload(Exercise.harder_exercise),
        )
        .where(Exercise.slug == slug)
        .where(Exercise.is_active is True)
    )
    exercise = result.scalar_one_or_none()

    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found",
        )

    # Get user progress
    progress_result = await session.execute(
        select(UserExerciseProgress)
        .where(UserExerciseProgress.user_id == user.id)
        .where(UserExerciseProgress.exercise_id == exercise.id)
    )
    progress = progress_result.scalar_one_or_none()

    user_progress = None
    if progress:
        user_progress = ExerciseProgressResponse(
            total_reps_ever=progress.total_reps_ever,
            best_single_set=progress.best_single_set,
            times_performed=progress.times_performed,
            recommended_upgrade=progress.recommended_upgrade,
        )

    return ExerciseWithProgressResponse(
        id=exercise.id,
        slug=exercise.slug,
        name=exercise.name,
        name_ru=exercise.name_ru,
        description=exercise.description,
        description_ru=exercise.description_ru,
        difficulty=exercise.difficulty,
        base_xp=exercise.base_xp,
        required_level=exercise.required_level,
        equipment=exercise.equipment,
        is_timed=exercise.is_timed,
        gif_url=exercise.gif_url,
        thumbnail_url=exercise.thumbnail_url,
        category_slug=exercise.category.slug if exercise.category else "",
        easier_exercise_slug=exercise.easier_exercise.slug if exercise.easier_exercise else None,
        harder_exercise_slug=exercise.harder_exercise.slug if exercise.harder_exercise else None,
        user_progress=user_progress,
    )


@router.get("/{slug}/progress", response_model=ExerciseProgressResponse)
async def get_exercise_progress(
    slug: str,
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """Get user's progress for a specific exercise."""
    # First get the exercise
    exercise_result = await session.execute(
        select(Exercise).where(Exercise.slug == slug)
    )
    exercise = exercise_result.scalar_one_or_none()

    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found",
        )

    # Get user progress
    progress_result = await session.execute(
        select(UserExerciseProgress)
        .where(UserExerciseProgress.user_id == user.id)
        .where(UserExerciseProgress.exercise_id == exercise.id)
    )
    progress = progress_result.scalar_one_or_none()

    if not progress:
        return ExerciseProgressResponse(
            total_reps_ever=0,
            best_single_set=0,
            times_performed=0,
            recommended_upgrade=False,
        )

    return ExerciseProgressResponse(
        total_reps_ever=progress.total_reps_ever,
        best_single_set=progress.best_single_set,
        times_performed=progress.times_performed,
        recommended_upgrade=progress.recommended_upgrade,
    )


# Routine models and endpoints
class RoutineExerciseResponse(BaseModel):
    slug: str
    reps: int | None = None
    duration: int | None = None  # duration in seconds


class RoutineResponse(BaseModel):
    slug: str
    name: str
    description: str
    category: str  # morning, home, pullup-bar, dip-bars
    duration_minutes: int
    difficulty: int
    exercises: list[RoutineExerciseResponse]


@router.get("/routines/all", response_model=list[RoutineResponse])
async def get_routines(
    category: str | None = Query(None, description="Filter by category: morning, home, pullup-bar, dip-bars")
):
    """Get all available workout routines from all categories."""
    routines = load_all_routines()

    if category:
        routines = [r for r in routines if r.get("category") == category]

    return [
        RoutineResponse(
            slug=r["slug"],
            name=r["name"],
            description=r["description"],
            category=r.get("category", "morning"),
            duration_minutes=r["duration_minutes"],
            difficulty=r["difficulty"],
            exercises=[
                RoutineExerciseResponse(
                    slug=ex["slug"],
                    reps=ex.get("reps"),
                    duration=ex.get("duration"),
                )
                for ex in r["exercises"]
            ],
        )
        for r in routines
    ]


@router.get("/routines/{slug}", response_model=RoutineResponse)
async def get_routine(slug: str):
    """Get a specific routine by slug."""
    routines = load_all_routines()

    for r in routines:
        if r["slug"] == slug:
            return RoutineResponse(
                slug=r["slug"],
                name=r["name"],
                description=r["description"],
                category=r.get("category", "morning"),
                duration_minutes=r["duration_minutes"],
                difficulty=r["difficulty"],
                exercises=[
                    RoutineExerciseResponse(
                        slug=ex["slug"],
                        reps=ex.get("reps"),
                        duration=ex.get("duration"),
                    )
                    for ex in r["exercises"]
                ],
            )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Routine not found",
    )


# ============== Favorites API ==============

class FavoriteResponse(BaseModel):
    exercise_id: int
    is_favorite: bool


@router.post("/{exercise_id}/favorite", response_model=FavoriteResponse)
async def toggle_favorite(
    exercise_id: int,
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """Toggle favorite status for an exercise."""
    # Check if exercise exists
    exercise_result = await session.execute(
        select(Exercise).where(Exercise.id == exercise_id)
    )
    exercise = exercise_result.scalar_one_or_none()

    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found",
        )

    # Check if already favorited
    favorite_result = await session.execute(
        select(UserFavoriteExercise)
        .where(UserFavoriteExercise.user_id == user.id)
        .where(UserFavoriteExercise.exercise_id == exercise_id)
    )
    existing = favorite_result.scalar_one_or_none()

    if existing:
        # Remove from favorites
        await session.delete(existing)
        await session.commit()
        return FavoriteResponse(exercise_id=exercise_id, is_favorite=False)
    else:
        # Add to favorites
        favorite = UserFavoriteExercise(user_id=user.id, exercise_id=exercise_id)
        session.add(favorite)
        await session.commit()
        return FavoriteResponse(exercise_id=exercise_id, is_favorite=True)


@router.get("/favorites/list", response_model=list[int])
async def get_favorite_ids(
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """Get list of favorite exercise IDs for the current user."""
    result = await session.execute(
        select(UserFavoriteExercise.exercise_id)
        .where(UserFavoriteExercise.user_id == user.id)
    )
    return list(result.scalars().all())
