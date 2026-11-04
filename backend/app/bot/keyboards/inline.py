from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from app.config import settings
from app.i18n import t


def get_webapp_button(start_param: str | None = None, lang: str | None = None) -> InlineKeyboardMarkup:
    """
    Get keyboard with WebApp button only.

    Args:
        start_param: Optional startapp parameter for deep linking
        lang: UI language for the button label ('ru'|'en')
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
                    text=t(lang, "bot.keyboard.open_app"),
                    web_app=WebAppInfo(url=url),
                )
            ]
        ]
    )


def get_main_keyboard(start_param: str | None = None, lang: str | None = None) -> InlineKeyboardMarkup:
    """
    Get main menu keyboard with single app button.

    Args:
        start_param: Not used anymore, kept for backward compatibility
        lang: UI language for the button label ('ru'|'en')
    """
    # Just open the app without parameters
    # Deep linking doesn't work reliably with Mini Apps
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "bot.keyboard.open_app_emoji"),
                    web_app=WebAppInfo(url=settings.mini_app_url),
                )
            ],
        ]
    )
