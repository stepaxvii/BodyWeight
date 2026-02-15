import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from sqlalchemy import select

from app.db.database import async_session_maker
from app.db.models import User
from app.bot.keyboards.inline import get_main_keyboard, get_webapp_button, get_leaderboard_consent_keyboard

router = Router()

LEADERBOARD_CONSENT_TEXT = """📊 <b>Рейтинг</b>

Показывать твой username (или имя) в общем рейтинге и у друзей?

Можно изменить позже в настройках приложения."""
logger = logging.getLogger(__name__)


async def get_or_create_user(telegram_id: int, username: str | None, first_name: str | None, last_name: str | None) -> User:
    """Get or create user in database."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            logger.info(f"Created new user: {telegram_id} ({username})")
        else:
            # Update user info
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            await session.commit()
            await session.refresh(user)

        return user


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command with optional deep link parameter."""
    user = message.from_user
    if not user:
        return

    # Create or update user
    db_user = await get_or_create_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    # Extract deep link parameter from /start command
    # Format: /start addfriend_123
    start_param = None
    if message.text and ' ' in message.text:
        _, param = message.text.split(' ', 1)
        start_param = param.strip()

    # Check if this is a friend invite
    if start_param and start_param.startswith('addfriend_'):
        try:
            friend_id = int(start_param.replace('addfriend_', ''))
            # Get friend's name from database
            async with async_session_maker() as session:
                result = await session.execute(
                    select(User).where(User.id == friend_id)
                )
                friend = result.scalar_one_or_none()

            if friend:
                friend_name = friend.username or friend.first_name or "Пользователь"
                welcome_text = f"""🎮 <b>PixelFit - 8-bit Фитнес Трекер</b>

Привет, {user.first_name or 'друг'}! 👋

<b>{friend_name}</b> приглашает тебя присоединиться к тренировкам!

💪 Большое количество упражнений
🏆 Система достижений и наград
📊 Соревнуйся с друзьями
⚡ Streaks и ежедневные бонусы

Открой приложение и начни тренироваться вместе!
"""
            else:
                welcome_text = f"""🎮 <b>PixelFit - 8-bit Фитнес Трекер</b>

Добро пожаловать, {user.first_name or 'друг'}! 👋

Тренируйся как в игре! Набирай опыт, прокачивай уровень, открывай достижения.

💪 Большое количество упражнений
🏆 Система достижений
📊 Соревнования с друзьями
⚡ Streaks и бонусы

Открой приложение и начни свой фитнес-путь!
"""
        except (ValueError, Exception) as e:
            logger.error(f"Error parsing friend invite: {e}")
            start_param = None
            welcome_text = f"""🎮 <b>PixelFit - 8-bit Фитнес Трекер</b>

Добро пожаловать, {user.first_name or 'друг'}! 👋

Тренируйся как в игре! Набирай опыт, прокачивай уровень, открывай достижения.

💪 Большое количество упражнений
🏆 Система достижений
📊 Соревнования с друзьями
⚡ Streaks и бонусы

Открой приложение и начни свой фитнес-путь!
"""
    else:
        # Returning user or first time without invite
        welcome_text = f"""🎮 <b>PixelFit - 8-bit Фитнес Трекер</b>

С возвращением, {user.first_name or 'друг'}! 👋

Готов продолжить тренировки? Открой приложение!

💪 Большое количество упражнений
🏆 Система достижений
📊 Соревнования с друзьями
⚡ Streaks и бонусы
"""

    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(start_param=start_param),
    )

    # Запрос согласия на показ в рейтинге (если ещё не в рейтинге — показываем каждый /start)
    if not db_user.leaderboard_visible:
        await message.answer(
            LEADERBOARD_CONSENT_TEXT,
            reply_markup=get_leaderboard_consent_keyboard(),
        )


@router.callback_query(F.data == "leaderboard_consent_yes")
async def callback_leaderboard_yes(callback: CallbackQuery):
    """Пользователь согласился на показ в рейтинге."""
    if not callback.from_user:
        await callback.answer()
        return
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.leaderboard_visible = True
            await session.commit()
    await callback.answer("Ок, ты будешь в рейтинге!")
    if callback.message:
        try:
            await callback.message.edit_text(
                LEADERBOARD_CONSENT_TEXT + "\n\n✅ Показывать в рейтинге.",
                reply_markup=None,
            )
        except Exception:
            pass


@router.callback_query(F.data == "leaderboard_consent_no")
async def callback_leaderboard_no(callback: CallbackQuery):
    """Пользователь отказался от показа в рейтинге."""
    if not callback.from_user:
        await callback.answer()
        return
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.leaderboard_visible = False
            await session.commit()
    await callback.answer("Ок, скрыт из рейтинга.")
    if callback.message:
        try:
            await callback.message.edit_text(
                LEADERBOARD_CONSENT_TEXT + "\n\n❌ Не показывать в рейтинге.",
                reply_markup=None,
            )
        except Exception:
            pass


@router.message(Command("workout"))
async def cmd_workout(message: Message):
    """Handle /workout command - open Mini App."""
    await message.answer(
        "Ready to work out? Open the app!",
        reply_markup=get_webapp_button(),
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Handle /stats command - show user statistics."""
    user = message.from_user
    if not user:
        return

    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == user.id)
        )
        db_user = result.scalar_one_or_none()

        if not db_user:
            await message.answer("Please use /start first!")
            return

        from app.services.xp_calculator import xp_for_level

        current_xp = db_user.total_xp
        current_level_xp = xp_for_level(db_user.level)
        next_level_xp = xp_for_level(db_user.level + 1)
        xp_progress = current_xp - current_level_xp
        xp_needed = next_level_xp - current_level_xp
        progress_percent = int((xp_progress / xp_needed) * 100) if xp_needed > 0 else 0

        # Create progress bar
        bar_length = 10
        filled = int(bar_length * progress_percent / 100)
        progress_bar = "█" * filled + "░" * (bar_length - filled)

        stats_text = f"""
<b>Your Stats</b>

<b>Level {db_user.level}</b>
{progress_bar} {progress_percent}%
{xp_progress}/{xp_needed} XP to next level

<b>Total XP:</b> {db_user.total_xp}
<b>Coins:</b> {db_user.coins}

<b>Streaks:</b>
Current: {db_user.current_streak} days
Best: {db_user.max_streak} days

Keep pushing! Open the app to continue your workout.
"""

        await message.answer(
            stats_text,
            reply_markup=get_webapp_button(),
        )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    help_text = """
<b>PixelFit - Workout Tracker</b>

<b>Commands:</b>
/start - Start the bot
/workout - Open workout app
/stats - View your statistics
/help - Show this message

<b>How it works:</b>
1. Open the Mini App
2. Choose exercises from 8 categories
3. Track your reps and sets
4. Earn XP and level up!
5. Maintain your streak for bonus XP
6. Compete with friends on leaderboards

<b>Tips:</b>
• Complete workouts daily to keep your streak
• Try harder variations as you progress
• Check achievements for bonus rewards

Questions? Just message me!
"""

    await message.answer(
        help_text,
        reply_markup=get_main_keyboard(),
    )


@router.callback_query(F.data == "open_app")
async def callback_open_app(callback: CallbackQuery):
    """Handle open app callback."""
    await callback.answer("Opening PixelFit app...")


@router.callback_query(F.data == "view_stats")
async def callback_view_stats(callback: CallbackQuery):
    """Handle view stats callback."""
    if callback.message:
        await cmd_stats(callback.message)
    await callback.answer()
