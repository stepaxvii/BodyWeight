# XP per rep = base_xp × rate. The rate is calibrated so a classic push-up
# (base_xp = 10) is worth 3 XP per rep. Difficulty is already baked into each
# exercise's base_xp, so there is no separate difficulty multiplier.
XP_PER_REP_RATE = 0.3

# A timed hold of this many seconds counts as one rep-equivalent.
SECONDS_PER_REP_EQUIVALENT = 10


def xp_per_rep(base_xp: int) -> float:
    """XP awarded for a single rep (or rep-equivalent) of this exercise."""
    return base_xp * XP_PER_REP_RATE


def calculate_exercise_xp(base_xp: int, total_reps: int, streak_days: int) -> int:
    """
    Calculate XP for a reps-based exercise.

    ALGORITHM (v3.0):
    XP = total_reps × xp_per_rep(base_xp) × streak_mult

    XP is strictly proportional to the TOTAL reps performed and is completely
    independent of how the work was split into sets — 30 reps award the same
    XP whether logged as 1×30, 3×10 or 6×5.

    Args:
        base_xp: Base XP from exercise definition (encodes difficulty)
        total_reps: Total reps across all sets of this exercise
        streak_days: Current streak in days

    Returns:
        Calculated XP amount for the whole exercise (integer)
    """
    if total_reps <= 0:
        return 0

    xp = total_reps * xp_per_rep(base_xp) * get_streak_multiplier(streak_days)
    return int(xp)


def calculate_timed_xp(base_xp: int, total_duration_seconds: int, streak_days: int) -> int:
    """
    Calculate XP for a timed/hold exercise, by analogy with reps.

    rep_equivalent = total_duration_seconds / 10   (10s = 1 rep)
    XP = rep_equivalent × xp_per_rep(base_xp) × streak_mult

    Like the reps formula, it depends only on the TOTAL hold time and is
    independent of how the hold was split across sets.

    Args:
        base_xp: Base XP from exercise definition
        total_duration_seconds: Total hold time across all sets, in seconds
        streak_days: Current streak in days

    Returns:
        Calculated XP amount for the whole exercise (integer)
    """
    if total_duration_seconds <= 0:
        return 0

    rep_equiv = total_duration_seconds / SECONDS_PER_REP_EQUIVALENT
    xp = rep_equiv * xp_per_rep(base_xp) * get_streak_multiplier(streak_days)
    return int(xp)


def calculate_coins(xp_earned: int, streak_days: int = 0, workout_duration_minutes: int = 0) -> int:
    """
    Calculate coins earned. Coins are rare and valuable!

    Sources:
    - Workout XP threshold: 1 coin only if earned 500+ XP (hard to reach)
    - Streak bonus: 1 coin per 7 days of streak (max 4 coins at 28+ days)
    - Long workout bonus: 1 coin if workout > 45 min

    Args:
        xp_earned: XP earned in this session
        streak_days: Current streak in days
        workout_duration_minutes: Duration of workout in minutes

    Returns:
        Calculated coins amount (0-5 per workout typically)
    """
    coins = 0

    # XP threshold bonus - only for really good workouts
    if xp_earned >= 500:
        coins += 1

    # Streak bonus (1 coin per week of streak, max 4 at 28+ days)
    # This rewards consistency - the main way to earn coins
    coins += min(streak_days // 7, 4)

    # Long workout bonus - only for serious sessions
    if workout_duration_minutes >= 45:
        coins += 1

    return coins


def calculate_cycling_xp(distance_km: float, duration_minutes: int, streak_days: int = 0) -> int:
    """
    Calculate XP for cycling based on distance, average speed and streak.

    Formula:
    - base_xp = distance_km * 15
    - avg_speed = distance_km / (duration_minutes / 60)
    - multiplier = clamp(1 + (avg_speed - 10) * 0.025, 1, 1.6)
    - xp = floor(base_xp * multiplier * streak_mult)
    """
    if distance_km <= 0:
        raise ValueError("distance_km must be positive")
    if duration_minutes <= 0:
        raise ValueError("duration_minutes must be positive")

    base_xp = distance_km * 15
    avg_speed = distance_km / (duration_minutes / 60)
    multiplier = max(1.0, min(1.6, 1 + (avg_speed - 10) * 0.025))

    return int(base_xp * multiplier * get_streak_multiplier(streak_days))


def calculate_walking_xp(steps: int, streak_days: int = 0) -> int:
    """
    Calculate XP for walking based on total step count and streak.

    Formula: xp = floor(steps // 50 * streak_mult) (10 000 steps = 200 XP at no streak)
    """
    if steps <= 0:
        raise ValueError("steps must be positive")

    return int((steps // 50) * get_streak_multiplier(streak_days))


def xp_for_level(level: int) -> int:
    """
    Calculate total XP required to reach a level.

    Formula: XP = 100 × (level-1)²

    Level 1: 0 XP (starting level)
    Level 2: 100 XP
    Level 3: 400 XP
    Level 4: 900 XP
    Level 10: 8,100 XP

    Args:
        level: Target level

    Returns:
        Total XP needed to reach this level
    """
    lvl = level - 1
    return 100 * lvl * lvl


def get_level_from_xp(total_xp: int) -> int:
    """
    Calculate level from total XP.

    Args:
        total_xp: Total accumulated XP

    Returns:
        Current level
    """
    level = 1
    while xp_for_level(level + 1) <= total_xp:
        level += 1
    return level


def get_streak_multiplier(streak_days: int) -> float:
    """
    Calculate streak multiplier.

    Ramps linearly from 1.0 (no streak) to 1.5 (+50%) over one week,
    then stays capped at 1.5 for 7+ days.

    Args:
        streak_days: Current streak in days

    Returns:
        Multiplier value (1.0 to 1.5)
    """
    return 1 + min(streak_days, 7) / 7 * 0.5
