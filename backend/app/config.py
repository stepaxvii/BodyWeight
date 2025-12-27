from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Telegram Bot
    bot_token: str

    # Database
    database_url: str = "sqlite+aiosqlite:///./bodyweight.db"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8002
    debug: bool = False

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Mini App
    mini_app_url: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
