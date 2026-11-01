import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import settings
from app.bot.session import make_ipv4_session

logger = logging.getLogger(__name__)

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
            # Bound each push to 5s so one slow/unreachable Telegram call can't
            # stall for aiogram's 60s default. Pushes are also dispatched off the
            # request path (see dispatch_in_background), so this is a safety net.
            session=make_ipv4_session(timeout=5),
        )
    return _bot


# Strong references to in-flight background push tasks — without them the event
# loop may garbage-collect a task before it finishes (see asyncio docs).
_background_tasks: set["asyncio.Task"] = set()


def dispatch_in_background(coro) -> None:
    """Fire a best-effort coroutine off the request path (non-blocking).

    Used so Telegram pushes never hold the DB transaction / HTTP response open
    while waiting on api.telegram.org. Exceptions inside the coroutine are the
    coroutine's own responsibility (it should be best-effort).
    """
    try:
        task = asyncio.create_task(coro)
    except RuntimeError:
        # No running event loop (e.g. called from a sync context) — best-effort.
        logger.warning("dispatch_in_background: no running event loop; push skipped")
        coro.close()  # avoid "coroutine was never awaited" warning
        return
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


async def mark_bot_blocked(telegram_id: int, blocked: bool) -> tuple[bool, int]:
    """Flip users.bot_blocked for a telegram_id (best-effort, own session).

    Called on a 403 send (user blocked the bot) and from the bot's
    my_chat_member handler. Returns ``(changed, total_blocked)``: ``changed``
    is True only on an actual transition — so callers notify the admin exactly
    once per fresh block, never on repeated sends to an already-blocked user.
    ``total_blocked`` is the current blocked count (computed only when changed).
    """
    from sqlalchemy import func, select, update
    from app.db.database import async_session_maker
    from app.db.models import User

    try:
        async with async_session_maker() as session:
            result = await session.execute(
                update(User)
                .where(User.telegram_id == telegram_id)
                .where(User.bot_blocked != blocked)
                .values(bot_blocked=blocked)
            )
            changed = (result.rowcount or 0) > 0
            total_blocked = 0
            if changed:
                total_blocked = (
                    await session.execute(
                        select(func.count())
                        .select_from(User)
                        .where(User.bot_blocked.is_(True))
                    )
                ).scalar_one()
            await session.commit()
            return changed, total_blocked
    except Exception:
        logger.exception("Failed to update bot_blocked for %s", telegram_id)
        return False, 0


async def _send(
    telegram_id: int,
    text: str,
    *,
    keyboard: InlineKeyboardMarkup | None = None,
    label: str = "push",
) -> bool:
    """Single Telegram-send path for every push. Returns True on success.

    A 403 means the user blocked the bot — expected, not an error: log at INFO,
    record the block, and ping the admin once if this is a fresh discovery.
    Any other failure logs with a traceback.
    """
    try:
        bot = get_bot()
        await bot.send_message(chat_id=telegram_id, text=text, reply_markup=keyboard)
        logger.info("%s sent to %s", label, telegram_id)
        return True
    except TelegramForbiddenError:
        logger.info("%s skipped: %s has blocked the bot", label, telegram_id)
        changed, total_blocked = await mark_bot_blocked(telegram_id, True)
        if changed:
            notify_admin_bot_blocked(total_blocked)
        return False
    except Exception:
        logger.exception("Failed to send %s to %s", label, telegram_id)
        return False


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
    text = (
        f"👋 <b>Новая заявка в друзья!</b>\n\n"
        f"Пользователь <b>{from_user_name}</b> хочет добавить тебя в друзья."
    )
    return await _send(
        telegram_id, text,
        keyboard=get_open_app_keyboard(), label="Friend request notification",
    )


async def send_daily_reminder(telegram_id: int, streak: int = 0) -> bool:
    """
    Send daily workout reminder.

    Args:
        telegram_id: Telegram ID of the user to notify
        streak: Current streak days

    Returns:
        True if notification was sent successfully
    """
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
    return await _send(
        telegram_id, text,
        keyboard=get_open_app_keyboard(), label="Daily reminder",
    )


async def send_inactivity_reminder(telegram_id: int, days_inactive: int) -> bool:
    """
    Send reminder to inactive user.

    Args:
        telegram_id: Telegram ID of the user to notify
        days_inactive: Number of days since last workout

    Returns:
        True if notification was sent successfully
    """
    text = (
        f"😢 <b>Мы скучаем!</b>\n\n"
        f"Прошло уже <b>{days_inactive}</b> дня без тренировок.\n"
        f"Твои мышцы тоже скучают! Вернись к занятиям — "
        f"начни с лёгкой разминки."
    )
    return await _send(
        telegram_id, text,
        keyboard=get_open_app_keyboard(),
        label=f"Inactivity reminder ({days_inactive}d)",
    )


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
    text = (
        f"✅ <b>Заявка принята!</b>\n\n"
        f"<b>{friend_name}</b> теперь твой друг.\n"
        f"Тренируйтесь вместе и соревнуйтесь!"
    )
    return await _send(
        telegram_id, text,
        keyboard=get_open_app_keyboard(), label="Friend accepted notification",
    )


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
    text = (
        f"💪 <b>{friend_name}</b> уже потренировался сегодня!\n\n"
        f"А ты? Не отставай от друзей!"
    )
    return await _send(
        telegram_id, text,
        keyboard=get_open_app_keyboard(), label="Friend workout notification",
    )


