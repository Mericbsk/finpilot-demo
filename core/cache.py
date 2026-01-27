"""
FinPilot Cache Manager
======================

Multi-layer cache sistemi:
- L1: Memory cache (LRU, hızlı, kısa TTL)
- L2: Redis cache (opsiyonel, uzun TTL, distributed)

Kullanım:
    from core.cache import cache_manager, cached

    # Decorator ile
    @cached(ttl=300, prefix="market")
    def get_stock_data(ticker: str) -> pd.DataFrame:
        ...

    # Manuel kullanım
    cache_manager.set("key", value, ttl=3600)
    value = cache_manager.get("key")

Author: FinPilot Team
Version: 1.0.0

SECURITY NOTE:
    This module uses JSON for serialization instead of pickle
    to prevent Remote Code Execution (RCE) vulnerabilities.
    Complex objects (DataFrames, numpy arrays) are converted
    to safe representations before caching.
"""

from __future__ import annotations

import functools
import hashlib
import json
import threading
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Generic, Optional, ParamSpec, TypeVar

if TYPE_CHECKING:
    import redis as redis_lib

P = ParamSpec("P")
T = TypeVar("T")


# =============================================================================
# SAFE SERIALIZATION (NO PICKLE!)
# =============================================================================


class SafeSerializer:
    """
    JSON-based serializer that safely handles common data types.

    SECURITY: Never uses pickle to prevent RCE attacks.

    Supported types:
    - Primitives: str, int, float, bool, None
    - Collections: list, dict, tuple, set
    - DateTime: datetime, date
    - Pandas: DataFrame, Series (converted to dict)
    - Numpy: ndarray (converted to list)
    """

    @staticmethod
    def serialize(value: Any) -> str:
        """Serialize value to JSON string safely."""
        return json.dumps(SafeSerializer._to_serializable(value))

    @staticmethod
    def deserialize(data: str) -> Any:
        """Deserialize JSON string to value safely."""
        parsed = json.loads(data)
        return SafeSerializer._from_serializable(parsed)

    @staticmethod
    def _to_serializable(obj: Any) -> Any:
        """Convert object to JSON-serializable format."""
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj

        if isinstance(obj, (list, tuple)):
            return {
                "__type__": "list" if isinstance(obj, list) else "tuple",
                "data": [SafeSerializer._to_serializable(item) for item in obj],
            }

        if isinstance(obj, set):
            return {
                "__type__": "set",
                "data": [SafeSerializer._to_serializable(item) for item in obj],
            }

        if isinstance(obj, dict):
            return {
                "__type__": "dict",
                "data": {str(k): SafeSerializer._to_serializable(v) for k, v in obj.items()},
            }

        if isinstance(obj, datetime):
            return {"__type__": "datetime", "data": obj.isoformat()}

        # Handle pandas DataFrame
        try:
            import pandas as pd

            if isinstance(obj, pd.DataFrame):
                return {
                    "__type__": "dataframe",
                    "data": obj.to_dict(orient="split"),
                    "index_name": obj.index.name,
                }
            if isinstance(obj, pd.Series):
                return {"__type__": "series", "data": obj.to_dict(), "name": obj.name}
        except ImportError:
            pass

        # Handle numpy array
        try:
            import numpy as np

            if isinstance(obj, np.ndarray):
                return {"__type__": "ndarray", "data": obj.tolist(), "dtype": str(obj.dtype)}
            if isinstance(obj, (np.integer, np.floating)):
                return float(obj)
        except ImportError:
            pass

        # Fallback: try to convert to dict or string
        if hasattr(obj, "__dict__"):
            return {
                "__type__": "object",
                "class": obj.__class__.__name__,
                "data": SafeSerializer._to_serializable(obj.__dict__),
            }

        return str(obj)

    @staticmethod
    def _from_serializable(obj: Any) -> Any:
        """Convert JSON-parsed object back to original type."""
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj

        if not isinstance(obj, dict):
            return obj

        type_hint = obj.get("__type__")

        if type_hint is None:
            # Plain dict from JSON
            return obj

        data = obj.get("data")

        if type_hint == "list":
            if data is None:
                return []
            return [SafeSerializer._from_serializable(item) for item in data]

        if type_hint == "tuple":
            if data is None:
                return ()
            return tuple(SafeSerializer._from_serializable(item) for item in data)

        if type_hint == "set":
            if data is None:
                return set()
            return set(SafeSerializer._from_serializable(item) for item in data)

        if type_hint == "dict":
            if data is None:
                return {}
            return {k: SafeSerializer._from_serializable(v) for k, v in data.items()}

        if type_hint == "datetime":
            if data is None or not isinstance(data, str):
                return None
            return datetime.fromisoformat(data)

        if type_hint == "dataframe":
            try:
                import pandas as pd

                if data is None:
                    return pd.DataFrame()
                df = pd.DataFrame(**data)
                if obj.get("index_name"):
                    df.index.name = obj["index_name"]
                return df
            except ImportError:
                return data

        if type_hint == "series":
            try:
                import pandas as pd

                return pd.Series(data, name=obj.get("name"))
            except ImportError:
                return data

        if type_hint == "ndarray":
            try:
                import numpy as np

                return np.array(data, dtype=obj.get("dtype"))
            except ImportError:
                return data

        if type_hint == "object":
            return SafeSerializer._from_serializable(data)

        return data


