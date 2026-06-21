"""Service to load initial data from JSON files into database."""
import json
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ExerciseCategory, Exercise, ShopItem


DATA_DIR = Path(__file__).parent.parent / "data"


def load_json(filename: str) -> dict | list:
    """Load JSON file from data directory."""
    data_path = DATA_DIR / filename
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


_categories_cache: list[dict] | None = None


def load_categories_data() -> list[dict]:
    """Load categories from categories.json."""
    global _categories_cache
    if _categories_cache is not None:
        return _categories_cache
    _categories_cache = load_json("categories.json")
    return _categories_cache


_exercises_cache: list[dict] | None = None


def load_all_exercises() -> list[dict]:
    """Load all exercises from exercises/ directory."""
    global _exercises_cache
    if _exercises_cache is not None:
        return _exercises_cache

    exercises_dir = DATA_DIR / "exercises"
    all_exercises = []

    for json_file in exercises_dir.glob("*.json"):
        exercises = load_json(f"exercises/{json_file.name}")
        all_exercises.extend(exercises)

    _exercises_cache = all_exercises
    return _exercises_cache


_routines_cache: list[dict] | None = None


def load_all_routines() -> list[dict]:
    """Load all routines from routines/ directory."""
    global _routines_cache
    if _routines_cache is not None:
        return _routines_cache

    routines_dir = DATA_DIR / "routines"
    all_routines = []

    for json_file in routines_dir.glob("*.json"):
        routines = load_json(f"routines/{json_file.name}")
        all_routines.extend(routines)

    _routines_cache = all_routines
    return _routines_cache


async def load_categories(session: AsyncSession) -> dict[str, int]:
    """Load exercise categories into database. Returns slug -> id mapping."""
    categories = load_categories_data()
    slug_to_id = {}

    for cat_data in categories:
        # Check if exists
        result = await session.execute(
            select(ExerciseCategory).where(ExerciseCategory.slug == cat_data["slug"])
        )
        category = result.scalar_one_or_none()

        if not category:
            category = ExerciseCategory(
                slug=cat_data["slug"],
                name=cat_data["name"],
                name_ru=cat_data["name_ru"],
                icon=cat_data.get("icon"),
                color=cat_data.get("color"),
                sort_order=cat_data.get("sort_order", 0),
            )
            session.add(category)
            await session.flush()

        slug_to_id[category.slug] = category.id

    return slug_to_id


async def load_exercises(session: AsyncSession) -> None:
    """Load exercises into database."""
    # First, load categories
    category_map = await load_categories(session)

    # Load all exercises from the exercises/ directory
    exercises_data = load_all_exercises()

    # Track exercise slug -> id for linking easier/harder
    slug_to_id = {}

    # First pass: create all exercises without links
    for ex_data in exercises_data:
        # Check if exists
        result = await session.execute(
            select(Exercise).where(Exercise.slug == ex_data["slug"])
        )
        exercise = result.scalar_one_or_none()

        category_slug = ex_data["category"]
        category_id = category_map.get(category_slug)
        if not category_id:
            continue

        # Use is_timed from JSON, default to False
        is_timed = ex_data.get("is_timed", False)

        # Get tags from data or default empty list
        tags = ex_data.get("tags", [])

        slug = ex_data["slug"]
        # SVG animation URL based on slug
        gif_url = f"/sprites/exercises/{slug}.svg"

        if not exercise:
            exercise = Exercise(
                slug=slug,
                category_id=category_id,
                name=ex_data["name"],
                name_ru=ex_data["name_ru"],
                description=ex_data.get("description"),
                description_ru=ex_data.get("description_ru"),
                tags=tags,
                difficulty=ex_data.get("difficulty", 1),
                base_xp=ex_data.get("base_xp", 10),
                required_level=ex_data.get("required_level", 1),
                equipment=ex_data.get("equipment", "none"),
                is_timed=is_timed,
                gif_url=gif_url,
            )
            session.add(exercise)
            await session.flush()
        else:
            # Keep existing DB rows in sync with JSON source
            exercise.name = ex_data["name"]
            exercise.name_ru = ex_data["name_ru"]
            exercise.description = ex_data.get("description")
            exercise.description_ru = ex_data.get("description_ru")
            exercise.difficulty = ex_data.get("difficulty", 1)
            exercise.base_xp = ex_data.get("base_xp", 10)
            exercise.required_level = ex_data.get("required_level", 1)
            exercise.equipment = ex_data.get("equipment", "none")
            exercise.is_timed = is_timed
            exercise.tags = tags
            exercise.category_id = category_id
            exercise.gif_url = gif_url

        slug_to_id[exercise.slug] = exercise.id

    # Second pass: link easier/harder exercises
    for ex_data in exercises_data:
        exercise_id = slug_to_id.get(ex_data["slug"])
        if not exercise_id:
            continue

        result = await session.execute(
            select(Exercise).where(Exercise.id == exercise_id)
        )
        exercise = result.scalar_one()

        easier_slug = ex_data.get("easier")
        harder_slug = ex_data.get("harder")

        if easier_slug and easier_slug in slug_to_id:
            exercise.easier_exercise_id = slug_to_id[easier_slug]

        if harder_slug and harder_slug in slug_to_id:
            exercise.harder_exercise_id = slug_to_id[harder_slug]

    await session.commit()


# Title catalog (roadmap 1.2). Free titles unlock by level (price 0); the rest
# cost coins. Equipping reuses the generic shop (item_type="title").
TITLES = [
    # slug, name, name_ru, price_coins, required_level
    ("title-novice", "Novice", "Новичок", 0, 1),
    ("title-sportsman", "Sportsman", "Спортсмен", 0, 5),
    ("title-athlete", "Athlete", "Атлет", 0, 10),
    ("title-iron-warrior", "Iron Warrior", "Железный воин", 150, 8),
    ("title-fitness-legend", "Fitness Legend", "Легенда фитнеса", 500, 15),
]


async def load_titles(session: AsyncSession) -> None:
    """Seed title shop items (idempotent by slug)."""
    for slug, name, name_ru, price, level in TITLES:
        result = await session.execute(
            select(ShopItem).where(ShopItem.slug == slug)
        )
        item = result.scalar_one_or_none()
        if not item:
            session.add(ShopItem(
                slug=slug,
                name=name,
                name_ru=name_ru,
                item_type="title",
                price_coins=price,
                required_level=level,
                sprite_url=None,
                is_active=True,
            ))
    await session.commit()


async def init_data(session: AsyncSession) -> None:
    """Initialize all data from JSON files."""
    await load_exercises(session)
    await load_titles(session)
