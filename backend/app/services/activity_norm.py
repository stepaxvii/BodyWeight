"""Daily activity norm helpers.

The activity calendar colours each day relative to the user's *daily norm* — the
target XP for one day. The current value lives on ``User.daily_activity_norm``;
the full history lives in ``user_activity_norms`` so past days are coloured
against the norm that was in force back then.
"""
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, UserActivityNorm

# Default for brand-new users (and the fallback when no history row applies).
DEFAULT_ACTIVITY_NORM = 1400
# Sanity bounds for a user-chosen norm.
MIN_ACTIVITY_NORM = 100
MAX_ACTIVITY_NORM = 100_000


async def get_norm_history(session: AsyncSession, user_id: int) -> list[tuple[date, int]]:
    """All (effective_from, norm) rows for a user, oldest first."""
    result = await session.execute(
        select(UserActivityNorm.effective_from, UserActivityNorm.norm)
        .where(UserActivityNorm.user_id == user_id)
        .order_by(UserActivityNorm.effective_from)
    )
    return [(row.effective_from, row.norm) for row in result.all()]


def resolve_norm(
    history: list[tuple[date, int]],
    on_date: date,
    fallback: int = DEFAULT_ACTIVITY_NORM,
) -> int:
    """Norm in force on ``on_date``: the latest row with effective_from <= date.

    ``history`` must be sorted ascending by effective_from. Falls back to
    ``fallback`` when no row applies (e.g. a user with no history yet).
    """
    norm = fallback
    for effective_from, value in history:
        if effective_from <= on_date:
            norm = value
        else:
            break
    return norm


async def set_user_norm(session: AsyncSession, user: User, norm: int) -> int:
    """Set the user's daily norm from today onward.

    Clamps to [MIN, MAX], upserts the history row for today, and updates the
    denormalised ``User.daily_activity_norm``. Returns the clamped value.
    """
    norm = max(MIN_ACTIVITY_NORM, min(MAX_ACTIVITY_NORM, int(norm)))
    today = date.today()

    existing = await session.execute(
        select(UserActivityNorm)
        .where(UserActivityNorm.user_id == user.id)
        .where(UserActivityNorm.effective_from == today)
    )
    row = existing.scalar_one_or_none()
    if row is not None:
        row.norm = norm
    else:
        session.add(
            UserActivityNorm(user_id=user.id, norm=norm, effective_from=today)
        )

    user.daily_activity_norm = norm
    await session.flush()
    return norm