# =============================================================================
# CACHE ENTRY
# =============================================================================


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with metadata."""

    value: T
    created_at: float
    ttl: Optional[float] = None
    hits: int = 0

    @property
    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    @property
    def age(self) -> float:
        return time.time() - self.created_at


# =============================================================================
# CACHE INTERFACE
# =============================================================================


class CacheBackend(ABC):
    """Cache backend abstract interface."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        pass

    @abstractmethod
    def clear(self) -> bool:
        """Clear all cache."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass

    @abstractmethod
    def get_stats(self) -> dict:
        """Get cache statistics."""
        pass


# =============================================================================
# MEMORY CACHE (L1)
# =============================================================================


class MemoryCache(CacheBackend):
    """
    Thread-safe in-memory LRU cache.

    Features:
    - LRU eviction
    - TTL support
    - Thread-safe
    - Size limit
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            entry = self._cache[key]

            # Check expiration
            if entry.is_expired:
                del self._cache[key]
                self._misses += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.hits += 1
            self._hits += 1

            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        with self._lock:
            # Evict if at capacity
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)

            self._cache[key] = CacheEntry(
                value=value,
                created_at=time.time(),
                ttl=ttl or self.default_ttl,
            )
            return True

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> bool:
        with self._lock:
            self._cache.clear()
            return True

    def exists(self, key: str) -> bool:
        with self._lock:
            if key not in self._cache:
                return False
            entry = self._cache[key]
            if entry.is_expired:
                del self._cache[key]
                return False
            return True

    def get_stats(self) -> dict:
        with self._lock:
            total = self._hits + self._misses
            return {
                "type": "memory",
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": self._hits / total if total > 0 else 0,
            }

    def cleanup_expired(self) -> int:
        """Remove all expired entries."""
        with self._lock:
            expired_keys = [k for k, v in self._cache.items() if v.is_expired]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)


# =============================================================================
# REDIS CACHE (L2)
# =============================================================================


class RedisCache(CacheBackend):
    """
    Redis cache backend (L2).

    Features:
    - Distributed cache
    - Persistence
    - Longer TTL
    """

    def __init__(self, url: str = "redis://localhost:6379/0", default_ttl: int = 3600):
        self.url = url
        self.default_ttl = default_ttl
        self._client = None
        self._enabled = False
        self._connect()

    def _connect(self) -> None:
        """Try to connect to Redis."""
        import logging

        logger = logging.getLogger(__name__)

        try:
            import redis  # type: ignore[import-not-found]

            self._client = redis.from_url(self.url)
            self._client.ping()
            self._enabled = True
            logger.info(f"Redis connected: {self.url.split('@')[-1]}")
        except ImportError:
            self._enabled = False
            self._client = None
            logger.warning(
                "Redis package not installed. Cache running in memory-only mode. "
                "Install with: pip install -r requirements-observability.txt"
            )
        except Exception as e:
            self._enabled = False
            self._client = None
            logger.warning(f"Redis connection failed: {e}. Cache running in memory-only mode.")

    @property
    def is_connected(self) -> bool:
        return self._enabled and self._client is not None

    def get(self, key: str) -> Optional[Any]:
        if not self.is_connected or self._client is None:
            return None
        try:
            data = self._client.get(key)
            if data is None:
                return None
            # SECURITY: Use safe JSON deserialization instead of pickle
            return SafeSerializer.deserialize(data.decode("utf-8"))
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        if not self.is_connected or self._client is None:
            return False
        try:
            # SECURITY: Use safe JSON serialization instead of pickle
            data = SafeSerializer.serialize(value)
            self._client.setex(key, ttl or self.default_ttl, data)
            return True
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        if not self.is_connected or self._client is None:
            return False
        try:
            return bool(self._client.delete(key))
        except Exception:
            return False

    def clear(self) -> bool:
        if not self.is_connected or self._client is None:
            return False
        try:
            self._client.flushdb()
            return True
        except Exception:
            return False

    def exists(self, key: str) -> bool:
        if not self.is_connected or self._client is None:
            return False
        try:
            return bool(self._client.exists(key))
        except Exception:
            return False

    def get_stats(self) -> dict:
        if not self.is_connected or self._client is None:
            return {"type": "redis", "connected": False}
        try:
            info = self._client.info("stats")
            return {
                "type": "redis",
                "connected": True,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "keys": self._client.dbsize(),
            }
        except Exception:
            return {"type": "redis", "connected": False}


