"""FinPilot Paper Portfolio — Sprint 5 (S5-5).

Tracks a virtual portfolio so the closed loop can produce a real P&L number:

  open_position(signal_id, symbol, direction, entry_price)
       -> push to ``finpilot:paper:positions``
  close_position(signal_id, exit_price)
       -> compute pnl, append to ``finpilot:paper:closed`` and update equity

Equity time-series is appended on every close so the UI / weekly report
can draw a curve.

Redis is the source of truth, with an in-memory fallback for tests / no-redis
environments. JSON-on-disk snapshot at ``data/paper_portfolio.json`` is
written after every close for crash recovery.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_OPEN_KEY = "finpilot:paper:positions"
_CLOSED_KEY = "finpilot:paper:closed"
_EQUITY_KEY = "finpilot:paper:equity"
_SNAPSHOT = Path("data") / "paper_portfolio.json"

INITIAL_EQUITY = 10_000.0
UNIT_NOTIONAL = 1_000.0  # per-trade dollar sizing
MAX_HISTORY = 500

_redis_client = None
_redis_unavailable = False

# In-memory fallback
_mem_open: dict[str, dict[str, Any]] = {}  # keyed by signal_id
_mem_closed: list[dict[str, Any]] = []
_mem_equity: list[dict[str, Any]] = []  # [{ts, equity, pnl}, ...]


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
    except Exception:
        _redis_unavailable = True
        return None


def _now_ms() -> int:
    return int(time.time() * 1000)


def open_position(
    signal_id: str,
    symbol: str,
    direction: str,
    entry_price: float,
    score: float = 0.0,
    cycle: int = 0,
) -> dict[str, Any]:
    """Open a paper position. Idempotent on signal_id."""
    if entry_price <= 0:
        raise ValueError("entry_price must be positive")
    qty = UNIT_NOTIONAL / entry_price
    pos = {
        "signal_id": signal_id,
        "symbol": symbol,
        "direction": direction,
        "entry_price": round(float(entry_price), 6),
        "qty": round(qty, 6),
        "score": round(float(score), 2),
        "cycle": int(cycle),
        "opened_at": _now_ms(),
        "status": "open",
    }

    r = _get_redis()
    if r is not None:
        try:
            # idempotency: only HSETNX equivalent
            existing = r.hget(_OPEN_KEY, signal_id)
            if existing:
                return json.loads(existing)
            r.hset(_OPEN_KEY, signal_id, json.dumps(pos))
            return pos
        except Exception as exc:
            logger.debug("paper.open redis error: %s", exc)
    if signal_id in _mem_open:
        return _mem_open[signal_id]
    _mem_open[signal_id] = pos
    return pos


def close_position(signal_id: str, exit_price: float) -> dict[str, Any] | None:
    """Close an open position and append to history. Returns the closed record."""
    if exit_price <= 0:
        raise ValueError("exit_price must be positive")

    r = _get_redis()
    pos: dict[str, Any] | None = None
    if r is not None:
        try:
            raw = r.hget(_OPEN_KEY, signal_id)
            if raw:
                pos = json.loads(raw)
        except Exception as exc:
            logger.debug("paper.close redis read error: %s", exc)
    if pos is None:
        pos = _mem_open.get(signal_id)
    if pos is None:
        logger.debug("paper.close: signal_id %s has no open position", signal_id)
        return None

    direction = pos.get("direction", "BUY")
    qty = float(pos["qty"])
    entry = float(pos["entry_price"])
    sign = 1.0 if direction == "BUY" else -1.0
    pnl = sign * (float(exit_price) - entry) * qty
    pct = sign * (float(exit_price) - entry) / entry * 100.0

    closed = {
        **pos,
        "exit_price": round(float(exit_price), 6),
        "pnl": round(pnl, 4),
        "pnl_pct": round(pct, 4),
        "closed_at": _now_ms(),
        "status": "closed",
    }

    # update equity
    prev_equity = _last_equity()
    new_equity = round(prev_equity + pnl, 4)
    equity_point = {"ts": closed["closed_at"], "equity": new_equity, "pnl": closed["pnl"]}

    if r is not None:
        try:
            pipe = r.pipeline()
            pipe.hdel(_OPEN_KEY, signal_id)
            pipe.lpush(_CLOSED_KEY, json.dumps(closed))
            pipe.ltrim(_CLOSED_KEY, 0, MAX_HISTORY - 1)
            pipe.lpush(_EQUITY_KEY, json.dumps(equity_point))
            pipe.ltrim(_EQUITY_KEY, 0, MAX_HISTORY - 1)
            pipe.execute()
        except Exception as exc:
            logger.debug("paper.close redis write error: %s", exc)
    _mem_open.pop(signal_id, None)
    _mem_closed.insert(0, closed)
    if len(_mem_closed) > MAX_HISTORY:
        _mem_closed.pop()
    _mem_equity.insert(0, equity_point)
    if len(_mem_equity) > MAX_HISTORY:
        _mem_equity.pop()

    _persist_snapshot()
    return closed


def _last_equity() -> float:
    r = _get_redis()
    if r is not None:
        try:
            raw = r.lindex(_EQUITY_KEY, 0)
            if raw:
                return float(json.loads(raw)["equity"])
        except Exception:
            pass
    if _mem_equity:
        return float(_mem_equity[0]["equity"])
    return INITIAL_EQUITY


def get_open_positions() -> list[dict[str, Any]]:
    r = _get_redis()
    if r is not None:
        try:
            return [json.loads(v) for v in (r.hvals(_OPEN_KEY) or [])]
        except Exception:
            pass
    return list(_mem_open.values())


def get_closed_history(limit: int = 50) -> list[dict[str, Any]]:
    r = _get_redis()
    if r is not None:
        try:
            raw = r.lrange(_CLOSED_KEY, 0, limit - 1)
            return [json.loads(item) for item in raw]
        except Exception:
            pass
    return _mem_closed[:limit]


def get_equity_curve(limit: int = 100) -> list[dict[str, Any]]:
    r = _get_redis()
    if r is not None:
        try:
            raw = r.lrange(_EQUITY_KEY, 0, limit - 1)
            return [json.loads(item) for item in raw][::-1]  # ascending time
        except Exception:
            pass
    return _mem_equity[:limit][::-1]


def get_summary() -> dict[str, Any]:
    """Return a flat portfolio summary suitable for the API / UI."""
    closed = get_closed_history(limit=MAX_HISTORY)
    wins = [c for c in closed if c["pnl"] > 0]
    losses = [c for c in closed if c["pnl"] <= 0]
    gross_profit = sum(c["pnl"] for c in wins)
    gross_loss = abs(sum(c["pnl"] for c in losses))
    return {
        "equity": _last_equity(),
        "initial_equity": INITIAL_EQUITY,
        "total_return_pct": round(
            (_last_equity() - INITIAL_EQUITY) / INITIAL_EQUITY * 100.0, 3
        ),
        "open_positions": len(get_open_positions()),
        "closed_count": len(closed),
        "win_count": len(wins),
        "loss_count": len(losses),
        "win_rate": round(len(wins) / len(closed) * 100, 2) if closed else 0.0,
        "profit_factor": round(gross_profit / gross_loss, 3) if gross_loss > 0 else None,
        "last_updated": _now_ms(),
    }


def _persist_snapshot() -> None:
    try:
        _SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
        snapshot = {
            "summary": get_summary(),
            "open": get_open_positions(),
            "closed": get_closed_history(limit=MAX_HISTORY),
        }
        _SNAPSHOT.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.debug("paper snapshot persist failed: %s", exc)


def reset_portfolio() -> None:
    """Wipe portfolio state (tests / manual reset)."""
    global _mem_open, _mem_closed, _mem_equity
    _mem_open = {}
    _mem_closed = []
    _mem_equity = []
    r = _get_redis()
    if r is not None:
        try:
            r.delete(_OPEN_KEY, _CLOSED_KEY, _EQUITY_KEY)
        except Exception:
            pass
