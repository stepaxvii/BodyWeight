"""
Streak freeze service.

Users buy "streak freezes" with coins. Each freeze is automatically spent
overnight to cover a single missed day so the streak survives (Duolingo-style).

The job runs hourly and evaluates each user against their OWN local calendar:
once a user's local day has rolled past a day they did NOT train, it either
spends one freeze (bridging ``last_workout_date`` so the streak continues) or,
if they have none, resets the streak to 0.
"""
import logging
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.i18n import t
from app.services.notifications import save_notification, send_announcement_push
from app.services.timezones import user_local_today

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
        raise ValueError(
            t(user.language, "content.streak_freeze_cap", max=MAX_STREAK_FREEZES)
        )
    if user.coins < STREAK_FREEZE_PRICE_COINS:
        raise ValueError(
            t(
                user.language,
                "content.streak_freeze_funds",
                price=STREAK_FREEZE_PRICE_COINS,
                coins=user.coins,
            )
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

    Timezone-aware: each user's "yesterday" is computed from their own local
    calendar (``last_workout_date`` is stored as the user's local date), so the
    job is run hourly and only acts on a user once their OWN local day has rolled
    past the missed day.

    Idempotent within a day: bridged users have ``last_workout_date`` bumped to
    their local yesterday and broken users drop to streak 0, so neither is acted
    on again on a re-run. Returns counts for logging.
    """
    # Fetch every user with a live streak; decide per-user against their local
    # calendar (a single global UTC "yesterday" would mis-fire across zones).
    result = await session.execute(
        select(User)
        .where(User.current_streak > 0)
        .where(User.last_workout_date.isnot(None))
    )
    candidates = list(result.scalars().all())

    frozen = 0
    broken = 0
    users = []
    for user in candidates:
        local_yesterday = user_local_today(user.timezone) - timedelta(days=1)
        # Trained yesterday or today (local) → streak intact, nothing to do yet.
        if user.last_workout_date >= local_yesterday:
            continue
        users.append(user)
        if user.streak_freezes > 0:
            # Spend a freeze and bridge: pretend they trained yesterday so the
            # streak continues and the next workout increments it normally.
            user.streak_freezes -= 1
            user.last_workout_date = local_yesterday
            frozen += 1

            await save_notification(
                session=session,
                user_id=user.id,
                notification_type="streak_freeze_used",
                title=t(user.language, "notifications.streak_freeze.title"),
                message=t(
                    user.language,
                    "notifications.streak_freeze.message",
                    streak=user.current_streak,
                    freezes=user.streak_freezes,
                ),
            )

            if user.notifications_enabled and user.telegram_id:
                try:
                    await send_announcement_push(
                        user.telegram_id,
                        t(
                            user.language,
                            "notifications.streak_freeze.push",
                            streak=user.current_streak,
                            freezes=user.streak_freezes,
                        ),
                        lang=user.language,
                    )
                except Exception:
                    logger.exception("Failed to push streak-freeze notice to %s", user.telegram_id)
        else:
            user.current_streak = 0
            broken += 1

    return {"frozen": frozen, "broken": broken, "checked": len(users)}
