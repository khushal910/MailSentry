import asyncio
import functools
import logging
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)


class InMemoryTTLCache:
    """
    Thread-safe & async-compatible in-memory TTL cache with automatic expiration.
    Used for caching email summaries, model info, and static/aggregated data.
    """

    def __init__(self, default_ttl_seconds: int = 300, max_size: int = 2000):
        self._cache: dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl_seconds
        self._max_size = max_size
        self._lock = asyncio.Lock()

    def get(self, key: str) -> Any | None:
        """
        Retrieves a cached value if it exists and has not expired.
        """
        if not key:
            return None

        entry = self._cache.get(key)
        if not entry:
            return None

        val, expiry = entry
        if time.time() > expiry:
            # Expired
            self._cache.pop(key, None)
            return None

        return val

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """
        Stores a value in cache with a TTL (seconds).
        """
        if not key:
            return

        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        expiry = time.time() + ttl

        # Evict oldest if max_size exceeded
        if len(self._cache) >= self._max_size and key not in self._cache:
            try:
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
                self._cache.pop(oldest_key, None)
            except Exception:
                pass

        self._cache[key] = (value, expiry)

    def delete(self, key: str) -> bool:
        """
        Deletes a specific key from the cache.
        """
        return self._cache.pop(key, None) is not None

    def invalidate_prefix(self, prefix: str) -> int:
        """
        Removes all cache keys matching the given prefix.
        """
        keys_to_remove = [k for k in self._cache if k.startswith(prefix)]
        for k in keys_to_remove:
            self._cache.pop(k, None)
        return len(keys_to_remove)

    def clear(self) -> None:
        """
        Clears all items in the cache.
        """
        self._cache.clear()

    def size(self) -> int:
        return len(self._cache)


# Global singleton instances
email_summary_cache = InMemoryTTLCache(default_ttl_seconds=3600, max_size=1000)  # 1 hour
static_data_cache = InMemoryTTLCache(default_ttl_seconds=600, max_size=500)      # 10 minutes
dashboard_stats_cache = InMemoryTTLCache(default_ttl_seconds=30, max_size=500)   # 30 seconds
