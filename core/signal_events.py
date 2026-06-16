"""Signal-event persistence helpers (Faz 2a).

Every agent step in ``core/pipeline.py`` emits a lightweight event so that
operators can audit the pipeline's activity and the UI can render a timeline.

Public API
----------
emit_event(signal_id, symbol, agent, to_state, *, from_state=None,
           payload=None, success=True, error=None) -> int | None
    Write one event row; returns the new row id (or None on failure — never
    raises so it cannot break the production pipeline).

get_events(symbol, limit=100) -> list[dict]
    Read the most-recent events for a given symbol (or all symbols when
    symbol is "*").

get_cycle_events(signal_id) -> list[dict]
    Read all events for a specific pipeline cycle / signal_id.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from core.database import get_sync_session

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Write helpers
# ---------------------------------------------------------------------------


def emit_event(
    signal_id: str,
    symbol: str,
    agent: str,
    to_state: str,
    *,
    from_state: str | None = None,
    payload: dict | None = None,
    success: bool = True,
    error: str | None = None,
) -> int | None:
    """Insert one row into ``signal_events``.

    Designed to be *fire-and-forget*: any exception is logged as a warning
    and ``None`` is returned so the caller's pipeline never crashes.
    """
    try:
        payload_json = json.dumps(payload) if payload else None
        ts = datetime.now(tz=UTC).replace(tzinfo=None)  # naive UTC for SQLite
        with get_sync_session() as session:
            session.execute(
                """
                INSERT INTO signal_events
                    (signal_id, symbol, from_state, to_state, agent,
                     payload, ts, success, error)
                VALUES
                    (:signal_id, :symbol, :from_state, :to_state, :agent,
                     :payload, :ts, :success, :error)
                """,
                {
                    "signal_id": str(signal_id),
                    "symbol": str(symbol),
                    "from_state": from_state,
                    "to_state": str(to_state),
                    "agent": str(agent),
                    "payload": payload_json,
                    "ts": ts,
                    "success": int(success),
                    "error": error,
                },
            )
            # Retrieve last inserted row id
            row = session.execute("SELECT last_insert_rowid()").fetchone()
            return int(row[0]) if row else None
    except Exception as exc:  # noqa: BLE001
        logger.warning("signal_events.emit_event failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------


def _row_to_dict(row) -> dict:
    keys = (
        "id",
        "signal_id",
        "symbol",
        "from_state",
        "to_state",
        "agent",
        "payload",
        "ts",
        "success",
        "error",
    )
    d = dict(zip(keys, row, strict=False))
    if d.get("payload"):
        try:
            d["payload"] = json.loads(d["payload"])
        except Exception:  # noqa: BLE001
            pass
    d["success"] = bool(d.get("success", 1))
    if isinstance(d.get("ts"), str):
        d["ts"] = d["ts"]  # keep as ISO string for JSON serialisation
    return d


def get_events(symbol: str = "*", limit: int = 100) -> list[dict]:
    """Return the most-recent *limit* events for *symbol* (or all symbols)."""
    try:
        with get_sync_session() as session:
            if symbol == "*":
                rows = session.execute(
                    "SELECT id, signal_id, symbol, from_state, to_state, "
                    "agent, payload, ts, success, error "
                    "FROM signal_events ORDER BY ts DESC LIMIT :lim",
                    {"lim": limit},
                ).fetchall()
            else:
                rows = session.execute(
                    "SELECT id, signal_id, symbol, from_state, to_state, "
                    "agent, payload, ts, success, error "
                    "FROM signal_events WHERE symbol = :sym "
                    "ORDER BY ts DESC LIMIT :lim",
                    {"sym": symbol, "lim": limit},
                ).fetchall()
        return [_row_to_dict(r) for r in rows]
    except Exception as exc:  # noqa: BLE001
        logger.warning("signal_events.get_events failed: %s", exc)
        return []


def get_cycle_events(signal_id: str) -> list[dict]:
    """Return all events for a specific pipeline cycle (signal_id)."""
    try:
        with get_sync_session() as session:
            rows = session.execute(
                "SELECT id, signal_id, symbol, from_state, to_state, "
                "agent, payload, ts, success, error "
                "FROM signal_events WHERE signal_id = :sid ORDER BY ts ASC",
                {"sid": str(signal_id)},
            ).fetchall()
        return [_row_to_dict(r) for r in rows]
    except Exception as exc:  # noqa: BLE001
        logger.warning("signal_events.get_cycle_events failed: %s", exc)
        return []
