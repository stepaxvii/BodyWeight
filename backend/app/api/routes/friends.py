from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.api.deps import get_current_user
from app.db.database import get_session
from app.db.models import User, Friendship, FriendshipStatus

router = APIRouter(prefix="/friends", tags=["friends"])


class FriendResponse(BaseModel):
    id: int
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    level: int
    experience: int
    streak_days: int
    total_workouts: int
    status: str


class FriendRequest(BaseModel):
    username: str


@router.get("/", response_model=List[FriendResponse])
async def get_friends(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get list of friends."""
    # Get accepted friendships where user is either side
    result = await session.execute(
        select(Friendship, User)
        .join(User, User.id == Friendship.friend_id)
        .where(Friendship.user_id == user.id)
        .where(Friendship.status == FriendshipStatus.ACCEPTED)
    )
    rows = result.all()

    return [
        FriendResponse(
            id=f.id,
            user_id=u.id,
            username=u.username,
            first_name=u.first_name,
            level=u.level,
            experience=u.experience,
            streak_days=u.streak_days,
            total_workouts=u.total_workouts,
            status=f.status.value,
        )
        for f, u in rows
    ]


@router.get("/requests", response_model=List[FriendResponse])
async def get_friend_requests(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get pending friend requests."""
    result = await session.execute(
        select(Friendship, User)
        .join(User, User.id == Friendship.user_id)
        .where(Friendship.friend_id == user.id)
        .where(Friendship.status == FriendshipStatus.PENDING)
    )
    rows = result.all()

    return [
        FriendResponse(
            id=f.id,
            user_id=u.id,
            username=u.username,
            first_name=u.first_name,
            level=u.level,
            experience=u.experience,
            streak_days=u.streak_days,
            total_workouts=u.total_workouts,
            status=f.status.value,
        )
        for f, u in rows
    ]


@router.post("/add")
async def add_friend(
    data: FriendRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Send friend request by username."""
    # Find user by username
    result = await session.execute(
        select(User).where(User.username == data.username)
    )
    friend = result.scalar_one_or_none()

    if not friend:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if friend.id == user.id:
        raise HTTPException(status_code=400, detail="Нельзя добавить себя в друзья")

    # Check if friendship exists
    result = await session.execute(
        select(Friendship)
        .where(
            or_(
                and_(Friendship.user_id == user.id, Friendship.friend_id == friend.id),
                and_(Friendship.user_id == friend.id, Friendship.friend_id == user.id),
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        if existing.status == FriendshipStatus.ACCEPTED:
            raise HTTPException(status_code=400, detail="Вы уже друзья")
        elif existing.status == FriendshipStatus.PENDING:
            raise HTTPException(status_code=400, detail="Запрос уже отправлен")

    # Create friendship request
    friendship = Friendship(
        user_id=user.id,
        friend_id=friend.id,
        status=FriendshipStatus.PENDING,
    )
    session.add(friendship)
    await session.commit()

    return {"message": "Запрос отправлен"}


@router.post("/{friendship_id}/accept")
async def accept_friend(
    friendship_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Accept friend request."""
    result = await session.execute(
        select(Friendship)
        .where(Friendship.id == friendship_id)
        .where(Friendship.friend_id == user.id)
        .where(Friendship.status == FriendshipStatus.PENDING)
    )
    friendship = result.scalar_one_or_none()

    if not friendship:
        raise HTTPException(status_code=404, detail="Запрос не найден")

    friendship.status = FriendshipStatus.ACCEPTED

    # Create reverse friendship
    reverse = Friendship(
        user_id=user.id,
        friend_id=friendship.user_id,
        status=FriendshipStatus.ACCEPTED,
    )
    session.add(reverse)

    await session.commit()

    return {"message": "Друг добавлен"}


@router.post("/{friendship_id}/reject")
async def reject_friend(
    friendship_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Reject friend request."""
    result = await session.execute(
        select(Friendship)
        .where(Friendship.id == friendship_id)
        .where(Friendship.friend_id == user.id)
        .where(Friendship.status == FriendshipStatus.PENDING)
    )
    friendship = result.scalar_one_or_none()

    if not friendship:
        raise HTTPException(status_code=404, detail="Запрос не найден")

    friendship.status = FriendshipStatus.REJECTED
    await session.commit()

    return {"message": "Запрос отклонён"}


@router.delete("/{friend_id}")
async def remove_friend(
    friend_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Remove friend."""
    # Delete both directions
    result = await session.execute(
        select(Friendship)
        .where(
            or_(
                and_(Friendship.user_id == user.id, Friendship.friend_id == friend_id),
                and_(Friendship.user_id == friend_id, Friendship.friend_id == user.id),
            )
        )
    )
    friendships = result.scalars().all()

    for f in friendships:
        await session.delete(f)

    await session.commit()

    return {"message": "Друг удалён"}
