from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import AsyncSessionDep, CurrentUser
from app.db.models import UserAchievement
from app.utils.achievement_loader import load_achievements
from app.schemas import (
    AchievementResponse, RecentAchievementResponse, PaginatedResponse
)

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[AchievementResponse],
    summary="Получить достижения",
    description="Возвращает список всех достижений с информацией о статусе разблокировки для текущего пользователя. Поддерживает пагинацию.",
    tags=["Achievements"]
)
async def get_achievements(
    session: AsyncSessionDep,
    user: CurrentUser,
    skip: int = Query(0, ge=0, description="Количество пропущенных элементов"),
    limit: int = Query(50, ge=1, le=100, description="Максимальное количество элементов"),
):
    achievements_data = load_achievements()

    # Get user's unlocked achievements
    result = await session.execute(
        select(UserAchievement)
        .where(UserAchievement.user_id == user.id)
    )
    user_achievements = {ua.achievement_slug: ua for ua in result.scalars().all()}

    # Build all achievements
    all_achievements = []
    for ach in achievements_data:
        user_ach = user_achievements.get(ach["slug"])
        all_achievements.append(AchievementResponse(
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

    # Calculate total
    total = len(all_achievements)

    # Apply pagination
    paginated_achievements = all_achievements[skip:skip + limit]

    return PaginatedResponse(
        items=paginated_achievements,
        total=total,
        skip=skip,
        limit=limit,
        has_more=skip + limit < total,
    )


@router.get(
    "/recent",
    response_model=list[RecentAchievementResponse],
    summary="Последние достижения",
    description="Возвращает список недавно разблокированных достижений пользователя.",
    tags=["Achievements"]
)
async def get_recent_achievements(
    session: AsyncSessionDep,
    user: CurrentUser,
    limit: int = Query(5, ge=1, le=20, description="Максимальное количество достижений"),
):
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
