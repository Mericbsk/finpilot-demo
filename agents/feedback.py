"""Inter-agent feedback mechanism.

Agents can emit feedback messages to one another via Redis queues.
Each agent has a dedicated list: ``finpilot:feedback:{agent_name}``.

Usage::

    from agents.feedback import emit_feedback, get_feedback

    # PerformanceMonitor tells Backtest that win-rate is low
    emit_feedback(
        from_agent="performance_monitor",
        to_agent="backtest",
        feedback_type="low_win_rate",
        data={"win_rate": 38.0, "recommendation": "switch to trend strategy"},
    )

    # Backtest reads its own feedback queue
    messages = get_feedback("backtest", limit=5)
    for msg in messages:
        print(msg["feedback_type"], msg["data"])

Keys are capped at MAX_QUEUE=50 and expire after TTL_SECONDS=86400 (24 h).
Falls back to in-memory when Redis is unavailable.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

_redis_client = None
_redis_unavailable = False

FEEDBACK_KEY_PREFIX = "finpilot:feedback:"
MAX_QUEUE = 50
TTL_SECONDS = 86400  # 24 hours — keep cross-agent feedback for a full day

# In-memory fallback — keyed by agent name
_mem_queues: dict[str, list[dict]] = {}


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
        client.ping()
        _redis_client = client
        return _redis_client
    except Exception as exc:
        logger.warning(
            "Feedback: Redis UNAVAILABLE (%s) — falling back to in-memory. "
            "Cross-agent feedback will be LOST on restart. Set REDIS_URL and start redis.",
            exc,
        )
        _redis_unavailable = True
        return None


def emit_feedback(
    from_agent: str,
    to_agent: str,
    feedback_type: str,
    data: dict[str, Any] | None = None,
) -> None:
    """Push a feedback message to the target agent's queue.

    Args:
        from_agent: Name of the sending agent (e.g. "performance_monitor").
        to_agent:   Name of the receiving agent (e.g. "backtest").
        feedback_type: Short label describing the feedback (e.g. "low_win_rate").
        data:       Optional payload dict with details.
    """
    message: dict[str, Any] = {
        "from": from_agent,
        "to": to_agent,
        "feedback_type": feedback_type,
        "data": data or {},
        "ts": int(time.time() * 1000),
    }

    r = _get_redis()
    key = f"{FEEDBACK_KEY_PREFIX}{to_agent}"

    if r is not None:
        try:
            pipe = r.pipeline()
            pipe.lpush(key, json.dumps(message))
            pipe.ltrim(key, 0, MAX_QUEUE - 1)
            pipe.expire(key, TTL_SECONDS)
            pipe.execute()
            return
        except Exception as exc:
            logger.debug("Feedback emit_feedback Redis error: %s", exc)

    queue = _mem_queues.setdefault(to_agent, [])
    queue.insert(0, message)
    if len(queue) > MAX_QUEUE:
        queue.pop()


def get_feedback(agent_name: str, limit: int = 10) -> list[dict]:
    """Return (and consume) up to *limit* feedback messages for the given agent.

    Messages are returned newest-first and removed from the queue.
    """
    r = _get_redis()
    key = f"{FEEDBACK_KEY_PREFIX}{agent_name}"

    if r is not None:
        try:
            # LRANGE then LTRIM to atomically pop the oldest items
            raw = r.lrange(key, 0, limit - 1)
            if raw:
                r.ltrim(key, len(raw), -1)
            return [json.loads(item) for item in raw]
        except Exception as exc:
            logger.debug("Feedback get_feedback Redis error: %s", exc)

    queue = _mem_queues.get(agent_name, [])
    messages = queue[:limit]
    _mem_queues[agent_name] = queue[limit:]
    return messages


def peek_feedback(agent_name: str, limit: int = 10) -> list[dict]:
    """Return up to *limit* feedback messages WITHOUT consuming them."""
    r = _get_redis()
    key = f"{FEEDBACK_KEY_PREFIX}{agent_name}"

    if r is not None:
        try:
            raw = r.lrange(key, 0, limit - 1)
            return [json.loads(item) for item in raw]
        except Exception as exc:
            logger.debug("Feedback peek_feedback Redis error: %s", exc)

    return _mem_queues.get(agent_name, [])[:limit]


def clear_feedback(agent_name: str) -> None:
    """Delete all pending feedback messages for the given agent."""
    r = _get_redis()
    key = f"{FEEDBACK_KEY_PREFIX}{agent_name}"

    if r is not None:
        try:
            r.delete(key)
            return
        except Exception as exc:
            logger.debug("Feedback clear_feedback Redis error: %s", exc)

    _mem_queues[agent_name] = []


def feedback_queue_length(agent_name: str) -> int:
    """Return the number of pending feedback messages for the given agent."""
    r = _get_redis()
    key = f"{FEEDBACK_KEY_PREFIX}{agent_name}"

    if r is not None:
        try:
            return r.llen(key)
        except Exception:
            pass

    return len(_mem_queues.get(agent_name, []))
