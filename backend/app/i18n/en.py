"""English server-side catalog (bot, notifications, emails).

Mirror of ru.py with the same key structure. English is the fallback language,
so every key used anywhere MUST exist here.
"""

MESSAGES: dict = {
    "bot": {
        "common": {
            "user_fallback": "User",
            "friend_fallback": "friend",
        },
        "start": {
            "inviter_joined_dm": (
                "🤝 <b>{invitee_name}</b> joined through your "
                "invite — you're friends now!"
            ),
            "welcome_invited": (
                "🎮 <b>PixelFit - 8-bit Fitness Tracker</b>\n\n"
                "Hi, {name}! 👋\n\n"
                "You're now friends with <b>{friend_name}</b>! 🤝\n"
                "Train together and compete!\n\n"
                "💪 Tons of exercises\n"
                "🏆 Achievements and rewards\n"
                "📊 Compete with friends\n"
                "⚡ Streaks and daily bonuses\n\n"
                "Open the app and start training together!\n"
            ),
            "welcome_new": (
                "🎮 <b>PixelFit - 8-bit Fitness Tracker</b>\n\n"
                "Welcome, {name}! 👋\n\n"
                "Train like it's a game! Earn XP, level up, unlock achievements.\n\n"
                "💪 Tons of exercises\n"
                "🏆 Achievement system\n"
                "📊 Compete with friends\n"
                "⚡ Streaks and bonuses\n\n"
                "Open the app and start your fitness journey!\n"
            ),
            "welcome_returning": (
                "🎮 <b>PixelFit - 8-bit Fitness Tracker</b>\n\n"
                "Welcome back, {name}! 👋\n\n"
                "Ready to keep training? Open the app!\n\n"
                "💪 Tons of exercises\n"
                "🏆 Achievement system\n"
                "📊 Compete with friends\n"
                "⚡ Streaks and bonuses\n"
            ),
        },
        "workout": {
            "prompt": "Ready to work out? Open the app!",
        },
        "stats": {
            "need_start": "Please use /start first!",
            "body": (
                "\n<b>Your Stats</b>\n\n"
                "<b>Level {level}</b>\n"
                "{progress_bar} {progress_percent}%\n"
                "{xp_progress}/{xp_needed} XP to next level\n\n"
                "<b>Total XP:</b> {total_xp}\n"
                "<b>Coins:</b> {coins}\n\n"
                "<b>Streaks:</b>\n"
                "Current: {current_streak} days\n"
                "Best: {max_streak} days\n\n"
                "Keep pushing! Open the app to continue your workout.\n"
            ),
        },
        "help": {
            "body": (
                "\n<b>PixelFit - Workout Tracker</b>\n\n"
                "<b>Commands:</b>\n"
                "/start - Start the bot\n"
                "/workout - Open workout app\n"
                "/stats - View your statistics\n"
                "/help - Show this message\n\n"
                "<b>How it works:</b>\n"
                "1. Open the Mini App\n"
                "2. Choose exercises from 8 categories\n"
                "3. Track your reps and sets\n"
                "4. Earn XP and level up!\n"
                "5. Maintain your streak for bonus XP\n"
                "6. Compete with friends on leaderboards\n\n"
                "<b>Tips:</b>\n"
                "• Complete workouts daily to keep your streak\n"
                "• Try harder variations as you progress\n"
                "• Check achievements for bonus rewards\n\n"
                "Questions? Just message me!\n"
            ),
        },
        "callback": {
            "opening_app": "Opening PixelFit app...",
        },
        "keyboard": {
            "open_app": "Open the app",
            "open_app_emoji": "🎮 Open the app",
            "open_challenge": "Open challenge",
        },
        "admin": {
            "digest_failed": "Couldn't build the digest, check the logs.",
        },
    },
    "notifications": {
        "welcome": {
            "title": "Welcome!",
            "message": "Glad to have you in BodyWeight! Start your first workout right now.",
        },
        "friend_request": {
            "push": (
                "👋 <b>New friend request!</b>\n\n"
                "<b>{from_user_name}</b> wants to add you as a friend."
            ),
            # Saved in-app (badge list).
            "title": "New friend request!",
            "message": "{from_user_name} wants to add you as a friend.",
        },
        "daily_reminder": {
            "with_streak": (
                "🏋️ <b>Workout time!</b>\n\n"
                "🔥 Your streak: <b>{streak}</b> days in a row!\n"
                "Don't stop now — keep it going!"
            ),
            "no_streak": (
                "🏋️ <b>Workout time!</b>\n\n"
                "Start your day with some exercise.\n"
                "Even 10 minutes is progress!"
            ),
            # Saved in-app (bell).
            "title": "Workout time!",
            "message_with_streak": "Your streak: {streak} days in a row! Keep it going!",
            "message_no_streak": "Start your day with some exercise. Even 10 minutes is progress!",
        },
        "inactivity": {
            "push": (
                "😢 <b>We miss you!</b>\n\n"
                "It's already been <b>{days_inactive}</b> days without a workout.\n"
                "Your muscles miss it too! Come back and "
                "start with a light warm-up."
            ),
            # Saved in-app (bell).
            "title": "We miss you!",
            "message": "It's been {days_inactive} days without a workout. Come back and train!",
        },
        "friend_accepted": {
            "push": (
                "✅ <b>Request accepted!</b>\n\n"
                "<b>{friend_name}</b> is now your friend.\n"
                "Train together and compete!"
            ),
            # Saved in-app (badge list).
            "title": "Request accepted!",
            "message": "{friend_name} is now your friend.",
        },
        "friend_workout": {
            "push": (
                "💪 <b>{friend_name}</b> already worked out today!\n\n"
                "How about you? Keep up with your friends!"
            ),
            # Saved in-app (bell).
            "title": "A friend already worked out!",
            "message": "{user_name} already worked out today. Don't fall behind!",
        },
        "new_challenge": {
            "push": (
                "🏆 <b>New challenge!</b>\n\n"
                "<b>{creator_name}</b> created “{challenge_title}”.\n"
                "Join while sign-ups are open — race each other!"
            ),
            # Saved in-app (badge list) for friends of the creator.
            "title": "New challenge from a friend",
            "message": "{creator_name} created “{challenge_title}” — join while sign-ups are open!",
        },
        "challenge_finished": {
            "title": "Challenge finished",
            "message": "“{challenge_title}”: you completed {percent}%. Claim your reward!",
        },
        "streak_freeze": {
            "title": "🧊 Streak freeze used",
            "message": (
                "You missed a day, but a freeze saved your streak — "
                "{streak}-day streak kept. Freezes left: {freezes}."
            ),
            "push": (
                "🧊 <b>A freeze saved your streak!</b>\n\n"
                "You missed a day, but your <b>{streak}</b>-day "
                "streak is safe.\nFreezes left: <b>{freezes}</b>."
            ),
        },
        "friend_joined": {
            "title": "A friend joined!",
            "message": "{invitee_name} joined through your invite — you're friends now!",
        },
        "level_up": {
            "title": "New level!",
            "message": "Congrats! You reached level {level}!",
        },
        "achievement": {
            "default_name": "Achievement",
            "title": "New achievement!",
            "message": "Unlocked: {name}",
        },
        "goal_completed": {
            "title": "Goal reached!",
            "message": "Goal completed: {target} {goal_type}",
        },
        "admin": {
            "new_user": "🆕 New registration!\nTotal users: {total_users}",
            "bot_blocked": "🚫 A user blocked the bot.\nTotal blocked: {total_blocked}",
        },
    },
    "referral": {
        "reward": {
            "title": "Invite reward!",
            "message": (
                "Your friend {invitee_name} completed their first workout! "
                "+{coins} coins"
            ),
            "push": (
                "🤝 <b>Invite reward!</b>\n\n"
                "Your friend <b>{invitee_name}</b> completed their first workout.\n"
                "You've been credited <b>+{coins}</b> coins "
                "({rewards_count}/{rewards_cap} rewards)."
            ),
        },
    },
    "boss": {
        "new": {
            "push": (
                "{emoji} <b>New boss of the month!</b>\n\n"
                "“{name}” has risen over the city.\n"
                "Jump in and land the first hit — rewards await!"
            ),
            "title": "New boss of the month!",
            "message": "{emoji} {name} has appeared. Join the battle!",
        },
        "milestone": {
            "title": "Boss at {pct}% HP!",
            "message": "{emoji} {name} is weakening. Finish it off!",
        },
        "defeat": {
            "title": "Boss defeated!",
            "message": "{emoji} {name} has been defeated. Claim your reward on the boss page.",
        },
    },
    "email": {
        # No transactional email bodies are currently sent by the backend.
    },
    "content": {
        # User-facing content/validation generated in API routes & services.
        "routine_copy_suffix": "(copy)",
        "streak_freeze_cap": "You can hold at most {max} freezes",
        "streak_freeze_funds": "Not enough coins: need {price}, have {coins}",
    },
    "share": {
        # Telegram share message (prepared inline message + invite button).
        "button_challenge": "Take the challenge 💪",
        "report_name_fallback": "PixelFit workout",
        "exercises_header": "Exercises",
        "unit_sec": "sec",
        "unit_reps": "reps",
        "coins_suffix": "coins",
        "caption": "Worked out in PixelFit: +{xp} XP! Join me",
        "report_title": "Workout report",
    },
    "sharecard": {
        # Labels rendered onto the shared workout PNG (services/share_card.py).
        "title": "Workout complete!",
        "reps": "Reps",
        "time": "Time",
        "time_unit": "min",
        "streak": "Streak",
        "boss": "Boss",
        # English has 2 plural forms; day_few mirrors day_many to keep keys symmetric.
        "day_one": "day",
        "day_few": "days",
        "day_many": "days",
    },
}
