"""
Notification scheduler for sending reminders.

This module provides functions to check and send notifications:
- Daily workout reminders (based on user's notification_time setting)
- Inactivity reminders (after 3 days without workout)

Includes built-in APScheduler integration for automatic scheduling.
"""

import logging
from datetime import datetime, date, timedelta, time
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.db.models import User
from app.services.notifications import send_daily_reminder, send_inactivity_reminder

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: AsyncIOScheduler | None = None


async def check_daily_reminders(session: AsyncSession) -> int:
    """
    Check and send daily workout reminders.

    Sends reminders to users who:
    - Have notifications_enabled = True
    - Have notification_time set
    - notification_time matches current hour:minute (within 1 minute window)
    - Haven't worked out today

    Returns:
        Number of reminders sent
    """
    now = datetime.now()
    current_time = now.time()
    today = now.date()

    # Find users whose notification time is now (within 1 minute window)
    # We check if notification_time hour and minute match current time
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

        # Check if it's time to send notification (same hour and minute)
        if (user.notification_time.hour == current_time.hour and
            user.notification_time.minute == current_time.minute):

            # Don't send if already worked out today
            if user.last_workout_date == today:
                continue

            # Send reminder
            success = await send_daily_reminder(
                telegram_id=user.telegram_id,
                streak=user.current_streak,
            )

            if success:
                sent_count += 1

    if sent_count > 0:
        logger.info(f"Sent {sent_count} daily reminders")

    return sent_count


async def check_inactivity_reminders(session: AsyncSession) -> int:
    """
    Check and send inactivity reminders.

    Sends reminders to users who:
    - Have notifications_enabled = True
    - Haven't worked out in exactly 3 days
    - Have done at least one workout before (last_workout_date is not None)

    Returns:
        Number of reminders sent
    """
    today = date.today()
    three_days_ago = today - timedelta(days=3)

    # Find users who last worked out exactly 3 days ago
    result = await session.execute(
        select(User)
        .where(User.notifications_enabled == True)
        .where(User.last_workout_date == three_days_ago)
    )
    users = result.scalars().all()

    sent_count = 0

    for user in users:
        success = await send_inactivity_reminder(
            telegram_id=user.telegram_id,
            days_inactive=3,
        )

        if success:
            sent_count += 1

    if sent_count > 0:
        logger.info(f"Sent {sent_count} inactivity reminders")

    return sent_count


async def run_notification_checks(session: AsyncSession) -> dict:
    """
    Run all notification checks.

    Call this function periodically (every minute) to send notifications.

    Returns:
        Dict with counts of sent notifications by type
    """
    results = {
        "daily_reminders": 0,
        "inactivity_reminders": 0,
    }

    try:
        results["daily_reminders"] = await check_daily_reminders(session)
    except Exception as e:
        logger.error(f"Error checking daily reminders: {e}")

    # Only check inactivity once per day (at noon)
    if datetime.now().hour == 12 and datetime.now().minute == 0:
        try:
            results["inactivity_reminders"] = await check_inactivity_reminders(session)
        except Exception as e:
            logger.error(f"Error checking inactivity reminders: {e}")

    return results


async def scheduled_notification_job():
    """
    Job function called by APScheduler every minute.
    Creates its own database session.
    """
    from app.db.database import async_session_maker

    async with async_session_maker() as session:
        try:
            results = await run_notification_checks(session)
            if results["daily_reminders"] > 0 or results["inactivity_reminders"] > 0:
                logger.info(f"Notification check results: {results}")
        except Exception as e:
            logger.error(f"Error in scheduled notification job: {e}")


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

    # Run notification checks every minute
    scheduler.add_job(
        scheduled_notification_job,
        trigger=IntervalTrigger(minutes=1),
        id="notification_checks",
        name="Check and send notifications",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Notification scheduler started (running every minute)")


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
