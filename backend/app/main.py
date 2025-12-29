from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging

from app.config import settings
from app.api import api_router
from app.db.database import async_engine, Base, async_session_maker
from app.services.data_loader import init_data
from app.services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO if settings.debug else logging.WARNING)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting BodyWeight API...")

    # Create tables (for development; use Alembic in production)
    if settings.debug:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")

        # Load initial data (categories, exercises)
        async with async_session_maker() as session:
            await init_data(session)
        logger.info("Initial data loaded")

    # Start notification scheduler
    start_scheduler()

    yield

    # Shutdown
    logger.info("Shutting down BodyWeight API...")
    stop_scheduler()
    await async_engine.dispose()


app = FastAPI(
    title="BodyWeight API",
    description="API for BodyWeight Telegram Mini App",
    version="1.0.0",
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
