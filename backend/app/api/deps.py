import hashlib
import hmac
import json
from urllib.parse import parse_qsl, unquote
from typing import Annotated
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_async_session
from app.db.models import User
from app.config import settings


def validate_telegram_init_data(init_data: str, bot_token: str) -> dict | None:
    """
    Validate Telegram Mini App init data.
    Returns parsed data if valid, None otherwise.

    See: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    try:
        parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))

        if "hash" not in parsed_data:
            return None

        received_hash = parsed_data.pop("hash")

        # Check auth_date (data should not be older than 24 hours)
        auth_date = int(parsed_data.get("auth_date", 0))
        if datetime.utcnow() - datetime.fromtimestamp(auth_date) > timedelta(hours=24):
            return None

        # Create data-check-string
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed_data.items())
        )

        # Create secret key
        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode(),
            hashlib.sha256
        ).digest()

        # Calculate hash
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(calculated_hash, received_hash):
            return None

        # Parse user data
        if "user" in parsed_data:
            parsed_data["user"] = json.loads(unquote(parsed_data["user"]))

        return parsed_data

    except Exception:
        return None


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """
    Get current user from Telegram init data.
    Authorization header format: "tma <init_data>"
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
        )

    if not authorization.startswith("tma "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format. Expected: tma <init_data>",
        )

    init_data = authorization[4:]  # Remove "tma " prefix

    # In debug mode, allow mock auth for testing
    if settings.debug and init_data.startswith("debug_"):
        try:
            telegram_id = int(init_data.split("_")[1])
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if user:
                return user
        except (ValueError, IndexError):
            pass

    # Validate Telegram init data
    validated_data = validate_telegram_init_data(init_data, settings.bot_token)

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

    # Get or create user
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found. Please start the bot first.",
        )

    return user


# Type alias for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]
