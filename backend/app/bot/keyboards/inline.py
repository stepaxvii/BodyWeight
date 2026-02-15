from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from app.config import settings


def get_webapp_button(start_param: str | None = None) -> InlineKeyboardMarkup:
    """
    Get keyboard with WebApp button only.

    Args:
        start_param: Optional startapp parameter for deep linking
    """
    url = settings.mini_app_url
    if start_param:
        # Add startapp parameter to URL fragment
        # Format: https://example.com/app#tgWebAppStartParam=addfriend_123
        url = f"{url}#tgWebAppStartParam={start_param}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть приложение",
                    web_app=WebAppInfo(url=url),
                )
            ]
        ]
    )


def get_migration_keyboard(new_bot_link: str) -> InlineKeyboardMarkup:
    """Клавиатура: кнопка перехода на нового бота (режим переезда)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Перейти к новому боту →",
                    url=new_bot_link,
                )
            ]
        ]
    )


def get_main_keyboard(start_param: str | None = None) -> InlineKeyboardMarkup:
    """
    Get main menu keyboard with single app button.

    Args:
        start_param: Not used anymore, kept for backward compatibility
    """
    # Just open the app without parameters
    # Deep linking doesn't work reliably with Mini Apps
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎮 Открыть приложение",
                    web_app=WebAppInfo(url=settings.mini_app_url),
                )
            ],
        ]
    )
