import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import settings
from app.bot.session import make_ipv4_session
from app.i18n import t

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


async def mark_bot_reachable(telegram_id: int, reachable: bool) -> bool:
    """Flip users.bot_reachable for a telegram_id (own session, on transition).

    Set False when a send hits "chat not found"/"user is deactivated" (the user
    never started this bot — distinct from a block). Set True from the bot's
    my_chat_member "member" update when they (re)start. Returns whether the flag
    actually changed.
    """
    from sqlalchemy import update
    from app.db.database import async_session_maker
    from app.db.models import User

    try:
        async with async_session_maker() as session:
            result = await session.execute(
                update(User)
                .where(User.telegram_id == telegram_id)
                .where(User.bot_reachable != reachable)
                .values(bot_reachable=reachable)
            )
            await session.commit()
            return (result.rowcount or 0) > 0
    except Exception:
        logger.exception("Failed to update bot_reachable for %s", telegram_id)
        return False


# Bad-Request messages that mean "we can't deliver to this chat at all" (the
# user never started this bot / deleted their account) — not a transient error.
_UNREACHABLE_MARKERS = (
    "chat not found",
    "user is deactivated",
    "bot can't initiate conversation",
)


async def _send(
    telegram_id: int,
    text: str,
    *,
    keyboard: InlineKeyboardMarkup | None = None,
    label: str = "push",
    notify_admin_on_block: bool = True,
) -> bool:
    """Single Telegram-send path for every push. Returns True on success.

    A 403 means the user blocked the bot — expected, not an error: log at INFO,
    record the block, and (unless suppressed) ping the admin once if this is a
    fresh discovery. ``notify_admin_on_block=False`` during mass broadcasts so a
    wave of historical blocks doesn't flood the admin — the digest still shows
    the jump. A "chat not found" means they never started this bot: flag them
    unreachable (no admin ping). Transient/other errors log with a traceback.
    """
    try:
        bot = get_bot()
        await bot.send_message(chat_id=telegram_id, text=text, reply_markup=keyboard)
        logger.info("%s sent to %s", label, telegram_id)
        return True
    except TelegramForbiddenError:
        logger.info("%s skipped: %s has blocked the bot", label, telegram_id)
        changed, total_blocked = await mark_bot_blocked(telegram_id, True)
        if changed and notify_admin_on_block:
            notify_admin_bot_blocked(total_blocked)
        return False
    except TelegramBadRequest as e:
        if any(m in (e.message or "").lower() for m in _UNREACHABLE_MARKERS):
            logger.info(
                "%s skipped: %s has no chat with the bot (%s)",
                label, telegram_id, e.message,
            )
            await mark_bot_reachable(telegram_id, False)
        else:
            logger.exception("Failed to send %s to %s", label, telegram_id)
        return False
    except Exception:
        logger.exception("Failed to send %s to %s", label, telegram_id)
        return False


def get_open_app_keyboard(lang: str | None = None) -> InlineKeyboardMarkup:
    """Get keyboard with button to open the Mini App."""
    from aiogram.types import WebAppInfo
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "bot.keyboard.open_app"),
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
    lang: str = "en",
) -> bool:
    """
    Send notification about new friend request.

    Args:
        telegram_id: Telegram ID of the user to notify
        from_user_name: Name/username of the user who sent the request
        lang: recipient's UI language ('ru'|'en')

    Returns:
        True if notification was sent successfully
    """
    text = t(lang, "notifications.friend_request.push", from_user_name=from_user_name)
    return await _send(
        telegram_id, text,
        keyboard=get_open_app_keyboard(lang), label="Friend request notification",
    )


async def send_daily_reminder(telegram_id: int, streak: int = 0, lang: str = "en") -> bool:
    """
    Send daily workout reminder.

    Args:
        telegram_id: Telegram ID of the user to notify
        streak: Current streak days
        lang: recipient's UI language ('ru'|'en')

    Returns:
        True if notification was sent successfully
    """
    if streak > 0:
        text = t(lang, "notifications.daily_reminder.with_streak", streak=streak)
    else:
        text = t(lang, "notifications.daily_reminder.no_streak")
    return await _send(
        telegram_id, text,
        keyboard=get_open_app_keyboard(lang), label="Daily reminder",
    )


async def send_inactivity_reminder(telegram_id: int, days_inactive: int, lang: str = "en") -> bool:
    """
    Send reminder to inactive user.

    Args:
        telegram_id: Telegram ID of the user to notify
        days_inactive: Number of days since last workout
        lang: recipient's UI language ('ru'|'en')

    Returns:
        True if notification was sent successfully
    """
    text = t(lang, "notifications.inactivity.push", days_inactive=days_inactive)
    return await _send(
        telegram_id, text,
        keyboard=get_open_app_keyboard(lang),
        label=f"Inactivity reminder ({days_inactive}d)",
    )


async def send_friend_accepted_notification(
    telegram_id: int,
    friend_name: str,
    lang: str = "en",
) -> bool:
    """
    Send notification that friend request was accepted.

    Args:
        telegram_id: Telegram ID of the user to notify
        friend_name: Name/username of the friend who accepted
        lang: recipient's UI language ('ru'|'en')

    Returns:
        True if notification was sent successfully
    """
    text = t(lang, "notifications.friend_accepted.push", friend_name=friend_name)
    return await _send(
        telegram_id, text,
        keyboard=get_open_app_keyboard(lang), label="Friend accepted notification",
    )


async def send_friend_workout_notification(
    telegram_id: int,
    friend_name: str,
    lang: str = "en",
) -> bool:
    """
    Send notification that a friend completed a workout today.

    Args:
        telegram_id: Telegram ID of the user to notify
        friend_name: Name/username of the friend who worked out
        lang: recipient's UI language ('ru'|'en')

    Returns:
        True if notification was sent successfully
    """
    text = t(lang, "notifications.friend_workout.push", friend_name=friend_name)
    return await _send(
        telegram_id, text,
        keyboard=get_open_app_keyboard(lang), label="Friend workout notification",
    )


async def send_friend_workout_notifications(
    telegram_ids: list[int],
    friend_name: str,
    langs: dict[int, str] | None = None,
) -> None:
    """Send the 'friend worked out today' push to many users concurrently.

    Best-effort: each send has its own try/except (returns False on failure) and
    we also pass return_exceptions=True so one failure can't cancel the rest.
    Meant to be run via dispatch_in_background so it never blocks the submit.

    ``langs`` optionally maps telegram_id -> UI language; missing entries fall
    back to English.
    """
    if not telegram_ids:
        return
    langs = langs or {}
    await asyncio.gather(
        *(
            send_friend_workout_notification(
                telegram_id=tid, friend_name=friend_name, lang=langs.get(tid, "en")
            )
            for tid in telegram_ids
        ),
        return_exceptions=True,
    )


def get_open_challenge_keyboard(challenge_id: int, lang: str | None = None) -> InlineKeyboardMarkup:
    """Keyboard whose button deep-links straight into a specific challenge.

    Uses the bot ``startapp`` deep link so tapping opens the Mini App with
    ``start_param = "challenge_<id>"`` (routed to /challenges/<id> on the front).
    """
    url = f"https://t.me/{settings.bot_username}?startapp=challenge_{challenge_id}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "bot.keyboard.open_challenge"), url=url)]
        ]
    )


async def send_new_challenge_push(
    telegram_id: int,
    creator_name: str,
    challenge_title: str,
    challenge_id: int,
    lang: str = "en",
) -> bool:
    """Tell a friend that someone created a new challenge they can still join."""
    text = t(
        lang,
        "notifications.new_challenge.push",
        creator_name=creator_name,
        challenge_title=challenge_title,
    )
    return await _send(
        telegram_id, text,
        keyboard=get_open_challenge_keyboard(challenge_id, lang),
        label="New-challenge notification",
    )


# --- RPG quests (districts) ---------------------------------------------------
# Push wrappers for quest events, mirroring send_new_challenge_push. The in-app
# row is written by the caller via save_notification (same txn as the state
# change); these fire the Telegram push post-commit via dispatch_in_background.
# Content ({quest_title}/{district_name}/{reward}) is passed already-localized by
# the caller from districts.json (decision 1); `lang` is the recipient's
# users.language used for the .push template + keyboard button label.


async def send_quest_accepted_push(
    telegram_id: int,
    quest_title: str,
    district_name: str,
    days: int,
    quest_challenge_id: int,
    lang: str = "en",
) -> bool:
    """Confirm to the player that they picked up a quest (deep-links into it)."""
    text = t(
        lang,
        "quest.accepted.push",
        quest_title=quest_title,
        district_name=district_name,
        days=days,
    )
    return await _send(
        telegram_id, text,
        keyboard=get_open_challenge_keyboard(quest_challenge_id, lang),
        label="Quest-accepted notification",
    )


async def send_quest_completed_push(
    telegram_id: int,
    quest_title: str,
    reward: str,
    quest_challenge_id: int,
    lang: str = "en",
) -> bool:
    """Tell the player they cleared a quest and what the fixed reward was."""
    text = t(
        lang,
        "quest.completed.push",
        quest_title=quest_title,
        reward=reward,
    )
    return await _send(
        telegram_id, text,
        keyboard=get_open_challenge_keyboard(quest_challenge_id, lang),
        label="Quest-completed notification",
    )


async def send_district_unlocked_push(
    telegram_id: int,
    district_name: str,
    lang: str = "en",
) -> bool:
    """Announce a newly unlocked district (opens the app, not a specific quest)."""
    text = t(lang, "quest.district_unlocked.push", district_name=district_name)
    return await _send(
        telegram_id, text,
        keyboard=get_open_app_keyboard(lang),
        label="District-unlocked notification",
    )


async def send_quest_failed_push(
    telegram_id: int,
    quest_title: str,
    days: int,
    lang: str = "en",
) -> bool:
    """Tell the player the quest window closed before they cleared every day."""
    text = t(lang, "quest.failed.push", quest_title=quest_title, days=days)
    return await _send(
        telegram_id, text,
        keyboard=get_open_app_keyboard(lang),
        label="Quest-failed notification",
    )


async def send_quest_invite_received_push(
    telegram_id: int,
    from_user_name: str,
    quest_title: str,
    district_name: str,
    quest_challenge_id: int,
    lang: str = "en",
) -> bool:
    """Tell a friend they were invited to a co-op quest (deep-links into it)."""
    text = t(
        lang,
        "quest.invite.received.push",
        from_user_name=from_user_name,
        quest_title=quest_title,
        district_name=district_name,
    )
    return await _send(
        telegram_id, text,
        keyboard=get_open_challenge_keyboard(quest_challenge_id, lang),
        label="Quest-invite-received notification",
    )


async def send_quest_invite_accepted_push(
    telegram_id: int,
    partner_name: str,
    quest_title: str,
    quest_challenge_id: int,
    lang: str = "en",
) -> bool:
    """Tell the inviter that the partner accepted the co-op invite."""
    text = t(
        lang,
        "quest.invite.accepted.push",
        partner_name=partner_name,
        quest_title=quest_title,
    )
    return await _send(
        telegram_id, text,
        keyboard=get_open_challenge_keyboard(quest_challenge_id, lang),
        label="Quest-invite-accepted notification",
    )


async def send_quest_invite_declined_push(
    telegram_id: int,
    partner_name: str,
    quest_title: str,
    quest_challenge_id: int,
    lang: str = "en",
) -> bool:
    """Tell the inviter that the partner declined the co-op invite."""
    text = t(
        lang,
        "quest.invite.declined.push",
        partner_name=partner_name,
        quest_title=quest_title,
    )
    return await _send(
        telegram_id, text,
        keyboard=get_open_challenge_keyboard(quest_challenge_id, lang),
        label="Quest-invite-declined notification",
    )


