from datetime import datetime, timedelta
from fastapi import APIRouter
from sqlalchemy import select, func, and_

from app.api.deps import AsyncSessionDep, CurrentUser
from app.db.models import User, WorkoutSession, Friendship, ShopItem, UserPurchase
from app.schemas import LeaderboardEntry, LeaderboardResponse

router = APIRouter()


async def _equipped_titles(session, user_ids: list[int]) -> dict[int, str]:
    """Map user_id -> equipped title name (RU) for the given users (roadmap 1.2)."""
    if not user_ids:
        return {}
    result = await session.execute(
        select(UserPurchase.user_id, ShopItem.name_ru)
        .join(ShopItem, UserPurchase.shop_item_id == ShopItem.id)
        .where(UserPurchase.user_id.in_(user_ids))
        .where(UserPurchase.is_equipped.is_(True))
        .where(ShopItem.item_type == "title")
    )
    return {row[0]: row[1] for row in result.all()}


@router.get(
    "",
    response_model=LeaderboardResponse,
    summary="Недельный рейтинг друзей",
    description="Возвращает рейтинг среди друзей текущего пользователя по XP, заработанным на текущей неделе (с понедельника).",
    tags=["Leaderboard"]
)
async def get_friends_weekly_leaderboard(
    session: AsyncSessionDep,
    user: CurrentUser,
):
    # Calculate week start (Monday, 00:00 UTC)
    today = datetime.utcnow().date()
    week_start = today - timedelta(days=today.weekday())
    week_start_dt = datetime.combine(week_start, datetime.min.time())

    # Subquery to get weekly XP per user
    weekly_xp_subq = (
        select(
            WorkoutSession.user_id,
            func.sum(WorkoutSession.total_xp_earned).label("weekly_xp")
        )
        .where(WorkoutSession.status == "completed")
        .where(WorkoutSession.finished_at >= week_start_dt)
        .group_by(WorkoutSession.user_id)
        .subquery()
    )

    # Accepted friends; outerjoin + coalesce so friends with zero XP this week
    # still appear — small friend lists should look alive.
    weekly_xp = func.coalesce(weekly_xp_subq.c.weekly_xp, 0)
    stmt = (
        select(User, weekly_xp.label("weekly_xp"))
        .join(
            Friendship,
            and_(
                Friendship.friend_id == User.id,
                Friendship.user_id == user.id,
                Friendship.status == "accepted"
            )
        )
        .outerjoin(weekly_xp_subq, User.id == weekly_xp_subq.c.user_id)
        .where(User.leaderboard_visible.is_(True))
        .order_by(weekly_xp.desc())
        .limit(50)
    )

    result = await session.execute(stmt)
    rows = [(u, xp or 0) for u, xp in result.all()]

    # Add current user only if they consented to leaderboard
    if user.leaderboard_visible:
        my_xp_result = await session.execute(
            select(func.sum(WorkoutSession.total_xp_earned))
            .where(WorkoutSession.user_id == user.id)
            .where(WorkoutSession.status == "completed")
            .where(WorkoutSession.finished_at >= week_start_dt)
        )
        rows.append((user, my_xp_result.scalar() or 0))

    rows.sort(key=lambda row: row[1], reverse=True)
    titles = await _equipped_titles(session, [u.id for u, _ in rows])

    entries = []
    current_user_rank = None

    for rank, (u, xp) in enumerate(rows, 1):
        is_current = u.id == user.id
        if is_current:
            current_user_rank = rank

        entries.append(LeaderboardEntry(
            rank=rank,
            user_id=u.id,
            username=u.username,
            first_name=u.first_name,
            avatar_id=u.avatar_id,
            level=u.level,
            total_xp=xp,  # This is weekly XP
            current_streak=u.current_streak,
            equipped_title=titles.get(u.id),
            is_current_user=is_current,
        ))

    return LeaderboardResponse(
        entries=entries,
        current_user_rank=current_user_rank,
    )
