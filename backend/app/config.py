from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

# Get absolute path to backend directory
BACKEND_DIR = Path(__file__).parent.parent.resolve()
DEFAULT_DB_PATH = BACKEND_DIR / "bodyweight.db"


class Settings(BaseSettings):
    # Telegram Bot
    bot_token: str = ""
    bot_username: str = "pixelfitbot"  # Bot username without @
    mini_app_name: str = "pixelfitbot"  # Mini App short name from BotFather

    # Security — HMAC key for signing share-card tokens (see api/routes/share.py)
    secret_key: str = "change-me-in-production"

    # Database (use absolute path to ensure bot and API use same DB)
    database_url: str = f"sqlite+aiosqlite:///{DEFAULT_DB_PATH}"

    # Mini App URL
    mini_app_url: str = "https://stepaproject.ru/bodyweight"

    # Debug mode
    debug: bool = False

    # Admin Telegram ID for the daily stats digest and /digest bot command
    # (env: ADMIN_TELEGRAM_ID; unset = digest disabled)
    admin_telegram_id: int | None = None

    # RPG "City" feature beta gate. True (default) => City is ADMIN-ONLY: only
    # ADMIN_TELEGRAM_ID sees the nav button and can call /api/districts. Flip to
    # False (env CITY_BETA=false) + restart to open it to everyone — no rebuild
    # needed (the frontend reads `city_enabled` from /users/me at runtime).
    city_beta: bool = True

    # Logging
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR

    # CORS
    cors_origins: list[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
