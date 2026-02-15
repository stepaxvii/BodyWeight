"""
Уведомление @bobaxvii о переезде: одна функция send_migration_notification_to_bobaxvii()
в app/services/notifications.py. При старте бота (main.py on_startup) она вызывается:
если задан OLD_BOT_TOKEN — создаётся временный Bot(OLD_BOT_TOKEN), bobaxvii получает
сообщение и кнопку на нового бота, сессия закрывается. Рабочий бот всегда BOT_TOKEN (новый).
"""

if __name__ == "__main__":
    print(__doc__.strip())
