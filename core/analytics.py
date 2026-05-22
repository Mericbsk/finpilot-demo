"""FinPilot Analytics — lightweight event counters backed by Redis.

Tracks user behaviour without third-party SDKs.  All counters persist in
Redis as a single hash and fall back to in-memory when Redis is unavailable.

Counter names
-------------
``page_view:<path>``       — HTTP request to a frontend page path
``event:<event_name>``     — named application event (champion_edge_query, scan_run, …)

Usage::

    from core.analytics import increment_page_view, increment_event, get_summary

    increment_page_view("/dashboard")
    increment_event("champion_edge_query")
    increment_event("scan_run")
    summary = get_summary()
"""

from __future__ import annotations

import logging
import threading
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Redis / in-memory counter store
# ---------------------------------------------------------------------------

_REDIS_KEY = "finpilot:analytics:counters"

_lock = threading.Lock()
_mem_counters: dict[str, int] = defaultdict(int)

_redis_client: Any = None
_redis_unavailable: bool = False


def _get_redis() -> Any | None:
    global _redis_client, _redis_unavailable
    if _redis_unavailable:
        return None
    if _redis_client is not None:
        return _redis_client
    try:
        import redis as _redis

        url = __import__("os").environ.get("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = _redis.from_url(url, socket_connect_timeout=1, socket_timeout=1)
        _redis_client.ping()
        return _redis_client
    except Exception as exc:
        logger.debug("Analytics: Redis unavailable (%s) — using in-memory counters", exc)
        _redis_unavailable = True
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def increment_page_view(path: str) -> None:
    """Increment the page-view counter for *path*."""
    _increment(f"page_view:{path}")


def increment_event(event: str) -> None:
    """Increment a named application event counter."""
    _increment(f"event:{event}")


def _increment(key: str) -> None:
    client = _get_redis()
    if client is not None:
        try:
            client.hincrby(_REDIS_KEY, key, 1)
            return
        except Exception as exc:
            logger.debug("Analytics: Redis HINCRBY failed (%s) — falling back", exc)
    with _lock:
        _mem_counters[key] += 1


def get_summary() -> dict[str, Any]:
    """Return all counters grouped by type.

    Returns::

        {
            "page_views": {"/dashboard": 42, ...},
            "events":     {"champion_edge_query": 5, "scan_run": 3, ...},
        }
    """
    raw = _get_raw_counters()
    page_views: dict[str, int] = {}
    events: dict[str, int] = {}

    for key, val in raw.items():
        count = int(val)
        if key.startswith("page_view:"):
            page_views[key[len("page_view:"):]] = count
        elif key.startswith("event:"):
            events[key[len("event:"):]] = count

    return {"page_views": page_views, "events": events}


def _get_raw_counters() -> dict[str, Any]:
    client = _get_redis()
    if client is not None:
        try:
            raw = client.hgetall(_REDIS_KEY)
            return {k.decode() if isinstance(k, bytes) else k:
                    v.decode() if isinstance(v, bytes) else v
                    for k, v in raw.items()}
        except Exception as exc:
            logger.debug("Analytics: Redis HGETALL failed (%s) — using in-memory", exc)
    with _lock:
        return dict(_mem_counters)
