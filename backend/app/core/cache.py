"""Simple in-memory TTL cache for frequently accessed data."""
import time
import asyncio
from functools import wraps


class TTLCache:
    """Thread-safe TTL cache with async support."""

    def __init__(self, max_size: int = 500):
        self._cache: dict[str, tuple[float, object]] = {}
        self._max_size = max_size
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> object | None:
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if time.time() > expires_at:
                del self._cache[key]
                return None
            return value

    async def set(self, key: str, value: object, ttl: float):
        async with self._lock:
            if len(self._cache) >= self._max_size:
                # Evict 20% oldest entries
                sorted_keys = sorted(
                    self._cache.keys(),
                    key=lambda k: self._cache[k][0],
                )
                for k in sorted_keys[: len(sorted_keys) // 5]:
                    del self._cache[k]
            self._cache[key] = (time.time() + ttl, value)

    def clear(self):
        self._cache.clear()


# Global cache instances
raster_cache = TTLCache(max_size=1000)  # 栅格数据缓存 (静态, 长TTL)
weather_cache = TTLCache(max_size=200)  # 天气数据缓存 (动态, 短TTL)


def cached(cache: TTLCache, ttl: float = 300):
    """Decorator: cache async function results with TTL."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key from function name + args
            key_parts = [func.__name__]
            key_parts.extend(str(a) for a in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            key = ":".join(key_parts)

            cached_val = await cache.get(key)
            if cached_val is not None:
                return cached_val

            result = await func(*args, **kwargs)
            if result is not None:
                await cache.set(key, result, ttl)
            return result

        return wrapper

    return decorator
