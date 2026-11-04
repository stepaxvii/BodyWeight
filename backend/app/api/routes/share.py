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
import os
import socket
from typing import Literal

import aiohttp
from fastapi import APIRouter, HTTPException, Query, Response, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import AsyncSessionDep, CurrentUser
from app.config import settings
from app.db.models import Exercise, MonthlyBoss, WorkoutExercise, WorkoutSession
from app.i18n import t
from app.schemas import ShareWorkoutRequest, ShareWorkoutResponse
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


async def _save_prepared_inline_message(result: dict) -> str | None:
    """Create a Telegram prepared inline message (Bot API 8.0).

    The pinned aiogram (3.4.1, Bot API 7.x) predates savePreparedInlineMessage,
    so this is a raw Bot API call instead of going through the notifications
    bot. The connector is pinned to IPv4 for the same reason as
    app/bot/session.py: this server's IPv6 route to api.telegram.org is a
    black hole.
    """
    payload = {
        "user_id": result.pop("_telegram_id"),
        "result": json.dumps(result),
        "allow_user_chats": True,
        "allow_group_chats": True,
    }
    url = (
        f"https://api.telegram.org/bot{settings.bot_token}"
        "/savePreparedInlineMessage"
    )
    proxy = os.environ.get("TG_PROXY") or None
    if proxy:
        # Same outbound proxy as app/bot/session.py (TG_PROXY): api.telegram.org
        # is DPI-blocked, so this raw Bot API call is tunnelled through SOCKS5 too.
        from aiohttp_socks import ProxyConnector

        connector = ProxyConnector.from_url(proxy)
    else:
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


def _challenge_button(invite_link: str, lang: str | None = None) -> dict:
    return {
        "inline_keyboard": [[{"text": t(lang, "share.button_challenge"), "url": invite_link}]]
    }


def _format_mmss(total_seconds: int) -> str:
    return f"{total_seconds // 60:02d}:{total_seconds % 60:02d}"


async def _build_report_text(
    session, workout: WorkoutSession, routine_name: str | None, lang: str | None = None
) -> str:
    """Text report with the full exercise list — mirrors the frontend share
    text in RoutinePlayer.svelte (same emoji/line layout)."""
    rows = (
        await session.execute(
            select(WorkoutExercise, Exercise)
            .join(Exercise, WorkoutExercise.exercise_id == Exercise.id)
            .where(WorkoutExercise.workout_session_id == workout.id)
            .order_by(WorkoutExercise.id)
        )
    ).all()
    is_ru = (lang or "").startswith("ru")
    lines = [
        f"🏆 {routine_name or t(lang, 'share.report_name_fallback')}",
        "",
        # duration_seconds — real workout time (start->finish);
        # total_duration_seconds — sum of seconds for TIMED exercises only
        # (0 for a reps-only workout) — do not use it here.
        f"⏱️ {_format_mmss(workout.duration_seconds or 0)}",
        f"🌟 +{workout.total_xp_earned} XP",
        f"🪙 {workout.total_coins_earned} {t(lang, 'share.coins_suffix')}",
    ]
    if rows:
        lines += ["", "━━━━━━━━━━", f"💪 {t(lang, 'share.exercises_header')}", "━━━━━━━━━━"]
        for we, ex in rows:
            unit = t(lang, "share.unit_sec") if ex.is_timed else t(lang, "share.unit_reps")
            value = we.total_duration_seconds if ex.is_timed else we.total_reps
            ex_name = ex.name_ru if is_ru else ex.name
            lines.append(f"  ▸ {ex_name}: {value} {unit}")
    return "\n".join(lines)


@router.post(
    "/workout/{session_id}",
    response_model=ShareWorkoutResponse,
    summary="Share a workout",
    description=(
        "Prepares a completed workout's card for sharing: PNG URLs "
        "(post and story), a personal invite link and a prepared inline "
        "message for WebApp.shareMessage. prepared_message_id = null if "
        "the message could not be prepared — the frontend falls back to "
        "t.me/share/url."
    ),
    tags=["Share"],
)
async def share_workout(
    session_id: int,
    session: AsyncSessionDep,
    user: CurrentUser,
    body: ShareWorkoutRequest | None = None,
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
    share_text = t(user.language, "share.caption", xp=workout.total_xp_earned)

    # Best-effort: on ANY failure the frontend still gets the urls and falls
    # back to a t.me/share/url link share.
    prepared_message_id: str | None = None
    prepared_text_message_id: str | None = None
    if user.telegram_id is not None:
        try:
            prepared_message_id = await _save_prepared_inline_message({
                "_telegram_id": user.telegram_id,
                "type": "photo",
                "id": "share",
                "photo_url": card_url,
                "thumbnail_url": card_url,
                "photo_width": 1080,
                "photo_height": 1350,
                "caption": share_text,
                "reply_markup": _challenge_button(invite_link, user.language),
            })
        except Exception as e:
            logger.warning(f"Failed to prepare inline share message: {e}")
        # Text variant: the full exercise report with the referral button —
        # used by the "Share" button in RoutinePlayer.
        try:
            report_text = await _build_report_text(
                session, workout, body.routine_name if body else None, user.language
            )
            prepared_text_message_id = await _save_prepared_inline_message({
                "_telegram_id": user.telegram_id,
                "type": "article",
                "id": "share_text",
                "title": t(user.language, "share.report_title"),
                "input_message_content": {"message_text": report_text},
                "reply_markup": _challenge_button(invite_link, user.language),
            })
        except Exception as e:
            logger.warning(f"Failed to prepare text share message: {e}")

    return ShareWorkoutResponse(
        card_url=card_url,
        story_url=story_url,
        prepared_message_id=prepared_message_id,
        prepared_text_message_id=prepared_text_message_id,
        invite_link=invite_link,
        share_text=share_text,
    )


@router.get(
    "/card/{token}.png",
    summary="Workout PNG card",
    description=(
        "Serves a completed workout's PNG card by its HMAC-signed "
        "token. Unauthenticated — the link is fetched by Telegram's servers."
    ),
    response_class=Response,
    responses={200: {"content": {"image/png": {}}}},
    tags=["Share"],
)
async def get_share_card(
    token: str,
    session: AsyncSessionDep,
    variant: Literal["post", "story"] = Query(
        "post", description="Card format: post (1080×1350) or story (1080×1920)"
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
        # Wall-clock workout time, NOT total_duration_seconds (which sums
        # only timed-exercise seconds and is 0 for reps-only workouts).
        duration_minutes=round((workout.duration_seconds or 0) / 60),
        streak_days=workout.user.current_streak,
        boss_damage=boss_damage,
        date_str=workout.finished_at.strftime("%d.%m"),
        bot_username=settings.bot_username,
    )
    # Pillow rendering is CPU-bound — keep it off the event loop. Card labels
    # follow the workout owner's UI language (en fallback).
    png = await run_in_threadpool(render_card, data, variant, workout.user.language)

    return Response(
        content=png,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )
