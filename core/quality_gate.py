"""FinPilot Quality Gate — degraded-mode flag.

When the autonomous eval harness reports ``overall_pass=False`` the system
enters a *degraded* state. While degraded:

  * Scheduler still runs cycles (so we keep collecting KPIs / outcomes)
  * New BUY signal alerts are suppressed (Telegram + agents.alert_agent)
  * UI / API can expose the flag for transparency

Redis is the source of truth (cross-process), with an in-memory fallback.
Manual override env var ``CLEAR_DEGRADED=1`` clears the flag on every read.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

_FLAG_KEY = "finpilot:quality_gate:degraded"
_TTL_SECONDS = 24 * 3600  # auto-recover after 24h with no eval pass refresh

_redis_client = None
_redis_unavailable = False
_mem_flag: dict[str, Any] | None = None


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
        logger.debug("quality_gate: Redis unavailable (%s) — in-memory only", exc)
        _redis_unavailable = True
        return None


def set_degraded(reason: str, eval_report: dict[str, Any] | None = None) -> None:
    """Mark the system as degraded. Idempotent: only updates timestamp."""
    global _mem_flag
    payload = {
        "reason": reason,
        "ts": int(time.time()),
        "eval_summary": {
            "overall_pass": (eval_report or {}).get("overall_pass"),
            "metrics": (eval_report or {}).get("metrics", {}),
        },
    }
    r = _get_redis()
    if r is not None:
        try:
            r.set(_FLAG_KEY, json.dumps(payload), ex=_TTL_SECONDS)
        except Exception as exc:
            logger.debug("quality_gate.set_degraded redis error: %s", exc)
    _mem_flag = payload
    logger.warning("Quality gate DEGRADED: %s", reason)


def clear_degraded() -> bool:
    """Clear the degraded flag. Returns True if a flag was cleared."""
    global _mem_flag
    cleared = False
    r = _get_redis()
    if r is not None:
        try:
            cleared = bool(r.delete(_FLAG_KEY))
        except Exception:
            pass
    if _mem_flag is not None:
        cleared = True
        _mem_flag = None
    if cleared:
        logger.info("Quality gate cleared — back to normal")
    return cleared


def get_status() -> dict[str, Any]:
    """Return current quality-gate status."""
    if os.getenv("CLEAR_DEGRADED") == "1":
        clear_degraded()
    r = _get_redis()
    payload: dict[str, Any] | None = None
    if r is not None:
        try:
            raw = r.get(_FLAG_KEY)
            if raw:
                payload = json.loads(raw)
        except Exception:
            payload = None
    if payload is None:
        payload = _mem_flag
    if payload is None:
        return {"degraded": False, "reason": None, "since": None}
    return {
        "degraded": True,
        "reason": payload.get("reason"),
        "since": payload.get("ts"),
        "eval_summary": payload.get("eval_summary", {}),
    }


def is_degraded() -> bool:
    """Convenience boolean check."""
    return get_status()["degraded"]
