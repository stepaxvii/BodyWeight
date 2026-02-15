#!/usr/bin/env python3
"""
Рассылка уведомления о переезде бота всем пользователям из БД.

Запуск на сервере из каталога backend (чтобы подхватился тот же .env и БД, что у API/бота):
  cd /home/BodyWeight/backend
  export OLD_BOT_TOKEN=...   # или в .env
  export NEW_BOT_LINK=https://t.me/pixelfitbot
  python scripts/send_migration_to_all.py

Скрипт берёт DATABASE_URL из app.config (тот же, что у приложения).
Если в docker БД в volume ./data, на хосте задайте в backend/.env:
  DATABASE_URL=sqlite+aiosqlite:////home/BodyWeight/data/bodyweight.db
"""
import asyncio
import os
import sys
from pathlib import Path

_backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend_dir))
# Рабочая директория = backend, чтобы app.config подхватил .env и пути к БД
os.chdir(_backend_dir)

# Подгрузить .env в os.environ до импорта settings (если скрипт вызван не из backend)
_env_file = _backend_dir / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and os.environ.get(k) is None:
                os.environ[k] = v

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import settings
from app.db.models import User

MESSAGE = """🚀 <b>PixelFit переезжает на нового бота!</b>

Привет! Мы переходим на обновлённого бота — все твои достижения сохранены и будут доступны там.

Нажми кнопку ниже, чтобы перейти к новому боту и нажать <b>Start</b> — после этого всё будет работать как раньше.

До встречи на новой стороне! 💪"""


def get_keyboard(link: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Перейти к новому боту →", url=link)]
        ]
    )


def _resolve_db_url() -> str:
    """Тот же DATABASE_URL, что у приложения; для хоста с docker — fallback на project_root/data/."""
    db_url = settings.database_url
    if "sqlite" not in db_url:
        return db_url
    path_raw = db_url.replace("sqlite+aiosqlite:///", "").strip()
    p = Path(path_raw)
    path_abs = p.resolve() if (p.is_absolute() or path_raw.startswith("/")) else (_backend_dir / path_raw).resolve()
    if path_abs.exists():
        return db_url
    # Дефолт из config = backend/bodyweight.db; на хосте с docker БД часто в project_root/data/
    fallback = _backend_dir.parent / "data" / "bodyweight.db"
    if fallback.exists():
        url = f"sqlite+aiosqlite:///{fallback.resolve().as_posix()}"
        print("БД по умолчанию не найдена, используем volume:", url)
        return url
    return db_url


async def main():
    old_token = (os.environ.get("OLD_BOT_TOKEN") or "").strip()
    new_link = (os.environ.get("NEW_BOT_LINK") or "https://t.me/pixelfitbot").strip()
    db_url = _resolve_db_url()

    if not old_token:
        print("Задайте OLD_BOT_TOKEN (токен старого бота)")
        sys.exit(1)
    if not new_link.startswith("http"):
        new_link = "https://t.me/pixelfitbot"

    engine = create_async_engine(db_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            r = await session.execute(select(User.telegram_id))
            telegram_ids = [row[0] for row in r.all()]
        except Exception as e:
            if "no such table" in str(e).lower() or "users" in str(e):
                print("Ошибка: таблица users не найдена в БД.")
                print("Убедитесь, что DATABASE_URL в backend/.env указывает на ту же БД, что и в docker (volume ./data).")
                print("На хосте обычно: DATABASE_URL=sqlite+aiosqlite:///АБСОЛЮТНЫЙ_ПУТЬ/data/bodyweight.db")
            raise

    await engine.dispose()

    print(f"Пользователей в БД: {len(telegram_ids)}")
    print(f"Ссылка на нового бота: {new_link}")
    print("Отправка...")

    bot = Bot(
        token=old_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    sent, failed = 0, 0
    try:
        for i, tg_id in enumerate(telegram_ids):
            try:
                await bot.send_message(tg_id, MESSAGE, reply_markup=get_keyboard(new_link))
                sent += 1
            except Exception as e:
                failed += 1
                print(f"  [{tg_id}] {e}")
            await asyncio.sleep(0.25)
            if (i + 1) % 20 == 0:
                print(f"  {i + 1}/{len(telegram_ids)}")
    finally:
        await bot.session.close()

    print(f"Готово. Отправлено: {sent}, ошибок: {failed}")


if __name__ == "__main__":
    asyncio.run(main())
