"""Script to initialize database with data from JSON files."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import async_engine, async_session_maker
from app.services.data_loader import init_data


async def main():
    """
    Initialize database with initial data.

    NOTE: This script assumes tables are already created via Alembic migrations.
    Run 'alembic upgrade head' before using this script.

    This script only loads initial data (categories, exercises).
    """
    print("Loading initial data...")
    print("NOTE: Make sure database tables are created via: alembic upgrade head")

    async with async_session_maker() as session:
        await init_data(session)
    print("Data loaded successfully!")

    await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
