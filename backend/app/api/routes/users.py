from datetime import date, timedelta
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, func

from app.api.deps import AsyncSessionDep, CurrentUser
from app.db.models import (
    User,
    WorkoutSession,
    UserAchievement,
    UserAvatarPurchase,
    UserExerciseProgress,
    Exercise,
    ShopItem,
    UserPurchase,
)
from app.services.xp_calculator import xp_for_level
from app.services.activity_norm import (
    get_norm_history,
    resolve_norm,
    set_user_norm,
)
from app.schemas import (
    UserResponse,
    UserStatsResponse,
    UpdateUserRequest,
    CompleteOnboardingRequest,
    UserProfileResponse,
    ExerciseRecord,
    UserRecordsResponse,
    DayActivityResponse,
    UserActivityResponse,
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
    # New heroes (Stardew redesign)
    'solar-lion': {'price': 350, 'required_level': 8},
    'crystal-stag': {'price': 450, 'required_level': 10},
    'storm-eagle': {'price': 600, 'required_level': 14},
    'void-serpent': {'price': 900, 'required_level': 18},
    'magma-golem': {'price': 1200, 'required_level': 22},
}


router = APIRouter()


async def get_equipped_title(session, user_id: int) -> str | None:
    """Name (RU) of the user's currently-equipped title, if any (roadmap 1.2)."""
    result = await session.execute(
        select(ShopItem.name_ru)
        .join(UserPurchase, UserPurchase.shop_item_id == ShopItem.id)
        .where(UserPurchase.user_id == user_id)
        .where(UserPurchase.is_equipped.is_(True))
        .where(ShopItem.item_type == "title")
        .limit(1)
    )
    return result.scalar_one_or_none()


async def build_user_response(session, user: User) -> UserResponse:
    """UserResponse enriched with the equipped title + City beta access flag."""
    from app.config import settings
    resp = UserResponse.model_validate(user)
    resp.equipped_title = await get_equipped_title(session, user.id)
    resp.city_enabled = (not settings.city_beta) or (
        user.telegram_id is not None and user.telegram_id == settings.admin_telegram_id
    )
    return resp


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the current user's profile",
    description="Returns full information about the currently authenticated user.",
    tags=["Users"]
)
async def get_current_user_profile(user: CurrentUser, session: AsyncSessionDep):
    return await build_user_response(session, user)


