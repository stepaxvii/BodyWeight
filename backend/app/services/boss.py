"""
Monthly boss raid service.

Boss lifecycle:
- 1st of each month a boss is created from the monthly catalogue (data/bosses.json)
- Each completed workout deals damage = total_xp_earned (capped per-workout)
- When current_hp reaches 0: status='defeated', defeated_at set
- At end of month finalize() distributes coin rewards by tier (50% on expiry)

Damage cap and milestones are tuned for v1; revisit after live data.
"""
import json
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MonthlyBoss, BossContribution, User
from app.services.notifications import save_notification


logger = logging.getLogger(__name__)

# Tunables
DAMAGE_CAP_PER_WORKOUT = 1500
REWARD_TIERS = [
    # (min_damage, tier_id, coins_full, coins_half_on_expiry)
    (50_000, "tier4", 150, 75),
    (10_000, "tier3", 50, 25),
    (1_000, "tier2", 15, 8),
    (1, "tier1", 5, 3),
]
TOP10_BONUS_COINS = 200
TOP10_BONUS_COINS_EXPIRED = 100

# Milestone notifications fire once each, in this order, when crossed
HP_MILESTONES = [0.50, 0.25, 0.10]


_BOSSES_DATA: list[dict[str, Any]] | None = None


def _load_bosses_catalogue() -> list[dict[str, Any]]:
    global _BOSSES_DATA
    if _BOSSES_DATA is None:
        path = Path(__file__).parent.parent / "data" / "bosses.json"
        with open(path, "r", encoding="utf-8") as f:
            _BOSSES_DATA = json.load(f)
    return _BOSSES_DATA


def _month_bounds(today: date) -> tuple[date, date]:
    """Return (first_day, last_day) of today's month in UTC."""
    start = today.replace(day=1)
    if start.month == 12:
        next_first = date(start.year + 1, 1, 1)
    else:
        next_first = date(start.year, start.month + 1, 1)
    end = next_first - timedelta(days=1)
    return start, end


async def get_or_create_current_boss(session: AsyncSession) -> MonthlyBoss:
    """Return the active boss for the current UTC month, creating it if missing."""
    today = datetime.utcnow().date()
    start, end = _month_bounds(today)

    result = await session.execute(
        select(MonthlyBoss).where(MonthlyBoss.start_date == start)
    )
    boss = result.scalar_one_or_none()
    if boss:
        return boss

    catalogue = _load_bosses_catalogue()
    template = next((b for b in catalogue if b["month"] == start.month), None)
    if template is None:
        raise RuntimeError(f"No boss template for month {start.month}")

    boss = MonthlyBoss(
        slug=template["slug"],
        name=template["name"],
        name_ru=template["name_ru"],
        image_emoji=template["image_emoji"],
        theme=template["theme"],
        legend_ru=template["legend_ru"],
        max_hp=template["max_hp"],
        current_hp=template["max_hp"],
        start_date=start,
        end_date=end,
        status="active",
    )
    session.add(boss)
    await session.flush()

    # Notify all opted-in users that a new boss appeared
    await _broadcast_new_boss_notification(session, boss)
    return boss


async def _broadcast_new_boss_notification(session: AsyncSession, boss: MonthlyBoss) -> None:
    """Save in-app notification for every user that a new boss arrived."""
    result = await session.execute(select(User.id).where(User.notifications_enabled.is_(True)))
    user_ids = [row[0] for row in result.all()]
    title = "Новый босс месяца!"
    msg = f"{boss.image_emoji} {boss.name_ru} появился. Вступай в битву!"
    for uid in user_ids:
        await save_notification(
            session=session,
            user_id=uid,
            notification_type="boss_appeared",
            title=title,
            message=msg,
        )


async def deal_damage(
    session: AsyncSession,
    user: User,
    xp_earned: int,
) -> int:
    """
    Apply damage from a completed workout to the active boss.

    Returns the actual damage dealt (after cap, possibly trimmed by remaining HP).
    Safe no-op if boss is not active or xp_earned <= 0.
    """
    if xp_earned <= 0:
        return 0

    boss = await get_or_create_current_boss(session)
    if boss.status != "active" or boss.current_hp <= 0:
        return 0

    damage = min(xp_earned, DAMAGE_CAP_PER_WORKOUT)
    # Don't overshoot below zero
    damage = min(damage, boss.current_hp)

    if damage <= 0:
        return 0

    hp_before = boss.current_hp
    now = datetime.utcnow()

    # Atomic decrement of boss HP — guards against parallel writers.
    await session.execute(
        update(MonthlyBoss)
        .where(MonthlyBoss.id == boss.id)
        .values(current_hp=MonthlyBoss.current_hp - damage)
    )

    # Upsert contribution row for this user
    contrib_result = await session.execute(
        select(BossContribution).where(
            BossContribution.boss_id == boss.id,
            BossContribution.user_id == user.id,
        )
    )
    contrib = contrib_result.scalar_one_or_none()
    if contrib is None:
        contrib = BossContribution(
            boss_id=boss.id,
            user_id=user.id,
            total_damage=damage,
            attacks_count=1,
            last_attack_at=now,
        )
        session.add(contrib)
    else:
        contrib.total_damage = (contrib.total_damage or 0) + damage
        contrib.attacks_count = (contrib.attacks_count or 0) + 1
        contrib.last_attack_at = now

    # Re-read post-update HP (after the atomic decrement)
    await session.flush()
    await session.refresh(boss)

    # Milestone & defeat notifications
    await _check_milestones(session, boss, hp_before, boss.current_hp, user)

    if boss.current_hp <= 0 and boss.status == "active":
        boss.status = "defeated"
        boss.defeated_at = now
        await _broadcast_defeat_notification(session, boss)

    return damage


