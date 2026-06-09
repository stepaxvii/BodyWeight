"""
Streak freeze service.

Users buy "streak freezes" with coins. Each freeze is automatically spent
overnight to cover a single missed day so the streak survives (Duolingo-style).

The nightly job (00:01 UTC, before the boss/challenge jobs) processes the day
that just ended: for anyone with an active streak who did NOT train yesterday it
either spends one freeze (bridging ``last_workout_date`` so the streak continues)
or, if they have none, resets the streak to 0.
"""
import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.services.notifications import save_notification, send_announcement_push

logger = logging.getLogger(__name__)

# Tunables
STREAK_FREEZE_PRICE_COINS = 500
MAX_STREAK_FREEZES = 2


async def buy_streak_freeze(session: AsyncSession, user: User) -> User:
    """
    Buy one streak freeze for the user.

    Raises ValueError if the user is already at the cap or can't afford it.
    """
    if user.streak_freezes >= MAX_STREAK_FREEZES:
        raise ValueError(f"Можно держать не больше {MAX_STREAK_FREEZES} заморозок")
    if user.coins < STREAK_FREEZE_PRICE_COINS:
        raise ValueError(
            f"Недостаточно монет: нужно {STREAK_FREEZE_PRICE_COINS}, есть {user.coins}"
        )

    user.coins -= STREAK_FREEZE_PRICE_COINS
    user.streak_freezes += 1
    await session.flush()
    return user


async def process_streak_freezes(session: AsyncSession) -> dict:
    """
    Overnight streak maintenance. Run once per day shortly after UTC midnight.

    For every user with an active streak who didn't train yesterday:
    - spend one freeze and bridge the gap (streak survives), or
    - reset the streak to 0 if they have no freeze left.

    Idempotent within a day: bridged/broken users are no longer selected on a
    re-run. Returns counts for logging.
    """
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)

    # last_workout_date < yesterday  ==  did not train yesterday or today
    result = await session.execute(
        select(User)
        .where(User.current_streak > 0)
        .where(User.last_workout_date.isnot(None))
        .where(User.last_workout_date < yesterday)
    )
    users = list(result.scalars().all())

    frozen = 0
    broken = 0
    for user in users:
        if user.streak_freezes > 0:
            # Spend a freeze and bridge: pretend they trained yesterday so the
            # streak continues and the next workout increments it normally.
            user.streak_freezes -= 1
            user.last_workout_date = yesterday
            frozen += 1

            await save_notification(
                session=session,
                user_id=user.id,
                notification_type="streak_freeze_used",
                title="🧊 Заморозка использована",
                message=(
                    f"Ты пропустил день, но заморозка спасла серию — "
                    f"стрик {user.current_streak} дней сохранён. "
                    f"Осталось заморозок: {user.streak_freezes}."
                ),
            )

            if user.notifications_enabled and user.telegram_id:
                try:
                    await send_announcement_push(
                        user.telegram_id,
                        (
                            f"🧊 <b>Заморозка спасла твой стрик!</b>\n\n"
                            f"Ты пропустил день, но серия в <b>{user.current_streak}</b> "
                            f"дней сохранена.\nОсталось заморозок: <b>{user.streak_freezes}</b>."
                        ),
                    )
                except Exception:
                    logger.exception("Failed to push streak-freeze notice to %s", user.telegram_id)
        else:
            user.current_streak = 0
            broken += 1

    return {"frozen": frozen, "broken": broken, "checked": len(users)}