@router.get(
    "/me/purchased-avatars",
    response_model=list[str],
    summary="Get purchased avatars",
    description="Returns the list of avatar IDs purchased by the current user.",
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
    summary="Update the user's profile",
    description="Updates the current user's settings (avatar, notifications).",
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
    if request.sound_enabled is not None:
        user.sound_enabled = request.sound_enabled
    if request.leaderboard_visible is not None:
        user.leaderboard_visible = request.leaderboard_visible
    if request.daily_activity_norm is not None:
        # Records a history row for today and updates the current-norm column.
        await set_user_norm(session, user, request.daily_activity_norm)
    if request.language is not None:
        if request.language not in ("ru", "en"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported language (expected 'ru' or 'en')",
            )
        user.language = request.language

    await session.flush()
    await session.refresh(user)
    return await build_user_response(session, user)


@router.post("/me/complete-onboarding", response_model=UserResponse)
async def complete_onboarding(
    user: CurrentUser,
    body: CompleteOnboardingRequest,
    session: AsyncSessionDep,
):
    """Mark user as onboarded and save leaderboard consent."""
    user.is_onboarded = True
    user.leaderboard_visible = body.leaderboard_consent
    await session.flush()
    await session.refresh(user)
    return await build_user_response(session, user)


@router.get(
    "/me/streak-freezes",
    summary="Streak freeze info",
    description="Current number of freezes, the limit, and the purchase price.",
    tags=["Users"],
)
async def get_streak_freeze_info(user: CurrentUser):
    from app.services.streak import STREAK_FREEZE_PRICE_COINS, MAX_STREAK_FREEZES

    return {
        "owned": user.streak_freezes,
        "max": MAX_STREAK_FREEZES,
        "price_coins": STREAK_FREEZE_PRICE_COINS,
        "coins": user.coins,
    }


@router.post(
    "/me/streak-freezes/buy",
    response_model=UserResponse,
    summary="Buy a streak freeze",
    description="Deducts coins and adds one freeze (up to the limit).",
    tags=["Users"],
)
async def buy_streak_freeze_endpoint(
    user: CurrentUser,
    session: AsyncSessionDep,
):
    from app.services.streak import buy_streak_freeze

    try:
        await buy_streak_freeze(session, user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    await session.refresh(user)
    return await build_user_response(session, user)


@router.get(
    "/me/stats",
    response_model=UserStatsResponse,
    summary="Get user statistics",
    description="Returns detailed user statistics: workouts, XP, level, streak, achievements, coins, etc.",
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
        streak_freezes=user.streak_freezes,
        achievements_count=achievements_count,
        coins=user.coins,
        this_week_workouts=this_week_workouts,
        this_week_xp=this_week_xp,
    )


@router.get(
    "/me/activity",
    response_model=UserActivityResponse,
    summary="Get the activity calendar",
    description="Returns per-day workout data for the activity calendar. Only workout XP, excluding achievements.",
    tags=["Users"]
)
async def get_user_activity(
    user: CurrentUser,
    session: AsyncSessionDep,
    year: int | None = None,
):
    """Get workout activity calendar data grouped by day."""
    # Default to current year
    if year is None:
        year = date.today().year

    # Get all completed workouts for the year
    result = await session.execute(
        select(
            WorkoutSession.started_at,
            WorkoutSession.total_xp_earned
        )
        .where(WorkoutSession.user_id == user.id)
        .where(WorkoutSession.status == "completed")
        .where(func.strftime('%Y', WorkoutSession.started_at) == str(year))
    )

    # Group by date manually in Python (more reliable across databases)
    days_data = {}
    for row in result.all():
        workout_datetime = row.started_at
        # Extract date part
        workout_date = workout_datetime.date() if hasattr(workout_datetime, 'date') else workout_datetime
        date_str = workout_date.isoformat() if hasattr(workout_date, 'isoformat') else str(workout_date)

        # Aggregate data
        if date_str not in days_data:
            days_data[date_str] = {"workouts": 0, "total_xp": 0}

        days_data[date_str]["workouts"] += 1
        days_data[date_str]["total_xp"] += row.total_xp_earned or 0

    # Each day carries the activity norm that was in force on that date, so the
    # calendar colours historically (e.g. days before a norm change keep their
    # original target). Fetched once; resolved per day below.
    norm_history = await get_norm_history(session, user.id)

    # Convert to response format
    response_days = {
        date_str: DayActivityResponse(
            date=date_str,
            workouts=data["workouts"],
            total_xp=data["total_xp"],
            norm=resolve_norm(
                norm_history,
                date.fromisoformat(date_str),
                fallback=user.daily_activity_norm,
            ),
        )
        for date_str, data in days_data.items()
    }

    return UserActivityResponse(days=response_days)


@router.get(
    "/me/records",
    response_model=UserRecordsResponse,
    summary="Personal records",
    description="The user's best personal results (records).",
    tags=["Users"],
)
async def get_user_records(
    user: CurrentUser,
    session: AsyncSessionDep,
):
    """Personal records: best set, best workout for an exercise, longest workout, max streak."""
    best_set_row = (await session.execute(
        select(Exercise.slug, Exercise.name, Exercise.name_ru, UserExerciseProgress.best_single_set)
        .join(Exercise, UserExerciseProgress.exercise_id == Exercise.id)
        .where(UserExerciseProgress.user_id == user.id)
        .where(UserExerciseProgress.best_single_set > 0)
        .order_by(UserExerciseProgress.best_single_set.desc())
        .limit(1)
    )).first()

    best_workout_row = (await session.execute(
        select(Exercise.slug, Exercise.name, Exercise.name_ru, UserExerciseProgress.best_workout_reps)
        .join(Exercise, UserExerciseProgress.exercise_id == Exercise.id)
        .where(UserExerciseProgress.user_id == user.id)
        .where(UserExerciseProgress.best_workout_reps > 0)
        .order_by(UserExerciseProgress.best_workout_reps.desc())
        .limit(1)
    )).first()

    longest_workout = (await session.execute(
        select(func.max(WorkoutSession.duration_seconds))
        .where(WorkoutSession.user_id == user.id)
        .where(WorkoutSession.status == "completed")
    )).scalar() or 0

    total_reps = (await session.execute(
        select(func.coalesce(func.sum(WorkoutSession.total_reps), 0))
        .where(WorkoutSession.user_id == user.id)
        .where(WorkoutSession.status == "completed")
    )).scalar() or 0

    return UserRecordsResponse(
        best_set=ExerciseRecord(
            exercise_slug=best_set_row[0],
            exercise_name=best_set_row[1],
            exercise_name_ru=best_set_row[2],
            value=best_set_row[3],
        ) if best_set_row else None,
        best_workout=ExerciseRecord(
            exercise_slug=best_workout_row[0],
            exercise_name=best_workout_row[1],
            exercise_name_ru=best_workout_row[2],
            value=best_workout_row[3],
        ) if best_workout_row else None,
        longest_workout_seconds=int(longest_workout),
        max_streak=user.max_streak,
        total_reps=int(total_reps),
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

    return await build_user_response(session, user)


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
        equipped_title=await get_equipped_title(session, user.id),
        is_friend=is_friend,
        friend_request_sent=friend_request_sent,
        friend_request_received=friend_request_received,
        friendship_id=friendship_id,
    )
