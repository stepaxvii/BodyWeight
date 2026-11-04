import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from sqlalchemy import and_, func, or_, select

from app.config import settings
from app.db.database import async_session_maker
from app.db.models import Friendship, User, WorkoutSession
from app.i18n import t
from app.bot.keyboards.inline import get_main_keyboard, get_webapp_button
from app.services.notifications import notify_admin_new_user, save_notification

router = Router()

logger = logging.getLogger(__name__)


async def get_or_create_user(telegram_id: int, username: str | None, first_name: str | None, last_name: str | None, language_code: str | None = None) -> User:
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
                # Detect UI language from the Telegram client; English fallback.
                language="ru" if (language_code or "").lower().startswith("ru") else "en",
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            logger.info("Created new user: %s (%s)", telegram_id, username)

            total_users = (
                await session.execute(select(func.count()).select_from(User))
            ).scalar_one()
            notify_admin_new_user(total_users)
        else:
            # Update user info
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            await session.commit()
            await session.refresh(user)

        return user


async def _connect_invited_friend(invitee_id: int, inviter_id: int) -> tuple[User | None, bool]:
    """Auto-create an accepted friendship between the invite clicker and the inviter.

    Returns (inviter, became_friends). inviter is None when the invite link
    points at a non-existent user; became_friends is True only when a new
    friendship was created or a pending one was upgraded to accepted.

    Also attributes the referral (users.invited_by_user_id) — but ONLY when the
    clicker hasn't really started yet: no inviter recorded and zero completed
    workouts. Veterans are never retroactively claimed (see services/referral.py).
    """
    async with async_session_maker() as session:
        me = await session.get(User, invitee_id)
        inviter_result = await session.execute(
            select(User).where(User.id == inviter_id)
        )
        inviter = inviter_result.scalar_one_or_none()
        if not me or not inviter:
            return None, False

        # Existing friendship rows between the two (either direction, any status)
        rows_result = await session.execute(
            select(Friendship).where(
                or_(
                    and_(Friendship.user_id == me.id, Friendship.friend_id == inviter.id),
                    and_(Friendship.user_id == inviter.id, Friendship.friend_id == me.id),
                )
            )
        )
        rows = {(f.user_id, f.friend_id): f for f in rows_result.scalars().all()}
        forward = rows.get((me.id, inviter.id))
        reverse = rows.get((inviter.id, me.id))

        already_friends = (
            forward is not None and forward.status == "accepted"
            and reverse is not None and reverse.status == "accepted"
        )
        became_friends = False
        if not already_friends:
            # Reciprocal accepted rows — same shape as the accept flow in
            # api/routes/friends.py (pending rows are upgraded in place).
            if forward is None:
                session.add(Friendship(user_id=me.id, friend_id=inviter.id, status="accepted"))
            else:
                forward.status = "accepted"
            if reverse is None:
                session.add(Friendship(user_id=inviter.id, friend_id=me.id, status="accepted"))
            else:
                reverse.status = "accepted"
            became_friends = True

        # Referral attribution: only for brand-new users or users with zero
        # completed workouts who have no inviter recorded yet.
        if me.invited_by_user_id is None:
            completed_workouts = (
                await session.execute(
                    select(func.count(WorkoutSession.id))
                    .where(WorkoutSession.user_id == me.id)
                    .where(WorkoutSession.status == "completed")
                )
            ).scalar() or 0
            if completed_workouts == 0:
                me.invited_by_user_id = inviter.id

        if became_friends:
            invitee_name = me.username or me.first_name or t(inviter.language, "bot.common.user_fallback")
            await save_notification(
                session=session,
                user_id=inviter.id,
                notification_type="friend_joined",
                title=t(inviter.language, "notifications.friend_joined.title"),
                message=t(inviter.language, "notifications.friend_joined.message", invitee_name=invitee_name),
                related_user_id=me.id,
            )

        await session.commit()
        await session.refresh(inviter)
        return inviter, became_friends


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
        language_code=user.language_code,
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
        friend = None
        became_friends = False
        try:
            friend_id = int(start_param.replace('addfriend_', ''))
            # Guard against self-invite: a user clicking their own link
            if friend_id != db_user.id:
                friend, became_friends = await _connect_invited_friend(
                    invitee_id=db_user.id,
                    inviter_id=friend_id,
                )
        except Exception:
            logger.exception("Error processing friend invite for %s", db_user.id)
            start_param = None

        if friend:
            friend_name = friend.username or friend.first_name or t(db_user.language, "bot.common.user_fallback")

            # Tell the inviter their invite worked (best-effort direct message)
            if became_friends and friend.telegram_id and message.bot:
                invitee_name = db_user.username or db_user.first_name or t(friend.language, "bot.common.user_fallback")
                try:
                    await message.bot.send_message(
                        chat_id=friend.telegram_id,
                        text=t(friend.language, "bot.start.inviter_joined_dm", invitee_name=invitee_name),
                    )
                except Exception:
                    logger.exception("Failed to notify inviter %s about joined friend", friend.id)

            welcome_text = t(
                db_user.language,
                "bot.start.welcome_invited",
                name=user.first_name or t(db_user.language, "bot.common.friend_fallback"),
                friend_name=friend_name,
            )
        else:
            welcome_text = t(
                db_user.language,
                "bot.start.welcome_new",
                name=user.first_name or t(db_user.language, "bot.common.friend_fallback"),
            )
    else:
        # Returning user or first time without invite
        welcome_text = t(
            db_user.language,
            "bot.start.welcome_returning",
            name=user.first_name or t(db_user.language, "bot.common.friend_fallback"),
        )

    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(start_param=start_param, lang=db_user.language),
    )


