import logging
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import select, func, and_

from app.api.deps import AsyncSessionDep, CurrentUser
from app.db.models import User, WorkoutSession, Friendship

router = APIRouter()
logger = logging.getLogger(__name__)


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    username: str | None
    first_name: str | None
    avatar_id: str
    level: int
    total_xp: int
    current_streak: int
    is_current_user: bool = False


class LeaderboardResponse(BaseModel):
    entries: List[LeaderboardEntry]
    current_user_rank: int | None = None


@router.get("", response_model=LeaderboardResponse)
async def get_global_leaderboard(
    session: AsyncSessionDep,
    user: CurrentUser,
    limit: int = Query(50, ge=1, le=100),
):
    """Get global leaderboard by total XP."""
    logger.info(f"[Leaderboard] Getting global leaderboard, user_id={user.id}, limit={limit}")

    result = await session.execute(
        select(User)
        .order_by(User.total_xp.desc())
        .limit(limit)
    )
    users = result.scalars().all()

    logger.info(f"[Leaderboard] Found {len(users)} users")

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
    """Get leaderboard among friends."""
    # Get friend IDs
    friends_result = await session.execute(
        select(Friendship.friend_id)
        .where(Friendship.user_id == user.id)
        .where(Friendship.status == "accepted")
    )
    friend_ids = [row[0] for row in friends_result.all()]

    # Include current user
    all_ids = friend_ids + [user.id]

    result = await session.execute(
        select(User)
        .where(User.id.in_(all_ids))
        .order_by(User.total_xp.desc())
    )
    users = result.scalars().all()

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

    return LeaderboardResponse(
        entries=entries,
        current_user_rank=current_user_rank,
    )
