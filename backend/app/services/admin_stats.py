"""
Admin stats digests (daily + weekly).

Day boundaries are Moscow time (UTC+3, fixed — Russia has no DST since 2014) so
"за 4 ноября" matches the admin's calendar day; stored timestamps are naive UTC.
Each metric is shown with context (Δ vs yesterday + trailing 7-day average) plus
a retention/activation block, because raw daily counts are meaningless without a
baseline. Russian HTML (aiogram HTML parse mode); admin-only.
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

_MSK_OFFSET = timedelta(hours=3)


def msk_today() -> date:
    """Current calendar day in Moscow time."""
    return (datetime.utcnow() + _MSK_OFFSET).date()


def _utc_window(day: date) -> tuple[datetime, datetime]:
    """[00:00, 24:00) of the Moscow day `day`, as the naive-UTC range to query."""
    start = datetime.combine(day, time.min) - _MSK_OFFSET
    return start, start + timedelta(days=1)


def _done_conds(day: date):
    s, e = _utc_window(day)
    return (
        WorkoutSession.status == "completed",
        WorkoutSession.finished_at >= s,
        WorkoutSession.finished_at < e,
    )


async def _core(session: AsyncSession, day: date) -> dict:
    """Light per-day aggregate reused for the reported day, yesterday and the
    7-day baseline."""
    s, e = _utc_window(day)
    active, workouts, xp = (
        await session.execute(
            select(
                func.count(func.distinct(WorkoutSession.user_id)),
                func.count(WorkoutSession.id),
                func.coalesce(func.sum(WorkoutSession.total_xp_earned), 0),
            ).where(*_done_conds(day))
        )
    ).one()
    new = (
        await session.execute(
            select(func.count())
            .select_from(User)
            .where(User.created_at >= s, User.created_at < e)
        )
    ).scalar_one()
    return {"active": int(active), "workouts": int(workouts), "xp": int(xp), "new": int(new)}


async def collect_daily_stats(session: AsyncSession, day: date) -> dict:
    """Full daily digest payload for the Moscow day `day`."""
    today = await _core(session, day)
    prev = await _core(session, day - timedelta(days=1))
    prior = [await _core(session, day - timedelta(days=i)) for i in range(1, 8)]
    n = len(prior)
    avg = {k: sum(d[k] for d in prior) / n for k in ("active", "workouts", "xp", "new")}

    s, e = _utc_window(day)
    done = _done_conds(day)

    total_users = (
        await session.execute(select(func.count()).select_from(User))
    ).scalar_one()

    total_sets, total_reps = (
        await session.execute(
            select(
                func.coalesce(func.sum(WorkoutExercise.sets_completed), 0),
                func.coalesce(func.sum(WorkoutExercise.total_reps), 0),
            )
            .join(WorkoutSession, WorkoutExercise.workout_session_id == WorkoutSession.id)
            .where(*done)
        )
    ).one()

    # WAU — distinct users with a completed workout in the trailing 7 Moscow days.
    wau_start = _utc_window(day - timedelta(days=6))[0]
    wau = (
        await session.execute(
            select(func.count(func.distinct(WorkoutSession.user_id))).where(
                WorkoutSession.status == "completed",
                WorkoutSession.finished_at >= wau_start,
                WorkoutSession.finished_at < e,
            )
        )
    ).scalar_one()

    # Activation / onboarding funnel.
    not_onboarded = (
        await session.execute(
            select(func.count()).select_from(User).where(User.is_onboarded.is_(False))
        )
    ).scalar_one()
    activated = (
        await session.execute(
            select(func.count()).select_from(User).where(User.last_workout_date.isnot(None))
        )
    ).scalar_one()

    # Sleeping: ever-active users idle N+ days (reactivation candidates).
    sleeping3 = (
        await session.execute(
            select(func.count())
            .select_from(User)
            .where(User.last_workout_date.isnot(None))
            .where(User.last_workout_date <= day - timedelta(days=3))
        )
    ).scalar_one()
    sleeping7 = (
        await session.execute(
            select(func.count())
            .select_from(User)
            .where(User.last_workout_date.isnot(None))
            .where(User.last_workout_date <= day - timedelta(days=7))
        )
    ).scalar_one()

    # New vs returning among today's active users.
    active_ids = [
        r[0]
        for r in (
            await session.execute(select(func.distinct(WorkoutSession.user_id)).where(*done))
        ).all()
    ]
    new_active = 0
    if active_ids:
        new_active = (
            await session.execute(
                select(func.count())
                .select_from(User)
                .where(User.id.in_(active_ids), User.created_at >= s, User.created_at < e)
            )
        ).scalar_one()
    returning_active = today["active"] - int(new_active)

    # D1 retention — of users who joined yesterday, how many trained today.
    ys, ye = _utc_window(day - timedelta(days=1))
    joined_prev = [
        r[0]
        for r in (
            await session.execute(
                select(User.id).where(User.created_at >= ys, User.created_at < ye)
            )
        ).all()
    ]
    d1_back = 0
    if joined_prev:
        d1_back = (
            await session.execute(
                select(func.count(func.distinct(WorkoutSession.user_id))).where(
                    WorkoutSession.status == "completed",
                    WorkoutSession.finished_at >= s,
                    WorkoutSession.finished_at < e,
                    WorkoutSession.user_id.in_(joined_prev),
                )
            )
        ).scalar_one()

    # Promo audience health.
    blocked = (
        await session.execute(
            select(func.count()).select_from(User).where(User.bot_blocked.is_(True))
        )
    ).scalar_one()
    reachable = (
        await session.execute(
            select(func.count())
            .select_from(User)
            .where(User.telegram_id.isnot(None))
            .where(User.bot_blocked.is_(False))
            .where(User.bot_reachable.is_(True))
        )
    ).scalar_one()
    not_started = (
        await session.execute(
            select(func.count())
            .select_from(User)
            .where(User.telegram_id.isnot(None))
            .where(User.bot_blocked.is_(False))
            .where(User.bot_reachable.is_(False))
        )
    ).scalar_one()

    top = (
        await session.execute(
            select(Exercise.name_ru, func.count(WorkoutExercise.id))
            .join(WorkoutExercise, WorkoutExercise.exercise_id == Exercise.id)
            .join(WorkoutSession, WorkoutExercise.workout_session_id == WorkoutSession.id)
            .where(*done)
            .group_by(Exercise.name_ru)
            .order_by(func.count(WorkoutExercise.id).desc())
            .limit(5)
        )
    ).all()

    challenge_joins = (
        await session.execute(
            select(func.count())
            .select_from(ChallengeParticipant)
            .where(ChallengeParticipant.joined_at >= s, ChallengeParticipant.joined_at < e)
        )
    ).scalar_one()
    freezes = (
        await session.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.notification_type == "streak_freeze_used")
            .where(Notification.created_at >= s, Notification.created_at < e)
        )
    ).scalar_one()
    referrals = (
        await session.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.notification_type == "referral_reward")
            .where(Notification.created_at >= s, Notification.created_at < e)
        )
    ).scalar_one()

    boss = (
        await session.execute(
            select(MonthlyBoss)
            .where(MonthlyBoss.start_date <= day)
            .where(MonthlyBoss.end_date >= day)
        )
    ).scalar_one_or_none()
    boss_stats = None
    if boss is not None:
        boss_stats = {
            "name_ru": boss.name_ru,
            "current_hp": boss.current_hp,
            "max_hp": boss.max_hp,
            # Damage == XP 1:1 (capped only on the kill-day), so today's XP is the
            # real HP drop on every normal day.
            "today_damage": today["xp"],
            "pct_down": round(100 * (boss.max_hp - boss.current_hp) / boss.max_hp) if boss.max_hp else 0,
        }

    return {
        "today": today,
        "prev": prev,
        "avg": avg,
        "total_users": int(total_users),
        "total_sets": int(total_sets),
        "total_reps": int(total_reps),
        "wau": int(wau),
        "not_onboarded": int(not_onboarded),
        "activated": int(activated),
        "sleeping3": int(sleeping3),
        "sleeping7": int(sleeping7),
        "new_active": int(new_active),
        "returning_active": int(returning_active),
        "d1": {"back": int(d1_back), "cohort": len(joined_prev)},
        "blocked": int(blocked),
        "reachable": int(reachable),
        "not_started": int(not_started),
        "top": [(name_ru, int(cnt)) for name_ru, cnt in top],
        "challenge_joins": int(challenge_joins),
        "freezes": int(freezes),
        "referrals": int(referrals),
        "boss": boss_stats,
    }


async def collect_weekly_stats(session: AsyncSession, end_day: date) -> dict:
    """7-day rollup ending on `end_day` (inclusive), with a vs-previous-week trend."""
    start_day = end_day - timedelta(days=6)
    week = [await _core(session, end_day - timedelta(days=i)) for i in range(0, 7)]
    prior = [await _core(session, start_day - timedelta(days=i)) for i in range(1, 8)]
    cur = {k: sum(d[k] for d in week) for k in ("active", "workouts", "xp", "new")}
    prevw = {k: sum(d[k] for d in prior) for k in ("workouts", "new", "xp")}

    s = _utc_window(start_day)[0]
    e = _utc_window(end_day)[1]

    total_users = (
        await session.execute(select(func.count()).select_from(User))
    ).scalar_one()
    wau = (
        await session.execute(
            select(func.count(func.distinct(WorkoutSession.user_id))).where(
                WorkoutSession.status == "completed",
                WorkoutSession.finished_at >= s,
                WorkoutSession.finished_at < e,
            )
        )
    ).scalar_one()
    total_sets, total_reps = (
        await session.execute(
            select(
                func.coalesce(func.sum(WorkoutExercise.sets_completed), 0),
                func.coalesce(func.sum(WorkoutExercise.total_reps), 0),
            )
            .join(WorkoutSession, WorkoutExercise.workout_session_id == WorkoutSession.id)
            .where(
                WorkoutSession.status == "completed",
                WorkoutSession.finished_at >= s,
                WorkoutSession.finished_at < e,
            )
        )
    ).one()
    top = (
        await session.execute(
            select(Exercise.name_ru, func.count(WorkoutExercise.id))
            .join(WorkoutExercise, WorkoutExercise.exercise_id == Exercise.id)
            .join(WorkoutSession, WorkoutExercise.workout_session_id == WorkoutSession.id)
            .where(
                WorkoutSession.status == "completed",
                WorkoutSession.finished_at >= s,
                WorkoutSession.finished_at < e,
            )
            .group_by(Exercise.name_ru)
            .order_by(func.count(WorkoutExercise.id).desc())
            .limit(5)
        )
    ).all()

    boss = (
        await session.execute(
            select(MonthlyBoss)
            .where(MonthlyBoss.start_date <= end_day)
            .where(MonthlyBoss.end_date >= end_day)
        )
    ).scalar_one_or_none()
    boss_stats = None
    if boss is not None:
        boss_stats = {
            "name_ru": boss.name_ru,
            "current_hp": boss.current_hp,
            "max_hp": boss.max_hp,
            "week_damage": cur["xp"],
            "pct_down": round(100 * (boss.max_hp - boss.current_hp) / boss.max_hp) if boss.max_hp else 0,
        }

    return {
        "start": start_day,
        "end": end_day,
        "cur": cur,
        "prev": prevw,
        "wau": int(wau),
        "total_users": int(total_users),
        "total_sets": int(total_sets),
        "total_reps": int(total_reps),
        "top": [(name_ru, int(cnt)) for name_ru, cnt in top],
        "boss": boss_stats,
    }


# --------------------------------------------------------------------------- #
# Formatting
# --------------------------------------------------------------------------- #

def _fmt(n: int) -> str:
    return f"{int(n):,}".replace(",", " ")


def _plural(n: int, one: str, few: str, many: str) -> str:
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def _avg_s(x: float) -> str:
    """Average with at most one decimal, trailing .0 trimmed."""
    return f"{x:.1f}".rstrip("0").rstrip(".")


def _trend(cur: int, prev: int, avg: float) -> str:
    """Compact ' (↑+3 · ср 5/дн)' context vs yesterday and the 7-day average."""
    arrow = "↑" if cur > prev else "↓" if cur < prev else "→"
    d = cur - prev
    sign = "+" if d >= 0 else ""
    return f" ({arrow}{sign}{d} · ср {_avg_s(avg)}/дн)"


def _wtrend(cur: int, prev: int) -> str:
    """Week-over-week delta with a percentage when meaningful."""
    arrow = "↑" if cur > prev else "↓" if cur < prev else "→"
    d = cur - prev
    sign = "+" if d >= 0 else ""
    if prev:
        pct = round(100 * (cur - prev) / prev)
        return f" ({arrow}{sign}{d} · {sign if pct>=0 else ''}{pct}% к пред. неделе)"
    return f" ({arrow}{sign}{d} к пред. неделе)"


def format_digest(stats: dict, day: date) -> str:
    """Build the daily digest: a headline line, then labelled sections."""
    t = stats["today"]
    total = stats["total_users"]
    dau_pct = round(100 * t["active"] / total) if total else 0

    # Headline — the one-glance pulse.
    head_bits = [f"DAU {t['active']}/{total} ({dau_pct}%)"]
    if t["new"]:
        head_bits.append(f"+{t['new']} новых")
    if stats["boss"]:
        head_bits.append(f"👹 {stats['boss']['pct_down']}%")
    lines = [
        f"📊 <b>PixelFit — за {day.strftime('%d.%m')} (МСК)</b>",
        " · ".join(head_bits),
    ]

    # 📈 Рост / удержание
    growth = ["", "<b>📈 Рост и удержание</b>"]
    growth.append(
        f"👤 Новых: {_fmt(t['new'])}{_trend(t['new'], stats['prev']['new'], stats['avg']['new'])} · всего {_fmt(total)}"
    )
    d1 = stats["d1"]
    ret = f"🔄 Активных: {_fmt(t['active'])} (вернулись {_fmt(stats['returning_active'])}, новых {_fmt(stats['new_active'])}) · WAU {_fmt(stats['wau'])}"
    if d1["cohort"]:
        ret += f" · D1 {d1['back']}/{d1['cohort']}"
    growth.append(ret)
    if stats["sleeping3"]:
        growth.append(
            f"😴 Спящие: {_fmt(stats['sleeping3'])} (3+ дн) · {_fmt(stats['sleeping7'])} (7+ дн)"
        )
    growth.append(
        f"🧩 Активация: тренировались ≥1 раз {_fmt(stats['activated'])}/{_fmt(total)}"
        + (f" · не прошли онбординг {_fmt(stats['not_onboarded'])}" if stats["not_onboarded"] else "")
    )
    lines += growth

    # 🏃 Активность
    if t["workouts"]:
        per_user = t["workouts"] / t["active"] if t["active"] else 0
        per_workout = stats["total_reps"] / t["workouts"] if t["workouts"] else 0
        w_word = _plural(t["workouts"], "тренировка", "тренировки", "тренировок")
        lines += [
            "",
            "<b>🏃 Активность</b>",
            f"Тренировки: {_fmt(t['workouts'])} {w_word}{_trend(t['workouts'], stats['prev']['workouts'], stats['avg']['workouts'])} · {_avg_s(per_user)} на чел",
            f"⚡ XP {_fmt(t['xp'])}{_trend(t['xp'], stats['prev']['xp'], stats['avg']['xp'])}",
            f"🔁 Подходы {_fmt(stats['total_sets'])} · повторения {_fmt(stats['total_reps'])} · ~{_fmt(round(per_workout))} повт/трен",
        ]
        if stats["top"]:
            top = " · ".join(f"{html.escape(name)} ({_fmt(cnt)})" for name, cnt in stats["top"])
            lines.append(f"🏆 Топ: {top}")

    # 👹 Босс
    boss = stats["boss"]
    if boss is not None:
        dmg = f"~{_fmt(boss['today_damage'])} урона · " if boss["today_damage"] else ""
        lines += [
            "",
            f"👹 <b>Босс «{html.escape(boss['name_ru'])}»</b>: {dmg}HP {_fmt(boss['current_hp'])}/{_fmt(boss['max_hp'])} ({boss['pct_down']}% побито)",
        ]

    # 🎯 Прочее
    extras = []
    if stats["challenge_joins"]:
        extras.append(f"🎯 Челленджи +{_fmt(stats['challenge_joins'])}")
    if stats["freezes"]:
        extras.append(f"🧊 Заморозок {_fmt(stats['freezes'])}")
    if stats["referrals"]:
        rn = stats["referrals"]
        extras.append(f"🤝 Рефералка {_fmt(rn)} {_plural(rn, 'награда', 'награды', 'наград')}")
    if extras:
        lines += ["", " · ".join(extras)]

    # 📣 Промо-аудитория
    promo = f"📣 Для промо: {_fmt(stats['reachable'])}"
    if stats["not_started"]:
        promo += f" · 📵 не открыли бота: {_fmt(stats['not_started'])}"
    if stats["blocked"]:
        promo += f" · 🚫 заблокировали: {_fmt(stats['blocked'])}"
    lines += ["", promo]

    if not (t["new"] or t["workouts"] or stats["challenge_joins"] or stats["freezes"] or stats["referrals"]):
        lines.append("")
        lines.append("Тишина — за день активности не было.")

    return "\n".join(lines)


def format_weekly_digest(stats: dict) -> str:
    """Build the weekly rollup: 7-day totals with week-over-week trend."""
    cur, prev = stats["cur"], stats["prev"]
    start, end = stats["start"], stats["end"]
    w_word = _plural(cur["workouts"], "тренировка", "тренировки", "тренировок")
    lines = [
        f"🗓 <b>PixelFit — неделя {start.strftime('%d.%m')}–{end.strftime('%d.%m')} (МСК)</b>",
        f"WAU {_fmt(stats['wau'])}/{_fmt(stats['total_users'])} · +{_fmt(cur['new'])} новых за неделю",
        "",
        f"🏃 Тренировки: {_fmt(cur['workouts'])} {w_word}{_wtrend(cur['workouts'], prev['workouts'])}",
        f"👤 Новых: {_fmt(cur['new'])}{_wtrend(cur['new'], prev['new'])}",
        f"⚡ XP {_fmt(cur['xp'])}{_wtrend(cur['xp'], prev['xp'])} · подходы {_fmt(stats['total_sets'])} · повторения {_fmt(stats['total_reps'])}",
    ]
    if stats["top"]:
        top = " · ".join(f"{html.escape(name)} ({_fmt(cnt)})" for name, cnt in stats["top"])
        lines.append(f"🏆 Топ недели: {top}")
    boss = stats["boss"]
    if boss is not None:
        lines.append(
            f"👹 Босс «{html.escape(boss['name_ru'])}»: HP {_fmt(boss['current_hp'])}/{_fmt(boss['max_hp'])} ({boss['pct_down']}% побито)"
        )
    return "\n".join(lines)
