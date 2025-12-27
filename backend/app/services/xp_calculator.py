def calculate_xp(
    base_xp: int,
    difficulty: int,
    reps: int,
    streak_days: int,
    is_first_today: bool,
) -> int:
    """
    Calculate XP earned for an exercise.

    Formula:
    XP = base_xp × difficulty_mult × streak_mult × volume_mult × first_bonus

    Args:
        base_xp: Base XP from exercise definition
        difficulty: Exercise difficulty (1-5)
        reps: Number of reps performed
        streak_days: Current streak in days
        is_first_today: Whether this is the first workout of the day

    Returns:
        Calculated XP amount (integer)
    """
    # Difficulty multiplier: 1.0, 1.25, 1.5, 1.75, 2.0
    difficulty_mult = 1 + (difficulty - 1) * 0.25

    # Streak bonus: max 50% at 30+ days
    streak_mult = 1 + min(streak_days, 30) * 0.0167  # ~1.5 max

    # Volume bonus with diminishing returns after 20 reps
    if reps <= 20:
        volume_mult = 1 + reps * 0.02  # 1.0 to 1.4
    else:
        volume_mult = 1.4 + (reps - 20) * 0.01  # slower growth

    # First workout of the day bonus
    first_bonus = 1.2 if is_first_today else 1.0

    xp = base_xp * difficulty_mult * streak_mult * volume_mult * first_bonus
    return int(xp)


def calculate_coins(xp_earned: int, has_new_achievement: bool = False) -> int:
    """
    Calculate coins earned.

    Formula:
    - Base: 1 coin per 10 XP
    - Achievement bonus: +50 coins

    Args:
        xp_earned: XP earned in this session
        has_new_achievement: Whether a new achievement was unlocked

    Returns:
        Calculated coins amount
    """
    coins = xp_earned // 10

    if has_new_achievement:
        coins += 50

    return coins


def xp_for_level(level: int) -> int:
    """
    Calculate total XP required to reach a level.

    Formula: XP = 100 × level²

    Level 1: 100 XP
    Level 2: 400 XP
    Level 3: 900 XP
    Level 10: 10,000 XP

    Args:
        level: Target level

    Returns:
        Total XP needed to reach this level
    """
    return 100 * level * level


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
    Calculate streak multiplier for display.

    Args:
        streak_days: Current streak in days

    Returns:
        Multiplier value (1.0 to 1.5)
    """
    return 1 + min(streak_days, 30) * 0.0167
