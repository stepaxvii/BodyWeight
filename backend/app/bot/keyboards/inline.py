from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from app.config import settings


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu with Mini App button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎮 Открыть приложение",
                    web_app=WebAppInfo(url=settings.MINI_APP_URL),
                )
            ],
            [
                InlineKeyboardButton(text="📊 Моя статистика", callback_data="stats"),
                InlineKeyboardButton(text="🏆 Достижения", callback_data="achievements"),
            ],
            [
                InlineKeyboardButton(text="🔥 Серия", callback_data="streak"),
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
            ],
        ]
    )


def get_workout_keyboard() -> InlineKeyboardMarkup:
    """Quick workout actions."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💪 Начать тренировку",
                    web_app=WebAppInfo(url=f"{settings.MINI_APP_URL}/workout"),
                )
            ],
            [
                InlineKeyboardButton(text="📋 История", callback_data="history"),
            ],
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="menu"),
            ],
        ]
    )


def get_notification_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for notification messages."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎮 Открыть приложение",
                    web_app=WebAppInfo(url=settings.MINI_APP_URL),
                )
            ],
        ]
    )


def get_settings_keyboard(notifications_enabled: bool) -> InlineKeyboardMarkup:
    """Settings keyboard."""
    notif_text = "🔔 Уведомления: ВКЛ" if notifications_enabled else "🔕 Уведомления: ВЫКЛ"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=notif_text, callback_data="toggle_notifications"),
            ],
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="menu"),
            ],
        ]
    )
