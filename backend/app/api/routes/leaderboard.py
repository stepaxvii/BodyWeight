from datetime import datetime, timedelta
from fastapi import APIRouter, Query
from sqlalchemy import select, func, and_, or_

from app.api.deps import AsyncSessionDep, CurrentUser
from app.db.models import User, WorkoutSession, Friendship
from app.schemas import LeaderboardEntry, LeaderboardResponse

router = APIRouter()


@router.get(
    "",
    response_model=LeaderboardResponse,
    summary="Глобальный рейтинг",
    description="Возвращает глобальный рейтинг пользователей по общему количеству XP.",
    tags=["Leaderboard"]
)
async def get_global_leaderboard(
    session: AsyncSessionDep,
    user: CurrentUser,
    limit: int = Query(50, ge=1, le=100, description="Максимальное количество пользователей в рейтинге"),
):
    # SQLite может хранить boolean как 0/1 или как строки 'false'/'true'
    visible = or_(User.leaderboard_visible.is_(True), User.leaderboard_visible == "true")
    result = await session.execute(
        select(User)
        .where(visible)
        .order_by(User.total_xp.desc())
        .limit(limit)
    )
    users = list(result.scalars().all())
    entries = []
    current_user_rank = None

    for rank, u in enumerate(users, 1):
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
            total_xp=u.total_xp,
            current_streak=u.current_streak,
            is_current_user=is_current,
        ))

    # If current user is not in top (or not in leaderboard), find their rank among visible users
    if current_user_rank is None:
        rank_result = await session.execute(
            select(func.count(User.id))
            .where(visible)
            .where(User.total_xp > user.total_xp)
        )
        current_user_rank = (rank_result.scalar() or 0) + 1

    return LeaderboardResponse(
        entries=entries,
        current_user_rank=current_user_rank,
    )


@router.get(
    "/weekly",
    response_model=LeaderboardResponse,
    summary="Недельный рейтинг",
    description="Возвращает рейтинг пользователей по XP, заработанным на текущей неделе (с понедельника).",
    tags=["Leaderboard"]
)
async def get_weekly_leaderboard(
    session: AsyncSessionDep,
    user: CurrentUser,
    limit: int = Query(50, ge=1, le=100, description="Максимальное количество пользователей в рейтинге"),
):
    # Calculate week start (Monday)
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

    visible = or_(User.leaderboard_visible.is_(True), User.leaderboard_visible == "true")
    result = await session.execute(
        select(User, weekly_xp_subq.c.weekly_xp)
        .join(weekly_xp_subq, User.id == weekly_xp_subq.c.user_id)
        .where(visible)
        .order_by(weekly_xp_subq.c.weekly_xp.desc())
        .limit(limit)
    )
    rows = result.all()

    entries = []
    current_user_rank = None

    for rank, (u, weekly_xp) in enumerate(rows, 1):
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
            total_xp=weekly_xp or 0,  # This is weekly XP
            current_streak=u.current_streak,
            is_current_user=is_current,
        ))

    return LeaderboardResponse(
        entries=entries,
        current_user_rank=current_user_rank,
    )


@router.get(
    "/friends",
    response_model=LeaderboardResponse,
    summary="Рейтинг друзей",
    description="Возвращает рейтинг среди друзей текущего пользователя по общему количеству XP.",
    tags=["Leaderboard"]
)
async def get_friends_leaderboard(
    session: AsyncSessionDep,
    user: CurrentUser,
):
    visible = or_(User.leaderboard_visible.is_(True), User.leaderboard_visible == "true")
    stmt = (
        select(User)
        .join(
            Friendship,
            and_(
                Friendship.friend_id == User.id,
                Friendship.user_id == user.id,
                Friendship.status == "accepted"
            )
        )
        .where(visible)
        .order_by(User.total_xp.desc())
        .limit(50)
    )

    result = await session.execute(stmt)
    friends = list(result.scalars().all())

    # Add current user only if they consented to leaderboard
    friends_with_me = ([user] if user.leaderboard_visible else []) + friends
    friends_with_me.sort(key=lambda u: u.total_xp, reverse=True)

    entries = []
    current_user_rank = None

    for rank, u in enumerate(friends_with_me, 1):
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
            total_xp=u.total_xp,
            current_streak=u.current_streak,
            is_current_user=is_current,
        ))

    return LeaderboardResponse(
        entries=entries,
        current_user_rank=current_user_rank,
    )
