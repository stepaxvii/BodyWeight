"""
Скрипт рассылки уведомления о переезде бота.

Запускается с токеном СТАРОГО бота, читает пользователей из БД и отправляет
каждому сообщение с ссылкой на нового бота.

Использование:
  cd backend
  set MIGRATION_OLD_BOT_TOKEN=123:OLD_BOT_TOKEN
  set NEW_BOT_LINK=https://t.me/pixelfitbot
  python scripts/notify_migration.py

  По умолчанию NEW_BOT_LINK=https://t.me/pixelfitbot.
  Сейчас рассылка только @bobaxvii (для отладки). Для полной рассылки см. FULL_MIGRATION ниже.
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

from app.db.database import async_session_maker, async_engine
from app.db.models import User


# Текст сообщения о переезде
MIGRATION_MESSAGE = """🚀 <b>PixelFit переезжает на нового бота!</b>

Привет! Мы переходим на обновлённого бота — все твои данные (уровень, XP, достижения, друзья) сохранены и будут доступны там.

Нажми кнопку ниже, чтобы перейти к новому боту и нажать <b>Start</b> — после этого всё будет работать как раньше.

До встречи на новой стороне! 💪"""


def get_migration_keyboard(new_bot_link: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Перейти к новому боту →",
                    url=new_bot_link,
                )
            ]
        ]
    )


# Пока рассылаем только этому пользователю (отладка)
ONLY_USERNAME = "bobaxvii"
DEFAULT_NEW_BOT_LINK = "https://t.me/pixelfitbot"
# Полная рассылка всем: set FULL_MIGRATION=1
FULL_MIGRATION = os.environ.get("FULL_MIGRATION", "").strip().lower() in ("1", "true", "yes")


async def main():
    old_token = os.environ.get("MIGRATION_OLD_BOT_TOKEN")
    new_bot_link = (os.environ.get("NEW_BOT_LINK") or DEFAULT_NEW_BOT_LINK).strip()
    if not new_bot_link.startswith("http"):
        new_bot_link = DEFAULT_NEW_BOT_LINK

    if not old_token:
        print("Ошибка: задайте MIGRATION_OLD_BOT_TOKEN (токен СТАРОГО бота)")
        sys.exit(1)

    bot = Bot(
        token=old_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    keyboard = get_migration_keyboard(new_bot_link)

    async with async_session_maker() as session:
        if FULL_MIGRATION:
            result = await session.execute(select(User.telegram_id))
            telegram_ids = [r[0] for r in result.all()]
            print("Режим: полная рассылка всем пользователям.")
        else:
            result = await session.execute(select(User.telegram_id, User.username))
            rows = result.all()
            telegram_ids = [
                tg_id for tg_id, username in rows
                if username and username.lower().strip().lstrip("@") == ONLY_USERNAME.lower()
            ]
            print("Режим: только @" + ONLY_USERNAME + ". Для полной рассылки задайте FULL_MIGRATION=1")

    total = len(telegram_ids)
    if total == 0:
        print("Нет получателей. В режиме отладки нужен пользователь @" + ONLY_USERNAME + " в БД.")
        await async_engine.dispose()
        sys.exit(0)
    print(f"Получателей: {total}")
    print(f"Ссылка на нового бота: {new_bot_link}")
    print("Отправка сообщений...")

    sent = 0
    failed = 0
    for i, tg_id in enumerate(telegram_ids, 1):
        try:
            await bot.send_message(
                tg_id,
                MIGRATION_MESSAGE,
                reply_markup=keyboard,
            )
            sent += 1
            if i % 10 == 0 or i == total:
                print(f"  {i}/{total} отправлено, ok={sent}, fail={failed}")
        except TelegramForbiddenError:
            failed += 1
            print(f"  [{i}] {tg_id}: пользователь заблокировал бота")
        except TelegramRetryAfter as e:
            print(f"  Rate limit, ждём {e.retry_after} сек...")
            await asyncio.sleep(e.retry_after)
            # повторить отправку этому же пользователю
            try:
                await bot.send_message(tg_id, MIGRATION_MESSAGE, reply_markup=keyboard)
                sent += 1
            except Exception:
                failed += 1
        except Exception as e:
            failed += 1
            print(f"  [{i}] {tg_id}: {e}")

        # Ограничение частоты (Telegram ~30 сообщений/сек, делаем с запасом)
        await asyncio.sleep(0.1)

    await bot.session.close()
    await async_engine.dispose()

    print("")
    print(f"Готово. Отправлено: {sent}, ошибок: {failed}, всего: {total}")


if __name__ == "__main__":
    asyncio.run(main())
