"""Shared logging setup for both processes (API and bot).

Single place that reads ``settings.log_level`` and quiets chatty third-party
loggers, so the bot no longer hardcodes INFO and both processes agree on
format and level.
"""
import logging

from app.config import settings

_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Third-party loggers that spam INFO/DEBUG we don't care about in prod.
_NOISY_LOGGERS = (
    "aiogram.event",
    "apscheduler.executors.default",
    "apscheduler.scheduler",
    "httpx",
    "httpcore",
)


def setup_logging() -> None:
    """Configure the root logger from settings.log_level (idempotent-ish)."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(level=level, format=_LOG_FORMAT)
    # Keep noisy libraries at WARNING unless we're explicitly debugging.
    if level > logging.DEBUG:
        for name in _NOISY_LOGGERS:
            logging.getLogger(name).setLevel(logging.WARNING)
