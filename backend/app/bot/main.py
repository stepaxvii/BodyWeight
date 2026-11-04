import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from app.config import settings
from app.bot.handlers import admin, chat_member, start
from app.bot.session import make_ipv4_session
from app.db.database import async_engine
from app.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    """Startup handler."""
    logger.info("Bot starting up...")

    # Slash-command menu. Users see start/stats/help (localized: English by
    # default, Russian for ru-language Telegram clients). The admin's private
    # chat additionally gets /digest and /weekdigest via a chat-scoped list —
    # so those stay hidden from everyone else. /workout was dropped: the app
    # opens from the menu button, the command was redundant.
    from aiogram.types import (
        BotCommand,
        BotCommandScopeChat,
        BotCommandScopeDefault,
    )
    from app.i18n import t

    def _user_cmds(lang: str) -> list[BotCommand]:
        return [
            BotCommand(command="start", description=t(lang, "bot.commands.start")),
            BotCommand(command="stats", description=t(lang, "bot.commands.stats")),
            BotCommand(command="help", description=t(lang, "bot.commands.help")),
        ]

    def _admin_cmds(lang: str) -> list[BotCommand]:
        return _user_cmds(lang) + [
            BotCommand(command="digest", description=t(lang, "bot.commands.digest")),
            BotCommand(command="weekdigest", description=t(lang, "bot.commands.weekdigest")),
        ]

    # Non-fatal: a transient Telegram error here must NOT crash startup and
    # send the container into a restart loop (polling still works without it).
    try:
        await bot.set_my_commands(_user_cmds("en"), scope=BotCommandScopeDefault())
        await bot.set_my_commands(
            _user_cmds("ru"), scope=BotCommandScopeDefault(), language_code="ru"
        )
        if settings.admin_telegram_id:
            await bot.set_my_commands(
                _admin_cmds("ru"),
                scope=BotCommandScopeChat(chat_id=settings.admin_telegram_id),
            )
    except Exception as e:
        logger.warning("set_my_commands failed (non-fatal, continuing to poll): %s", e)

    logger.info("Bot started successfully")


async def on_shutdown(bot: Bot):
    """Shutdown handler."""
    logger.info("Bot shutting down...")
    await async_engine.dispose()


async def main():
    """Main bot entry point."""
    if not settings.bot_token:
        logger.error("BOT_TOKEN is not set!")
        return

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=make_ipv4_session(),
    )

    dp = Dispatcher()

    # Register routers (admin: /digest, только для ADMIN_TELEGRAM_ID)
    dp.include_router(admin.router)
    # Tracks block/unblock of the bot (users.bot_blocked) + notifies admin.
    dp.include_router(chat_member.router)
    dp.include_router(start.router)

    # Register startup/shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Start polling
    logger.info("Starting bot polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
