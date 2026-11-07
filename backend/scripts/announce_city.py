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
    send_announcement_photo,
    close_bot,
)

# Dedup identifier. Don't change unless you intentionally re-announce to everyone.
NOTIFICATION_TYPE = "feature_announcement_city"

# The district render shown with the push — the new 2D Cossacks ("Старая окраина")
# scene, localized (the title banner is burned into the image per language).
# Colocated with this script so it ships in the API container; falls back to a
# text push if the asset is missing.
ASSETS_DIR = Path(__file__).parent / "assets"


def image_for(lang: str) -> Path:
    return ASSETS_DIR / f"city-cossack-{lang}.png"

# Per-language copy. In-app (bell) title/message (plain text) + Telegram push
# (HTML caption on the district photo). Captions are kept < 1024 chars.
COPY = {
    "ru": {
        "title": "Открылся Город 🏙",
        "message": (
            "Открылась карта Города! Районы, боссы и квесты. Заходи к боссу, "
            "бери квест (норма на несколько дней) и проходи его обычными "
            "тренировками — прогресс идёт сам из твоих подходов. Закрыл квест → "
            "титул, XP, монеты и новый район. Начни со двора — Тренер Лев ждёт. "
            "Открой вкладку «Город»."
        ),
        "push": (
            "🏙 <b>В PixelFit открылся ГОРОД</b> — целый мир районов, боссов и "
            "квестов.\n\n"
            "Как это работает:\n"
            "🗺 Город — это карта районов. В каждом свой босс со своим "
            "испытанием.\n"
            "💬 Заходишь к боссу → он даёт <b>квест</b>: норму на несколько дней "
            "(например, «Чистый жим» — 7 дней).\n"
            "🏋️ Проходишь квест <b>обычными тренировками</b> — прогресс "
            "считается сам из твоих подходов.\n"
            "🏆 Закрыл квест → титул, XP, монеты и новый открытый район.\n\n"
            "🦁 Старт — во дворе: Тренер Лев ждёт с тремя основами. Дальше — "
            "Французский квартал и Казаки.\n\n"
            "Открывай Mini App → вкладка <b>Город</b> и в путь!"
        ),
    },
    "en": {
        "title": "The City is open 🏙",
        "message": (
            "A city map just opened! Districts, bosses and quests. Visit a boss, "
            "take a quest (a daily goal for a few days) and clear it with your "
            "normal workouts — progress fills itself from your sets. Finish a "
            "quest → a title, XP, coins and a new district. Start in the yard — "
            "Coach Leo is waiting. Open the 'City' tab."
        ),
        "push": (
            "🏙 <b>The CITY is open in PixelFit</b> — a whole world of districts, "
            "bosses and quests.\n\n"
            "How it works:\n"
            "🗺 The city is a map of districts, each with its own boss "
            "and challenge.\n"
            "💬 Visit a boss → he gives you a <b>quest</b>: a daily goal for a "
            "few days (e.g. 'Clean Press' — 7 days).\n"
            "🏋️ Clear it with your <b>normal workouts</b> — progress fills "
            "itself from your sets.\n"
            "🏆 Finish the quest → a title, XP, coins and a new district "
            "unlocked.\n\n"
            "🦁 Start in the yard: Coach Leo is waiting with three basics. Then "
            "the French Quarter and the Cossacks.\n\n"
            "Open the Mini App → <b>City</b> tab and go!"
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

    # Surface a missing photo asset loudly: the push silently degrades to text, so
    # without this a missing/unshipped image looks like a successful photo run.
    if not no_push:
        missing = [lng for lng in ("ru", "en") if not image_for(lng).exists()]
        if missing:
            print(f"WARNING: announcement image(s) missing for {missing} in {ASSETS_DIR} — those langs get TEXT-ONLY pushes.")

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

            # Telegram push (best-effort, localized). Lead with the district photo
            # (localized render) when present; otherwise fall back to a text push.
            if not no_push and user.notifications_enabled and user.telegram_id:
                img = image_for(lang)
                if img.exists():
                    ok = await send_announcement_photo(
                        user.telegram_id, copy["push"], str(img),
                        notify_admin_on_block=False, lang=lang,
                    )
                else:
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
