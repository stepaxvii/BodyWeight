from typing import List
from fastapi import APIRouter, HTTPException, Query, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select, or_, and_

from app.api.deps import AsyncSessionDep, CurrentUser
from app.db.models import User, Friendship, Notification
from app.services.notifications import send_friend_request_notification, send_friend_accepted_notification

router = APIRouter()


class FriendResponse(BaseModel):
    id: int
    user_id: int
    username: str | None
    first_name: str | None
    avatar_id: str
    level: int
    total_xp: int
    current_streak: int
    status: str

    class Config:
        from_attributes = True


class AddFriendRequest(BaseModel):
    user_id: int | None = None
    username: str | None = None


@router.get("", response_model=List[FriendResponse])
async def get_friends(
    session: AsyncSessionDep,
    user: CurrentUser,
    status_filter: str = Query("accepted", description="Filter by status: accepted, pending, all"),
):
    """Get list of friends."""
    query = (
        select(Friendship, User)
        .join(User, Friendship.friend_id == User.id)
        .where(Friendship.user_id == user.id)
    )

    if status_filter != "all":
        query = query.where(Friendship.status == status_filter)

    result = await session.execute(query)
    rows = result.all()

    return [
        FriendResponse(
            id=friendship.id,
            user_id=friend.id,
            username=friend.username,
            first_name=friend.first_name,
            avatar_id=friend.avatar_id,
            level=friend.level,
            total_xp=friend.total_xp,
            current_streak=friend.current_streak,
            status=friendship.status,
        )
        for friendship, friend in rows
    ]


@router.get("/requests", response_model=List[FriendResponse])
async def get_friend_requests(
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """Get pending friend requests (where someone added current user)."""
    result = await session.execute(
        select(Friendship, User)
        .join(User, Friendship.user_id == User.id)
        .where(Friendship.friend_id == user.id)
        .where(Friendship.status == "pending")
    )
    rows = result.all()

    return [
        FriendResponse(
            id=friendship.id,
            user_id=from_user.id,
            username=from_user.username,
            first_name=from_user.first_name,
            avatar_id=from_user.avatar_id,
            level=from_user.level,
            total_xp=from_user.total_xp,
            current_streak=from_user.current_streak,
            status=friendship.status,
        )
        for friendship, from_user in rows
    ]


@router.post("/add", response_model=FriendResponse)
async def add_friend(
    request: AddFriendRequest,
    session: AsyncSessionDep,
    user: CurrentUser,
    background_tasks: BackgroundTasks,
):
    """Send friend request."""
    if not request.user_id and not request.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either user_id or username is required",
        )

    # Find target user
    if request.user_id:
        result = await session.execute(
            select(User).where(User.id == request.user_id)
        )
    else:
        result = await session.execute(
            select(User).where(User.username == request.username)
        )

    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if target_user.id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add yourself as friend",
        )

    # Check existing friendship
    existing_result = await session.execute(
        select(Friendship)
        .where(Friendship.user_id == user.id)
        .where(Friendship.friend_id == target_user.id)
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Friend request already exists (status: {existing.status})",
        )

    # Create friendship
    friendship = Friendship(
        user_id=user.id,
        friend_id=target_user.id,
        status="pending",
    )
    session.add(friendship)
    await session.flush()

    # Send notification to target user in background
    from_name = user.username or user.first_name or "Пользователь"
    background_tasks.add_task(
        send_friend_request_notification,
        telegram_id=target_user.telegram_id,
        from_user_name=from_name,
    )

    # Save notification to database for badge counter
    notification = Notification(
        user_id=target_user.id,
        notification_type="friend_request",
        title="Новая заявка в друзья!",
        message=f"{from_name} хочет добавить тебя в друзья.",
        related_user_id=user.id,
    )
    session.add(notification)
    await session.flush()

    return FriendResponse(
        id=friendship.id,
        user_id=target_user.id,
        username=target_user.username,
        first_name=target_user.first_name,
        avatar_id=target_user.avatar_id,
        level=target_user.level,
        total_xp=target_user.total_xp,
        current_streak=target_user.current_streak,
        status=friendship.status,
    )


