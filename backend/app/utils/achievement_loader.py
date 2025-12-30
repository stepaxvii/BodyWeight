"""
Utility for loading and caching achievement data.
Centralizes achievement loading to avoid duplication.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import List, Dict, Optional


@lru_cache(maxsize=1)
def load_achievements() -> List[Dict]:
    """
    Load achievements from JSON file with caching.
    Cache persists for the lifetime of the application.

    Returns:
        List of achievement dictionaries
    """
    achievements_file = Path(__file__).parent.parent / "data" / "achievements.json"

    with open(achievements_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("achievements", [])


def get_achievement_by_slug(slug: str) -> Optional[Dict]:
    """
    Get a specific achievement by its slug.

    Args:
        slug: The achievement slug to find

    Returns:
        Achievement dictionary or None if not found
    """
    achievements = load_achievements()
    return next((a for a in achievements if a["slug"] == slug), None)


def get_achievements_by_condition_type(condition_type: str) -> List[Dict]:
    """
    Get all achievements matching a specific condition type.

    Args:
        condition_type: The condition type to filter by (e.g., 'total_workouts', 'streak')

    Returns:
        List of matching achievements
    """
    achievements = load_achievements()
    return [
        a for a in achievements
        if a.get("condition", {}).get("type") == condition_type
    ]


def clear_cache():
    """
    Clear the achievements cache.
    Useful for testing or if achievements.json is updated at runtime.
    """
    load_achievements.cache_clear()
