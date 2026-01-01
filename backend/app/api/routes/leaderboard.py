import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Query
from sqlalchemy import select, func, and_

from app.api.deps import AsyncSessionDep, CurrentUser
from app.db.models import User, WorkoutSession, Friendship
from app.schemas import LeaderboardEntry, LeaderboardResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=LeaderboardResponse)
async def get_global_leaderboard(
    session: AsyncSessionDep,
    user: CurrentUser,
    limit: int = Query(50, ge=1, le=100),
):
    """Get global leaderboard by total XP."""
    logger.warning(f"[Leaderboard/Global] === REQUEST RECEIVED === user_id={user.id}, limit={limit}")

    # Debug: count all users
    count_result = await session.execute(select(func.count(User.id)))
    total_count = count_result.scalar()
    logger.info(f"[Leaderboard] Total users in database: {total_count}")

    result = await session.execute(
        select(User)
        .order_by(User.total_xp.desc())
        .limit(limit)
    )
    users = list(result.scalars().all())

    logger.info(f"[Leaderboard] Found {len(users)} users in query result")
    for u in users[:3]:  # Log first 3 users for debug
        logger.info(f"[Leaderboard] User: id={u.id}, username={u.username}, xp={u.total_xp}")

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

    # If current user is not in top, find their rank
    if current_user_rank is None:
        rank_result = await session.execute(
            select(func.count(User.id))
            .where(User.total_xp > user.total_xp)
        )
        current_user_rank = (rank_result.scalar() or 0) + 1

    return LeaderboardResponse(
        entries=entries,
        current_user_rank=current_user_rank,
    )


@router.get("/weekly", response_model=LeaderboardResponse)
async def get_weekly_leaderboard(
    session: AsyncSessionDep,
    user: CurrentUser,
    limit: int = Query(50, ge=1, le=100),
):
    """Get weekly leaderboard by XP earned this week."""
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

    result = await session.execute(
        select(User, weekly_xp_subq.c.weekly_xp)
        .join(weekly_xp_subq, User.id == weekly_xp_subq.c.user_id)
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


@router.get("/friends", response_model=LeaderboardResponse)
async def get_friends_leaderboard(
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """Get leaderboard among friends with optimized JOIN query."""
    logger.info(f"[Leaderboard/Friends] Getting friends leaderboard, user_id={user.id}")

    # Optimized: One JOIN query instead of two separate queries
    # Get friends where current user is the requester
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
        .order_by(User.total_xp.desc())
        .limit(50)
    )

    result = await session.execute(stmt)
    friends = list(result.scalars().all())
    logger.info(f"[Leaderboard/Friends] Found {len(friends)} friends via JOIN")

    # Add current user to the list
    friends_with_me = [user] + friends
    # Re-sort to include current user in correct position
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
