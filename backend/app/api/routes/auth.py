from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import AsyncSessionDep, validate_telegram_init_data
from app.db.models import User, Notification
from app.config import settings
from app.schemas import AuthRequest, AuthResponse, UserResponse

router = APIRouter()


@router.post("/validate", response_model=AuthResponse)
async def validate_auth(
    request: AuthRequest,
    session: AsyncSessionDep,
):
    """
    Validate Telegram init data and create/update user.
    This is the main auth endpoint called when Mini App opens.
    """
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
                # Create debug user
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
        # Create new user
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

        # Create welcome notification
        welcome_notification = Notification(
            user_id=user.id,
            notification_type="welcome",
            title="Добро пожаловать!",
            message="Рады видеть тебя в BodyWeight! Начни первую тренировку прямо сейчас.",
        )
        session.add(welcome_notification)
        await session.flush()
    else:
        # Update existing user info
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        # Fix legacy users with level 0 (old default was 0, should be 1)
        if user.level < 1:
            user.level = 1
        await session.flush()
        # Refresh to get updated_at from database trigger
        await session.refresh(user)

    return AuthResponse(
        user=UserResponse.model_validate(user),
        is_new=is_new,
    )