# =============================================================================
# MULTI-LAYER CACHE MANAGER
# =============================================================================


class CacheManager:
    """
    Multi-layer cache manager.

    L1: Memory (fast, small, short TTL)
    L2: Redis (slower, large, long TTL)

    Usage:
        cache = CacheManager()

        # Set with automatic L1+L2
        cache.set("key", value, ttl=3600)

        # Get (checks L1 first, then L2)
        value = cache.get("key")

        # With prefix/namespace
        cache.set("market:AAPL:price", 150.0)
    """

    def __init__(
        self,
        memory_max_size: int = 1000,
        memory_ttl: int = 300,
        redis_url: Optional[str] = None,
        redis_ttl: int = 3600,
    ):
        # L1: Memory cache
        self._l1 = MemoryCache(max_size=memory_max_size, default_ttl=memory_ttl)

        # L2: Redis cache (optional)
        self._l2: Optional[RedisCache] = None
        if redis_url:
            self._l2 = RedisCache(url=redis_url, default_ttl=redis_ttl)

        self._l1_ttl = memory_ttl
        self._l2_ttl = redis_ttl

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.

        Checks L1 first, then L2. If found in L2 but not L1,
        promotes to L1.
        """
        # Check L1
        value = self._l1.get(key)
        if value is not None:
            return value

        # Check L2
        if self._l2 and self._l2.is_connected:
            value = self._l2.get(key)
            if value is not None:
                # Promote to L1
                self._l1.set(key, value)
                return value

        return default

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        l1_only: bool = False,
        l2_only: bool = False,
    ) -> bool:
        """Set value in cache."""
        success = True

        # Set in L1
        if not l2_only:
            l1_ttl = min(ttl or self._l1_ttl, self._l1_ttl)
            success = self._l1.set(key, value, l1_ttl) and success

        # Set in L2
        if not l1_only and self._l2 and self._l2.is_connected:
            l2_ttl = ttl or self._l2_ttl
            success = self._l2.set(key, value, l2_ttl) and success

        return success

    def delete(self, key: str) -> bool:
        """Delete from all cache layers."""
        success = self._l1.delete(key)
        if self._l2:
            success = self._l2.delete(key) or success
        return success

    def clear(self, l1_only: bool = False) -> bool:
        """Clear cache."""
        success = self._l1.clear()
        if not l1_only and self._l2:
            success = self._l2.clear() and success
        return success

    def exists(self, key: str) -> bool:
        """Check if key exists in any layer."""
        if self._l1.exists(key):
            return True
        if self._l2 and self._l2.is_connected:
            return self._l2.exists(key)
        return False

    def get_or_set(
        self,
        key: str,
        factory: Callable[[], T],
        ttl: Optional[int] = None,
    ) -> T:
        """Get from cache or compute and cache."""
        value = self.get(key)
        if value is not None:
            return value

        value = factory()
        self.set(key, value, ttl)
        return value

    def get_stats(self) -> dict:
        """Get cache statistics."""
        stats = {
            "l1": self._l1.get_stats(),
            "l2": self._l2.get_stats() if self._l2 else None,
        }
        return stats

    def cleanup(self) -> dict:
        """Cleanup expired entries."""
        result = {
            "l1_cleaned": self._l1.cleanup_expired(),
        }
        return result


# =============================================================================
# CACHE DECORATOR
# =============================================================================


def make_cache_key(
    prefix: str,
    func_name: str,
    args: tuple,
    kwargs: dict,
) -> str:
    """Generate cache key from function call."""
    # Create a hashable representation
    key_parts = [prefix, func_name]

    for arg in args:
        try:
            key_parts.append(str(arg))
        except Exception:
            key_parts.append(str(id(arg)))

    for k, v in sorted(kwargs.items()):
        try:
            key_parts.append(f"{k}={v}")
        except Exception:
            key_parts.append(f"{k}={id(v)}")

    key_str = ":".join(key_parts)

    # Hash if too long (not for security, just for key shortening)
    if len(key_str) > 200:
        hash_suffix = hashlib.md5(key_str.encode(), usedforsecurity=False).hexdigest()[:16]
        key_str = f"{prefix}:{func_name}:{hash_suffix}"

    return key_str


def cached(
    ttl: int = 300,
    prefix: str = "cache",
    key_builder: Optional[Callable[..., str]] = None,
    skip_cache_if: Optional[Callable[..., bool]] = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Cache decorator.

    Args:
        ttl: Time to live in seconds
        prefix: Cache key prefix
        key_builder: Custom key builder function
        skip_cache_if: Function that returns True to skip caching

    Usage:
        @cached(ttl=300, prefix="market")
        def get_stock_data(ticker: str) -> pd.DataFrame:
            ...

        @cached(
            ttl=3600,
            key_builder=lambda ticker, **_: f"stock:{ticker}",
            skip_cache_if=lambda ticker: ticker == "TEST"
        )
        def fetch_data(ticker: str, force: bool = False) -> dict:
            ...
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Check if should skip cache
            if skip_cache_if and skip_cache_if(*args, **kwargs):
                return func(*args, **kwargs)

            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = make_cache_key(prefix, func.__name__, args, kwargs)

            # Try to get from cache
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Compute and cache
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)

            return result

        # Add cache control methods
        wrapper.cache_clear = lambda: cache_manager.clear()  # type: ignore
        wrapper.cache_key = lambda *a, **kw: (  # type: ignore
            key_builder(*a, **kw) if key_builder else make_cache_key(prefix, func.__name__, a, kw)
        )

        return wrapper

    return decorator


# =============================================================================
# SPECIALIZED CACHE DECORATORS
# =============================================================================


def cache_market_data(ttl: int = 60):
    """Cache decorator for market data (short TTL)."""
    return cached(ttl=ttl, prefix="market")


def cache_feature(ttl: int = 300):
    """Cache decorator for computed features."""
    return cached(ttl=ttl, prefix="feature")


def cache_model(ttl: int = 3600):
    """Cache decorator for model results."""
    return cached(ttl=ttl, prefix="model")


def cache_api(ttl: int = 60):
    """Cache decorator for API responses."""
    return cached(ttl=ttl, prefix="api")


# =============================================================================
# GLOBAL CACHE MANAGER
# =============================================================================

# Initialize global cache manager
# Will be configured with settings when imported
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create global cache manager."""
    global _cache_manager

    if _cache_manager is None:
        try:
            from core.config import settings

            _cache_manager = CacheManager(
                memory_max_size=settings.cache.memory_max_size,
                memory_ttl=settings.cache.memory_ttl_seconds,
                redis_url=settings.cache.redis_url if settings.cache.redis_enabled else None,
                redis_ttl=settings.cache.redis_ttl_seconds,
            )
        except ImportError:
            # Fallback to defaults
            _cache_manager = CacheManager()

    return _cache_manager


# Lazy-loaded global instance
class _CacheManagerProxy:
    """Lazy proxy for cache manager."""

    def __getattr__(self, name: str) -> Any:
        return getattr(get_cache_manager(), name)


cache_manager: CacheManager = _CacheManagerProxy()  # type: ignore


__all__ = [
    "CacheManager",
    "CacheEntry",
    "CacheBackend",
    "MemoryCache",
    "RedisCache",
    "cache_manager",
    "get_cache_manager",
    "cached",
    "cache_market_data",
    "cache_feature",
    "cache_model",
    "cache_api",
    "make_cache_key",
]
