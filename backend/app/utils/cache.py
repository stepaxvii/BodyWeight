"""
Cache utilities for API endpoints.

Provides timed_cache decorator for caching function results with TTL.
"""

from functools import wraps
from typing import Callable, Any
import time
import hashlib
import json
import threading


def timed_cache(seconds: int = 300, maxsize: int = 128):
    """
    Decorator for caching async function results with TTL.

    Args:
        seconds: Time to live in seconds (default: 5 minutes)
        maxsize: Maximum number of cached entries (default: 128)
    """
    def decorator(func: Callable) -> Callable:
        cache: dict[str, Any] = {}
        cache_time: dict[str, float] = {}
        lock = threading.Lock()

        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key_parts = [func.__name__]

            for arg in args:
                if not hasattr(arg, '__dict__'):
                    cache_key_parts.append(str(arg))

            for key, value in sorted(kwargs.items()):
                if key not in ('session', 'db') and not hasattr(value, '__dict__'):
                    cache_key_parts.append(f"{key}:{value}")

            cache_key = hashlib.md5(
                json.dumps(cache_key_parts, sort_keys=True).encode()
            ).hexdigest()

            now = time.time()

            with lock:
                if cache_key in cache:
                    if now - cache_time[cache_key] < seconds:
                        return cache[cache_key]

            result = await func(*args, **kwargs)

            with lock:
                cache[cache_key] = result
                cache_time[cache_key] = time.time()

                if len(cache) > maxsize:
                    oldest = min(cache_time, key=cache_time.get)
                    del cache[oldest]
                    del cache_time[oldest]

            return result

        return wrapper
    return decorator
