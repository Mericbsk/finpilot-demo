"""FinPilot Research — Champion/Challenger Model Registry.

SQLite-backed registry for tracking model candidates. Each entry records
weight configuration, evaluation metrics, and promotion status.

Usage::

    from research.registry import ModelRegistry, register_candidate, get_champion

    reg = ModelRegistry()
    reg.register_candidate(weights={"w_rsi": 0.12, ...}, brier=0.21, win_rate=0.58)
    champion = reg.get_champion()
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DB_PATH = Path("data/model_registry.db")

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS model_registry (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    weights         TEXT NOT NULL,
    brier_score     REAL,
    win_rate        REAL,
    profit_factor   REAL,
    n_samples       INTEGER,
    status          TEXT DEFAULT 'challenger',
    promoted_at     TEXT,
    created_at      TEXT NOT NULL,
    strike_count    INTEGER DEFAULT 0,
    promotion_notes TEXT
);
"""

_ADD_STRIKE_SQL = """
UPDATE model_registry SET strike_count = COALESCE(strike_count, 0) + 1 WHERE id = ?;
"""

_RESET_STRIKE_SQL = """
UPDATE model_registry SET strike_count = 0 WHERE id = ?;
"""

_MIGRATE_SQL = """
ALTER TABLE model_registry ADD COLUMN strike_count INTEGER DEFAULT 0;
"""

_MIGRATE_NOTES_SQL = """
ALTER TABLE model_registry ADD COLUMN promotion_notes TEXT;
"""

_INSERT_SQL = """
INSERT INTO model_registry (name, weights, brier_score, win_rate, profit_factor, n_samples, status, created_at)
VALUES (?, ?, ?, ?, ?, ?, 'challenger', ?);
"""

_PROMOTE_SQL = """
UPDATE model_registry SET status = 'champion', promoted_at = ?
WHERE id = ?;
"""

_RETIRE_OLD_SQL = """
UPDATE model_registry SET status = 'retired'
WHERE status = 'champion' AND id != ?;
"""


