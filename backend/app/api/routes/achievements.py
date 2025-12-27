import json
from pathlib import Path
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime

from app.api.deps import get_current_user
from app.db.database import get_session
from app.db.models import User, Achievement, UserAchievement

router = APIRouter(prefix="/achievements", tags=["achievements"])


class AchievementResponse(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    category: str
    threshold: int
    exp_reward: int
    is_unlocked: bool
    unlocked_at: Optional[datetime]


@router.get("/", response_model=List[AchievementResponse])
async def get_achievements(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get all achievements with unlock status."""
    # Get all achievements
    result = await session.execute(select(Achievement))
    achievements = result.scalars().all()

    # Get user's unlocked achievements
    result = await session.execute(
        select(UserAchievement)
        .where(UserAchievement.user_id == user.id)
    )
    unlocked = {ua.achievement_id: ua.unlocked_at for ua in result.scalars().all()}

    return [
        AchievementResponse(
            id=a.id,
            name=a.name,
            description=a.description,
            icon=a.icon,
            category=a.category,
            threshold=a.threshold,
            exp_reward=a.exp_reward,
            is_unlocked=a.id in unlocked,
            unlocked_at=unlocked.get(a.id),
        )
        for a in achievements
    ]


@router.get("/unlocked", response_model=List[AchievementResponse])
async def get_unlocked_achievements(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get user's unlocked achievements."""
    result = await session.execute(
        select(UserAchievement, Achievement)
        .join(Achievement)
        .where(UserAchievement.user_id == user.id)
        .order_by(UserAchievement.unlocked_at.desc())
    )
    rows = result.all()

    return [
        AchievementResponse(
            id=a.id,
            name=a.name,
            description=a.description,
            icon=a.icon,
            category=a.category,
            threshold=a.threshold,
            exp_reward=a.exp_reward,
            is_unlocked=True,
            unlocked_at=ua.unlocked_at,
        )
        for ua, a in rows
    ]


@router.post("/check")
async def check_achievements(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Check and unlock new achievements."""
    from app.db.models import Workout, WorkoutExercise
    from sqlalchemy import func

    # Get all achievements
    result = await session.execute(select(Achievement))
    all_achievements = result.scalars().all()

    # Get already unlocked
    result = await session.execute(
        select(UserAchievement.achievement_id)
        .where(UserAchievement.user_id == user.id)
    )
    unlocked_ids = {row[0] for row in result.all()}

    new_unlocks = []

    for achievement in all_achievements:
        if achievement.id in unlocked_ids:
            continue

        unlocked = False

        # Check streak achievements
        if achievement.category == "streak":
            if user.streak_days >= achievement.threshold:
                unlocked = True

        # Check volume achievements
        elif achievement.category == "volume":
            if "reps" in achievement.id:
                if user.total_reps >= achievement.threshold:
                    unlocked = True
            elif "workouts" in achievement.id:
                if user.total_workouts >= achievement.threshold:
                    unlocked = True

        # Check level achievements
        elif achievement.category == "level":
            if user.level >= achievement.threshold:
                unlocked = True

        # Check record achievements (simplified)
        elif achievement.category == "record":
            if "pushups" in achievement.id:
                result = await session.execute(
                    select(func.max(WorkoutExercise.reps))
                    .join(Workout)
                    .where(Workout.user_id == user.id)
                    .where(WorkoutExercise.exercise_id == 1)  # Push-ups
                )
                max_reps = result.scalar() or 0
                if max_reps >= achievement.threshold:
                    unlocked = True

            elif "pullups" in achievement.id:
                result = await session.execute(
                    select(func.max(WorkoutExercise.reps))
                    .join(Workout)
                    .where(Workout.user_id == user.id)
                    .where(WorkoutExercise.exercise_id == 10)  # Pull-ups
                )
                max_reps = result.scalar() or 0
                if max_reps >= achievement.threshold:
                    unlocked = True

            elif "plank" in achievement.id:
                result = await session.execute(
                    select(func.max(WorkoutExercise.duration_seconds))
                    .join(Workout)
                    .where(Workout.user_id == user.id)
                    .where(WorkoutExercise.exercise_id == 40)  # Plank
                )
                max_time = result.scalar() or 0
                if max_time >= achievement.threshold:
                    unlocked = True

        if unlocked:
            user_achievement = UserAchievement(
                user_id=user.id,
                achievement_id=achievement.id,
            )
            session.add(user_achievement)
            user.experience += achievement.exp_reward
            new_unlocks.append({
                "id": achievement.id,
                "name": achievement.name,
                "icon": achievement.icon,
                "exp_reward": achievement.exp_reward,
            })

    if new_unlocks:
        await session.commit()

    return {"new_achievements": new_unlocks}


async def seed_achievements(session: AsyncSession):
    """Seed achievements from JSON file."""
    data_path = Path(__file__).parent.parent.parent / "data" / "achievements.json"

    if not data_path.exists():
        return

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for ach_data in data.get("achievements", []):
        result = await session.execute(
            select(Achievement).where(Achievement.id == ach_data["id"])
        )
        existing = result.scalar_one_or_none()

        if not existing:
            achievement = Achievement(
                id=ach_data["id"],
                name=ach_data["name"],
                description=ach_data["description"],
                icon=ach_data["icon"],
                category=ach_data["category"],
                threshold=ach_data["threshold"],
                exp_reward=ach_data.get("exp_reward", 100),
            )
            session.add(achievement)

    await session.commit()
