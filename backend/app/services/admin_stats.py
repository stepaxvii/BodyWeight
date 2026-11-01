"""
Admin daily stats digest.

Collects aggregate product stats for a single UTC day and formats them as a
compact Russian HTML message (aiogram HTML parse mode). Used by the daily
scheduler job (05:00 UTC) and the admin-only /digest bot command.
"""
import html
import logging
from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    ChallengeParticipant,
    Exercise,
    MonthlyBoss,
    Notification,
    User,
    WorkoutExercise,
    WorkoutSession,
)
logger = logging.getLogger(__name__)


async def collect_daily_stats(session: AsyncSession, day: date) -> dict:
    """
    Collect aggregate stats for the given UTC day ([day 00:00, day+1 00:00)).

    Returns a plain dict consumed by format_digest().
    """
    day_start = datetime.combine(day, time.min)
    day_end = day_start + timedelta(days=1)

    # New + total users
    new_users = (
        await session.execute(
            select(func.count())
            .select_from(User)
            .where(User.created_at >= day_start)
            .where(User.created_at < day_end)
        )
    ).scalar_one()
    total_users = (
        await session.execute(select(func.count()).select_from(User))
    ).scalar_one()
    # Audience health: how many blocked the bot, and how many are still
    # reachable for a promo push (have a telegram_id and haven't blocked).
    blocked_users = (
        await session.execute(
            select(func.count())
            .select_from(User)
            .where(User.bot_blocked.is_(True))
        )
    ).scalar_one()
    reachable_users = (
        await session.execute(
            select(func.count())
            .select_from(User)
            .where(User.telegram_id.isnot(None))
            .where(User.bot_blocked.is_(False))
            .where(User.bot_reachable.is_(True))
        )
    ).scalar_one()
    # Have a telegram_id but never started THIS bot (e.g. after a bot
    # migration): can't be pushed until they (re)start.
    not_started_users = (
        await session.execute(
            select(func.count())
            .select_from(User)
            .where(User.telegram_id.isnot(None))
            .where(User.bot_blocked.is_(False))
            .where(User.bot_reachable.is_(False))
        )
    ).scalar_one()

    # Completed sessions that day: active users, workouts, XP
    day_sessions = (
        WorkoutSession.status == "completed",
        WorkoutSession.finished_at >= day_start,
        WorkoutSession.finished_at < day_end,
    )
    active_users, workouts, total_xp = (
        await session.execute(
            select(
                func.count(func.distinct(WorkoutSession.user_id)),
                func.count(WorkoutSession.id),
                func.coalesce(func.sum(WorkoutSession.total_xp_earned), 0),
            ).where(*day_sessions)
        )
    ).one()

    # Sets + reps over the day's completed sessions
    total_sets, total_reps = (
        await session.execute(
            select(
                func.coalesce(func.sum(WorkoutExercise.sets_completed), 0),
                func.coalesce(func.sum(WorkoutExercise.total_reps), 0),
            )
            .join(WorkoutSession, WorkoutExercise.workout_session_id == WorkoutSession.id)
            .where(*day_sessions)
        )
    ).one()

    # Top 5 exercises by number of workout_exercises rows that day
    top_exercises = (
        await session.execute(
            select(Exercise.name_ru, func.count(WorkoutExercise.id).label("cnt"))
            .join(WorkoutExercise, WorkoutExercise.exercise_id == Exercise.id)
            .join(WorkoutSession, WorkoutExercise.workout_session_id == WorkoutSession.id)
            .where(*day_sessions)
            .group_by(Exercise.name_ru)
            .order_by(func.count(WorkoutExercise.id).desc())
            .limit(5)
        )
    ).all()

    # Challenge joins that day
    challenge_joins = (
        await session.execute(
            select(func.count())
            .select_from(ChallengeParticipant)
            .where(ChallengeParticipant.joined_at >= day_start)
            .where(ChallengeParticipant.joined_at < day_end)
        )
    ).scalar_one()

    # Streak freezes burned: streak.py writes a "streak_freeze_used"
    # notification for every spent freeze — count those.
    streak_freezes_used = (
        await session.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.notification_type == "streak_freeze_used")
            .where(Notification.created_at >= day_start)
            .where(Notification.created_at < day_end)
        )
    ).scalar_one()

    # Referral rewards granted: referral.py writes a "referral_reward"
    # notification for every rewarded invite — count those.
    referral_rewards = (
        await session.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.notification_type == "referral_reward")
            .where(Notification.created_at >= day_start)
            .where(Notification.created_at < day_end)
        )
    ).scalar_one()

    # Boss covering that day + approximate damage dealt. Damage is 1:1 with
    # workout XP (services/boss.py); still an APPROXIMATION — real damage is
    # trimmed by remaining boss HP at the moment of each workout.
    boss = (
        await session.execute(
            select(MonthlyBoss)
            .where(MonthlyBoss.start_date <= day)
            .where(MonthlyBoss.end_date >= day)
        )
    ).scalar_one_or_none()
    boss_stats = None
    if boss is not None:
        boss_damage = (
            await session.execute(
                select(
                    func.coalesce(func.sum(WorkoutSession.total_xp_earned), 0)
                ).where(*day_sessions)
            )
        ).scalar_one()
        boss_stats = {
            "name_ru": boss.name_ru,
            "current_hp": boss.current_hp,
            "max_hp": boss.max_hp,
            "damage": boss_damage,
        }

    return {
        "new_users": new_users,
        "total_users": total_users,
        "blocked_users": blocked_users,
        "reachable_users": reachable_users,
        "not_started_users": not_started_users,
        "active_users": active_users,
        "workouts": workouts,
        "total_xp": total_xp,
        "total_sets": total_sets,
        "total_reps": total_reps,
        "top_exercises": [(name_ru, cnt) for name_ru, cnt in top_exercises],
        "challenge_joins": challenge_joins,
        "streak_freezes_used": streak_freezes_used,
        "referral_rewards": referral_rewards,
        "boss": boss_stats,
    }


