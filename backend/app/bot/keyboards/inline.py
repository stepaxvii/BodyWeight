from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from app.config import settings


def get_webapp_button() -> InlineKeyboardMarkup:
    """Get keyboard with WebApp button only."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть приложение",
                    web_app=WebAppInfo(url=settings.mini_app_url),
                )
            ]
        ]
    )


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Get main menu keyboard with single app button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть приложение",
                    web_app=WebAppInfo(url=settings.mini_app_url),
                )
            ],
        ]
    )
