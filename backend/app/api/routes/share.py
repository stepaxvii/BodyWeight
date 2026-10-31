"""Workout share card endpoints (Strava-style share, NES look).

POST /share/workout/{session_id} — owner-only: builds the public card URLs,
the personal invite link (feeds the referral program) and, best-effort, a
Telegram *prepared inline message* (Bot API 8.0 savePreparedInlineMessage) so
the Mini App can share the card one-tap into any chat via WebApp.shareMessage.

GET /share/card/{token}.png — UNAUTHENTICATED PNG renderer. The token is
HMAC-signed with the server secret, so the URL is unguessable; it has to be
public because Telegram's servers fetch photo_url without credentials.
"""
import hashlib
import hmac
import json
import logging
import socket
from typing import Literal

import aiohttp
from fastapi import APIRouter, HTTPException, Query, Response, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import AsyncSessionDep, CurrentUser
from app.config import settings
from app.db.models import MonthlyBoss, WorkoutSession
from app.schemas import ShareWorkoutResponse
from app.services.share_card import CardData, render_card

logger = logging.getLogger(__name__)

router = APIRouter()


def _card_token(session_id: int) -> str:
    """Unguessable token for the unauthenticated card URL."""
    signature = hmac.new(
        settings.secret_key.encode(),
        f"share-card:{session_id}".encode(),
        hashlib.sha256,
    ).hexdigest()[:20]
    return f"{session_id}.{signature}"


def _parse_card_token(token: str) -> int | None:
    """Verify the token signature; return the session id or None."""
    session_id_str, sep, _signature = token.partition(".")
    # Cap the length too: WorkoutSession.id is a 32-bit Integer, a huge number
    # would overflow the DB driver before the signature even mattered.
    if not sep or not session_id_str.isdigit() or len(session_id_str) > 9:
        return None
    session_id = int(session_id_str)
    # Compare as bytes: compare_digest raises TypeError on non-ASCII str.
    if not hmac.compare_digest(
        token.encode(), _card_token(session_id).encode()
    ):
        return None
    return session_id


async def _save_prepared_inline_message(
    telegram_id: int,
    card_url: str,
    share_text: str,
    invite_link: str,
) -> str | None:
    """Create a Telegram prepared inline message (Bot API 8.0) for the card.

    The pinned aiogram (3.4.1, Bot API 7.x) predates savePreparedInlineMessage,
    so this is a raw Bot API call instead of going through the notifications
    bot. The connector is pinned to IPv4 for the same reason as
    app/bot/session.py: this server's IPv6 route to api.telegram.org is a
    black hole.
    """
    result = {
        "type": "photo",
        "id": "share",
        "photo_url": card_url,
        "thumbnail_url": card_url,
        "photo_width": 1080,
        "photo_height": 1350,
        "caption": share_text,
        "reply_markup": {
            "inline_keyboard": [
                [{"text": "Принять вызов 💪", "url": invite_link}]
            ]
        },
    }
    payload = {
        "user_id": telegram_id,
        "result": json.dumps(result),
        "allow_user_chats": True,
        "allow_group_chats": True,
    }
    url = (
        f"https://api.telegram.org/bot{settings.bot_token}"
        "/savePreparedInlineMessage"
    )
    connector = aiohttp.TCPConnector(family=socket.AF_INET)
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as http:
        async with http.post(url, json=payload) as resp:
            data = await resp.json()
    if not data.get("ok"):
        logger.warning(
            f"savePreparedInlineMessage failed: {data.get('description')}"
        )
        return None
    prepared_id = (data.get("result") or {}).get("id")
    return str(prepared_id) if prepared_id else None


