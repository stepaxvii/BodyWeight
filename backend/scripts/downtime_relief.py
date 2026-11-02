"""
One-shot downtime relief: protect streaks + gift compensation coins.

Run this ONCE, right after the provider outage is resolved and BEFORE users
start training again — so the streak bridge lands before any post-outage
workout would otherwise reset a streak.

Two independent actions (toggle with --no-streak / --no-coins):

1. Streak bridge (a FREE freeze covering the whole outage): every user with an
   active streak who couldn't train during the outage gets last_workout_date
   advanced to yesterday, so their next workout continues the streak. It does
   NOT consume paid streak_freezes. Forward-only, so re-running is a safe no-op.

2. Compensation: +COINS coins to every user, exactly once, with an in-app
   notification and a Telegram push explaining the gift. Idempotent via a dedup
   notification (type "downtime_compensation"), so re-runs never double-grant.

Run inside the API container:

    # 1) see what WOULD happen — nothing is written
    docker exec bodyweight-api python scripts/downtime_relief.py --dry-run

    # 2) test on a few users first
    docker exec bodyweight-api python scripts/downtime_relief.py --limit 3

    # 3) for real, everyone
    docker exec bodyweight-api python scripts/downtime_relief.py

Flags:
    --coins N      Coins to grant (default 500)
    --dry-run      Count only, write nothing, send nothing
    --no-push      Grant coins + in-app notice, but skip the Telegram push
    --no-streak    Skip the streak bridge
    --no-coins     Skip the compensation coins
    --limit N      Only the first N users (staged/test run)
"""
import argparse
import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Make `app.*` importable when run as `python scripts/downtime_relief.py`
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.db.database import async_engine, async_session_maker
from app.db.models import Notification, User
from app.logging_config import setup_logging
from app.services.notifications import (
    close_bot,
    save_notification,
    send_announcement_push,
)

logger = logging.getLogger("downtime_relief")

# Dedup identity for the compensation. Don't change unless you deliberately
# want to compensate everyone again.
COMP_TYPE = "downtime_compensation"
COMP_TITLE = "🎁 Подарок за неполадки"


def comp_message(coins: int) -> str:
    """In-app notification body (shown in the bell badge)."""
    return (
        f"Из-за неполадок у провайдера приложение было временно недоступно. "
        f"Извини за неудобства — дарим тебе {coins} монет, а серии за дни "
        f"простоя мы сохранили."
    )


def comp_push(coins: int) -> str:
    """Telegram push (HTML)."""
    return (
        f"🎁 <b>Приносим извинения за неполадки</b>\n\n"
        f"Наш хостинг-провайдер временно лёг, и PixelFit был недоступен — "
        f"ты не виноват, что не смог тренироваться.\n\n"
        f"В качестве извинения дарим тебе <b>{coins}</b> монет 🪙, "
        f"а серии за дни простоя мы сохранили 🔥"
    )


async def already_compensated(session, user_id: int) -> bool:
    """True if this user already received the downtime compensation."""
    result = await session.execute(
        select(Notification.id)
        .where(Notification.user_id == user_id)
        .where(Notification.notification_type == COMP_TYPE)
        .where(Notification.title == COMP_TITLE)
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def main(args: argparse.Namespace) -> None:
    setup_logging()
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)

    bridged = granted = skipped = push_sent = push_failed = 0

    async with async_session_maker() as session:
        users = list((await session.execute(select(User).order_by(User.id))).scalars().all())
        if args.limit is not None:
            users = users[: args.limit]
        logger.info(
            "Relief over %s users | streak=%s coins=%s push=%s dry_run=%s",
            len(users), not args.no_streak, (0 if args.no_coins else args.coins),
            not args.no_push, args.dry_run,
        )

        for user in users:
            did_write = False

            # 1) Streak bridge — free, forward-only. Any active streak that is
            #    behind (couldn't train during the outage) is carried to
            #    yesterday so the next workout continues it. Paid freezes untouched.
            if (
                not args.no_streak
                and user.current_streak > 0
                and user.last_workout_date is not None
                and user.last_workout_date < yesterday
            ):
                if not args.dry_run:
                    user.last_workout_date = yesterday
                bridged += 1
                did_write = True

            # 2) Compensation coins — once per user.
            grant = False
            if not args.no_coins:
                if await already_compensated(session, user.id):
                    skipped += 1
                else:
                    grant = True

            if grant:
                granted += 1
                if not args.dry_run:
                    user.coins += args.coins
                    await save_notification(
                        session=session,
                        user_id=user.id,
                        notification_type=COMP_TYPE,
                        title=COMP_TITLE,
                        message=comp_message(args.coins),
                    )
                    did_write = True

            # Commit per user so a mid-run failure keeps progress and re-runs
            # deduplicate cleanly.
            if did_write and not args.dry_run:
                await session.commit()

            # Telegram push (best-effort, after the coins are committed). The
            # in-app notification above (same transaction as the coins) is the
            # guaranteed copy — the push is just a proactive nudge, so a dropped
            # push (transient failure, or a crash in the narrow commit→push
            # window) is not retried on re-run: the user is already_compensated
            # and still has the bell message. notify_admin_on_block=False: a mass
            # send would otherwise ping the admin for every historical block.
            if (
                grant
                and not args.no_push
                and user.notifications_enabled
                and user.telegram_id
            ):
                if args.dry_run:
                    push_sent += 1  # speculative preview count
                else:
                    ok = await send_announcement_push(
                        user.telegram_id, comp_push(args.coins),
                        notify_admin_on_block=False,
                    )
                    if ok:
                        push_sent += 1
                    else:
                        push_failed += 1

    tag = " (DRY RUN)" if args.dry_run else ""
    print("=" * 50)
    print(f"Users processed:      {len(users)}")
    print(f"Streaks bridged:      {bridged}{tag}")
    print(f"Coins granted:        {granted}{tag}")
    print(f"Already compensated:  {skipped}")
    print(f"Telegram pushes:      {push_sent}{tag}")
    print(f"Push failures:        {push_failed}")
    print("=" * 50)

    await close_bot()
    await async_engine.dispose()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Downtime relief: streak bridge + compensation coins.")
    p.add_argument("--coins", type=int, default=500, help="Coins to grant (default 500)")
    p.add_argument("--dry-run", action="store_true", help="Count only, write/send nothing")
    p.add_argument("--no-push", action="store_true", help="Skip the Telegram push")
    p.add_argument("--no-streak", action="store_true", help="Skip the streak bridge")
    p.add_argument("--no-coins", action="store_true", help="Skip the compensation coins")
    p.add_argument("--limit", type=int, default=None, help="Only the first N users")
    return p.parse_args()


if __name__ == "__main__":
    asyncio.run(main(parse_args()))
