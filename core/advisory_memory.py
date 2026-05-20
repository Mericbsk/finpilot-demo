"""Advisory sliding-window chat memory — Sprint 3.

Persists the last N messages per (advisor, user) tuple in Redis using a LIST
data structure (LPUSH + LTRIM = O(1) sliding window). Falls back to in-memory
when Redis is unavailable.

Usage::

    from core.advisory_memory import append_message, get_history

    append_message("cto", user_id="u1", role="user", content="Best DB?")
    append_message("cto", user_id="u1", role="assistant", content="Postgres.")
    history = get_history("cto", user_id="u1", limit=10)
    # → [{"role":"user","content":"Best DB?","ts":...},
    #    {"role":"assistant","content":"Postgres.","ts":...}]
"""

from __future__ import annotations

import json
import logging
import time
from collections import deque
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_LIMIT = 10
_TTL_SECONDS = 7 * 24 * 3600  # 1 week
_KEY_PREFIX = "finpilot:advisory:history"

_redis: Any | None = None
try:
    import redis as _redis_lib  # type: ignore[import-not-found]

    from core.config import get_settings

    _url = get_settings().redis_url
    _redis = _redis_lib.Redis.from_url(_url, decode_responses=True, socket_connect_timeout=2)
    _redis.ping()
    logger.info("advisory_memory: Redis backend active (%s)", _url)
except Exception as exc:  # noqa: BLE001
    _redis = None
    logger.warning("advisory_memory: Redis unavailable (%s) — in-memory fallback", exc)

_mem_store: dict[str, deque[str]] = {}


def _key(advisor: str, user_id: str) -> str:
    return f"{_KEY_PREFIX}:{advisor.lower()}:{user_id}"


def append_message(
    advisor: str,
    user_id: str,
    role: str,
    content: str,
    *,
    limit: int = _DEFAULT_LIMIT,
    extra: dict[str, Any] | None = None,
) -> None:
    """Append a message to the (advisor,user) sliding window.

    Args:
        advisor: advisor agent key (e.g. "cto", "cpo")
        user_id: opaque user identifier (anonymous="anon" allowed)
        role: "user" | "assistant" | "system"
        content: message body
        limit: keep at most this many messages (oldest dropped)
        extra: optional metadata merged into the stored entry
    """
    if not advisor or not user_id or not content:
        return
    payload = {"role": role, "content": content, "ts": time.time()}
    if extra:
        payload.update(extra)
    raw = json.dumps(payload, ensure_ascii=False)
    key = _key(advisor, user_id)
    try:
        if _redis is not None:
            pipe = _redis.pipeline()
            pipe.lpush(key, raw)
            pipe.ltrim(key, 0, limit - 1)
            pipe.expire(key, _TTL_SECONDS)
            pipe.execute()
        else:
            dq = _mem_store.setdefault(key, deque(maxlen=limit))
            dq.appendleft(raw)
    except Exception as exc:  # noqa: BLE001
        logger.warning("advisory_memory: append failed (%s): %s", key, exc)


def get_history(
    advisor: str,
    user_id: str,
    *,
    limit: int = _DEFAULT_LIMIT,
    chronological: bool = True,
) -> list[dict[str, Any]]:
    """Return up to ``limit`` recent messages for (advisor,user).

    Args:
        chronological: True → oldest-first; False → newest-first.
    """
    if not advisor or not user_id:
        return []
    key = _key(advisor, user_id)
    try:
        if _redis is not None:
            raw_items = _redis.lrange(key, 0, limit - 1)
        else:
            raw_items = list(_mem_store.get(key, deque()))[:limit]
    except Exception as exc:  # noqa: BLE001
        logger.warning("advisory_memory: get failed (%s): %s", key, exc)
        return []

    items: list[dict[str, Any]] = []
    for raw in raw_items:
        try:
            items.append(json.loads(raw))
        except Exception:  # noqa: BLE001, S110
            continue
    if chronological:
        items.reverse()  # LPUSH stores newest at index 0
    return items


def clear_history(advisor: str, user_id: str) -> bool:
    """Delete the conversation history for (advisor,user). Returns success."""
    key = _key(advisor, user_id)
    try:
        if _redis is not None:
            _redis.delete(key)
        else:
            _mem_store.pop(key, None)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("advisory_memory: clear failed (%s): %s", key, exc)
        return False


def format_history_as_context(history: list[dict[str, Any]]) -> str:
    """Render history into a plain-text block for LLM context injection."""
    if not history:
        return ""
    lines: list[str] = ["Önceki konuşma özeti:"]
    for msg in history:
        role = msg.get("role", "?").upper()
        content = msg.get("content", "")
        lines.append(f"[{role}] {content}")
    return "\n".join(lines)
