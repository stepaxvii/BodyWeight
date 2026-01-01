from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import settings
from app.api import api_router
from app.db.database import async_engine, async_session_maker
from app.services.data_loader import init_data
from app.services.scheduler import start_scheduler, stop_scheduler

# Configure logging based on settings
log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting BodyWeight API...")

    # NOTE: Database tables should be created via Alembic migrations
    # Run: alembic upgrade head
    # Do NOT use Base.metadata.create_all() in production!

    # Load initial data (categories, exercises) if needed
    # This should be idempotent and safe to run multiple times
    if settings.debug:
        async with async_session_maker() as session:
            try:
                await init_data(session)
                logger.info("Initial data loaded")
            except Exception as e:
                logger.warning(f"Failed to load initial data: {e}")

    # Start notification scheduler
    start_scheduler()

    yield

    # Shutdown
    logger.info("Shutting down BodyWeight API...")
    stop_scheduler()
    await async_engine.dispose()


app = FastAPI(
    title="BodyWeight Fitness API",
    description="""
    API для Telegram Mini App фитнес-трекера с геймификацией.

    ## Основные возможности:

    * 🏋️ **Тренировки** - создание, отслеживание и завершение тренировок
    * 💪 **Упражнения** - каталог упражнений с фильтрацией и избранным
    * 🏆 **Достижения** - система достижений и наград
    * 📊 **Статистика** - отслеживание прогресса, XP, уровней и монет
    * 👥 **Социальные функции** - друзья, рейтинг, лидерборды
    * 🎯 **Цели** - постановка и отслеживание целей
    * 🛒 **Магазин** - покупка аватаров и предметов за монеты

    ## Аутентификация

    Все запросы требуют заголовок:
    ```
    Authorization: tma <telegram_init_data>
    ```

    Где `telegram_init_data` - данные от Telegram WebApp.
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    openapi_url="/api/openapi.json" if settings.debug else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router
app.include_router(api_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}


# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