@router.post("/accept/{friendship_id}", response_model=FriendResponse)
async def accept_friend_request(
    friendship_id: int,
    session: AsyncSessionDep,
    user: CurrentUser,
    background_tasks: BackgroundTasks,
):
    """Accept a friend request."""
    result = await session.execute(
        select(Friendship)
        .where(Friendship.id == friendship_id)
        .where(Friendship.friend_id == user.id)
        .where(Friendship.status == "pending")
    )
    friendship = result.scalar_one_or_none()

    if not friendship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friend request not found",
        )

    # Update status
    friendship.status = "accepted"

    # Create reverse friendship
    reverse = Friendship(
        user_id=user.id,
        friend_id=friendship.user_id,
        status="accepted",
    )
    session.add(reverse)

    # Get the friend user (who sent the original request)
    friend_result = await session.execute(
        select(User).where(User.id == friendship.user_id)
    )
    friend_user = friend_result.scalar_one()

    await session.flush()

    # Notify the original requester that their request was accepted
    accepter_name = user.username or user.first_name or "Пользователь"
    background_tasks.add_task(
        send_friend_accepted_notification,
        telegram_id=friend_user.telegram_id,
        friend_name=accepter_name,
    )

    # Save notification to database for badge counter
    notification = Notification(
        user_id=friend_user.id,
        notification_type="friend_accepted",
        title="Заявка принята!",
        message=f"{accepter_name} теперь твой друг.",
        related_user_id=user.id,
    )
    session.add(notification)
    await session.flush()

    return FriendResponse(
        id=reverse.id,
        user_id=friend_user.id,
        username=friend_user.username,
        first_name=friend_user.first_name,
        avatar_id=friend_user.avatar_id,
        level=friend_user.level,
        total_xp=friend_user.total_xp,
        current_streak=friend_user.current_streak,
        status=reverse.status,
    )


@router.delete("/{friendship_id}")
async def remove_friend(
    friendship_id: int,
    session: AsyncSessionDep,
    user: CurrentUser,
):
    """Remove a friend or decline a friend request."""
    result = await session.execute(
        select(Friendship)
        .where(Friendship.id == friendship_id)
        .where(
            or_(
                Friendship.user_id == user.id,
                Friendship.friend_id == user.id,
            )
        )
    )
    friendship = result.scalar_one_or_none()

    if not friendship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friendship not found",
        )

    # Also remove reverse friendship if it exists
    if friendship.status == "accepted":
        reverse_result = await session.execute(
            select(Friendship)
            .where(Friendship.user_id == friendship.friend_id)
            .where(Friendship.friend_id == friendship.user_id)
        )
        reverse = reverse_result.scalar_one_or_none()
        if reverse:
            await session.delete(reverse)

    await session.delete(friendship)

    return {"message": "Friend removed"}


@router.get("/search", response_model=List[FriendResponse])
async def search_users(
    session: AsyncSessionDep,
    user: CurrentUser,
    q: str = Query(..., min_length=2, description="Search query (username or name)"),
    limit: int = Query(10, ge=1, le=50),
):
    """Search users by username or name."""
    search_pattern = f"%{q}%"

    result = await session.execute(
        select(User)
        .where(User.id != user.id)
        .where(
            or_(
                User.username.ilike(search_pattern),
                User.first_name.ilike(search_pattern),
                User.last_name.ilike(search_pattern),
            )
        )
        .limit(limit)
    )
    users = result.scalars().all()

    # Get existing friendships
    friend_result = await session.execute(
        select(Friendship)
        .where(Friendship.user_id == user.id)
        .where(Friendship.friend_id.in_([u.id for u in users]))
    )
    friendships = {f.friend_id: f for f in friend_result.scalars().all()}

    return [
        FriendResponse(
            id=friendships[u.id].id if u.id in friendships else 0,
            user_id=u.id,
            username=u.username,
            first_name=u.first_name,
            avatar_id=u.avatar_id,
            level=u.level,
            total_xp=u.total_xp,
            current_streak=u.current_streak,
            status=friendships[u.id].status if u.id in friendships else "none",
        )
        for u in users
    ]
