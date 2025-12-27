from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Telegram Bot
    bot_token: str = ""

    # Security
    secret_key: str = "change-me-in-production"

    # Database
    database_url: str = "sqlite+aiosqlite:///./bodyweight.db"

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
