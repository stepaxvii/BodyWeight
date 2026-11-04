"""Admin-only bot commands (stats digests on demand)."""
import logging
from datetime import timedelta

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import settings
from app.db.database import async_session_maker
from app.i18n import t
from app.services.admin_stats import (
    collect_daily_stats,
    collect_weekly_stats,
    format_digest,
    format_weekly_digest,
    msk_today,
)

router = Router()
logger = logging.getLogger(__name__)


def _is_admin(message: Message) -> bool:
    """Match only the configured admin; everyone else's command is ignored."""
    return bool(
        settings.admin_telegram_id
        and message.from_user
        and message.from_user.id == settings.admin_telegram_id
    )


@router.message(Command("digest"), _is_admin)
async def cmd_admin_digest(message: Message):
    """Handle /digest from the admin — yesterday's (Moscow day) stats digest."""
    yesterday = msk_today() - timedelta(days=1)
    try:
        async with async_session_maker() as session:
            stats = await collect_daily_stats(session, yesterday)
        await message.answer(format_digest(stats, yesterday))
    except Exception as e:
        logger.error(f"Failed to build admin digest for {yesterday}: {e}")
        await message.answer(t("ru", "bot.admin.digest_failed"))


@router.message(Command("weekdigest"), _is_admin)
async def cmd_admin_week_digest(message: Message):
    """Handle /weekdigest — the 7-day rollup ending yesterday (Moscow)."""
    end_day = msk_today() - timedelta(days=1)
    try:
        async with async_session_maker() as session:
            stats = await collect_weekly_stats(session, end_day)
        await message.answer(format_weekly_digest(stats))
    except Exception as e:
        logger.error(f"Failed to build weekly admin digest for {end_day}: {e}")
        await message.answer(t("ru", "bot.admin.digest_failed"))
