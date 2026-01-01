def calculate_xp(
    base_xp: int,
    difficulty: int,
    reps: int,
    streak_days: int,
    is_first_today: bool,
) -> int:
    """
    Calculate XP earned for ONE set of an exercise.
    
    ALGORITHM (v2.0):
    XP = base_xp × difficulty_mult × volume_mult × streak_mult × first_bonus
    
    Each set is calculated separately, then results are summed.
    This ensures fair XP distribution across all sets.

    Args:
        base_xp: Base XP from exercise definition
        difficulty: Exercise difficulty (1-5)
        reps: Number of reps in THIS set (or rep equivalent for timed)
        streak_days: Current streak in days
        is_first_today: Whether this is the first workout of the day

    Returns:
        Calculated XP amount for this set (integer)
    """
    # 1. Difficulty multiplier: 1.0, 1.25, 1.5, 1.75, 2.0
    difficulty_mult = 1 + (difficulty - 1) * 0.25

    # 2. Volume multiplier (applied to THIS set's reps)
    # Diminishing returns after 20 reps
    if reps <= 20:
        volume_mult = 1 + reps * 0.02  # 1.0 to 1.4
    else:
        volume_mult = 1.4 + (reps - 20) * 0.01  # slower growth

    # 3. Streak multiplier: max 50% at 30+ days
    streak_mult = 1 + min(streak_days, 30) * 0.0167  # ~1.5 max

    # 4. First workout of the day bonus
    first_bonus = 1.2 if is_first_today else 1.0

    # Calculate XP for this set
    xp = base_xp * difficulty_mult * volume_mult * streak_mult * first_bonus
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
    Calculate streak multiplier for display.

    Args:
        streak_days: Current streak in days

    Returns:
        Multiplier value (1.0 to 1.5)
    """
    return 1 + min(streak_days, 30) * 0.0167