@router.post(
    "/workout/{session_id}",
    response_model=ShareWorkoutResponse,
    summary="Поделиться тренировкой",
    description=(
        "Готовит карточку завершённой тренировки к шерингу: ссылки на PNG "
        "(пост и сторис), персональную инвайт-ссылку и prepared inline "
        "message для WebApp.shareMessage. prepared_message_id = null, если "
        "подготовить сообщение не удалось — фронтенд делает фолбэк на "
        "t.me/share/url."
    ),
    tags=["Share"],
)
async def share_workout(
    session_id: int,
    session: AsyncSessionDep,
    user: CurrentUser,
):
    result = await session.execute(
        select(WorkoutSession)
        .where(WorkoutSession.id == session_id)
        .where(WorkoutSession.user_id == user.id)
        .where(WorkoutSession.status == "completed")
    )
    workout = result.scalar_one_or_none()
    if workout is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Completed workout not found",
        )

    token = _card_token(workout.id)
    # Host nginx proxies {mini_app_url}/api/* -> backend /api/* (see
    # deploy/nginx-bodyweight.conf), and mini_app_url already contains the
    # /bodyweight base path — so the public card URL lives right under it.
    base_url = settings.mini_app_url.rstrip("/")
    card_url = f"{base_url}/api/share/card/{token}.png?variant=post"
    story_url = f"{base_url}/api/share/card/{token}.png?variant=story"
    invite_link = f"https://t.me/{settings.bot_username}?start=addfriend_{user.id}"
    share_text = (
        f"Потренировался в PixelFit: +{workout.total_xp_earned} XP! Присоединяйся"
    )

    # Best-effort: on ANY failure the frontend still gets the urls and falls
    # back to a t.me/share/url link share.
    prepared_message_id: str | None = None
    if user.telegram_id is not None:
        try:
            prepared_message_id = await _save_prepared_inline_message(
                telegram_id=user.telegram_id,
                card_url=card_url,
                share_text=share_text,
                invite_link=invite_link,
            )
        except Exception as e:
            logger.warning(f"Failed to prepare inline share message: {e}")

    return ShareWorkoutResponse(
        card_url=card_url,
        story_url=story_url,
        prepared_message_id=prepared_message_id,
        invite_link=invite_link,
        share_text=share_text,
    )


@router.get(
    "/card/{token}.png",
    summary="PNG-карточка тренировки",
    description=(
        "Отдаёт PNG-карточку завершённой тренировки по HMAC-подписанному "
        "токену. Без авторизации — ссылку скачивают серверы Telegram."
    ),
    response_class=Response,
    responses={200: {"content": {"image/png": {}}}},
    tags=["Share"],
)
async def get_share_card(
    token: str,
    session: AsyncSessionDep,
    variant: Literal["post", "story"] = Query(
        "post", description="Формат карточки: пост (1080×1350) или сторис (1080×1920)"
    ),
):
    session_id = _parse_card_token(token)
    if session_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Card not found"
        )

    result = await session.execute(
        select(WorkoutSession)
        .options(selectinload(WorkoutSession.user))
        .where(WorkoutSession.id == session_id)
    )
    workout = result.scalar_one_or_none()
    if (
        workout is None
        or workout.status != "completed"
        or workout.finished_at is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Card not found"
        )

    # Boss damage is 1:1 with workout XP (services/boss.py), shown only while
    # a boss covers the workout's date. It is an APPROXIMATION — real damage
    # is also trimmed by remaining boss HP.
    day = workout.finished_at.date()
    boss_result = await session.execute(
        select(MonthlyBoss)
        .where(MonthlyBoss.start_date <= day)
        .where(MonthlyBoss.end_date >= day)
    )
    boss = boss_result.scalar_one_or_none()
    boss_damage = workout.total_xp_earned if boss is not None else 0

    data = CardData(
        xp=workout.total_xp_earned,
        total_reps=workout.total_reps,
        duration_minutes=round(workout.total_duration_seconds / 60),
        streak_days=workout.user.current_streak,
        boss_damage=boss_damage,
        date_str=workout.finished_at.strftime("%d.%m"),
        bot_username=settings.bot_username,
    )
    # Pillow rendering is CPU-bound — keep it off the event loop.
    png = await run_in_threadpool(render_card, data, variant)

    return Response(
        content=png,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )
