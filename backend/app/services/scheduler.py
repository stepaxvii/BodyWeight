"""
Notification scheduler for sending Telegram push reminders.

This module provides functions to send Telegram notifications:
- Daily workout reminders (based on user's notification_time setting)
- Inactivity reminders (after 3 days without workout)

Note: In-app notifications (bell icon) are created separately in API routes.
Telegram pushes respect user's notification preferences.

Includes built-in APScheduler integration for automatic scheduling.
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.db.models import Notification, User
from app.i18n import t
from app.services.notifications import (
    send_daily_reminder,
    send_inactivity_reminder,
    save_notification,
)
from app.services.timezones import local_day_bounds_utc, user_local_now

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: AsyncIOScheduler | None = None

# Local hour (in each user's own timezone) at which inactivity nudges go out.
INACTIVITY_LOCAL_HOUR = 12


async def _already_sent_today(
    session: AsyncSession, user: User, notif_type: str, local_today
) -> bool:
    """True if a notification of ``notif_type`` already landed for this user on
    their current LOCAL calendar day. Used to make the hourly jobs idempotent
    across a DST fall-back, when the gated local wall-clock hour repeats and the
    cron would otherwise fire a second identical push + bell row."""
    day_start, _ = local_day_bounds_utc(local_today, user.timezone)
    existing = await session.execute(
        select(Notification.id)
        .where(Notification.user_id == user.id)
        .where(Notification.notification_type == notif_type)
        .where(Notification.created_at >= day_start)
        .limit(1)
    )
    return existing.scalar_one_or_none() is not None


async def check_daily_reminders(session: AsyncSession) -> int:
    """
    Send daily workout reminders via Telegram at each user's LOCAL notification hour.

    Fires for users who:
    - have notifications_enabled = True (opted in for Telegram pushes),
    - have notification_time set whose HOUR matches the current hour in THEIR
      timezone (``user.timezone``), and
    - haven't worked out yet on their own local calendar day.

    Run hourly: the local-hour match is true for exactly one hour per user, the
    last_workout_date guard drops users once they train, and a per-local-day
    dedup guard covers the DST fall-back case where the gated hour repeats — so
    each user is reminded at most once per local day.

    Returns:
        Number of reminders sent
    """
    result = await session.execute(
        select(User)
        .where(User.notifications_enabled == True)
        .where(User.notification_time.isnot(None))
    )
    users = result.scalars().all()

    sent_count = 0

    for user in users:
        local_now = user_local_now(user.timezone)
        # Match the user's chosen hour against their OWN local clock.
        if user.notification_time.hour != local_now.hour:
            continue
        # Already trained on their local day → nothing to nudge.
        if user.last_workout_date == local_now.date():
            continue
        # Idempotency across a repeated DST wall-clock hour.
        if await _already_sent_today(session, user, "daily_reminder", local_now.date()):
            continue

        # Send Telegram push
        success = await send_daily_reminder(
            telegram_id=user.telegram_id,
            streak=user.current_streak,
            lang=user.language,
        )

        if success:
            sent_count += 1
            # Also save as in-app notification (recipient's language)
            title = t(user.language, "notifications.daily_reminder.title")
            if user.current_streak > 0:
                message = t(
                    user.language,
                    "notifications.daily_reminder.message_with_streak",
                    streak=user.current_streak,
                )
            else:
                message = t(user.language, "notifications.daily_reminder.message_no_streak")
            await save_notification(
                session=session,
                user_id=user.id,
                notification_type="daily_reminder",
                title=title,
                message=message,
            )

    if sent_count > 0:
        logger.info(f"Sent {sent_count} daily reminders")

    return sent_count


async def check_inactivity_reminders(session: AsyncSession) -> int:
    """
    Send inactivity reminders via Telegram at each user's local noon.

    Fires for users who:
    - have notifications_enabled = True,
    - have done at least one workout before,
    - are exactly 3, 7 or 14 days inactive on THEIR local calendar, and
    - it is currently ~noon in their timezone.

    Run hourly: the local-noon gate, the exact-day-count match and a per-local-day
    dedup guard (for the DST fall-back repeated hour) mean each threshold fires at
    most once per user. After 14 days no more are sent.

    Returns:
        Number of reminders sent
    """
    reminder_days = {3, 7, 14}

    # Coarse pre-filter: only users whose last workout falls inside the widest
    # threshold window, padded by a day on each side for timezone skew (a user's
    # local "today" can be UTC today ±1). The exact day count is verified below
    # against each user's local calendar.
    utc_today = datetime.utcnow().date()
    coarse_lo = utc_today - timedelta(days=15)
    coarse_hi = utc_today - timedelta(days=2)

    result = await session.execute(
        select(User)
        .where(User.notifications_enabled == True)
        .where(User.last_workout_date.isnot(None))
        .where(User.last_workout_date >= coarse_lo)
        .where(User.last_workout_date <= coarse_hi)
    )
    users = result.scalars().all()

    sent_count = 0

    for user in users:
        local_now = user_local_now(user.timezone)
        if local_now.hour != INACTIVITY_LOCAL_HOUR:
            continue
        days_inactive = (local_now.date() - user.last_workout_date).days
        if days_inactive not in reminder_days:
            continue
        # Idempotency across a repeated DST wall-clock hour.
        if await _already_sent_today(session, user, "inactivity_reminder", local_now.date()):
            continue

        # Send Telegram push
        success = await send_inactivity_reminder(
            telegram_id=user.telegram_id,
            days_inactive=days_inactive,
            lang=user.language,
        )

        if success:
            sent_count += 1
            # Also save as in-app notification (recipient's language)
            await save_notification(
                session=session,
                user_id=user.id,
                notification_type="inactivity_reminder",
                title=t(user.language, "notifications.inactivity.title"),
                message=t(
                    user.language,
                    "notifications.inactivity.message",
                    days_inactive=days_inactive,
                ),
            )

    if sent_count > 0:
        logger.info(f"Sent {sent_count} inactivity reminders")

    return sent_count


async def hourly_notification_job():
    """
    Job function called by APScheduler every hour. Handles both personal push
    streams, each gated on the user's OWN local clock:
    - daily workout reminders at the user's local notification hour, and
    - inactivity reminders at the user's local noon (3/7/14 days).
    """
    from app.db.database import async_session_maker

    async with async_session_maker() as session:
        try:
            daily = await check_daily_reminders(session)
            inactivity = await check_inactivity_reminders(session)
            await session.commit()
            if daily or inactivity:
                logger.info(
                    f"Hourly job: {daily} daily reminders, {inactivity} inactivity reminders"
                )
        except Exception:
            logger.exception("Error in hourly notification job")


async def hourly_streak_freeze_job():
    """
    Run every hour, a couple of minutes before the challenge-lifecycle job.
    Spends a streak freeze for users whose OWN local day has rolled past a
    missed day, or breaks the streak if they have none. Per-user timezone-aware
    and idempotent (see services.streak.process_streak_freezes).
    """
    from app.db.database import async_session_maker
    from app.services.streak import process_streak_freezes

    async with async_session_maker() as session:
        try:
            stats = await process_streak_freezes(session)
            await session.commit()
            if stats["frozen"] or stats["broken"]:
                logger.info(
                    f"Hourly job: streaks frozen={stats['frozen']}, broken={stats['broken']}"
                )
        except Exception:
            logger.exception("Error in hourly streak freeze job")


async def daily_boss_finalization_job():
    """
    Run shortly after midnight UTC. Finalizes any boss whose end_date passed
    or who was defeated. Idempotent — safe if no work to do.
    """
    from app.db.database import async_session_maker
    from app.services.boss import finalize_due_bosses, get_or_create_current_boss

    async with async_session_maker() as session:
        try:
            count = await finalize_due_bosses(session)
            # Ensure a fresh boss exists for the new month so it shows up
            # to users immediately rather than on first /boss/current call.
            await get_or_create_current_boss(session)
            await session.commit()
            if count > 0:
                logger.info(f"Daily job: finalized {count} boss(es)")
        except Exception:
            logger.exception("Error in daily boss finalization job")


async def hourly_challenge_lifecycle_job():
    """
    Run every hour. Transitions challenge statuses (upcoming->active->finished)
    and finalizes finished co-op challenges. Quests advance on the OWNER's local
    day (so the active->finished flip lands at the player's own midnight, wherever
    they live); co-op challenges use a shared UTC boundary. Idempotent.
    """
    from app.db.database import async_session_maker
    from app.services.challenges import (
        update_all_statuses,
        finalize_due_challenges,
    )

    async with async_session_maker() as session:
        try:
            changed = await update_all_statuses(session)
            finalized = await finalize_due_challenges(session)
            await session.commit()
            if changed or finalized:
                logger.info(
                    f"Hourly job: challenges changed={changed}, finalized={finalized}"
                )
        except Exception:
            logger.exception("Error in hourly challenge lifecycle job")


async def daily_admin_stats_job():
    """
    Run at 05:00 UTC (08:00 МСК). Sends the digest for the Moscow day that just
    ended. Skipped when ADMIN_TELEGRAM_ID is not configured.
    """
    from app.config import settings
    from app.db.database import async_session_maker
    from app.services.admin_stats import collect_daily_stats, format_digest, msk_today
    from app.services.notifications import send_admin_digest

    if not settings.admin_telegram_id:
        logger.info("Daily admin stats job skipped: ADMIN_TELEGRAM_ID is not set")
        return

    async with async_session_maker() as session:
        try:
            yesterday = msk_today() - timedelta(days=1)
            stats = await collect_daily_stats(session, yesterday)
            text = format_digest(stats, yesterday)
            if await send_admin_digest(text):
                logger.info(f"Daily job: admin digest for {yesterday} sent")
        except Exception:
            logger.exception("Error in daily admin stats job")


async def weekly_admin_stats_job():
    """
    Run Mondays at 06:00 UTC (09:00 МСК). Sends a 7-day rollup for the Moscow
    week that just ended (Mon–Sun). Skipped when ADMIN_TELEGRAM_ID is unset.
    """
    from app.config import settings
    from app.db.database import async_session_maker
    from app.services.admin_stats import (
        collect_weekly_stats,
        format_weekly_digest,
        msk_today,
    )
    from app.services.notifications import send_admin_digest

    if not settings.admin_telegram_id:
        logger.info("Weekly admin stats job skipped: ADMIN_TELEGRAM_ID is not set")
        return

    async with async_session_maker() as session:
        try:
            end_day = msk_today() - timedelta(days=1)  # yesterday (Sunday)
            stats = await collect_weekly_stats(session, end_day)
            text = format_weekly_digest(stats)
            if await send_admin_digest(text):
                logger.info(f"Weekly job: admin digest for week ending {end_day} sent")
        except Exception:
            logger.exception("Error in weekly admin stats job")


def start_scheduler():
    """
    Start the APScheduler for periodic notification checks.
    Called during application startup.
    """
    global scheduler

    if scheduler is not None:
        logger.warning("Scheduler already running")
        return

    scheduler = AsyncIOScheduler()

    # Personal pushes every hour at :00 — daily reminders fire at each user's
    # local notification hour and inactivity nudges at each user's local noon.
    scheduler.add_job(
        hourly_notification_job,
        trigger=CronTrigger(minute=0),
        id="hourly_reminders",
        name="Personal reminders (hourly, per-user local time)",
        replace_existing=True,
    )

    # Streak maintenance every hour at :02 — must run BEFORE the hourly challenge
    # job. Each user is evaluated against their OWN local midnight, so this has to
    # run hourly to catch every timezone's day rollover.
    scheduler.add_job(
        hourly_streak_freeze_job,
        trigger=CronTrigger(minute=2),
        id="hourly_streak_freeze",
        name="Streak freeze maintenance (hourly, per-user local midnight)",
        replace_existing=True,
    )

    # Challenge lifecycle every hour at :12 — quests flip on the owner's local
    # midnight (so it must run hourly); co-op challenges use a shared UTC boundary.
    scheduler.add_job(
        hourly_challenge_lifecycle_job,
        trigger=CronTrigger(minute=12),
        id="hourly_challenge_lifecycle",
        name="Challenge lifecycle (hourly, owner-local quests)",
        replace_existing=True,
    )

    # Finalize bosses + spawn new monthly boss shortly after UTC midnight. The
    # monthly boss is a single GLOBAL event, so its boundary stays UTC.
    scheduler.add_job(
        daily_boss_finalization_job,
        trigger=CronTrigger(hour=0, minute=5, timezone="UTC"),
        id="daily_boss_finalization",
        name="Finalize bosses + spawn new monthly boss (UTC midnight)",
        replace_existing=True,
    )

    # Yesterday's stats digest to the project admin
    scheduler.add_job(
        daily_admin_stats_job,
        trigger=CronTrigger(hour=5, minute=0, timezone="UTC"),
        id="daily_admin_stats",
        name="Admin daily stats digest (05:00 UTC)",
        replace_existing=True,
    )

    # Weekly rollup every Monday (covers the Moscow Mon–Sun that just ended)
    scheduler.add_job(
        weekly_admin_stats_job,
        trigger=CronTrigger(day_of_week="mon", hour=6, minute=0, timezone="UTC"),
        id="weekly_admin_stats",
        name="Admin weekly stats digest (Mon 06:00 UTC)",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Notification scheduler started (hourly + daily jobs)")


def stop_scheduler():
    """
    Stop the APScheduler.
    Called during application shutdown.
    """
    global scheduler

    if scheduler is not None:
        scheduler.shutdown(wait=False)
        scheduler = None
        logger.info("Notification scheduler stopped")