async def _check_milestones(
    session: AsyncSession,
    boss: MonthlyBoss,
    hp_before: int,
    hp_after: int,
    triggering_user: User,
) -> None:
    """Send a community notification the first time HP crosses a milestone."""
    if boss.max_hp <= 0:
        return
    for ratio in HP_MILESTONES:
        threshold = int(boss.max_hp * ratio)
        if hp_before > threshold >= hp_after:
            await _broadcast_milestone_notification(session, boss, ratio)


async def _broadcast_milestone_notification(
    session: AsyncSession, boss: MonthlyBoss, ratio: float
) -> None:
    pct = int(ratio * 100)
    title = f"Босс на {pct}% HP!"
    msg = f"{boss.image_emoji} {boss.name_ru} ослабевает. Добей его!"
    result = await session.execute(select(User.id).where(User.notifications_enabled.is_(True)))
    for (uid,) in result.all():
        await save_notification(
            session=session,
            user_id=uid,
            notification_type="boss_milestone",
            title=title,
            message=msg,
        )


async def _broadcast_defeat_notification(
    session: AsyncSession, boss: MonthlyBoss
) -> None:
    title = "Босс повержен!"
    msg = f"{boss.image_emoji} {boss.name_ru} побеждён. Забери награду на странице босса."
    result = await session.execute(
        select(BossContribution.user_id).where(BossContribution.boss_id == boss.id)
    )
    for (uid,) in result.all():
        await save_notification(
            session=session,
            user_id=uid,
            notification_type="boss_defeated",
            title=title,
            message=msg,
        )


async def finalize_boss(session: AsyncSession, boss: MonthlyBoss) -> None:
    """
    Resolve reward tiers for a boss whose lifecycle is over.
    Called by the scheduler at month end (and lazily on read if late).

    Idempotent: won't process the same boss twice.
    """
    if boss.finalized_at is not None:
        return

    is_victory = boss.status == "defeated"
    if not is_victory and boss.status == "active":
        boss.status = "expired"

    # Pull contributions sorted by damage desc to identify top 10
    result = await session.execute(
        select(BossContribution)
        .where(BossContribution.boss_id == boss.id)
        .order_by(BossContribution.total_damage.desc())
    )
    contribs = list(result.scalars().all())

    for rank, contrib in enumerate(contribs, start=1):
        coins = 0
        tier_id = None
        for min_dmg, tid, full_coins, half_coins in REWARD_TIERS:
            if contrib.total_damage >= min_dmg:
                coins = full_coins if is_victory else half_coins
                tier_id = tid
                break

        if rank <= 10 and contrib.total_damage > 0:
            coins += TOP10_BONUS_COINS if is_victory else TOP10_BONUS_COINS_EXPIRED
            contrib.is_top10 = True

        contrib.reward_tier = tier_id
        contrib.reward_coins = coins

    boss.finalized_at = datetime.utcnow()


async def claim_reward(session: AsyncSession, user: User, boss_id: int) -> int:
    """
    Claim coins for a finalized boss. Returns coins awarded.
    Raises ValueError on invalid state.
    """
    result = await session.execute(
        select(BossContribution).where(
            BossContribution.boss_id == boss_id,
            BossContribution.user_id == user.id,
        )
    )
    contrib = result.scalar_one_or_none()
    if contrib is None:
        raise ValueError("No contribution to this boss")
    if contrib.reward_claimed_at is not None:
        raise ValueError("Reward already claimed")

    boss = await session.get(MonthlyBoss, boss_id)
    if boss is None or boss.finalized_at is None:
        raise ValueError("Boss not finalized yet")

    # Reward TTL: 7 days from finalization
    if datetime.utcnow() > boss.finalized_at + timedelta(days=7):
        raise ValueError("Reward window expired")

    if contrib.reward_coins > 0:
        user.coins += contrib.reward_coins
    contrib.reward_claimed_at = datetime.utcnow()

    return contrib.reward_coins


async def get_user_rank(
    session: AsyncSession, boss_id: int, user_id: int
) -> tuple[int | None, int]:
    """Return (rank, total_damage) for the user against a boss. Rank=None if no contribution."""
    result = await session.execute(
        select(BossContribution.user_id, BossContribution.total_damage)
        .where(BossContribution.boss_id == boss_id)
        .order_by(BossContribution.total_damage.desc())
    )
    rows = result.all()
    for idx, (uid, dmg) in enumerate(rows, start=1):
        if uid == user_id:
            return idx, dmg
    return None, 0


async def finalize_due_bosses(session: AsyncSession) -> int:
    """Find bosses whose end_date has passed but aren't finalized; finalize them."""
    today = datetime.utcnow().date()
    result = await session.execute(
        select(MonthlyBoss)
        .where(MonthlyBoss.finalized_at.is_(None))
        .where(
            (MonthlyBoss.status == "defeated")
            | (MonthlyBoss.end_date < today)
        )
    )
    bosses = list(result.scalars().all())
    for boss in bosses:
        await finalize_boss(session, boss)
    return len(bosses)
