import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from app.config import settings
from app.bot.handlers import admin, start
from app.bot.session import make_ipv4_session
from app.db.database import async_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    """Startup handler."""
    logger.info("Bot starting up...")

    # Set bot commands
    from aiogram.types import BotCommand
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="workout", description="Open workout app"),
        BotCommand(command="stats", description="View your stats"),
        BotCommand(command="help", description="Get help"),
    ]
    # Non-fatal: a transient Telegram error here must NOT crash startup and
    # send the container into a restart loop (polling still works without it).
    try:
        await bot.set_my_commands(commands)
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
    dp.include_router(start.router)

    # Register startup/shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Start polling
    logger.info("Starting bot polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
