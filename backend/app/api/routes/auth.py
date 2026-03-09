import hashlib
import logging
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, or_

from app.api.deps import (
    AsyncSessionDep,
    CurrentUser,
    validate_telegram_init_data,
    create_jwt_token,
)
from app.db.models import User, Notification
from app.config import settings
from app.schemas import (
    AuthRequest,
    AuthResponse,
    UserResponse,
    WebRegisterRequest,
    WebLoginRequest,
    WebAuthResponse,
    SetPasswordRequest,
    LinkTelegramRequest,
    ConfirmLinkResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory store for pending telegram link requests
# In production, use Redis or a DB table with TTL
# Format: {telegram_id: {"user_id": int, "token": str, "expires": datetime}}
_pending_links: dict[int, dict] = {}


def _hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{hashed}"


def _verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    salt, hashed = password_hash.split(":", 1)
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() == hashed


@router.post(
    "/validate",
    response_model=AuthResponse,
    summary="Аутентификация через Telegram",
    tags=["Auth"],
)
async def validate_auth(
    request: AuthRequest,
    session: AsyncSessionDep,
):
    # In debug mode, allow mock auth
    if settings.debug and request.init_data.startswith("debug_"):
        try:
            telegram_id = int(request.init_data.split("_")[1])
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if user:
                return AuthResponse(user=UserResponse.model_validate(user), is_new=False)
            else:
                user = User(
                    telegram_id=telegram_id,
                    username=f"debug_user_{telegram_id}",
                    first_name="Debug",
                    last_name="User",
                )
                session.add(user)
                await session.flush()
                return AuthResponse(user=UserResponse.model_validate(user), is_new=True)
        except (ValueError, IndexError):
            pass

    # Validate Telegram init data
    validated_data = validate_telegram_init_data(request.init_data, settings.bot_token)

    if not validated_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Telegram init data",
        )

    user_data = validated_data.get("user")
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User data not found in init data",
        )

    telegram_id = user_data.get("id")
    username = user_data.get("username")
    first_name = user_data.get("first_name")
    last_name = user_data.get("last_name")

    # Get or create user
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    is_new = False

    if not user:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        session.add(user)
        await session.flush()
        await session.refresh(user)
        is_new = True

        welcome_notification = Notification(
            user_id=user.id,
            notification_type="welcome",
            title="Добро пожаловать!",
            message="Рады видеть тебя в BodyWeight! Начни первую тренировку прямо сейчас.",
        )
        session.add(welcome_notification)
        await session.flush()
    else:
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        if user.level < 1:
            user.level = 1
        await session.flush()
        await session.refresh(user)

    return AuthResponse(
        user=UserResponse.model_validate(user),
        is_new=is_new,
    )


@router.post(
    "/register",
    response_model=WebAuthResponse,
    summary="Регистрация через email и пароль",
    tags=["Auth"],
)
async def web_register(
    request: WebRegisterRequest,
    session: AsyncSessionDep,
):
    if len(request.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пароль должен быть не менее 6 символов",
        )

    # Check if email already taken
    result = await session.execute(
        select(User).where(User.email == request.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует",
        )

    # Check if username already taken (if provided)
    if request.username:
        result = await session.execute(
            select(User).where(User.username == request.username)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Этот username уже занят",
            )

    user = User(
        email=request.email,
        password_hash=_hash_password(request.password),
        username=request.username,
        first_name=request.first_name,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)

    # Create welcome notification
    welcome_notification = Notification(
        user_id=user.id,
        notification_type="welcome",
        title="Добро пожаловать!",
        message="Рады видеть тебя в BodyWeight! Начни первую тренировку прямо сейчас.",
    )
    session.add(welcome_notification)
    await session.flush()

    token = create_jwt_token(user.id)

    return WebAuthResponse(
        user=UserResponse.model_validate(user),
        token=token,
        is_new=True,
    )


@router.post(
    "/login",
    response_model=WebAuthResponse,
    summary="Вход через email/username и пароль",
    tags=["Auth"],
)
async def web_login(
    request: WebLoginRequest,
    session: AsyncSessionDep,
):
    # Find user by email, username, or telegram_id
    filters = [
        User.email == request.login,
        User.username == request.login,
    ]
    # If login looks like a number, also try telegram_id
    try:
        tid = int(request.login)
        filters.append(User.telegram_id == tid)
    except ValueError:
        pass

    result = await session.execute(
        select(User).where(or_(*filters))
    )
    user = result.scalar_one_or_none()

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
        )

    if not _verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
        )

    token = create_jwt_token(user.id)

    return WebAuthResponse(
        user=UserResponse.model_validate(user),
        token=token,
    )


