"""
One-shot announcement to all users about the City (RPG districts) feature.

Idempotent: re-running won't double-send. Each user receives the in-app
notification + Telegram push once. Dedup is keyed by (user_id,
notification_type) so copy edits below don't re-fire to users already notified.

Per-user localized: each recipient gets the push + in-app text in THEIR
language (``users.language``; English fallback), like broadcast_new_boss_push.

Run from the server (inside the API container):

    docker exec bodyweight-api python scripts/announce_city.py --dry-run
    docker exec bodyweight-api python scripts/announce_city.py --limit 1
    docker exec bodyweight-api python scripts/announce_city.py

Flags:
    --dry-run         Don't send anything, just show counts
    --no-push         Skip Telegram push, only save in-app notifications
    --limit N         Send to first N users (staged rollout / testing)

Safe to re-run after a partial failure; already-notified users are skipped.
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

# Dedup identifier. Don't change unless you intentionally re-announce to everyone.
NOTIFICATION_TYPE = "feature_announcement_city"

# Per-language copy. In-app (bell) title/message + Telegram push (HTML).
COPY = {
    "ru": {
        "title": "Город: новая фича",
        "message": (
            "Открылась карта города! Заходи в районы, бери задания у боссов "
            "и проходи их обычными тренировками. Начни со двора — Тренер Лев "
            "ждёт. Открой «Город» в нижнем меню."
        ),
        "push": (
            "🏙 <b>В PixelFit открылся Город!</b>\n\n"
            "Карта районов: заходишь к боссу, берёшь задание (норма на несколько "
            "дней) и проходишь его обычными тренировками — прогресс идёт сам. "
            "Закрыл задание → награда и новый район.\n\n"
            "🦁 Начни со двора — Тренер Лев уже ждёт. Открой Mini App и загляни "
            "во вкладку <b>Город</b>."
        ),
    },
    "en": {
        "title": "The City: new feature",
        "message": (
            "A city map just opened! Step into districts, take quests from their "
            "bosses, and clear them with your normal workouts. Start in the yard "
            "— Coach Leo is waiting. Open 'City' in the bottom menu."
        ),
        "push": (
            "🏙 <b>The City is now open in PixelFit!</b>\n\n"
            "A district map: meet a boss, take a quest (a daily goal for a few "
            "days) and clear it with your normal workouts — progress fills "
            "itself. Clear the quest → reward and a new district.\n\n"
            "🦁 Start in the yard — Coach Leo is waiting. Open the Mini App and "
            "check the <b>City</b> tab."
        ),
    },
}


def _lang(user: User) -> str:
    return "ru" if (getattr(user, "language", None) or "en").lower().startswith("ru") else "en"


async def already_announced(session: AsyncSession, user_id: int) -> bool:
    """True if this user already received the City announcement (any language)."""
    result = await session.execute(
        select(Notification.id)
        .where(Notification.user_id == user_id)
        .where(Notification.notification_type == NOTIFICATION_TYPE)
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

            lang = _lang(user)
            copy = COPY[lang]

            if dry_run:
                saved_in_app += 1
                if not no_push and user.notifications_enabled and user.telegram_id:
                    push_sent += 1  # speculative count
                continue

            # In-app notification (always), in the user's language.
            await save_notification(
                session=session,
                user_id=user.id,
                notification_type=NOTIFICATION_TYPE,
                title=copy["title"],
                message=copy["message"],
            )
            saved_in_app += 1

            # Commit per-user so a mid-run failure doesn't lose progress and
            # re-runs deduplicate cleanly.
            await session.commit()

            # Telegram push (best-effort, localized).
            if not no_push and user.notifications_enabled and user.telegram_id:
                ok = await send_announcement_push(
                    user.telegram_id, copy["push"], notify_admin_on_block=False, lang=lang
                )
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
