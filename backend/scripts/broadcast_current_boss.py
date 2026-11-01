"""
One-shot: broadcast the CURRENT monthly boss to all reachable users.

Use when a boss spawned before the auto-broadcast shipped (so the monthly
push never went out). Reachable = has a telegram_id, notifications on, hasn't
blocked the bot. Running it also refreshes the bot_blocked flags (every 403
records the block), so the digest's reachable/blocked counts become accurate.

Reuses the production sender (services/notifications.broadcast_new_boss_push):
same copy, same ~22 msg/s throttle, same 403 handling (admin NOT pinged per
user during a mass send).

Run inside the API container:

    # 1) see the boss + audience size, send nothing
    docker exec bodyweight-api python scripts/broadcast_current_boss.py --dry-run

    # 2) test to a few recipients first (first N of the audience)
    docker exec bodyweight-api python scripts/broadcast_current_boss.py --limit 1

    # 3) for real, to everyone
    docker exec bodyweight-api python scripts/broadcast_current_boss.py

Not idempotent — a second full run sends the push again. Prefer --dry-run,
then --limit, then the full run.
"""
import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Make `app.*` importable when run as `python scripts/broadcast_current_boss.py`
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func, select

from app.db.database import async_engine, async_session_maker
from app.db.models import MonthlyBoss, User
from app.logging_config import setup_logging
from app.services.notifications import broadcast_new_boss_push, close_bot

import logging

logger = logging.getLogger("broadcast_current_boss")


async def _current_boss(session) -> MonthlyBoss | None:
    today = datetime.utcnow().date()
    return (
        await session.execute(
            select(MonthlyBoss)
            .where(MonthlyBoss.start_date <= today)
            .where(MonthlyBoss.end_date >= today)
            .where(MonthlyBoss.status == "active")
        )
    ).scalar_one_or_none()


async def _reachable_count(session) -> int:
    return (
        await session.execute(
            select(func.count())
            .select_from(User)
            .where(User.telegram_id.isnot(None))
            .where(User.notifications_enabled.is_(True))
            .where(User.bot_blocked.is_(False))
        )
    ).scalar_one()


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Broadcast the current monthly boss to all reachable users."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show the boss and audience size, send nothing.",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Cap recipients to the first N (for a staged/test run).",
    )
    args = parser.parse_args()

    setup_logging()

    async with async_session_maker() as session:
        boss = await _current_boss(session)
        reachable = await _reachable_count(session)

    if boss is None:
        logger.error("No active boss for the current month — nothing to broadcast.")
        return

    logger.info(
        "Boss of the month: %s %s  |  reachable audience: %s",
        boss.image_emoji, boss.name_ru, reachable,
    )

    if args.dry_run:
        logger.info("Dry run — no messages sent.")
        return

    if reachable == 0:
        logger.info("No reachable users — nothing to send.")
        return

    target = min(reachable, args.limit) if args.limit else reachable
    logger.info("Sending to %s user(s)%s …", target, " (limited)" if args.limit else "")

    try:
        await broadcast_new_boss_push(boss.name_ru, boss.image_emoji, limit=args.limit)
    finally:
        await close_bot()
        await async_engine.dispose()

    logger.info("Done. Check the logs above for the delivered count.")


if __name__ == "__main__":
    asyncio.run(main())
