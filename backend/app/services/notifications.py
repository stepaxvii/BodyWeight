import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import settings
from app.db.database import async_session_maker
from app.db.models import User
from app.bot.keyboards.inline import get_migration_keyboard

logger = logging.getLogger(__name__)

MIGRATION_NOTIFY_USERNAME = "bobaxvii"
MIGRATION_MESSAGE = """🚀 <b>PixelFit переезжает на нового бота!</b>

Привет! Мы переходим на обновлённого бота — все твои данные (уровень, XP, достижения, друзья) сохранены и будут доступны там.

Нажми кнопку ниже, чтобы перейти к новому боту и нажать <b>Start</b> — после этого всё будет работать как раньше.

До встречи на новой стороне! 💪"""


async def send_migration_notification_to_bobaxvii() -> None:
    """
    Один раз отправить @bobaxvii уведомление о переезде, используя OLD_BOT_TOKEN.
    Вызывается при старте приложения. BOT_TOKEN при этом остаётся токеном нового бота.
    """
    root_log = logging.getLogger()
    old_token = (getattr(settings, "old_bot_token", None) or "").strip()
    if not old_token:
        root_log.info("Migration: OLD_BOT_TOKEN not set, skipping notification to @%s", MIGRATION_NOTIFY_USERNAME)
        return
    link = (settings.new_bot_link or "https://t.me/pixelfitbot").strip()
    if not link.startswith("http"):
        link = "https://t.me/pixelfitbot"
    root_log.info("Migration: OLD_BOT_TOKEN set, looking for @%s in DB", MIGRATION_NOTIFY_USERNAME)
    async with async_session_maker() as session:
        result = await session.execute(
            select(User.telegram_id, User.username).where(User.username.isnot(None))
        )
        rows = result.all()
        target = MIGRATION_NOTIFY_USERNAME.lower()
        for tg_id, username in rows:
            if not username:
                continue
            if username.lower().strip().lstrip("@") != target:
                continue
            old_bot = Bot(
                token=old_token,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            )
            try:
                await old_bot.send_message(
                    tg_id,
                    MIGRATION_MESSAGE,
                    reply_markup=get_migration_keyboard(link),
                )
                root_log.info("Migration: notification sent to @%s (telegram_id=%s) via OLD_BOT_TOKEN", username, tg_id)
            except Exception as e:
                root_log.error("Migration: failed to send to @%s: %s", username, e)
            finally:
                await old_bot.session.close()
            return
    usernames = [r[1] for r in rows if r[1]]
    root_log.warning(
        "Migration: user @%s not found in DB. Users with username: %s",
        MIGRATION_NOTIFY_USERNAME,
        usernames[:20] if len(usernames) > 20 else usernames,
    )

# Global bot instance for sending notifications
_bot: Bot | None = None


def get_bot() -> Bot:
    """Get or create bot instance for notifications."""
    global _bot
    if _bot is None:
        if not settings.bot_token:
            raise ValueError("BOT_TOKEN is not configured")
        _bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
    return _bot


