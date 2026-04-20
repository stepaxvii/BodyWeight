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


def get_leaderboard_consent_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура согласия на показ в рейтинге."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да, показывать", callback_data="leaderboard_consent_yes"),
                InlineKeyboardButton(text="Нет, скрыть", callback_data="leaderboard_consent_no"),
            ]
        ]
    )


def get_link_confirmation_keyboard(link_token: str) -> InlineKeyboardMarkup:
    """Keyboard for confirming Telegram account linking."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"link_confirm_{link_token}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"link_reject_{link_token}"),
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
