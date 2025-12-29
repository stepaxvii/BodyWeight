from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

# Get absolute path to backend directory
BACKEND_DIR = Path(__file__).parent.parent.resolve()
DEFAULT_DB_PATH = BACKEND_DIR / "bodyweight.db"


class Settings(BaseSettings):
    # Telegram Bot
    bot_token: str = ""
    bot_username: str = ""  # Bot username without @, e.g. "bodyweight_bot"

    # Security
    secret_key: str = "change-me-in-production"

    # Database (use absolute path to ensure bot and API use same DB)
    database_url: str = f"sqlite+aiosqlite:///{DEFAULT_DB_PATH}"

    # Mini App URL
    mini_app_url: str = "https://stepaproject.ru/bodyweight"

    # Debug mode
    debug: bool = False

    # CORS
    cors_origins: list[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
