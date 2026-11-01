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

from app.services.notifications import mark_bot_blocked, notify_admin_bot_blocked

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

    # Same write path as the 403 catch: flips the flag only on a real
    # transition (so no duplicate pings on echo updates / missing users).
    changed, total_blocked = await mark_bot_blocked(telegram_id, blocked)
    if not changed:
        return
    if blocked:
        logger.info("User %s blocked the bot (total blocked=%s)", telegram_id, total_blocked)
        notify_admin_bot_blocked(total_blocked)
    else:
        logger.info("User %s unblocked the bot", telegram_id)
