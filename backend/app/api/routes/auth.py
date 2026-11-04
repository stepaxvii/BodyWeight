import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import (
    AsyncSessionDep,
    validate_telegram_init_data,
)
from app.db.models import User, Notification
from app.config import settings
from app.i18n import normalize_lang, t
from app.schemas import AuthRequest, AuthResponse, UserResponse
from app.services.notifications import notify_admin_new_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/validate",
    response_model=AuthResponse,
    summary="Telegram Mini App authentication",
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
    language_code = user_data.get("language_code")

    # Get or create user
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    is_new = False

    if not user:
        # Detect UI language from the Telegram client (en fallback).
        lang = normalize_lang(language_code)
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language=lang,
        )
        session.add(user)
        await session.flush()
        await session.refresh(user)
        is_new = True

        welcome_notification = Notification(
            user_id=user.id,
            notification_type="welcome",
            title=t(lang, "notifications.welcome.title"),
            message=t(lang, "notifications.welcome.message"),
        )
        session.add(welcome_notification)
        await session.flush()

        total_users = (
            await session.execute(select(func.count()).select_from(User))
        ).scalar_one()
        notify_admin_new_user(total_users)
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
