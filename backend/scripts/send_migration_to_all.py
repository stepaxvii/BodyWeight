#!/usr/bin/env python3
"""
Рассылка уведомления о переезде бота всем пользователям из БД.

Запуск на сервере (из корня проекта или из backend):
  export OLD_BOT_TOKEN=токен_старого_бота
  export NEW_BOT_LINK=https://t.me/pixelfitbot
  export DATABASE_URL=sqlite+aiosqlite:///./data/bodyweight.db   # или путь к вашей БД
  python scripts/send_migration_to_all.py

  Либо положите OLD_BOT_TOKEN и NEW_BOT_LINK в .env в backend/ и запустите из backend/.
"""
import asyncio
import os
import sys
from pathlib import Path

# Добавить backend в path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Загрузить .env если есть (без pydantic)
_env = Path(__file__).resolve().parent.parent / ".env"
if _env.exists():
    for line in _env.read_text().splitlines():
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

# Модель User — минимально нужны только telegram_id
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


async def main():
    old_token = (os.environ.get("OLD_BOT_TOKEN") or "").strip()
    new_link = (os.environ.get("NEW_BOT_LINK") or "https://t.me/pixelfitbot").strip()
    db_url = (os.environ.get("DATABASE_URL") or "").strip()
    if not db_url:
        # Путь к БД относительно каталога backend (не от cwd)
        _backend = Path(__file__).resolve().parent.parent
        _db_file = _backend / "data" / "bodyweight.db"
        db_url = f"sqlite+aiosqlite:///{_db_file.resolve().as_posix()}"

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
                print("Убедитесь, что DATABASE_URL указывает на БД приложения (тот же URL, что и у API/бота).")
                print("Если используете SQLite — путь по умолчанию:", Path(db_url.replace("sqlite+aiosqlite:///", "")))
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
