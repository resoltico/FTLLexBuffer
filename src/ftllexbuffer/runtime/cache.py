"""Thread-safe LRU cache for message formatting results.

Provides transparent caching of format_pattern() calls with automatic
invalidation on resource/function changes.

Architecture:
    - Thread-safe using threading.RLock (reentrant lock)
    - LRU eviction via OrderedDict
    - Immutable cache keys (tuples of hashable types)
    - Automatic invalidation on bundle mutation
    - Zero overhead when disabled

Cache Key Structure:
    (message_id, args_tuple, attribute, locale_code)
    - message_id: str
    - args_tuple: tuple[tuple[str, Any], ...] (sorted, frozen)
    - attribute: str | None
    - locale_code: str (for multi-bundle scenarios)

Thread Safety:
    All operations protected by RLock. Safe for concurrent reads and writes.

Python 3.13+.
"""

from collections import OrderedDict
from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from threading import RLock

from ftllexbuffer.diagnostics import FluentError

# Type alias for Fluent values (matches resolver.FluentValue)
type _FluentValue = str | int | float | bool | Decimal | datetime | None

# Internal type alias for cache keys (prefixed with _ per naming convention)
type _CacheKey = tuple[str, tuple[tuple[str, _FluentValue], ...], str | None, str]

# Internal type alias for cache values (prefixed with _ per naming convention)
type _CacheValue = tuple[str, list[FluentError]]


class FormatCache:
    """Thread-safe LRU cache for format_pattern() results.

    Uses OrderedDict for LRU eviction and RLock for thread safety.
    Transparent to caller - returns None on cache miss.

    Attributes:
        maxsize: Maximum number of cache entries
        hits: Number of cache hits (for metrics)
        misses: Number of cache misses (for metrics)
    """

    __slots__ = ("_cache", "_hits", "_lock", "_maxsize", "_misses", "_unhashable_skips")

    def __init__(self, maxsize: int = 1000) -> None:
        """Initialize format cache.

        Args:
            maxsize: Maximum number of entries (default: 1000)
        """
        if maxsize <= 0:
            msg = "maxsize must be positive"
            raise ValueError(msg)

        self._cache: OrderedDict[_CacheKey, _CacheValue] = OrderedDict()
        self._maxsize = maxsize
        self._lock = RLock()  # Reentrant lock for safety
        self._hits = 0
        self._misses = 0
        self._unhashable_skips = 0

    def get(
        self,
        message_id: str,
        args: Mapping[str, _FluentValue] | None,
        attribute: str | None,
        locale_code: str,
    ) -> _CacheValue | None:
        """Get cached result if exists.

        Thread-safe. Returns None on cache miss.

        Args:
            message_id: Message identifier
            args: Message arguments (may contain unhashable values like lists)
            attribute: Attribute name
            locale_code: Locale code

        Returns:
            Cached (result, errors) tuple or None
        """
        key = self._make_key(message_id, args, attribute, locale_code)

        if key is None:
            with self._lock:
                self._unhashable_skips += 1
                self._misses += 1
            return None

        with self._lock:
            if key in self._cache:
                # Move to end (mark as recently used)
                self._cache.move_to_end(key)
                self._hits += 1
                return self._cache[key]

            self._misses += 1
            return None

    def put(
        self,
        message_id: str,
        args: Mapping[str, _FluentValue] | None,
        attribute: str | None,
        locale_code: str,
        result: _CacheValue,
    ) -> None:
        """Store result in cache.

        Thread-safe. Evicts LRU entry if cache is full.

        Args:
            message_id: Message identifier
            args: Message arguments (may contain unhashable values like lists)
            attribute: Attribute name
            locale_code: Locale code
            result: Format result to cache
        """
        key = self._make_key(message_id, args, attribute, locale_code)

        if key is None:
            with self._lock:
                self._unhashable_skips += 1
            return

        with self._lock:
            # Update existing or add new
            if key in self._cache:
                # Move to end (mark as recently used)
                self._cache.move_to_end(key)
            # Evict LRU if cache is full
            elif len(self._cache) >= self._maxsize:
                self._cache.popitem(last=False)  # Remove first (oldest)

            self._cache[key] = result

    def clear(self) -> None:
        """Clear all cached entries.

        Thread-safe. Call when bundle is mutated (add_resource, add_function).
        """
        with self._lock:
            self._cache.clear()
            # Reset metrics on clear
            self._hits = 0
            self._misses = 0
            self._unhashable_skips = 0

    def get_stats(self) -> dict[str, int]:
        """Get cache statistics.

        Thread-safe. Returns current metrics.

        Returns:
            Dict with keys: size, maxsize, hits, misses, hit_rate, unhashable_skips
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0.0

            return {
                "size": len(self._cache),
                "maxsize": self._maxsize,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": int(hit_rate),
                "unhashable_skips": self._unhashable_skips,
            }

    @staticmethod
    def _make_key(
        message_id: str,
        args: Mapping[str, _FluentValue] | None,
        attribute: str | None,
        locale_code: str,
    ) -> _CacheKey | None:
        """Create immutable cache key from arguments.

        Dicts are converted to sorted tuples. Verifies all values are hashable.

        Args:
            message_id: Message identifier
            args: Message arguments (may contain unhashable values)
            attribute: Attribute name
            locale_code: Locale code

        Returns:
            Immutable cache key tuple, or None if args contain unhashable values
        """
        # Convert args dict to sorted tuple of tuples
        if args is None:
            args_tuple: tuple[tuple[str, _FluentValue], ...] = ()
        else:
            try:
                # Sort by key for consistent hashing
                args_tuple = tuple(sorted(args.items()))
                hash(args_tuple)
            except TypeError:
                # Args contain unhashable values (lists, dicts, etc.)
                return None

        return (message_id, args_tuple, attribute, locale_code)

    def __len__(self) -> int:
        """Get current cache size.

        Thread-safe.

        Returns:
            Number of entries in cache
        """
        with self._lock:
            return len(self._cache)

    @property
    def maxsize(self) -> int:
        """Maximum cache size."""
        return self._maxsize

    @property
    def hits(self) -> int:
        """Number of cache hits.

        Thread-safe.
        """
        with self._lock:
            return self._hits

    @property
    def misses(self) -> int:
        """Number of cache misses.

        Thread-safe.
        """
        with self._lock:
            return self._misses

    @property
    def unhashable_skips(self) -> int:
        """Number of operations skipped due to unhashable args.

        Thread-safe.
        """
        with self._lock:
            return self._unhashable_skips