async def send_friend_workout_notifications(
    telegram_ids: list[int],
    friend_name: str,
) -> None:
    """Send the 'friend worked out today' push to many users concurrently.

    Best-effort: each send has its own try/except (returns False on failure) and
    we also pass return_exceptions=True so one failure can't cancel the rest.
    Meant to be run via dispatch_in_background so it never blocks the submit.
    """
    if not telegram_ids:
        return
    await asyncio.gather(
        *(
            send_friend_workout_notification(telegram_id=tid, friend_name=friend_name)
            for tid in telegram_ids
        ),
        return_exceptions=True,
    )


def get_open_challenge_keyboard(challenge_id: int) -> InlineKeyboardMarkup:
    """Keyboard whose button deep-links straight into a specific challenge.

    Uses the bot ``startapp`` deep link so tapping opens the Mini App with
    ``start_param = "challenge_<id>"`` (routed to /challenges/<id> on the front).
    """
    url = f"https://t.me/{settings.bot_username}?startapp=challenge_{challenge_id}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть челлендж", url=url)]
        ]
    )


async def send_new_challenge_push(
    telegram_id: int,
    creator_name: str,
    challenge_title: str,
    challenge_id: int,
) -> bool:
    """Tell a friend that someone created a new challenge they can still join."""
    text = (
        f"🏆 <b>Новый челлендж!</b>\n\n"
        f"<b>{creator_name}</b> создал «{challenge_title}».\n"
        f"Впишись, пока открыт приём — потренируйтесь наперегонки!"
    )
    return await _send(
        telegram_id, text,
        keyboard=get_open_challenge_keyboard(challenge_id),
        label="New-challenge notification",
    )


async def send_announcement_push(telegram_id: int, text: str) -> bool:
    """
    Send a generic announcement push to a user via Telegram bot.
    Used for one-off feature announcements (new release, etc.).

    Args:
        telegram_id: Telegram ID of the user to notify
        text: HTML-formatted message body

    Returns:
        True if notification was sent successfully
    """
    return await _send(
        telegram_id, text,
        keyboard=get_open_app_keyboard(), label="Announcement push",
    )


async def send_referral_reward_push(telegram_id: int, text: str) -> bool:
    """
    Send the referral reward push to the inviter via Telegram bot.
    Used when an invited user completes their first workout.

    Args:
        telegram_id: Telegram ID of the inviter to notify
        text: HTML-formatted message body

    Returns:
        True if notification was sent successfully
    """
    return await _send(
        telegram_id, text,
        keyboard=get_open_app_keyboard(), label="Referral reward push",
    )


async def send_admin_digest(text: str) -> bool:
    """
    Send the daily stats digest to the project admin via Telegram bot.
    No open-app keyboard — it's a plain informational message.

    Args:
        text: HTML-formatted message body

    Returns:
        True if the digest was sent successfully
    """
    if not settings.admin_telegram_id:
        logger.debug("Admin digest skipped: ADMIN_TELEGRAM_ID is not set")
        return False
    return await _send(settings.admin_telegram_id, text, label="Admin digest")


async def send_admin_notice(text: str) -> bool:
    """Push a short event notice to the admin (new registration, bot blocked).

    No-op when ADMIN_TELEGRAM_ID is unset. Meant to be fired best-effort via
    dispatch_in_background so it never blocks the triggering request.
    """
    if not settings.admin_telegram_id:
        return False
    return await _send(settings.admin_telegram_id, text, label="Admin notice")


def notify_admin_new_user(total_users: int) -> None:
    """Best-effort admin ping on a new registration — no PII, just the total."""
    dispatch_in_background(send_admin_notice(
        f"🆕 Новая регистрация!\nВсего пользователей: {total_users}"
    ))


def notify_admin_bot_blocked(total_blocked: int) -> None:
    """Best-effort admin ping on a fresh bot block — no PII, just the total."""
    dispatch_in_background(send_admin_notice(
        f"🚫 Пользователь заблокировал бота.\nВсего заблокировали: {total_blocked}"
    ))


async def close_bot():
    """Close bot session (call on app shutdown)."""
    global _bot
    if _bot is not None:
        await _bot.session.close()
        _bot = None
