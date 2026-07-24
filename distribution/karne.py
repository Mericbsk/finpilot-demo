"""Direct-from-DB karne (scorecard) computation — no HTTP dependency.

Mirrors the semantics of jobs._resolve_karne_by_grade / the watchlist
performance endpoint, but reads watchlist_signals lifecycle outcomes straight
from finpilot.db so the morning manual publish works while the API is down.

Honesty rules (product contract):
  * only DECIDED outcomes count (resolved_win / resolved_loss) — open or
    watching signals are never counted as observations;
  * no minimum-n smoothing here: if the closed sample is tiny or brutal, the
    caller/UI decides how to present it, the data layer never hides it.

Stdlib only — safe to import anywhere, trivially testable.
"""

from __future__ import annotations

import logging
import os
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "finpilot.db"

# Single user-facing label mapping — keep in sync with snapshot_builder._grade_of
_TIER_TO_GRADE = {"CONFIRM": "B", "TRIGGER": "C"}


def _grade_of_row(conviction_tier: str | None, tier: str | None) -> str | None:
    conv = (conviction_tier or "").strip().upper()
    if conv in ("A", "B", "C"):
        return conv
    return _TIER_TO_GRADE.get((tier or "").strip().upper())


def compute_karne_db(
    db_path: Path | str | None = None,
    days: int | None = None,
) -> dict[str, Any] | None:
    """Return {"by_grade": {...}, "window": ..., "raw": True} or None.

    by_grade entries: {"n": closed, "hit_rate": 0-1, "avg_pnl": None}
    (realized pnl is not stored in watchlist_signals; None keeps the
    schema identical to the API-sourced karne).
    """
    if days is None:
        try:
            days = int(os.getenv("FINPILOT_KARNE_WINDOW_DAYS", "5"))
        except ValueError:
            days = 5
    path = Path(db_path) if db_path else DEFAULT_DB
    if not path.exists():
        logger.warning("karne db missing: %s", path)
        return None
    tracked_total = 0
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            try:
                # Karar B (2026-07-24): Masthead shows a transparency count
                # ("N picks publicly tracked"), not a naked win-rate.
                tracked_total = int(
                    con.execute("SELECT COUNT(*) FROM signals_archive").fetchone()[0]
                )
            except sqlite3.Error:
                tracked_total = 0
            rows = con.execute(
                """
                SELECT conviction_tier, tier, status_lifecycle, COUNT(*)
                FROM   watchlist_signals
                WHERE  signal_date >= date('now', ?)
                  AND  status_lifecycle IN ('resolved_win', 'resolved_loss')
                GROUP BY conviction_tier, tier, status_lifecycle
                """,
                (f"-{int(days)} day",),
            ).fetchall()
        finally:
            con.close()
    except sqlite3.Error as exc:
        logger.warning("karne db read failed: %s", exc)
        return None

    tallies: dict[str, dict[str, int]] = {}
    for conviction_tier, tier, status, count in rows:
        grade = _grade_of_row(conviction_tier, tier)
        if grade is None:
            continue
        bucket = tallies.setdefault(grade, {"tp": 0, "stop": 0})
        bucket["tp" if status == "resolved_win" else "stop"] += int(count)

    by_grade: dict[str, dict[str, Any]] = {}
    for grade in ("A", "B", "C"):
        bucket = tallies.get(grade)
        if not bucket:
            continue
        closed = bucket["tp"] + bucket["stop"]
        if closed == 0:
            continue
        by_grade[grade] = {
            "n": closed,
            "hit_rate": round(bucket["tp"] / closed, 3),
            "avg_pnl": None,
        }

    if not by_grade:
        return None
    return {
        "by_grade": by_grade,
        "window": f"last {days}d eval",
        "raw": True,
        "source": "db",
        "tracked_total": tracked_total,
    }