def _fmt(n: int) -> str:
    """Format a number with regular spaces as thousands separators (14 350)."""
    return f"{n:,}".replace(",", " ")


def _plural(n: int, one: str, few: str, many: str) -> str:
    """Russian plural form: 1 тренировка, 2 тренировки, 5 тренировок."""
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def format_digest(stats: dict, day: date) -> str:
    """Build the compact Russian HTML digest message. Zero/absent lines are omitted."""
    lines = [f"📊 <b>PixelFit — сводка за {day.strftime('%d.%m')}</b>"]

    if stats["new_users"]:
        lines.append(
            f"👤 Новых: {_fmt(stats['new_users'])} (всего {_fmt(stats['total_users'])})"
        )

    # Audience for promo — always shown; reachable = has telegram_id, hasn't
    # blocked the bot, and has an open chat (started this bot).
    audience = f"📣 Для промо: {_fmt(stats['reachable_users'])}"
    if stats["not_started_users"]:
        audience += f" · 📵 не открыли бота: {_fmt(stats['not_started_users'])}"
    if stats["blocked_users"]:
        audience += f" · 🚫 заблокировали: {_fmt(stats['blocked_users'])}"
    lines.append(audience)

    if stats["workouts"]:
        workouts_word = _plural(stats["workouts"], "тренировка", "тренировки", "тренировок")
        lines.append(
            f"🏃 Тренировались: {_fmt(stats['active_users'])} чел · "
            f"{_fmt(stats['workouts'])} {workouts_word}"
        )

    if stats["total_xp"] or stats["total_sets"] or stats["total_reps"]:
        lines.append(
            f"⚡ XP: {_fmt(stats['total_xp'])} · подходы: {_fmt(stats['total_sets'])} · "
            f"повторения: {_fmt(stats['total_reps'])}"
        )

    if stats["top_exercises"]:
        top = " · ".join(
            f"{html.escape(name)} ({_fmt(cnt)})" for name, cnt in stats["top_exercises"]
        )
        lines.append(f"🏆 Топ: {top}")

    boss = stats["boss"]
    if boss is not None:
        hp = f"HP {_fmt(boss['current_hp'])} / {_fmt(boss['max_hp'])}"
        if boss["damage"]:
            lines.append(
                f"👹 Босс «{html.escape(boss['name_ru'])}»: "
                f"~{_fmt(boss['damage'])} урона · {hp}"
            )
        else:
            lines.append(f"👹 Босс «{html.escape(boss['name_ru'])}»: {hp}")

    extras = []
    if stats["challenge_joins"]:
        extras.append(f"🎯 Челленджи: +{_fmt(stats['challenge_joins'])}")
    if stats["streak_freezes_used"]:
        extras.append(f"🧊 Заморозок: {_fmt(stats['streak_freezes_used'])}")
    if stats["referral_rewards"]:
        n = stats["referral_rewards"]
        extras.append(f"🤝 Рефералка: {_fmt(n)} {_plural(n, 'награда', 'награды', 'наград')}")
    if extras:
        lines.append(" · ".join(extras))

    # The audience line is always present, so judge "silence" by activity only.
    had_activity = any((
        stats["new_users"], stats["workouts"], stats["total_xp"],
        stats["challenge_joins"], stats["streak_freezes_used"],
        stats["referral_rewards"],
        stats["boss"] is not None and stats["boss"]["damage"],
    ))
    if not had_activity:
        lines.append("Тишина — за день активности не было.")

    return "\n".join(lines)
