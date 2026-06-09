"""
One-shot announcement to all users about the Challenges feature.

Idempotent: re-running won't double-send. Each user receives the in-app
notification + Telegram push once. Dedup is keyed by (user_id,
notification_type, title) — so changing the TITLE constant below would
"reset" dedup for new copy.

Run from server (or inside the API container):

    docker exec bodyweight-api python scripts/announce_challenges.py

Flags:
    --dry-run         Don't send anything, just show counts
    --no-push         Skip Telegram push, only save in-app notifications
    --limit N         Send to first N users (for staged rollout / testing)

It is safe to re-run after a partial failure; users who already got the
announcement will be skipped automatically.
"""
import asyncio
import sys
from pathlib import Path

# Make `app.*` importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import async_engine, async_session_maker
from app.db.models import User, Notification
from app.services.notifications import (
    save_notification,
    send_announcement_push,
    close_bot,
)


# Identifier for dedup. Don't change unless you intentionally want to
# re-announce to everyone.
ANNOUNCEMENT_KEY = "Челленджи: новая фича"

NOTIFICATION_TYPE = "feature_announcement"

# In-app notification (shown in the bell badge)
TITLE = ANNOUNCEMENT_KEY
MESSAGE = (
    "Появились челленджи — публичные задания на N дней. "
    "Создавай свои или присоединяйся к чужим, отмечай дни в календаре, "
    "забирай монеты в конце. Открой вкладку «Челленджи» (иконка календаря)."
)

# Telegram push (HTML)
PUSH_TEXT = (
    "🏆 <b>В PixelFit появились челленджи!</b>\n\n"
    "Публичные задания на N дней — создавай свои или присоединяйся к чужим. "
    "Каждый день тренируешься = галочка в календаре. "
    "В конце — монеты по проценту выполнения.\n\n"
    "📅 Открой Mini App и переключись на вкладку <b>Челленджи</b> (иконка календаря в нав-баре)."
)


async def already_announced(session: AsyncSession, user_id: int) -> bool:
    """True if this user already received this announcement."""
    result = await session.execute(
        select(Notification.id)
        .where(Notification.user_id == user_id)
        .where(Notification.notification_type == NOTIFICATION_TYPE)
        .where(Notification.title == TITLE)
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def main(dry_run: bool, no_push: bool, limit: int | None) -> None:
    saved_in_app = 0
    push_sent = 0
    push_failed = 0
    skipped = 0
    total_seen = 0

    async with async_session_maker() as session:
        users_q = await session.execute(select(User).order_by(User.id))
        users = list(users_q.scalars().all())
        if limit is not None:
            users = users[:limit]

        for user in users:
            total_seen += 1

            if await already_announced(session, user.id):
                skipped += 1
                continue

            if dry_run:
                # Just count — don't write or push
                saved_in_app += 1
                if not no_push and user.notifications_enabled and user.telegram_id:
                    push_sent += 1  # speculative count
                continue

            # In-app notification (always)
            await save_notification(
                session=session,
                user_id=user.id,
                notification_type=NOTIFICATION_TYPE,
                title=TITLE,
                message=MESSAGE,
            )
            saved_in_app += 1

            # Commit per-user so a failure midway doesn't lose progress and
            # subsequent re-runs deduplicate cleanly.
            await session.commit()

            # Telegram push (best-effort)
            if not no_push and user.notifications_enabled and user.telegram_id:
                ok = await send_announcement_push(user.telegram_id, PUSH_TEXT)
                if ok:
                    push_sent += 1
                else:
                    push_failed += 1

    print("=" * 50)
    print(f"Total users seen:     {total_seen}")
    print(f"Already announced:    {skipped}")
    print(f"In-app notifications: {saved_in_app}{' (DRY RUN)' if dry_run else ''}")
    print(f"Telegram pushes:      {push_sent}{' (DRY RUN)' if dry_run else ''}")
    print(f"Push failures:        {push_failed}")
    print("=" * 50)

    await close_bot()
    await async_engine.dispose()


def parse_args() -> tuple[bool, bool, int | None]:
    dry_run = "--dry-run" in sys.argv
    no_push = "--no-push" in sys.argv
    limit: int | None = None
    for i, arg in enumerate(sys.argv):
        if arg == "--limit" and i + 1 < len(sys.argv):
            try:
                limit = int(sys.argv[i + 1])
            except ValueError:
                print(f"Invalid --limit value: {sys.argv[i + 1]}")
                sys.exit(2)
    return dry_run, no_push, limit


if __name__ == "__main__":
    dry_run, no_push, limit = parse_args()
    print(f"Mode: dry_run={dry_run}, no_push={no_push}, limit={limit}")
    asyncio.run(main(dry_run, no_push, limit))
