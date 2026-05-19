"""Agent event log — Redis-backed activity stream.

Every time an agent completes a task, call ``log_event()`` to persist
a lightweight record.  The Agent Hub frontend polls ``get_recent_events()``
every 5 seconds to power the live activity feed.

Events are stored in a Redis list (LPUSH / LTRIM) capped at MAX_EVENTS=200.
If Redis is unavailable the module silently no-ops so agents still run.
"""

from __future__ import annotations

import json
import logging
import time

logger = logging.getLogger(__name__)

_redis_client = None
_redis_unavailable = False  # flip once to avoid repeated connection noise

EVENTS_KEY = "finpilot:agent_events"
MAX_EVENTS = 200


def _get_redis():
    global _redis_client, _redis_unavailable
    if _redis_unavailable:
        return None
    if _redis_client is not None:
        return _redis_client
    try:
        import redis  # type: ignore

        from core.config import get_settings

        url = get_settings().redis_url
        client = redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=2)
        client.ping()  # verify connectivity immediately
        _redis_client = client
        logger.info("Agent event log connected to Redis at %s", url)
        return _redis_client
    except Exception as exc:
        logger.debug("Agent event log: Redis unavailable (%s) — events will not be persisted", exc)
        _redis_unavailable = True
        return None


def log_event(
    agent_name: str,
    task: str,
    status: str,  # "ok" | "error" | "running"
    duration_ms: float = 0.0,
    output_summary: str = "",
    symbols: list[str] | None = None,
    layer: str = "",
) -> None:
    """Append a single agent-run event to the Redis stream.

    Silently discards the event if Redis is unavailable.
    """
    event: dict = {
        "ts": int(time.time() * 1000),  # epoch-ms for easy JS Date parsing
        "agent": agent_name,
        "task": task,
        "status": status,
        "duration_ms": round(duration_ms, 1),
        "summary": (output_summary or "")[:200],
        "symbols": (symbols or [])[:10],
        "layer": layer,
    }
    r = _get_redis()
    if r is None:
        return
    try:
        pipe = r.pipeline()
        pipe.lpush(EVENTS_KEY, json.dumps(event))
        pipe.ltrim(EVENTS_KEY, 0, MAX_EVENTS - 1)
        pipe.execute()
    except Exception as exc:
        logger.debug("Event log write failed: %s", exc)


def get_recent_events(limit: int = 50) -> list[dict]:
    """Return the ``limit`` most-recent events, newest first."""
    r = _get_redis()
    if r is None:
        return []
    try:
        raw = r.lrange(EVENTS_KEY, 0, min(limit, MAX_EVENTS) - 1)
        return [json.loads(item) for item in raw]
    except Exception as exc:
        logger.debug("Event log read failed: %s", exc)
        return []


def clear_events() -> None:
    """Delete all stored events (useful for testing)."""
    r = _get_redis()
    if r is None:
        return
    try:
        r.delete(EVENTS_KEY)
    except Exception:
        pass
