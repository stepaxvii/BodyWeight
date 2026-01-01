from datetime import date, timedelta
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, func

from app.api.deps import AsyncSessionDep, CurrentUser
from app.db.models import (
    User,
    WorkoutSession,
    UserAchievement,
    UserAvatarPurchase,
)
from app.services.xp_calculator import xp_for_level
from app.schemas import (
    UserResponse,
    UserStatsResponse,
    UpdateUserRequest,
    UserProfileResponse,
)


def get_week_start(d: date) -> date:
    """Get Monday of the current week."""
    return d - timedelta(days=d.weekday())


# Avatar prices and requirements (must match frontend)
AVATAR_DATA = {
    # Free avatars
    'shadow-wolf': {'price': 0, 'required_level': 1},
    'iron-bear': {'price': 0, 'required_level': 1},
    'fire-fox': {'price': 0, 'required_level': 1},
    'night-panther': {'price': 0, 'required_level': 1},
    # Paid avatars
    'phoenix': {'price': 100, 'required_level': 3},
    'griffin': {'price': 200, 'required_level': 5},
    'cerberus': {'price': 300, 'required_level': 7},
    'thunder-fang': {'price': 350, 'required_level': 7},
    'cyber-ape': {'price': 375, 'required_level': 7},
    'hydra': {'price': 400, 'required_level': 10},
    'minotaur': {'price': 500, 'required_level': 12},
    'kraken': {'price': 750, 'required_level': 15},
    'leviathan': {'price': 1000, 'required_level': 20},
    'titan': {'price': 1500, 'required_level': 25},
}


router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Получить профиль текущего пользователя",
    description="Возвращает полную информацию о текущем аутентифицированном пользователе.",
    tags=["Users"]
)
async def get_current_user_profile(user: CurrentUser):
    return UserResponse.model_validate(user)


@router.get(
    "/me/purchased-avatars",
    response_model=list[str],
    summary="Получить купленные аватары",
    description="Возвращает список ID аватаров, купленных текущим пользователем.",
    tags=["Users"]
)
async def get_purchased_avatars(
    user: CurrentUser,
    session: AsyncSessionDep,
):
    result = await session.execute(
        select(UserAvatarPurchase.avatar_id)
        .where(UserAvatarPurchase.user_id == user.id)
    )
    purchased_avatar_ids = [row[0] for row in result.all()]
    return purchased_avatar_ids


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Обновить профиль пользователя",
    description="Обновляет настройки текущего пользователя (аватар, уведомления).",
    tags=["Users"]
)
async def update_current_user(
    user: CurrentUser,
    request: UpdateUserRequest,
    session: AsyncSessionDep,
):
    if request.avatar_id is not None:
        # Validate avatar_id is a valid option
        if request.avatar_id not in AVATAR_DATA:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid avatar_id",
            )

        avatar_info = AVATAR_DATA[request.avatar_id]

        # Check level requirement
        if user.level < avatar_info['required_level']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requires level {avatar_info['required_level']}",
            )

        # If avatar is paid and it's a new avatar, handle purchase
        price = avatar_info['price']
        is_new_avatar = request.avatar_id != user.avatar_id
        if price > 0 and is_new_avatar:
            # Check if user already owns this avatar
            purchase_check = await session.execute(
                select(UserAvatarPurchase)
                .where(UserAvatarPurchase.user_id == user.id)
                .where(UserAvatarPurchase.avatar_id == request.avatar_id)
            )
            existing_purchase = purchase_check.scalar_one_or_none()

            if not existing_purchase:
                # Check if user has enough coins
                if user.coins < price:
                    msg = f"Not enough coins. Need {price}, have {user.coins}"
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=msg,
                    )

                # Deduct coins
                user.coins -= price

                # Store purchase
                purchase = UserAvatarPurchase(
                    user_id=user.id,
                    avatar_id=request.avatar_id,
                )
                session.add(purchase)

        # Update avatar
        user.avatar_id = request.avatar_id
    if request.notification_time is not None:
        user.notification_time = request.notification_time
    if request.notifications_enabled is not None:
        user.notifications_enabled = request.notifications_enabled

    await session.flush()
    await session.refresh(user)
    return UserResponse.model_validate(user)


@router.post("/me/complete-onboarding", response_model=UserResponse)
async def complete_onboarding(
    user: CurrentUser,
    session: AsyncSessionDep,
):
    """Mark user as onboarded."""
    user.is_onboarded = True
    await session.flush()
    await session.refresh(user)
    return UserResponse.model_validate(user)


