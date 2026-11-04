"""Admin-only bot commands (daily stats digest on demand)."""
import logging
from datetime import datetime, timedelta

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import settings
from app.db.database import async_session_maker
from app.services.admin_stats import collect_daily_stats, format_digest

router = Router()
logger = logging.getLogger(__name__)


def _is_admin(message: Message) -> bool:
    """Match only the configured admin; everyone else's /digest is ignored."""
    return bool(
        settings.admin_telegram_id
        and message.from_user
        and message.from_user.id == settings.admin_telegram_id
    )


@router.message(Command("digest"), _is_admin)
async def cmd_admin_digest(message: Message):
    """Handle /digest from the admin — send yesterday's stats digest."""
    yesterday = (datetime.utcnow() - timedelta(days=1)).date()
    try:
        async with async_session_maker() as session:
            stats = await collect_daily_stats(session, yesterday)
        await message.answer(format_digest(stats, yesterday))
    except Exception as e:
        logger.error(f"Failed to build admin digest for {yesterday}: {e}")
        await message.answer("Не удалось собрать сводку, посмотри логи.")
