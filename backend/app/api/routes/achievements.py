from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import AsyncSessionDep, CurrentUser
from app.db.models import UserAchievement
from app.utils.achievement_loader import load_achievements, get_achievement_by_slug

router = APIRouter()


class AchievementResponse(BaseModel):
    slug: str
    name: str
    name_ru: str
    description: str
    description_ru: str
    icon: str
    xp_reward: int
    coin_reward: int
    unlocked: bool
    unlocked_at: str | None = None
    condition: dict


class RecentAchievementResponse(BaseModel):
    slug: str
    name: str
    name_ru: str
    icon: str
    unlocked_at: str


@router.get("", response_model=list[AchievementResponse])
async def get_achievements(
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """Get all achievements with unlock status for current user."""
    achievements_data = load_achievements()

    # Get user's unlocked achievements
    result = await session.execute(
        select(UserAchievement)
        .where(UserAchievement.user_id == user.id)
    )
    user_achievements = {ua.achievement_slug: ua for ua in result.scalars().all()}

    response = []
    for ach in achievements_data:
        user_ach = user_achievements.get(ach["slug"])
        response.append(AchievementResponse(
            slug=ach["slug"],
            name=ach["name"],
            name_ru=ach["name_ru"],
            description=ach["description"],
            description_ru=ach["description_ru"],
            icon=ach["icon"],
            xp_reward=ach.get("xp_reward", 0),
            coin_reward=ach.get("coin_reward", 0),
            unlocked=user_ach is not None,
            unlocked_at=user_ach.unlocked_at.isoformat() if user_ach else None,
            condition=ach.get("condition", {}),
        ))

    return response


@router.get("/recent", response_model=list[RecentAchievementResponse])
async def get_recent_achievements(
    session: AsyncSessionDep,
    user: CurrentUser,
    limit: int = Query(5, ge=1, le=20),
):
    """Get recently unlocked achievements."""
    achievements_data = load_achievements()
    achievements_by_slug = {a["slug"]: a for a in achievements_data}

    result = await session.execute(
        select(UserAchievement)
        .where(UserAchievement.user_id == user.id)
        .order_by(UserAchievement.unlocked_at.desc())
        .limit(limit)
    )
    user_achievements = result.scalars().all()

    response = []
    for ua in user_achievements:
        ach = achievements_by_slug.get(ua.achievement_slug)
        if ach:
            response.append(RecentAchievementResponse(
                slug=ua.achievement_slug,
                name=ach["name"],
                name_ru=ach["name_ru"],
                icon=ach["icon"],
                unlocked_at=ua.unlocked_at.isoformat(),
            ))

    return response
