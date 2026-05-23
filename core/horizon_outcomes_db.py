"""Horizon outcomes table — task 26.

Persistent relational store for T+3 / T+5 / T+10 outcome reconciliation rows.
Used by core.outcome_reconciler so we can later analyse decay-by-horizon
without re-walking the entire signals archive.

Schema:
    outcomes_horizon(
        signal_id     TEXT,
        horizon_days  INTEGER,
        pct           REAL,
        status        TEXT,   -- 'win' | 'loss' | 'flat'
        resolved_at   TEXT,
        PRIMARY KEY (signal_id, horizon_days)
    )
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from core.config import DB_PATH

_SCHEMA = """
CREATE TABLE IF NOT EXISTS outcomes_horizon (
    signal_id     TEXT NOT NULL,
    horizon_days  INTEGER NOT NULL,
    pct           REAL,
    status        TEXT,
    resolved_at   TEXT,
    PRIMARY KEY (signal_id, horizon_days)
);
CREATE INDEX IF NOT EXISTS ix_outcomes_horizon_signal ON outcomes_horizon(signal_id);
CREATE INDEX IF NOT EXISTS ix_outcomes_horizon_horizon ON outcomes_horizon(horizon_days);
"""

# Standard horizons reconciled by core.outcome_reconciler
DEFAULT_HORIZONS: tuple[int, ...] = (3, 5, 10)


def _conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(DB_PATH))


def ensure_table() -> None:
    with _conn() as cx:
        cx.executescript(_SCHEMA)


def record_horizon_outcome(
    signal_id: str,
    horizon_days: int,
    pct: float,
    status: str | None = None,
) -> None:
    """Upsert one horizon outcome row. Idempotent via INSERT OR REPLACE."""
    if not signal_id:
        return
    if status is None:
        status = "win" if pct > 0 else ("loss" if pct < 0 else "flat")
    ensure_table()
    with _conn() as cx:
        cx.execute(
            "INSERT OR REPLACE INTO outcomes_horizon "
            "(signal_id, horizon_days, pct, status, resolved_at) VALUES (?,?,?,?,?)",
            (
                str(signal_id),
                int(horizon_days),
                float(pct),
                str(status),
                datetime.now(UTC).isoformat(),
            ),
        )


def fetch_outcomes(signal_id: str) -> list[dict]:
    ensure_table()
    with _conn() as cx:
        rows = cx.execute(
            "SELECT signal_id, horizon_days, pct, status, resolved_at "
            "FROM outcomes_horizon WHERE signal_id=? ORDER BY horizon_days",
            (str(signal_id),),
        ).fetchall()
    return [
        {
            "signal_id": r[0],
            "horizon_days": r[1],
            "pct": r[2],
            "status": r[3],
            "resolved_at": r[4],
        }
        for r in rows
    ]
