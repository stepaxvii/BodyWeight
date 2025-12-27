"""Script to initialize database with data from JSON files."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import async_engine, async_session_maker, Base
from app.services.data_loader import init_data


async def main():
    print("Creating database tables...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")

    print("Loading initial data...")
    async with async_session_maker() as session:
        await init_data(session)
    print("Data loaded successfully!")

    await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
