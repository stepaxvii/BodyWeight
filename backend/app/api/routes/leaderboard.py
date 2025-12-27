from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.api.deps import get_current_user
from app.db.database import get_session
from app.db.models import User, Friendship, FriendshipStatus

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    level: int
    experience: int
    streak_days: int
    total_workouts: int
    is_current_user: bool


class LeaderboardResponse(BaseModel):
    entries: List[LeaderboardEntry]
    total_users: int
    my_rank: Optional[int]


@router.get("/global", response_model=LeaderboardResponse)
async def get_global_leaderboard(
    limit: int = 50,
    sort_by: str = "experience",  # experience, streak, workouts
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get global leaderboard."""
    # Determine sort column
    if sort_by == "streak":
        order_col = User.streak_days
    elif sort_by == "workouts":
        order_col = User.total_workouts
    else:
        order_col = User.experience

    # Get total users
    result = await session.execute(select(func.count(User.id)))
    total_users = result.scalar() or 0

    # Get top users
    result = await session.execute(
        select(User)
        .where(User.is_active == True)
        .order_by(order_col.desc())
        .limit(limit)
    )
    users = result.scalars().all()

    entries = []
    for i, u in enumerate(users, 1):
        entries.append(LeaderboardEntry(
            rank=i,
            user_id=u.id,
            username=u.username,
            first_name=u.first_name,
            level=u.level,
            experience=u.experience,
            streak_days=u.streak_days,
            total_workouts=u.total_workouts,
            is_current_user=u.id == user.id,
        ))

    # Find current user's rank
    my_rank = None
    for entry in entries:
        if entry.is_current_user:
            my_rank = entry.rank
            break

    if my_rank is None:
        # User not in top, calculate their rank
        if sort_by == "streak":
            value = user.streak_days
            col = User.streak_days
        elif sort_by == "workouts":
            value = user.total_workouts
            col = User.total_workouts
        else:
            value = user.experience
            col = User.experience

        result = await session.execute(
            select(func.count(User.id))
            .where(User.is_active == True)
            .where(col > value)
        )
        my_rank = (result.scalar() or 0) + 1

    return LeaderboardResponse(
        entries=entries,
        total_users=total_users,
        my_rank=my_rank,
    )


@router.get("/friends", response_model=LeaderboardResponse)
async def get_friends_leaderboard(
    sort_by: str = "experience",
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get leaderboard among friends."""
    # Get friend IDs
    result = await session.execute(
        select(Friendship.friend_id)
        .where(Friendship.user_id == user.id)
        .where(Friendship.status == FriendshipStatus.ACCEPTED)
    )
    friend_ids = [row[0] for row in result.all()]

    # Add current user
    all_ids = friend_ids + [user.id]

    # Determine sort column
    if sort_by == "streak":
        order_col = User.streak_days
    elif sort_by == "workouts":
        order_col = User.total_workouts
    else:
        order_col = User.experience

    # Get friends
    result = await session.execute(
        select(User)
        .where(User.id.in_(all_ids))
        .order_by(order_col.desc())
    )
    users = result.scalars().all()

    entries = []
    my_rank = None
    for i, u in enumerate(users, 1):
        is_current = u.id == user.id
        if is_current:
            my_rank = i
        entries.append(LeaderboardEntry(
            rank=i,
            user_id=u.id,
            username=u.username,
            first_name=u.first_name,
            level=u.level,
            experience=u.experience,
            streak_days=u.streak_days,
            total_workouts=u.total_workouts,
            is_current_user=is_current,
        ))

    return LeaderboardResponse(
        entries=entries,
        total_users=len(entries),
        my_rank=my_rank,
    )