async def send_announcement_push(
    telegram_id: int, text: str, *, notify_admin_on_block: bool = True, lang: str = "en"
) -> bool:
    """
    Send a generic announcement push to a user via Telegram bot.
    Used for one-off feature announcements (new release, etc.).

    Args:
        telegram_id: Telegram ID of the user to notify
        text: HTML-formatted message body (already localized by the caller)
        notify_admin_on_block: set False for mass broadcasts so a wave of
            historical blocks doesn't flood the admin (the digest still shows it)
        lang: recipient's UI language, used only for the keyboard button label

    Returns:
        True if notification was sent successfully
    """
    return await _send(
        telegram_id, text,
        keyboard=get_open_app_keyboard(lang), label="Announcement push",
        notify_admin_on_block=notify_admin_on_block,
    )


async def send_referral_reward_push(telegram_id: int, text: str, lang: str = "en") -> bool:
    """
    Send the referral reward push to the inviter via Telegram bot.
    Used when an invited user completes their first workout.

    Args:
        telegram_id: Telegram ID of the inviter to notify
        text: HTML-formatted message body (already localized by the caller)
        lang: recipient's UI language, used only for the keyboard button label

    Returns:
        True if notification was sent successfully
    """
    return await _send(
        telegram_id, text,
        keyboard=get_open_app_keyboard(lang), label="Referral reward push",
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
        t("ru", "notifications.admin.new_user", total_users=total_users)
    ))


def notify_admin_bot_blocked(total_blocked: int) -> None:
    """Best-effort admin ping on a fresh bot block — no PII, just the total."""
    dispatch_in_background(send_admin_notice(
        t("ru", "notifications.admin.bot_blocked", total_blocked=total_blocked)
    ))


async def broadcast_new_boss_push(
    boss_name_ru: str,
    boss_emoji: str,
    boss_name_en: str | None = None,
    limit: int | None = None,
) -> None:
    """Push the monthly new-boss announcement to every reachable user.

    Reachable = has a telegram_id, notifications on, hasn't blocked the bot.
    Each recipient gets the push in their own UI language (``users.language``);
    the boss name is localized too (``boss_name_en`` for English, falling back to
    the Russian name when no English name is supplied).
    Throttled (~22/s) to respect Telegram's rate limit; 403s still record the
    block (counts update) but DON'T ping the admin per user — a mass broadcast
    would otherwise flood them. Best-effort: dispatched off the request path
    (see get_or_create_current_boss) so it never blocks boss creation.
    ``limit`` caps recipients (staged/test runs from the one-off script).
    """
    from sqlalchemy import select
    from app.db.database import async_session_maker
    from app.db.models import User

    try:
        async with async_session_maker() as session:
            rows = (
                await session.execute(
                    select(User.telegram_id, User.language)
                    .where(User.telegram_id.isnot(None))
                    .where(User.notifications_enabled.is_(True))
                    .where(User.bot_blocked.is_(False))
                    .where(User.bot_reachable.is_(True))
                )
            ).all()
    except Exception:
        logger.exception("New-boss broadcast: failed to load audience")
        return

    recipients = [(r[0], r[1]) for r in rows]
    if limit is not None:
        recipients = recipients[:limit]
    if not recipients:
        return

    def _text(lang: str | None) -> str:
        name = boss_name_en if (lang == "en" and boss_name_en) else boss_name_ru
        return t(lang, "boss.new.push", emoji=boss_emoji, name=name)

    logger.info("New-boss broadcast: sending to %s users", len(recipients))

    sent = 0
    chunk = 25
    for i in range(0, len(recipients), chunk):
        batch = recipients[i:i + chunk]
        results = await asyncio.gather(
            *(
                _send(
                    tid, _text(lang),
                    keyboard=get_open_app_keyboard(lang),
                    label="New-boss push",
                    notify_admin_on_block=False,
                )
                for tid, lang in batch
            ),
            return_exceptions=True,
        )
        sent += sum(1 for r in results if r is True)
        if i + chunk < len(recipients):
            await asyncio.sleep(1.1)  # stay under Telegram's ~30 msg/s cap

    logger.info("New-boss broadcast done: %s/%s delivered", sent, len(recipients))


async def close_bot():
    """Close bot session (call on app shutdown)."""
    global _bot
    if _bot is not None:
        await _bot.session.close()
        _bot = None