class ModelRegistry:
    """Champion/challenger registry backed by SQLite."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(_CREATE_SQL)
            # Migrate existing DBs that predate strike_count / promotion_notes columns
            for migration in (_MIGRATE_SQL, _MIGRATE_NOTES_SQL):
                try:
                    conn.execute(migration)
                except Exception:
                    pass  # column already exists
            conn.commit()

    def register_candidate(
        self,
        weights: dict[str, float],
        brier_score: float = 0.0,
        win_rate: float = 0.0,
        profit_factor: float = 0.0,
        n_samples: int = 0,
        name: str | None = None,
    ) -> int:
        """Register a new challenger. Returns the row id."""
        ts = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC")
        auto_name = name or f"candidate_{ts[:10].replace('-', '')}"
        with self._conn() as conn:
            cur = conn.execute(
                _INSERT_SQL,
                (
                    auto_name,
                    json.dumps(weights),
                    brier_score,
                    win_rate,
                    profit_factor,
                    n_samples,
                    ts,
                ),
            )
            conn.commit()
            row_id = cur.lastrowid
        logger.info(
            "registry: registered challenger id=%d name=%s brier=%.4f",
            row_id,
            auto_name,
            brier_score,
        )
        return row_id

    def promote(self, row_id: int) -> None:
        """Promote a challenger to champion, retiring the current champion."""
        ts = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC")
        with self._conn() as conn:
            conn.execute(_RETIRE_OLD_SQL, (row_id,))
            conn.execute(_PROMOTE_SQL, (ts, row_id))
            conn.commit()
        logger.info("registry: promoted id=%d to champion", row_id)

    def get_champion(self) -> dict[str, Any] | None:
        """Return the current champion record, or None if none promoted yet."""
        with self._conn() as conn:
            cur = conn.execute(
                "SELECT id, name, weights, brier_score, win_rate, profit_factor, n_samples, promoted_at "
                "FROM model_registry WHERE status='champion' ORDER BY promoted_at DESC LIMIT 1"
            )
            row = cur.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "name": row[1],
            "weights": json.loads(row[2]),
            "brier_score": row[3],
            "win_rate": row[4],
            "profit_factor": row[5],
            "n_samples": row[6],
            "promoted_at": row[7],
        }

    def get_challengers(self, limit: int = 10) -> list[dict[str, Any]]:
        """Return most recent challengers, sorted by Brier score ascending."""
        with self._conn() as conn:
            cur = conn.execute(
                "SELECT id, name, weights, brier_score, win_rate, profit_factor, n_samples, created_at "
                "FROM model_registry WHERE status='challenger' "
                "ORDER BY brier_score ASC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
        return [
            {
                "id": r[0],
                "name": r[1],
                "weights": json.loads(r[2]),
                "brier_score": r[3],
                "win_rate": r[4],
                "profit_factor": r[5],
                "n_samples": r[6],
                "created_at": r[7],
            }
            for r in rows
        ]

    def add_strike(self, row_id: int) -> int:
        """Increment the strike counter for a model. Returns the new count."""
        with self._conn() as conn:
            conn.execute(_ADD_STRIKE_SQL, (row_id,))
            conn.commit()
            cur = conn.execute(
                "SELECT strike_count FROM model_registry WHERE id = ?", (row_id,)
            )
            row = cur.fetchone()
        new_count = row[0] if row else 1
        logger.info("registry: strike id=%d count=%d", row_id, new_count)
        return new_count

    def reset_strikes(self, row_id: int) -> None:
        """Reset strike counter for a model (after successful evaluation)."""
        with self._conn() as conn:
            conn.execute(_RESET_STRIKE_SQL, (row_id,))
            conn.commit()
        logger.info("registry: strikes reset id=%d", row_id)

    def auto_promote_best(
        self,
        min_brier_improvement: float = 0.01,
        min_win_rate: float = 0.50,
        max_strikes_before_retire: int = 2,
    ) -> bool:
        """Promotion gate: 2-condition check (Brier + win rate).

        A challenger is promoted only when **both** conditions pass:
          1. Its Brier score beats the current champion by at least
             ``min_brier_improvement``.
          2. Its win rate is at least ``min_win_rate``.

        If the best challenger fails the gate, its strike counter is
        incremented.  After ``max_strikes_before_retire`` consecutive
        failures the challenger is retired (removed from consideration).

        Returns True if a new champion was promoted.
        """
        champion = self.get_champion()
        challengers = self.get_challengers(limit=1)
        if not challengers:
            return False

        best = challengers[0]
        if best["brier_score"] is None:
            return False

        # --- Condition 1: Brier improvement ---
        brier_ok = champion is None or (
            champion["brier_score"] is None
            or best["brier_score"] < champion["brier_score"] - min_brier_improvement
        )

        # --- Condition 2: minimum win rate ---
        win_rate_ok = (best.get("win_rate") or 0.0) >= min_win_rate

        notes: dict[str, Any] = {
            "brier_ok": brier_ok,
            "win_rate_ok": win_rate_ok,
            "challenger_brier": best["brier_score"],
            "challenger_win_rate": best.get("win_rate"),
            "champion_brier": (champion or {}).get("brier_score"),
            "min_brier_improvement": min_brier_improvement,
            "min_win_rate": min_win_rate,
        }

        if brier_ok and win_rate_ok:
            # Persist gate notes then promote
            with self._conn() as conn:
                conn.execute(
                    "UPDATE model_registry SET promotion_notes = ? WHERE id = ?",
                    (json.dumps(notes), best["id"]),
                )
                conn.commit()
            self.promote(best["id"])
            logger.info(
                "registry: auto-promoted id=%d (brier=%.4f, win_rate=%.4f)",
                best["id"],
                best["brier_score"],
                best.get("win_rate", 0),
            )
            return True

        # Gate failed — add strike
        strikes = self.add_strike(best["id"])
        notes["strike_count"] = strikes
        logger.info(
            "registry: gate failed id=%d strikes=%d (brier_ok=%s win_rate_ok=%s)",
            best["id"], strikes, brier_ok, win_rate_ok,
        )

        if strikes >= max_strikes_before_retire:
            with self._conn() as conn:
                conn.execute(
                    "UPDATE model_registry SET status = 'retired', promotion_notes = ? WHERE id = ?",
                    (json.dumps({**notes, "retired_reason": "max_strikes"}), best["id"]),
                )
                conn.commit()
            logger.warning(
                "registry: retired challenger id=%d after %d strikes", best["id"], strikes
            )

        return False


# Module-level convenience functions
_registry: ModelRegistry | None = None


def _get_registry() -> ModelRegistry:
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry


def register_candidate(weights: dict[str, float], **metrics: Any) -> int:
    return _get_registry().register_candidate(weights, **metrics)


def get_champion() -> dict[str, Any] | None:
    return _get_registry().get_champion()


def auto_promote_best(
    min_brier_improvement: float = 0.01,
    min_win_rate: float = 0.50,
    max_strikes_before_retire: int = 2,
    **kwargs: Any,
) -> bool:
    return _get_registry().auto_promote_best(
        min_brier_improvement=min_brier_improvement,
        min_win_rate=min_win_rate,
        max_strikes_before_retire=max_strikes_before_retire,
    )
