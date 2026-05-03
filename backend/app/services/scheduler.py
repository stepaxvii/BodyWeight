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
from datetime import datetime, date, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.db.models import User
from app.services.notifications import (
    send_daily_reminder,
    send_inactivity_reminder,
    save_notification,
)

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: AsyncIOScheduler | None = None


async def check_daily_reminders(session: AsyncSession) -> int:
    """
    Check and send daily workout reminders via Telegram.

    Sends to users who:
    - Have notifications_enabled = True (opted in for Telegram pushes)
    - Have notification_time set matching current hour
    - Haven't worked out today

    Returns:
        Number of reminders sent
    """
    now = datetime.now()
    current_hour = now.hour
    today = now.date()

    # Find users whose notification_time hour matches current hour
    result = await session.execute(
        select(User)
        .where(User.notifications_enabled == True)
        .where(User.notification_time.isnot(None))
    )
    users = result.scalars().all()

    sent_count = 0

    for user in users:
        if user.notification_time is None:
            continue

        # Check if it's the right hour for this user
        if user.notification_time.hour != current_hour:
            continue

        # Don't send if already worked out today
        if user.last_workout_date == today:
            continue

        # Send Telegram push
        success = await send_daily_reminder(
            telegram_id=user.telegram_id,
            streak=user.current_streak,
        )

        if success:
            sent_count += 1
            # Also save as in-app notification
            if user.current_streak > 0:
                title = "Время тренировки!"
                message = f"Твой streak: {user.current_streak} дней подряд! Не останавливайся!"
            else:
                title = "Время тренировки!"
                message = "Начни свой день с упражнений. Даже 10 минут — это уже прогресс!"
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
    Check and send inactivity reminders via Telegram.

    Sends to users who:
    - Have notifications_enabled = True
    - Haven't worked out in 3+ days
    - Have done at least one workout before

    Reminders are sent only on specific days: 3, 7, 14 days of inactivity.
    After 14 days, no more reminders are sent.

    Returns:
        Number of reminders sent
    """
    today = date.today()

    # Days when we send reminders (not every day)
    reminder_days = {3, 7, 14}

    # Find users who last worked out 3+ days ago
    result = await session.execute(
        select(User)
        .where(User.notifications_enabled == True)
        .where(User.last_workout_date.isnot(None))
        .where(User.last_workout_date <= today - timedelta(days=3))
    )
    users = result.scalars().all()

    sent_count = 0

    for user in users:
        days_inactive = (today - user.last_workout_date).days

        # Only send on specific days (3, 7, 14)
        if days_inactive not in reminder_days:
            continue

        # Send Telegram push
        success = await send_inactivity_reminder(
            telegram_id=user.telegram_id,
            days_inactive=days_inactive,
        )

        if success:
            sent_count += 1
            # Also save as in-app notification
            await save_notification(
                session=session,
                user_id=user.id,
                notification_type="inactivity_reminder",
                title="Мы скучаем!",
                message=f"Прошло уже {days_inactive} дней без тренировок. Вернись к занятиям!",
            )

    if sent_count > 0:
        logger.info(f"Sent {sent_count} inactivity reminders")

    return sent_count


async def hourly_notification_job():
    """
    Job function called by APScheduler every hour.
    Checks daily reminders for users whose notification_time matches current hour.
    """
    from app.db.database import async_session_maker

    async with async_session_maker() as session:
        try:
            count = await check_daily_reminders(session)
            await session.commit()
            if count > 0:
                logger.info(f"Hourly job: sent {count} daily reminders")
        except Exception as e:
            logger.error(f"Error in hourly notification job: {e}")


async def daily_inactivity_job():
    """
    Job function called by APScheduler once per day at noon.
    Checks for inactive users and sends reminders.
    """
    from app.db.database import async_session_maker

    async with async_session_maker() as session:
        try:
            count = await check_inactivity_reminders(session)
            await session.commit()
            if count > 0:
                logger.info(f"Daily job: sent {count} inactivity reminders")
        except Exception as e:
            logger.error(f"Error in daily inactivity job: {e}")


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
        except Exception as e:
            logger.error(f"Error in daily boss finalization job: {e}")


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

    # Check daily reminders every hour at :00
    scheduler.add_job(
        hourly_notification_job,
        trigger=CronTrigger(minute=0),
        id="hourly_reminders",
        name="Check daily reminders (hourly)",
        replace_existing=True,
    )

    # Check inactivity once per day at 12:00
    scheduler.add_job(
        daily_inactivity_job,
        trigger=CronTrigger(hour=12, minute=0),
        id="daily_inactivity",
        name="Check inactivity reminders (daily)",
        replace_existing=True,
    )

    # Finalize bosses + spawn new monthly boss shortly after UTC midnight
    scheduler.add_job(
        daily_boss_finalization_job,
        trigger=CronTrigger(hour=0, minute=5, timezone="UTC"),
        id="daily_boss_finalization",
        name="Finalize bosses + spawn new monthly boss (UTC midnight)",
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
