"""Track block/unblock of the bot via my_chat_member updates.

Telegram sends a my_chat_member update whenever a user blocks the bot
(new status -> "kicked") or unblocks/restarts it (-> "member"). We mirror that
into users.bot_blocked so the admin digest's reachable-audience count stays
honest, and notify the admin on each fresh block (no nicknames — just a count).
"""
import logging

from aiogram import Router
from aiogram.enums import ChatMemberStatus
from aiogram.types import ChatMemberUpdated
from sqlalchemy import func, select

from app.db.database import async_session_maker
from app.db.models import User
from app.services.notifications import dispatch_in_background, send_admin_notice

router = Router()
logger = logging.getLogger(__name__)


@router.my_chat_member()
async def on_my_chat_member(event: ChatMemberUpdated):
    """A user blocked or unblocked the bot in their private chat."""
    # Only care about the private chat with the bot itself.
    if event.chat.type != "private":
        return

    telegram_id = event.from_user.id
    blocked = event.new_chat_member.status == ChatMemberStatus.KICKED

    async with async_session_maker() as session:
        user = (
            await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
        ).scalar_one_or_none()
        if user is None:
            return
        was_blocked = bool(user.bot_blocked)
        if was_blocked == blocked:
            return  # no change — ignore duplicate/echo updates
        user.bot_blocked = blocked
        await session.commit()

        if blocked:
            total_blocked = (
                await session.execute(
                    select(func.count())
                    .select_from(User)
                    .where(User.bot_blocked.is_(True))
                )
            ).scalar_one()
            logger.info("User %s blocked the bot (total blocked=%s)", telegram_id, total_blocked)
            dispatch_in_background(send_admin_notice(
                f"🚫 Пользователь заблокировал бота.\nВсего заблокировали: {total_blocked}"
            ))
        else:
            logger.info("User %s unblocked the bot", telegram_id)
