"""Sync CRUD service for the watchlist_signals table (S2-8).

All functions use `core.database.get_sync_session()` and execute raw SQL so
they stay compatible with both SQLite (dev) and PostgreSQL (prod).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from sqlalchemy import text

from core.database import get_sync_session

logger = logging.getLogger(__name__)

# Ordered column list — must match CREATE TABLE in migration 002
_COLS = (
    "id",
    "symbol",
    "signal",
    "entry_price",
    "stop_loss",
    "take_profit",
    "score",
    "regime",
    "sentiment",
    "risk_reward",
    "reason",
    "explanation",
    "source_model",
    "notes",
    "tags",
    "status_lifecycle",
    "signal_date",
    "added_at",
)

_CREATE_SQL = """
    CREATE TABLE IF NOT EXISTS watchlist_signals (
        id           TEXT PRIMARY KEY,
        symbol       TEXT NOT NULL,
        signal       TEXT DEFAULT '—',
        entry_price  REAL DEFAULT 0.0,
        stop_loss    REAL DEFAULT 0.0,
        take_profit  REAL DEFAULT 0.0,
        score        REAL DEFAULT 0.0,
        regime       TEXT DEFAULT '',
        sentiment    TEXT DEFAULT '',
        risk_reward  REAL DEFAULT 0.0,
        reason       TEXT DEFAULT '',
        explanation  TEXT DEFAULT '',
        source_model TEXT DEFAULT 'scanner_v2',
        notes        TEXT DEFAULT '',
        tags         TEXT DEFAULT '[]',
        status_lifecycle TEXT DEFAULT 'new',
        signal_date  TEXT NOT NULL,
        added_at     TEXT NOT NULL
    )
"""


# ─── Internal helpers ─────────────────────────────────────────────────────────


def _row_to_dict(row: Any) -> dict:
    d = dict(row._mapping)
    if isinstance(d.get("tags"), str):
        try:
            d["tags"] = json.loads(d["tags"])
        except Exception:
            d["tags"] = []
    return d


def _entry_to_params(entry: dict) -> dict:
    params: dict[str, Any] = {col: entry.get(col) for col in _COLS}
    if isinstance(params.get("tags"), list):
        params["tags"] = json.dumps(params["tags"])
    return params


def _insert_sql() -> str:
    cols = ", ".join(_COLS)
    vals = ", ".join(f":{c}" for c in _COLS)
    return f"INSERT INTO watchlist_signals ({cols}) VALUES ({vals})"


# ─── Public API ───────────────────────────────────────────────────────────────


def ensure_table() -> None:
    """Create watchlist_signals table + indexes if they do not exist (idempotent)."""
    with get_sync_session() as session:
        session.execute(text(_CREATE_SQL))
        session.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_watchlist_signals_symbol"
                " ON watchlist_signals(symbol)"
            )
        )
        session.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_watchlist_signals_date"
                " ON watchlist_signals(signal_date)"
            )
        )


def migrate_from_json(json_path: Path) -> int:
    """One-time migration: import existing JSON watchlist into DB.

    Only runs if the table is empty and the JSON file exists.
    Returns the number of rows imported.
    """
    if not json_path.exists():
        return 0
    with get_sync_session() as session:
        count = session.execute(text("SELECT COUNT(*) FROM watchlist_signals")).scalar_one()
        if count > 0:
            return 0

        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            items = data if isinstance(data, list) else []
        except Exception as exc:
            logger.warning("watchlist JSON migration read failed: %s", exc)
            return 0

        imported = 0
        sql = _insert_sql()
        for entry in items:
            if not entry.get("id"):
                continue
            try:
                session.execute(text(sql), _entry_to_params(entry))
                imported += 1
            except Exception as exc:
                logger.debug("watchlist migration skip %s: %s", entry.get("symbol"), exc)

    logger.info("watchlist_db: migrated %d signals from JSON", imported)
    return imported


def load_active() -> list[dict]:
    """Return all watchlist signals ordered by added_at (oldest first)."""
    with get_sync_session() as session:
        rows = session.execute(text("SELECT * FROM watchlist_signals ORDER BY added_at")).fetchall()
    return [_row_to_dict(r) for r in rows]


def upsert_signal(entry: dict) -> None:
    """Insert or replace a signal for the given symbol (removes old entry first)."""
    params = _entry_to_params(entry)
    with get_sync_session() as session:
        session.execute(
            text("DELETE FROM watchlist_signals WHERE symbol = :symbol"),
            {"symbol": entry["symbol"]},
        )
        session.execute(text(_insert_sql()), params)


def replace_all_active(items: list[dict]) -> None:
    """Atomically delete all signals and re-insert the provided list."""
    with get_sync_session() as session:
        session.execute(text("DELETE FROM watchlist_signals"))
        sql = _insert_sql()
        for entry in items:
            session.execute(text(sql), _entry_to_params(entry))


def update_field(item_id: str, **fields: Any) -> bool:
    """Update specific fields for a signal by ID. Returns True if found."""
    if not fields:
        return False
    if "tags" in fields and isinstance(fields["tags"], list):
        fields["tags"] = json.dumps(fields["tags"])
    set_clause = ", ".join(f"{k} = :{k}" for k in fields)
    params: dict[str, Any] = {"item_id": item_id, **fields}
    with get_sync_session() as session:
        result = session.execute(
            text(f"UPDATE watchlist_signals SET {set_clause} WHERE id = :item_id"),
            params,
        )
    return result.rowcount > 0


def delete_by_symbol(symbol: str) -> int:
    """Delete signal by symbol. Returns number of rows deleted."""
    with get_sync_session() as session:
        result = session.execute(
            text("DELETE FROM watchlist_signals WHERE symbol = :symbol"),
            {"symbol": symbol},
        )
    return result.rowcount


def clear_active() -> None:
    """Delete all watchlist signals."""
    with get_sync_session() as session:
        session.execute(text("DELETE FROM watchlist_signals"))