@router.post(
    "/set-password",
    response_model=WebAuthResponse,
    summary="Установить пароль для входа через браузер (для TMA-пользователей)",
    tags=["Auth"],
)
async def set_password(
    request: SetPasswordRequest,
    user: CurrentUser,
    session: AsyncSessionDep,
):
    if len(request.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пароль должен быть не менее 6 символов",
        )

    # Check if email already taken by another user
    result = await session.execute(
        select(User).where(User.email == request.email, User.id != user.id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Этот email уже используется другим аккаунтом",
        )

    user.email = request.email
    user.password_hash = _hash_password(request.password)
    await session.flush()
    await session.refresh(user)

    token = create_jwt_token(user.id)

    return WebAuthResponse(
        user=UserResponse.model_validate(user),
        token=token,
    )


@router.post(
    "/link-telegram",
    summary="Запрос на привязку Telegram аккаунта",
    tags=["Auth"],
)
async def link_telegram(
    request: LinkTelegramRequest,
    user: CurrentUser,
    session: AsyncSessionDep,
):
    if user.telegram_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram уже привязан к этому аккаунту",
        )

    # Check if this telegram_id is already linked to another account
    result = await session.execute(
        select(User).where(User.telegram_id == request.telegram_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Этот Telegram аккаунт уже привязан к другому пользователю",
        )

    # Create pending link request
    link_token = secrets.token_urlsafe(32)
    _pending_links[request.telegram_id] = {
        "user_id": user.id,
        "username": user.username or user.email or f"User #{user.id}",
        "token": link_token,
        "expires": datetime.utcnow() + timedelta(minutes=15),
    }

    # Send confirmation message via bot
    try:
        from app.bot.handlers.start import send_link_confirmation
        await send_link_confirmation(
            telegram_id=request.telegram_id,
            web_username=user.username or user.email or f"User #{user.id}",
            link_token=link_token,
        )
    except Exception as e:
        logger.error(f"Failed to send link confirmation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось отправить подтверждение в Telegram. Убедитесь, что вы начали диалог с ботом.",
        )

    return {"message": "Запрос отправлен в Telegram. Подтвердите привязку в боте."}


@router.post(
    "/confirm-link/{link_token}",
    response_model=ConfirmLinkResponse,
    summary="Подтверждение привязки Telegram (вызывается ботом)",
    tags=["Auth"],
)
async def confirm_link(
    link_token: str,
    session: AsyncSessionDep,
):
    # Find pending link by token
    pending = None
    telegram_id = None
    for tid, data in _pending_links.items():
        if data["token"] == link_token:
            pending = data
            telegram_id = tid
            break

    if not pending or telegram_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запрос на привязку не найден или истёк",
        )

    if datetime.utcnow() > pending["expires"]:
        del _pending_links[telegram_id]
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Запрос на привязку истёк",
        )

    # Get web user
    result = await session.execute(
        select(User).where(User.id == pending["user_id"])
    )
    web_user = result.scalar_one_or_none()
    if not web_user:
        del _pending_links[telegram_id]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    # Check if telegram user has a separate account with data to merge
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    tg_user = result.scalar_one_or_none()

    if tg_user and tg_user.id != web_user.id:
        # Merge: transfer telegram user's data to web user
        await _merge_accounts(session, source=tg_user, target=web_user)

    # Link telegram to web account
    web_user.telegram_id = telegram_id
    if tg_user and not web_user.username:
        web_user.username = tg_user.username
    if tg_user and not web_user.first_name:
        web_user.first_name = tg_user.first_name
    if tg_user and not web_user.last_name:
        web_user.last_name = tg_user.last_name

    await session.flush()
    del _pending_links[telegram_id]

    return ConfirmLinkResponse(
        success=True,
        message="Telegram аккаунт успешно привязан!",
    )


async def _merge_accounts(session, source: User, target: User):
    """Merge source user's data into target user, then delete source."""
    from app.db.models import (
        WorkoutSession, UserAchievement, UserGoal, UserPurchase,
        UserExerciseProgress, UserFavoriteExercise, UserCustomRoutine,
        Notification, UserAvatarPurchase,
    )
    from app.db.models.friendship import Friendship

    # Merge gamification (take the best)
    target.total_xp = max(target.total_xp, source.total_xp)
    target.level = max(target.level, source.level)
    target.coins += source.coins
    target.current_streak = max(target.current_streak, source.current_streak)
    target.max_streak = max(target.max_streak, source.max_streak)
    if source.last_workout_date:
        if not target.last_workout_date or source.last_workout_date > target.last_workout_date:
            target.last_workout_date = source.last_workout_date

    # Transfer settings if target doesn't have them
    if not target.is_onboarded and source.is_onboarded:
        target.is_onboarded = source.is_onboarded
        target.leaderboard_visible = source.leaderboard_visible

    # Reassign all related records from source to target
    from sqlalchemy import update
    for model in [WorkoutSession, UserAchievement, UserGoal, UserPurchase,
                  UserExerciseProgress, UserFavoriteExercise, UserCustomRoutine,
                  Notification, UserAvatarPurchase]:
        await session.execute(
            update(model).where(model.user_id == source.id).values(user_id=target.id)
        )

    # Reassign friendships
    await session.execute(
        update(Friendship).where(Friendship.user_id == source.id).values(user_id=target.id)
    )
    await session.execute(
        update(Friendship).where(Friendship.friend_id == source.id).values(friend_id=target.id)
    )

    # Delete source user
    await session.delete(source)
    await session.flush()


def get_pending_link(telegram_id: int) -> dict | None:
    """Get pending link request for a telegram_id (used by bot)."""
    pending = _pending_links.get(telegram_id)
    if not pending:
        return None
    if datetime.utcnow() > pending["expires"]:
        del _pending_links[telegram_id]
        return None
    return pending
