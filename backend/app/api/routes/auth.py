import hashlib
import hmac
from datetime import datetime, timedelta
from urllib.parse import parse_qsl

from fastapi import APIRouter, HTTPException, status, Depends
from jose import jwt
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.database import get_session
from app.db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


class TelegramAuthRequest(BaseModel):
    init_data: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_new_user: bool
    user: dict


def validate_init_data(init_data: str, bot_token: str) -> dict | None:
    """Validate Telegram WebApp init data."""
    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))

        if "hash" not in parsed:
            return None

        received_hash = parsed.pop("hash")

        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed.items())
        )

        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode(),
            hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        if calculated_hash != received_hash:
            return None

        return parsed
    except Exception:
        return None


def create_access_token(telegram_id: int) -> str:
    """Create JWT access token."""
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode = {
        "sub": str(telegram_id),
        "exp": expire,
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


@router.post("/telegram", response_model=AuthResponse)
async def auth_telegram(
    request: TelegramAuthRequest,
    session: AsyncSession = Depends(get_session),
):
    """Authenticate user via Telegram WebApp."""
    validated = validate_init_data(request.init_data, settings.bot_token)

    if not validated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid init data",
        )

    import json
    user_data = json.loads(validated.get("user", "{}"))

    telegram_id = user_data.get("id")
    if not telegram_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID not found",
        )

    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()

    is_new_user = False

    if not user:
        is_new_user = True
        user = User(
            telegram_id=telegram_id,
            username=user_data.get("username"),
            first_name=user_data.get("first_name"),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    else:
        user.username = user_data.get("username")
        user.first_name = user_data.get("first_name")
        await session.commit()

    access_token = create_access_token(telegram_id)

    return AuthResponse(
        access_token=access_token,
        is_new_user=is_new_user,
        user={
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "level": user.level,
            "experience": user.experience,
            "streak_days": user.streak_days,
            "total_workouts": user.total_workouts,
            "total_reps": user.total_reps,
        }
    )