def get_open_app_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard with button to open the Mini App."""
    from aiogram.types import WebAppInfo
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть приложение",
                    web_app=WebAppInfo(url=settings.mini_app_url),
                )
            ]
        ]
    )


async def save_notification(
    session: AsyncSession,
    user_id: int,
    notification_type: str,
    title: str,
    message: str,
    related_user_id: int | None = None,
) -> None:
    """Save notification to database for badge display."""
    from app.db.models import Notification

    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        related_user_id=related_user_id,
    )
    session.add(notification)
    await session.flush()


async def send_friend_request_notification(
    telegram_id: int,
    from_user_name: str,
) -> bool:
    """
    Send notification about new friend request.

    Args:
        telegram_id: Telegram ID of the user to notify
        from_user_name: Name/username of the user who sent the request

    Returns:
        True if notification was sent successfully
    """
    try:
        bot = get_bot()

        text = (
            f"👋 <b>Новая заявка в друзья!</b>\n\n"
            f"Пользователь <b>{from_user_name}</b> хочет добавить тебя в друзья."
        )

        await bot.send_message(
            chat_id=telegram_id,
            text=text,
            reply_markup=get_open_app_keyboard(),
        )

        logger.info(f"Friend request notification sent to {telegram_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to send friend request notification to {telegram_id}: {e}")
        return False




async def send_daily_reminder(telegram_id: int, streak: int = 0) -> bool:
    """
    Send daily workout reminder.

    Args:
        telegram_id: Telegram ID of the user to notify
        streak: Current streak days

    Returns:
        True if notification was sent successfully
    """
    try:
        bot = get_bot()

        if streak > 0:
            text = (
                f"🏋️ <b>Время тренировки!</b>\n\n"
                f"🔥 Твой streak: <b>{streak}</b> дней подряд!\n"
                f"Не останавливайся — продолжай в том же духе!"
            )
        else:
            text = (
                f"🏋️ <b>Время тренировки!</b>\n\n"
                f"Начни свой день с упражнений.\n"
                f"Даже 10 минут — это уже прогресс!"
            )

        await bot.send_message(
            chat_id=telegram_id,
            text=text,
            reply_markup=get_open_app_keyboard(),
        )

        logger.info(f"Daily reminder sent to {telegram_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to send daily reminder to {telegram_id}: {e}")
        return False


async def send_inactivity_reminder(telegram_id: int, days_inactive: int) -> bool:
    """
    Send reminder to inactive user.

    Args:
        telegram_id: Telegram ID of the user to notify
        days_inactive: Number of days since last workout

    Returns:
        True if notification was sent successfully
    """
    try:
        bot = get_bot()

        text = (
            f"😢 <b>Мы скучаем!</b>\n\n"
            f"Прошло уже <b>{days_inactive}</b> дня без тренировок.\n"
            f"Твои мышцы тоже скучают! Вернись к занятиям — "
            f"начни с лёгкой разминки."
        )

        await bot.send_message(
            chat_id=telegram_id,
            text=text,
            reply_markup=get_open_app_keyboard(),
        )

        logger.info(f"Inactivity reminder sent to {telegram_id} ({days_inactive} days)")
        return True

    except Exception as e:
        logger.error(f"Failed to send inactivity reminder to {telegram_id}: {e}")
        return False


async def send_friend_accepted_notification(
    telegram_id: int,
    friend_name: str,
) -> bool:
    """
    Send notification that friend request was accepted.

    Args:
        telegram_id: Telegram ID of the user to notify
        friend_name: Name/username of the friend who accepted

    Returns:
        True if notification was sent successfully
    """
    try:
        bot = get_bot()

        text = (
            f"✅ <b>Заявка принята!</b>\n\n"
            f"<b>{friend_name}</b> теперь твой друг.\n"
            f"Тренируйтесь вместе и соревнуйтесь!"
        )

        await bot.send_message(
            chat_id=telegram_id,
            text=text,
            reply_markup=get_open_app_keyboard(),
        )

        logger.info(f"Friend accepted notification sent to {telegram_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to send friend accepted notification to {telegram_id}: {e}")
        return False


async def send_friend_workout_notification(
    telegram_id: int,
    friend_name: str,
) -> bool:
    """
    Send notification that a friend completed a workout today.

    Args:
        telegram_id: Telegram ID of the user to notify
        friend_name: Name/username of the friend who worked out

    Returns:
        True if notification was sent successfully
    """
    try:
        bot = get_bot()

        text = (
            f"💪 <b>{friend_name}</b> уже потренировался сегодня!\n\n"
            f"А ты? Не отставай от друзей!"
        )

        await bot.send_message(
            chat_id=telegram_id,
            text=text,
            reply_markup=get_open_app_keyboard(),
        )

        logger.info(f"Friend workout notification sent to {telegram_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to send friend workout notification to {telegram_id}: {e}")
        return False


async def close_bot():
    """Close bot session (call on app shutdown)."""
    global _bot
    if _bot is not None:
        await _bot.session.close()
        _bot = None
