"""Russian server-side catalog (bot, notifications, emails).

Nested dicts; keys are referenced dotted via app.i18n.t, e.g.
    t("ru", "bot.start.greeting", name="Дима")
The string-extraction phase fills these from the hard-coded Russian texts in
app/bot/** and app/services/** (notifications, referral, boss, email).
"""

MESSAGES: dict = {
    "bot": {
        "common": {
            "user_fallback": "Пользователь",
            "friend_fallback": "друг",
        },
        # Slash-command menu descriptions (bot.set_my_commands).
        "commands": {
            "start": "Запустить бота",
            "stats": "Моя статистика",
            "help": "Помощь",
            "digest": "Сводка за день",
            "weekdigest": "Сводка за неделю",
        },
        "start": {
            # Shown to the inviter (direct message) when their invite worked.
            "inviter_joined_dm": (
                "🤝 <b>{invitee_name}</b> присоединился по твоему "
                "приглашению — вы теперь друзья!"
            ),
            # Welcome after a successful friend invite.
            "welcome_invited": (
                "🎮 <b>PixelFit - 8-bit Фитнес Трекер</b>\n\n"
                "Привет, {name}! 👋\n\n"
                "Вы теперь друзья с <b>{friend_name}</b>! 🤝\n"
                "Тренируйтесь вместе и соревнуйтесь!\n\n"
                "💪 Большое количество упражнений\n"
                "🏆 Система достижений и наград\n"
                "📊 Соревнуйся с друзьями\n"
                "⚡ Streaks и ежедневные бонусы\n\n"
                "Открой приложение и начни тренироваться вместе!\n"
            ),
            # Welcome for a first-time user without an invite.
            "welcome_new": (
                "🎮 <b>PixelFit - 8-bit Фитнес Трекер</b>\n\n"
                "Добро пожаловать, {name}! 👋\n\n"
                "Тренируйся как в игре! Набирай опыт, прокачивай уровень, открывай достижения.\n\n"
                "💪 Большое количество упражнений\n"
                "🏆 Система достижений\n"
                "📊 Соревнования с друзьями\n"
                "⚡ Streaks и бонусы\n\n"
                "Открой приложение и начни свой фитнес-путь!\n"
            ),
            # Welcome for a returning user.
            "welcome_returning": (
                "🎮 <b>PixelFit - 8-bit Фитнес Трекер</b>\n\n"
                "С возвращением, {name}! 👋\n\n"
                "Готов продолжить тренировки? Открой приложение!\n\n"
                "💪 Большое количество упражнений\n"
                "🏆 Система достижений\n"
                "📊 Соревнования с друзьями\n"
                "⚡ Streaks и бонусы\n"
            ),
        },
        "workout": {
            "prompt": "Готов к тренировке? Открой приложение!",
        },
        "stats": {
            "need_start": "Сначала используй /start!",
            "body": (
                "\n<b>Твоя статистика</b>\n\n"
                "<b>Уровень {level}</b>\n"
                "{progress_bar} {progress_percent}%\n"
                "{xp_progress}/{xp_needed} XP до следующего уровня\n\n"
                "<b>Всего XP:</b> {total_xp}\n"
                "<b>Монеты:</b> {coins}\n\n"
                "<b>Streaks:</b>\n"
                "Текущий: {current_streak} дн.\n"
                "Лучший: {max_streak} дн.\n\n"
                "Продолжай в том же духе! Открой приложение, чтобы продолжить тренировку.\n"
            ),
        },
        "help": {
            "body": (
                "\n<b>PixelFit - Трекер тренировок</b>\n\n"
                "<b>Команды:</b>\n"
                "/start - Запустить бота\n"
                "/stats - Посмотреть свою статистику\n"
                "/help - Показать это сообщение\n\n"
                "<b>Как это работает:</b>\n"
                "1. Открой Mini App\n"
                "2. Выбери упражнения из каталога\n"
                "3. Отслеживай повторения и подходы\n"
                "4. Зарабатывай XP и повышай уровень!\n"
                "5. Поддерживай streak ради бонусного XP\n"
                "6. Соревнуйся с друзьями в таблицах лидеров\n\n"
                "<b>Советы:</b>\n"
                "• Тренируйся каждый день, чтобы не терять streak\n"
                "• Пробуй более сложные варианты по мере прогресса\n"
                "• Загляни в достижения за бонусными наградами\n\n"
                "Есть вопросы? Просто напиши мне!\n"
            ),
        },
        "callback": {
            "opening_app": "Открываю приложение PixelFit...",
        },
        "keyboard": {
            "open_app": "Открыть приложение",
            "open_app_emoji": "🎮 Открыть приложение",
            "open_challenge": "Открыть челлендж",
        },
        "admin": {
            "digest_failed": "Не удалось собрать сводку, посмотри логи.",
        },
    },
    "notifications": {
        "welcome": {
            "title": "Добро пожаловать!",
            "message": "Рады видеть тебя в BodyWeight! Начни первую тренировку прямо сейчас.",
        },
        "friend_request": {
            "push": (
                "👋 <b>Новая заявка в друзья!</b>\n\n"
                "Пользователь <b>{from_user_name}</b> хочет добавить тебя в друзья."
            ),
            # Saved in-app (badge list).
            "title": "Новая заявка в друзья!",
            "message": "{from_user_name} хочет добавить тебя в друзья.",
        },
        "daily_reminder": {
            "with_streak": (
                "🏋️ <b>Время тренировки!</b>\n\n"
                "🔥 Твой streak: <b>{streak}</b> дней подряд!\n"
                "Не останавливайся — продолжай в том же духе!"
            ),
            "no_streak": (
                "🏋️ <b>Время тренировки!</b>\n\n"
                "Начни свой день с упражнений.\n"
                "Даже 10 минут — это уже прогресс!"
            ),
            # Saved in-app (bell).
            "title": "Время тренировки!",
            "message_with_streak": "Твой streak: {streak} дней подряд! Не останавливайся!",
            "message_no_streak": "Начни свой день с упражнений. Даже 10 минут — это уже прогресс!",
        },
        "inactivity": {
            "push": (
                "😢 <b>Мы скучаем!</b>\n\n"
                "Прошло уже <b>{days_inactive}</b> дня без тренировок.\n"
                "Твои мышцы тоже скучают! Вернись к занятиям — "
                "начни с лёгкой разминки."
            ),
            # Saved in-app (bell).
            "title": "Мы скучаем!",
            "message": "Прошло уже {days_inactive} дней без тренировок. Вернись к занятиям!",
        },
        "friend_accepted": {
            "push": (
                "✅ <b>Заявка принята!</b>\n\n"
                "<b>{friend_name}</b> теперь твой друг.\n"
                "Тренируйтесь вместе и соревнуйтесь!"
            ),
            # Saved in-app (badge list).
            "title": "Заявка принята!",
            "message": "{friend_name} теперь твой друг.",
        },
        "friend_workout": {
            "push": (
                "💪 <b>{friend_name}</b> уже потренировался сегодня!\n\n"
                "А ты? Не отставай от друзей!"
            ),
            # Saved in-app (bell).
            "title": "Друг уже потренировался!",
            "message": "{user_name} уже потренировался сегодня. Не отставай!",
        },
        "new_challenge": {
            "push": (
                "🏆 <b>Новый челлендж!</b>\n\n"
                "<b>{creator_name}</b> создал «{challenge_title}».\n"
                "Впишись, пока открыт приём — потренируйтесь наперегонки!"
            ),
            # Saved in-app (badge list) for friends of the creator.
            "title": "Новый челлендж от друга",
            "message": "{creator_name} создал «{challenge_title}» — впишись, пока открыт приём!",
        },
        "challenge_finished": {
            "title": "Челлендж завершён",
            "message": "«{challenge_title}»: ты выполнил {percent}%. Забери награду!",
        },
        "streak_freeze": {
            "title": "🧊 Заморозка использована",
            "message": (
                "Ты пропустил день, но заморозка спасла серию — "
                "стрик {streak} дней сохранён. Осталось заморозок: {freezes}."
            ),
            "push": (
                "🧊 <b>Заморозка спасла твой стрик!</b>\n\n"
                "Ты пропустил день, но серия в <b>{streak}</b> "
                "дней сохранена.\nОсталось заморозок: <b>{freezes}</b>."
            ),
        },
        "friend_joined": {
            # In-app notification saved when an invited friend joins.
            "title": "Друг присоединился!",
            "message": "{invitee_name} присоединился по твоему приглашению — вы теперь друзья!",
        },
        "level_up": {
            "title": "Новый уровень!",
            "message": "Поздравляем! Ты достиг {level} уровня!",
        },
        "achievement": {
            "default_name": "Достижение",
            "title": "Новое достижение!",
            "message": "Получено: {name}",
        },
        "goal_completed": {
            "title": "Цель достигнута!",
            "message": "Цель выполнена: {target} {goal_type}",
        },
        "admin": {
            "new_user": "🆕 Новая регистрация!\nВсего пользователей: {total_users}",
            "bot_blocked": "🚫 Пользователь заблокировал бота.\nВсего заблокировали: {total_blocked}",
        },
    },
    "referral": {
        "reward": {
            "title": "Награда за приглашение!",
            "message": (
                "Твой друг {invitee_name} провёл первую тренировку! "
                "+{coins} монет"
            ),
            "push": (
                "🤝 <b>Награда за приглашение!</b>\n\n"
                "Твой друг <b>{invitee_name}</b> провёл первую тренировку.\n"
                "Тебе начислено <b>+{coins}</b> монет "
                "({rewards_count}/{rewards_cap} наград)."
            ),
        },
    },
    "boss": {
        "new": {
            # Monthly new-boss broadcast push.
            "push": (
                "{emoji} <b>Новый босс месяца!</b>\n\n"
                "«{name}» появился над городом.\n"
                "Заходи и нанеси первый удар — награды ждут!"
            ),
            # In-app notification.
            "title": "Новый босс месяца!",
            "message": "{emoji} {name} появился. Вступай в битву!",
        },
        "milestone": {
            "title": "Босс на {pct}% HP!",
            "message": "{emoji} {name} ослабевает. Добей его!",
        },
        "defeat": {
            "title": "Босс повержен!",
            "message": "{emoji} {name} побеждён. Забери награду на странице босса.",
        },
    },
    "quest": {
        # RPG-районы и квесты. Контент (quest_title/district_name/reward)
        # передаёт вызывающий код уже локализованным из districts.json; здесь
        # только статическая обёртка + {плейсхолдеры} (байт-в-байт как в en.py).
        "accepted": {
            "title": "Квест принят!",
            "message": (
                "«{quest_title}» — {district_name}. У тебя {days} дн., чтобы его "
                "закрыть. Тренируйся каждый день!"
            ),
            "push": (
                "🗺️ <b>Квест принят!</b>\n\n"
                "«{quest_title}» в районе <b>{district_name}</b>.\n"
                "Выполняй дневную норму каждый день в течение {days} дн."
            ),
        },
        "day_progress": {
            "title": "День квеста закрыт!",
            "message": (
                "«{quest_title}»: день {full_days}/{days} выполнен. Держи серию — "
                "пропустишь день, и квест провален."
            ),
        },
        "completed": {
            "title": "Квест пройден!",
            "message": "«{quest_title}» пройден в районе {district_name}! Награда: {reward}.",
            "push": (
                "🏆 <b>Квест пройден!</b>\n\n"
                "Ты завершил «{quest_title}».\n"
                "Награда: <b>{reward}</b>."
            ),
        },
        "district_unlocked": {
            "title": "Открыт район!",
            "message": "Ты открыл район {district_name}. Тебя ждут новые квесты.",
            "push": (
                "🏙️ <b>Открыт новый район!</b>\n\n"
                "{district_name} доступен. Заходи и бери квест."
            ),
        },
        "failed": {
            "title": "Квест провален",
            "message": (
                "«{quest_title}»: окно в {days} дн. закончилось до того, как ты "
                "закрыл каждый день. Откажись и попробуй снова, когда будешь готов."
            ),
            "push": (
                "❌ <b>Квест провален</b>\n\n"
                "«{quest_title}» истёк. Нужны все {days} дн. — попробуй снова."
            ),
        },
        "invite": {
            # Co-op приглашение (явное согласие): received -> declined/accepted.
            "received": {
                "title": "Приглашение в co-op квест",
                "message": (
                    "{from_user_name} зовёт тебя в «{quest_title}» в районе "
                    "{district_name}. Прими, чтобы тренироваться вместе."
                ),
                "push": (
                    "🤝 <b>Приглашение в co-op квест!</b>\n\n"
                    "<b>{from_user_name}</b> зовёт тебя в «{quest_title}».\n"
                    "Прими, чтобы начать вместе завтра."
                ),
            },
            "accepted": {
                "title": "Напарник присоединился",
                "message": (
                    "{partner_name} принял «{quest_title}». "
                    "Вы начинаете вместе завтра!"
                ),
                "push": (
                    "💪 <b>{partner_name} присоединился к твоему квесту!</b>\n\n"
                    "«{quest_title}» — вы начинаете вместе завтра."
                ),
            },
            "declined": {
                "title": "Приглашение отклонено",
                "message": (
                    "{partner_name} отклонил «{quest_title}». "
                    "Можешь пройти соло или нанять наёмника."
                ),
                "push": (
                    "🙅 <b>{partner_name} отклонил твоё co-op приглашение.</b>\n\n"
                    "«{quest_title}» — проходи соло или найми наёмника."
                ),
            },
        },
        "mercenary": {
            # ValueError-сообщения hire_mercenary (НЕ пуши).
            "funds": "Недостаточно монет: нужно {price}, есть {coins}",
            "already": "Наёмник для этого квеста уже нанят.",
            "not_quest": "Наёмника можно нанять только для квеста.",
        },
    },
    "email": {
        # No transactional email bodies are currently sent by the backend.
        # This namespace is reserved so future email copy has a home.
    },
    "content": {
        # User-facing content/validation generated in API routes & services.
        "routine_copy_suffix": "(копия)",
        "streak_freeze_cap": "Можно держать не больше {max} заморозок",
        "streak_freeze_funds": "Недостаточно монет: нужно {price}, есть {coins}",
    },
    "share": {
        # Telegram share message (prepared inline message + invite button).
        "button_challenge": "Принять вызов 💪",
        "report_name_fallback": "Тренировка в PixelFit",
        "exercises_header": "Упражнения",
        "unit_sec": "сек",
        "unit_reps": "повт.",
        "coins_suffix": "монет",
        "caption": "Потренировался в PixelFit: +{xp} XP! Присоединяйся",
        "report_title": "Отчёт о тренировке",
    },
    "sharecard": {
        # Labels rendered onto the shared workout PNG (services/share_card.py).
        "title": "Тренировка завершена!",
        "reps": "Повторения",
        "time": "Время",
        "time_unit": "мин",
        "streak": "Серия",
        "boss": "Боссу",
        # Day-count plural forms (RU has 3; the helper picks by count).
        "day_one": "день",
        "day_few": "дня",
        "day_many": "дней",
    },
}
