#!/usr/bin/env python3
"""Проверить leaderboard_visible в той же БД, что и API/бот.
Запуск: docker compose exec backend python scripts/check_leaderboard_visible.py
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.chdir(Path(__file__).resolve().parent.parent)

from sqlalchemy import select
from app.config import settings
from app.db.database import async_session_maker
from app.db.models import User


def _mask_url(url: str) -> str:
    if "postgresql" in url:
        return "postgresql://... (Postgres)"
    if "sqlite" in url:
        return "sqlite (файл в volume)"
    return url[:50] + "..."


async def main():
    print("БД:", _mask_url(settings.database_url))
    print()
    async with async_session_maker() as session:
        result = await session.execute(
            select(User.id, User.telegram_id, User.username, User.leaderboard_visible, User.total_xp)
        )
        rows = result.all()
    print("id | telegram_id | username | leaderboard_visible | total_xp")
    print("-" * 60)
    for r in rows:
        print(f"{r[0]} | {r[1]} | {r[2] or '-'} | {r[3]} | {r[4]}")


if __name__ == "__main__":
    asyncio.run(main())