@router.get(
    "/me/stats",
    response_model=UserStatsResponse,
    summary="Получить статистику пользователя",
    description="Возвращает подробную статистику пользователя: тренировки, XP, уровень, streak, достижения, монеты и т.д.",
    tags=["Users"]
)
async def get_current_user_stats(
    user: CurrentUser,
    session: AsyncSessionDep,
):
    # Total workouts
    workouts_result = await session.execute(
        select(func.count(WorkoutSession.id))
        .where(WorkoutSession.user_id == user.id)
        .where(WorkoutSession.status == "completed")
    )
    total_workouts = workouts_result.scalar() or 0

    # Total reps
    reps_result = await session.execute(
        select(func.sum(WorkoutSession.total_reps))
        .where(WorkoutSession.user_id == user.id)
        .where(WorkoutSession.status == "completed")
    )
    total_reps = reps_result.scalar() or 0

    # Total workout time (sum of duration_seconds, convert to minutes)
    time_result = await session.execute(
        select(func.sum(WorkoutSession.duration_seconds))
        .where(WorkoutSession.user_id == user.id)
        .where(WorkoutSession.status == "completed")
        .where(WorkoutSession.duration_seconds.isnot(None))
    )
    total_time_seconds = time_result.scalar() or 0
    total_time_minutes = total_time_seconds // 60

    # Achievements count
    achievements_result = await session.execute(
        select(func.count(UserAchievement.id))
        .where(UserAchievement.user_id == user.id)
    )
    achievements_count = achievements_result.scalar() or 0

    # This week stats
    week_start = get_week_start(date.today())
    week_workouts_result = await session.execute(
        select(func.count(WorkoutSession.id))
        .where(WorkoutSession.user_id == user.id)
        .where(WorkoutSession.status == "completed")
        .where(func.date(WorkoutSession.started_at) >= week_start)
    )
    this_week_workouts = week_workouts_result.scalar() or 0

    week_xp_result = await session.execute(
        select(func.sum(WorkoutSession.total_xp_earned))
        .where(WorkoutSession.user_id == user.id)
        .where(WorkoutSession.status == "completed")
        .where(func.date(WorkoutSession.started_at) >= week_start)
    )
    this_week_xp = week_xp_result.scalar() or 0

    # Level progress
    current_level = user.level
    current_level_xp = xp_for_level(current_level)
    next_level_xp = xp_for_level(current_level + 1)
    xp_in_current_level = user.total_xp - current_level_xp
    xp_needed_for_level = next_level_xp - current_level_xp
    if xp_needed_for_level > 0:
        xp_progress_percent = (xp_in_current_level / xp_needed_for_level) * 100
    else:
        xp_progress_percent = 0

    return UserStatsResponse(
        total_workouts=total_workouts,
        total_xp=user.total_xp,
        total_reps=total_reps,
        total_time_minutes=total_time_minutes,
        current_level=current_level,
        xp_for_next_level=next_level_xp,
        xp_progress_percent=min(xp_progress_percent, 100),
        current_streak=user.current_streak,
        max_streak=user.max_streak,
        achievements_count=achievements_count,
        coins=user.coins,
        this_week_workouts=this_week_workouts,
        this_week_xp=this_week_xp,
    )




@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    session: AsyncSessionDep,
    current_user: CurrentUser,  # Require auth to view profiles
):
    """Get user profile by ID (public info only)."""
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse.model_validate(user)


@router.get("/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: int,
    session: AsyncSessionDep,
    current_user: CurrentUser,
):
    """Get user profile with achievements and friendship status."""
    from app.db.models import Friendship

    # Get user
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Get unlocked achievements
    achievements_result = await session.execute(
        select(UserAchievement.achievement_slug)
        .where(UserAchievement.user_id == user_id)
    )
    achievements = [row[0] for row in achievements_result.all()]

    # Check friendship status
    # For accepted friendships, there are 2 records (bidirectional).
    # For pending, only 1 record exists (from requester to target).
    is_friend = False
    friend_request_sent = False
    friend_request_received = False
    friendship_id = None

    if current_user.id != user_id:
        # Check friendship from current user's side (I → them)
        friendship_result = await session.execute(
            select(Friendship)
            .where(Friendship.user_id == current_user.id)
            .where(Friendship.friend_id == user_id)
        )
        friendship = friendship_result.scalar_one_or_none()

        if friendship:
            is_friend = friendship.status == "accepted"
            friend_request_sent = friendship.status == "pending"
            friendship_id = friendship.id
        else:
            # Check reverse direction (them → me)
            reverse_result = await session.execute(
                select(Friendship)
                .where(Friendship.user_id == user_id)
                .where(Friendship.friend_id == current_user.id)
                .where(Friendship.status == "pending")
            )
            reverse_friendship = reverse_result.scalar_one_or_none()
            if reverse_friendship:
                friend_request_received = True
                friendship_id = reverse_friendship.id

    return UserProfileResponse(
        id=user.id,
        username=user.username,
        first_name=user.first_name,
        avatar_id=user.avatar_id or "shadow-wolf",
        level=user.level,
        total_xp=user.total_xp,
        coins=user.coins,
        current_streak=user.current_streak,
        achievements=achievements,
        is_friend=is_friend,
        friend_request_sent=friend_request_sent,
        friend_request_received=friend_request_received,
        friendship_id=friendship_id,
    )
