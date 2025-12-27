import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.api.deps import get_current_user
from app.db.database import get_session
from app.db.models import User, Exercise, ExerciseCategory, MetricType

router = APIRouter(prefix="/exercises", tags=["exercises"])


class ExerciseResponse(BaseModel):
    id: int
    name: str
    category: str
    metric_type: str
    description: Optional[str]
    icon: str
    difficulty: int
    exp_per_rep: int
    exp_per_second: int

    class Config:
        from_attributes = True


class CategoryResponse(BaseModel):
    id: str
    name: str
    icon: str
    exercises_count: int


CATEGORY_INFO = {
    "push": {"name": "Жимовые", "icon": "💪"},
    "pull": {"name": "Тяговые", "icon": "🏋️"},
    "legs": {"name": "Ноги", "icon": "🦵"},
    "core": {"name": "Кор", "icon": "🔄"},
    "static": {"name": "Статика", "icon": "🧘"},
    "cardio": {"name": "Кардио", "icon": "🔥"},
    "warmup": {"name": "Разминка", "icon": "🌡️"},
    "stretch": {"name": "Растяжка", "icon": "🤸"},
}


@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Get all exercise categories with counts."""
    from sqlalchemy import func

    result = await session.execute(
        select(Exercise.category, func.count(Exercise.id))
        .group_by(Exercise.category)
    )
    counts = {cat: count for cat, count in result.all()}

    categories = []
    for cat_id, info in CATEGORY_INFO.items():
        categories.append(CategoryResponse(
            id=cat_id,
            name=info["name"],
            icon=info["icon"],
            exercises_count=counts.get(ExerciseCategory(cat_id), 0),
        ))

    return categories


@router.get("/", response_model=List[ExerciseResponse])
async def get_exercises(
    category: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Get all exercises, optionally filtered by category."""
    query = select(Exercise)

    if category:
        try:
            cat = ExerciseCategory(category)
            query = query.where(Exercise.category == cat)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid category")

    query = query.order_by(Exercise.difficulty, Exercise.name)
    result = await session.execute(query)
    exercises = result.scalars().all()

    return [
        ExerciseResponse(
            id=e.id,
            name=e.name,
            category=e.category.value,
            metric_type=e.metric_type.value,
            description=e.description,
            icon=e.icon,
            difficulty=e.difficulty,
            exp_per_rep=e.exp_per_rep,
            exp_per_second=e.exp_per_second,
        )
        for e in exercises
    ]


@router.get("/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(
    exercise_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Get single exercise by ID."""
    result = await session.execute(
        select(Exercise).where(Exercise.id == exercise_id)
    )
    exercise = result.scalar_one_or_none()

    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    return ExerciseResponse(
        id=exercise.id,
        name=exercise.name,
        category=exercise.category.value,
        metric_type=exercise.metric_type.value,
        description=exercise.description,
        icon=exercise.icon,
        difficulty=exercise.difficulty,
        exp_per_rep=exercise.exp_per_rep,
        exp_per_second=exercise.exp_per_second,
    )


async def seed_exercises(session: AsyncSession):
    """Seed exercises from JSON file."""
    data_path = Path(__file__).parent.parent.parent / "data" / "exercises.json"

    if not data_path.exists():
        return

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for ex_data in data.get("exercises", []):
        result = await session.execute(
            select(Exercise).where(Exercise.id == ex_data["id"])
        )
        existing = result.scalar_one_or_none()

        if not existing:
            exercise = Exercise(
                id=ex_data["id"],
                name=ex_data["name"],
                category=ExerciseCategory(ex_data["category"]),
                metric_type=MetricType(ex_data["metric_type"]),
                description=ex_data.get("description"),
                icon=ex_data.get("icon", "💪"),
                difficulty=ex_data.get("difficulty", 1),
                exp_per_rep=ex_data.get("exp_per_rep", 1),
                exp_per_second=ex_data.get("exp_per_second", 1),
            )
            session.add(exercise)

    await session.commit()
