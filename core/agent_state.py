"""Shared agent state store — bridges CEO Graph results into Scheduler pipeline.

Problem solved:
    CEO Graph (scan→analyze→risk→alert) and Scheduler Pipeline
    (market_intel→research→backtest→monitor) run independently on the same
    symbols with no shared context.  This module provides a lightweight
    shared state layer so both pipelines can exchange results.

Storage: Redis (key-value, TTL=3600s) with in-memory fallback.

Usage::

    from core.agent_state import save_agent_result, get_agent_result, get_latest_scan

    # In CEO graph / agent run endpoint:
    save_agent_result("scan", symbols=["THYAO.IS"], data=scan_results)
    save_agent_result("analyze", symbols=["THYAO.IS"], data=analyze_results)

    # In Scheduler pipeline (research step):
    latest = get_latest_scan(symbols)  # dict or None
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Backend selection (Redis → in-memory fallback)
# ---------------------------------------------------------------------------

_TTL = 3600  # seconds — 1 hour window matches default scheduler interval
_mem_store: dict[str, tuple[float, Any]] = {}  # key → (expires_at, value)

try:
    import redis as _redis_lib  # type: ignore[import-not-found]

    _redis: _redis_lib.Redis | None = _redis_lib.Redis(
        host="localhost", port=6379, decode_responses=True, socket_connect_timeout=1
    )
    _redis.ping()
    logger.info("agent_state: Redis backend active")
except Exception:
    _redis = None
    logger.info("agent_state: in-memory fallback active")


def _key(agent: str, symbols: list[str]) -> str:
    sym_hash = ",".join(sorted(symbols))
    return f"finpilot:agent_state:{agent}:{sym_hash}"


def _mem_get(key: str) -> Any | None:
    entry = _mem_store.get(key)
    if entry is None:
        return None
    expires_at, value = entry
    if time.time() > expires_at:
        _mem_store.pop(key, None)
        return None
    return value


def _mem_set(key: str, value: Any) -> None:
    _mem_store[key] = (time.time() + _TTL, value)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def save_agent_result(
    agent_name: str,
    symbols: list[str],
    data: dict[str, Any],
) -> None:
    """Persist an agent result so other pipeline stages can read it.

    Args:
        agent_name: e.g. ``"scan"``, ``"analyze"``, ``"market_intel"``
        symbols: list of ticker symbols this result covers
        data: the result payload (must be JSON-serialisable)
    """
    key = _key(agent_name, symbols)
    payload = json.dumps({"agent": agent_name, "symbols": symbols, "ts": time.time(), "data": data})
    try:
        if _redis is not None:
            _redis.setex(key, _TTL, payload)
        else:
            _mem_set(key, payload)
        logger.debug("agent_state: saved %s for %s", agent_name, symbols)
    except Exception as exc:
        logger.warning("agent_state: save failed for %s: %s", agent_name, exc)


def get_agent_result(
    agent_name: str,
    symbols: list[str],
) -> dict[str, Any] | None:
    """Retrieve the latest cached result for *agent_name* + *symbols*.

    Returns the ``data`` dict or ``None`` if not found / expired.
    """
    key = _key(agent_name, symbols)
    try:
        raw: str | None
        if _redis is not None:
            raw = _redis.get(key)
        else:
            raw = _mem_get(key)
        if raw is None:
            return None
        return json.loads(raw).get("data")
    except Exception as exc:
        logger.warning("agent_state: get failed for %s: %s", agent_name, exc)
        return None


def get_latest_scan(symbols: list[str]) -> dict[str, Any] | None:
    """Return the most recent CEO scan results for *symbols* (or None)."""
    return get_agent_result("scan", symbols)


def get_latest_analysis(symbols: list[str]) -> dict[str, Any] | None:
    """Return the most recent CEO analysis results for *symbols* (or None)."""
    return get_agent_result("analyze", symbols)
