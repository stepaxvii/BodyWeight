from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from sqlalchemy import select

from app.db.database import async_session_maker
from app.db.models import User, Workout, UserAchievement
from app.bot.keyboards.inline import (
    get_main_menu_keyboard,
    get_workout_keyboard,
    get_settings_keyboard,
)

router = Router()


async def get_or_create_user(
    telegram_id: int,
    username: str = None,
    first_name: str = None,
) -> tuple[User, bool]:
    """Get existing user or create new one."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if user:
            user.username = username
            user.first_name = first_name
            await session.commit()
            return user, False

        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user, True


def get_level_progress(experience: int, level: int) -> int:
    """Calculate progress to next level in percent."""
    current_threshold = 100 * (level ** 2)
    next_threshold = 100 * ((level + 1) ** 2)
    progress_in_level = experience - current_threshold
    level_range = next_threshold - current_threshold
    return int((progress_in_level / level_range) * 100) if level_range > 0 else 0


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command."""
    tg_user = message.from_user

    user, is_new = await get_or_create_user(
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
    )

    if is_new:
        text = (
            "🎮 Добро пожаловать в BodyWeight!\n\n"
            "⚔️ Ты - воин, который решил стать сильнее!\n\n"
            "💪 Тренируйся каждый день, зарабатывай опыт, "
            "открывай достижения и соревнуйся с друзьями!\n\n"
            "🏆 Твой уровень: 1\n"
            "⭐ Опыт: 0 XP"
        )
    else:
        name = user.first_name or user.username or "воин"
        progress = get_level_progress(user.experience, user.level)
        text = (
            f"⚔️ С возвращением, {name}!\n\n"
            f"🏆 Уровень: {user.level}\n"
            f"⭐ Опыт: {user.experience} XP\n"
            f"📊 Прогресс: {progress}%\n"
            f"🔥 Серия: {user.streak_days} дней\n"
            f"💪 Всего тренировок: {user.total_workouts}"
        )

    await message.answer(text, reply_markup=get_main_menu_keyboard())


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Show user stats."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await message.answer("❌ Сначала используй /start")
            return

        progress = get_level_progress(user.experience, user.level)

        text = (
            "📊 Твоя статистика:\n\n"
            f"🏆 Уровень: {user.level}\n"
            f"⭐ Опыт: {user.experience} XP\n"
            f"📈 До следующего уровня: {progress}%\n\n"
            f"🔥 Текущая серия: {user.streak_days} дней\n"
            f"💪 Всего тренировок: {user.total_workouts}\n"
            f"🔢 Всего повторений: {user.total_reps}"
        )

        await message.answer(text, reply_markup=get_main_menu_keyboard())


@router.callback_query(F.data == "menu")
async def handle_menu(callback: CallbackQuery):
    """Show main menu."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await callback.answer("Ошибка")
            return

        name = user.first_name or user.username or "воин"
        progress = get_level_progress(user.experience, user.level)

        text = (
            f"⚔️ {name}\n\n"
            f"🏆 Уровень: {user.level}\n"
            f"⭐ Опыт: {user.experience} XP ({progress}%)\n"
            f"🔥 Серия: {user.streak_days} дней\n"
            f"💪 Тренировок: {user.total_workouts}"
        )

    await callback.message.edit_text(text, reply_markup=get_main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "stats")
async def handle_stats(callback: CallbackQuery):
    """Show stats."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await callback.answer("Ошибка")
            return

        progress = get_level_progress(user.experience, user.level)

        text = (
            "📊 Твоя статистика:\n\n"
            f"🏆 Уровень: {user.level}\n"
            f"⭐ Опыт: {user.experience} XP\n"
            f"📈 До следующего уровня: {progress}%\n\n"
            f"🔥 Текущая серия: {user.streak_days} дней\n"
            f"💪 Всего тренировок: {user.total_workouts}\n"
            f"🔢 Всего повторений: {user.total_reps}"
        )

    await callback.message.edit_text(text, reply_markup=get_workout_keyboard())
    await callback.answer()


@router.callback_query(F.data == "streak")
async def handle_streak(callback: CallbackQuery):
    """Show streak info."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await callback.answer("Ошибка")
            return

        # Check if trained today
        today = datetime.utcnow().date()
        workout_result = await session.execute(
            select(Workout)
            .where(Workout.user_id == user.id)
            .where(Workout.completed_at >= datetime.combine(today, datetime.min.time()))
        )
        trained_today = workout_result.scalar_one_or_none() is not None

        if trained_today:
            status = "✅ Сегодня тренировка выполнена!"
        else:
            status = "⏰ Сегодня ещё не тренировался!"

        streak_emoji = "🔥" if user.streak_days > 0 else "❄️"

        text = (
            f"{streak_emoji} Твоя серия: {user.streak_days} дней\n\n"
            f"{status}\n\n"
            "💡 Тренируйся каждый день, чтобы не потерять серию!"
        )

    await callback.message.edit_text(text, reply_markup=get_main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "achievements")
async def handle_achievements(callback: CallbackQuery):
    """Show achievements summary."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await callback.answer("Ошибка")
            return

        # Count unlocked achievements
        unlocked_result = await session.execute(
            select(UserAchievement).where(UserAchievement.user_id == user.id)
        )
        unlocked = len(unlocked_result.scalars().all())

        text = (
            "🏆 Достижения\n\n"
            f"🔓 Открыто: {unlocked}\n\n"
            "Открой приложение, чтобы увидеть все достижения!"
        )

    await callback.message.edit_text(text, reply_markup=get_main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "history")
async def handle_history(callback: CallbackQuery):
    """Show recent workouts."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await callback.answer("Ошибка")
            return

        # Get last 5 workouts
        workouts_result = await session.execute(
            select(Workout)
            .where(Workout.user_id == user.id)
            .order_by(Workout.completed_at.desc())
            .limit(5)
        )
        workouts = workouts_result.scalars().all()

        if not workouts:
            text = "📋 История тренировок\n\nУ тебя пока нет тренировок."
        else:
            text = "📋 Последние тренировки:\n\n"
            for w in workouts:
                date = w.completed_at.strftime("%d.%m.%Y")
                text += f"• {date} — +{w.total_exp} XP\n"

    await callback.message.edit_text(text, reply_markup=get_workout_keyboard())
    await callback.answer()


@router.callback_query(F.data == "settings")
async def handle_settings(callback: CallbackQuery):
    """Show settings."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await callback.answer("Ошибка")
            return

        text = "⚙️ Настройки"

    await callback.message.edit_text(
        text,
        reply_markup=get_settings_keyboard(user.notifications_enabled)
    )
    await callback.answer()


@router.callback_query(F.data == "toggle_notifications")
async def handle_toggle_notifications(callback: CallbackQuery):
    """Toggle notifications."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await callback.answer("Ошибка")
            return

        user.notifications_enabled = not user.notifications_enabled
        await session.commit()

        status = "включены" if user.notifications_enabled else "выключены"
        await callback.answer(f"🔔 Уведомления {status}")

    await callback.message.edit_reply_markup(
        reply_markup=get_settings_keyboard(user.notifications_enabled)
    )
