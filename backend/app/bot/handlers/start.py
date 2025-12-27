import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from sqlalchemy import select

from app.db.database import async_session_maker
from app.db.models import User
from app.bot.keyboards.inline import get_main_keyboard, get_webapp_button

router = Router()
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
            logger.info(f"Created new user: {telegram_id} ({username})")
        else:
            # Update user info
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            await session.commit()

        return user


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command."""
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

    welcome_text = f"""
<b>BodyWeight</b>

Привет, {user.first_name or 'друг'}!

Тренируйся, зарабатывай опыт, соревнуйся с друзьями.
"""

    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(),
    )


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
<b>BodyWeight - Workout Tracker</b>

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
    await callback.answer("Opening BodyWeight app...")


@router.callback_query(F.data == "view_stats")
async def callback_view_stats(callback: CallbackQuery):
    """Handle view stats callback."""
    if callback.message:
        await cmd_stats(callback.message)
    await callback.answer()