@router.message(Command("workout"))
async def cmd_workout(message: Message):
    """Handle /workout command - open Mini App."""
    user = message.from_user
    lang = None
    if user:
        async with async_session_maker() as session:
            db_user = (
                await session.execute(select(User).where(User.telegram_id == user.id))
            ).scalar_one_or_none()
            lang = db_user.language if db_user else None
    await message.answer(
        t(lang, "bot.workout.prompt"),
        reply_markup=get_webapp_button(lang=lang),
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
            await message.answer(t(None, "bot.stats.need_start"))
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

        stats_text = t(
            db_user.language,
            "bot.stats.body",
            level=db_user.level,
            progress_bar=progress_bar,
            progress_percent=progress_percent,
            xp_progress=xp_progress,
            xp_needed=xp_needed,
            total_xp=db_user.total_xp,
            coins=db_user.coins,
            current_streak=db_user.current_streak,
            max_streak=db_user.max_streak,
        )

        await message.answer(
            stats_text,
            reply_markup=get_webapp_button(lang=db_user.language),
        )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    user = message.from_user
    lang = None
    if user:
        async with async_session_maker() as session:
            db_user = (
                await session.execute(select(User).where(User.telegram_id == user.id))
            ).scalar_one_or_none()
            lang = db_user.language if db_user else None

    await message.answer(
        t(lang, "bot.help.body"),
        reply_markup=get_main_keyboard(lang=lang),
    )


@router.callback_query(F.data == "open_app")
async def callback_open_app(callback: CallbackQuery):
    """Handle open app callback."""
    lang = None
    if callback.from_user:
        async with async_session_maker() as session:
            db_user = (
                await session.execute(
                    select(User).where(User.telegram_id == callback.from_user.id)
                )
            ).scalar_one_or_none()
            lang = db_user.language if db_user else None
    await callback.answer(t(lang, "bot.callback.opening_app"))


@router.callback_query(F.data == "view_stats")
async def callback_view_stats(callback: CallbackQuery):
    """Handle view stats callback."""
    if callback.message:
        await cmd_stats(callback.message)
    await callback.answer()
