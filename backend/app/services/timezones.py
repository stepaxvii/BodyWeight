"""User-local time helpers.

Every day-boundary in the app (streaks, "did I train today", quest days, the daily
reminder hour) must be computed in the PLAYER's timezone, not the server's UTC.
Users store an IANA zone name (``User.timezone``, e.g. "Europe/Moscow"); these
helpers turn that into the player's local date / day window using the stdlib
``zoneinfo`` (no new dependency). Every function tolerates a bad/legacy/empty zone
name by falling back to UTC — never raise on user data.

Storage convention: all DB timestamps (``finished_at``, ``created_at``, …) are
naive UTC, and all date columns (``last_workout_date``, ``Challenge.start_date``,
``ChallengeProgress.progress_date`` …) now mean "the owner's local calendar date".
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

_UTC = ZoneInfo("UTC")


def zone(tz_name: str | None) -> ZoneInfo:
    """Resolve an IANA name to a ZoneInfo, falling back to UTC on anything bad."""
    if not tz_name:
        return _UTC
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return _UTC


def is_valid_zone(tz_name: str | None) -> bool:
    if not tz_name:
        return False
    try:
        ZoneInfo(tz_name)
        return True
    except Exception:
        return False


def user_local_now(tz_name: str | None) -> datetime:
    """The player's current local time as an aware datetime."""
    return datetime.now(timezone.utc).astimezone(zone(tz_name))


def user_local_today(tz_name: str | None) -> date:
    """The player's current local calendar date — the replacement for every
    ``datetime.utcnow().date()`` / ``date.today()`` that means 'today for the user'."""
    return user_local_now(tz_name).date()


def local_date_of(instant_utc: datetime, tz_name: str | None) -> date:
    """The player's local calendar date for a stored naive-UTC instant (e.g. a
    workout's ``finished_at``) — so a late-evening workout lands on the right day."""
    aware = instant_utc.replace(tzinfo=timezone.utc) if instant_utc.tzinfo is None else instant_utc
    return aware.astimezone(zone(tz_name)).date()


def local_day_bounds_utc(day: date, tz_name: str | None) -> tuple[datetime, datetime]:
    """[start, end) of a LOCAL calendar day, expressed as naive-UTC datetimes for
    querying UTC-stored timestamp columns. Generalises the hardcoded +3 window in
    admin_stats to any zone."""
    tz = zone(tz_name)
    start_local = datetime.combine(day, time.min, tzinfo=tz)
    start_utc = start_local.astimezone(timezone.utc).replace(tzinfo=None)
    end_utc = (start_local + timedelta(days=1)).astimezone(timezone.utc).replace(tzinfo=None)
    return start_utc, end_utc
