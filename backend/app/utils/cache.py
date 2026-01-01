"""
Cache utilities for API endpoints.

Provides timed_cache decorator for caching function results with TTL.
"""

from functools import wraps
from typing import Callable, Any
import time
import hashlib
import json


def timed_cache(seconds: int = 300):
    """
    Decorator for caching async function results with TTL.

    Args:
        seconds: Time to live in seconds (default: 5 minutes)

    Example:
        @timed_cache(seconds=300)
        async def get_exercises():
            ...
    """
    def decorator(func: Callable) -> Callable:
        cache: dict[str, Any] = {}
        cache_time: dict[str, float] = {}

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            # Exclude 'session' and 'db' from cache key as they change
            cache_key_parts = [func.__name__]

            # Add args (skip session/db objects)
            for arg in args:
                if not hasattr(arg, '__dict__'):  # Skip objects
                    cache_key_parts.append(str(arg))

            # Add kwargs (skip session/db)
            for key, value in sorted(kwargs.items()):
                if key not in ('session', 'db') and not hasattr(value, '__dict__'):
                    cache_key_parts.append(f"{key}:{value}")

            cache_key = hashlib.md5(
                json.dumps(cache_key_parts, sort_keys=True).encode()
            ).hexdigest()

            # Check cache
            if cache_key in cache:
                if time.time() - cache_time[cache_key] < seconds:
                    return cache[cache_key]

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            cache[cache_key] = result
            cache_time[cache_key] = time.time()

            # Cleanup old entries (optional, prevents memory leak)
            current_time = time.time()
            keys_to_remove = [
                key for key, timestamp in cache_time.items()
                if current_time - timestamp >= seconds
            ]
            for key in keys_to_remove:
                cache.pop(key, None)
                cache_time.pop(key, None)

            return result

        return wrapper
    return decorator
