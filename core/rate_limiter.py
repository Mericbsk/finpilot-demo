"""Token bucket rate limiter — Sprint 4.

In-process token bucket implementation. Use one bucket per resource (e.g.
per LLM provider, per data API). Thread-safe.

Public API::

    bucket = TokenBucket(rate=5, capacity=10)   # 5 tokens/sec, burst 10
    if bucket.acquire():
        do_work()
    else:
        sleep_or_skip()

    # Or block until available (with timeout):
    bucket.wait(timeout=30.0)

A small registry exposes named buckets so the same limit is shared across
call sites in the same process::

    from core.rate_limiter import get_bucket
    bucket = get_bucket("llm:groq", rate=5, capacity=10)
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Final

logger = logging.getLogger(__name__)


class TokenBucket:
    """Thread-safe token bucket rate limiter."""

    __slots__ = ("_rate", "_capacity", "_tokens", "_last", "_lock", "name")

    def __init__(self, rate: float, capacity: float, name: str = "bucket"):
        if rate <= 0 or capacity <= 0:
            raise ValueError("rate and capacity must be > 0")
        self._rate: Final = float(rate)
        self._capacity: Final = float(capacity)
        self._tokens = float(capacity)
        self._last = time.monotonic()
        self._lock = threading.Lock()
        self.name = name

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last
        if elapsed > 0:
            self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
            self._last = now

    def acquire(self, tokens: float = 1.0) -> bool:
        """Try to take ``tokens`` immediately. Returns True on success."""
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def wait(self, tokens: float = 1.0, timeout: float | None = None) -> bool:
        """Block until ``tokens`` are available or ``timeout`` elapses."""
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            with self._lock:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True
                deficit = tokens - self._tokens
                wait_for = deficit / self._rate
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                wait_for = min(wait_for, remaining)
            time.sleep(min(wait_for, 1.0))

    @property
    def available(self) -> float:
        with self._lock:
            self._refill()
            return self._tokens


_buckets: dict[str, TokenBucket] = {}
_registry_lock = threading.Lock()


def get_bucket(name: str, rate: float = 5.0, capacity: float = 10.0) -> TokenBucket:
    """Return a process-wide named bucket (creates one on first use).

    The first call defines the (rate, capacity) for that name; subsequent
    calls return the existing bucket and ignore the parameters.
    """
    with _registry_lock:
        bucket = _buckets.get(name)
        if bucket is None:
            bucket = TokenBucket(rate=rate, capacity=capacity, name=name)
            _buckets[name] = bucket
            logger.debug("rate_limiter: created bucket %s rate=%.2f cap=%.2f", name, rate, capacity)
        return bucket


def reset_buckets() -> None:
    """Clear all named buckets (test hook)."""
    with _registry_lock:
        _buckets.clear()


__all__ = ["TokenBucket", "get_bucket", "reset_buckets"]
