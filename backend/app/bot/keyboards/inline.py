from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from app.config import settings


def get_webapp_button() -> InlineKeyboardMarkup:
    """Get keyboard with WebApp button only."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Open BodyWeight",
                    web_app=WebAppInfo(url=settings.mini_app_url),
                )
            ]
        ]
    )


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Get main menu keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Start Workout",
                    web_app=WebAppInfo(url=settings.mini_app_url),
                )
            ],
            [
                InlineKeyboardButton(
                    text="View Stats",
                    callback_data="view_stats",
                ),
                InlineKeyboardButton(
                    text="Help",
                    callback_data="help",
                ),
            ],
        ]
    )
