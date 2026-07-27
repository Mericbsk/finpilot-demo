"""Direct-from-DB karne (scorecard) computation — no HTTP dependency.

Mirrors the semantics of jobs._resolve_karne_by_grade / the watchlist
performance endpoint, but reads finpilot.db straight so the morning manual
publish works while the API is down.

Two honest views:
  * by_grade  — per-grade (A/B/C) hit-rate + expectancy from watchlist_signals,
                counting only DECIDED and MATURED outcomes (see rules below).
                Empty until the (recently introduced) graded signals age past
                the maturity gate — never faked.
  * overall   — all-time ungraded track record from signals_archive barrier
                labels (resolved_pct_barrier). This is the real, positive
                published-pick record that already exists today.

Honesty rules (product contract):
  * only DECIDED outcomes count (resolved_win / resolved_loss);
  * MATURITY GATE: a graded signal is only counted once its triple-barrier race
    has had time to finish (~21 trading days ≈ 30 calendar days). Fresh signals
    are excluded — their near stop resolves fast while their far take-profit is
    still pending, which would depress the hit-rate into a lie;
  * avg_pnl = mean barrier-hit realized return (win → TP distance, loss → SL
    distance) = expectancy. A low hit-rate at a high reward/risk ratio is
    honest and can still be positive;
  * no minimum-n smoothing: the data layer never hides a tiny/brutal sample.

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

_WINDOW_DEFAULT = 365  # rolling lookback (calendar days) for the graded track record
_MATURITY_DEFAULT = 30  # min age (calendar days) so the ~21 trading-day barrier completes


def _grade_of_row(conviction_tier: str | None, tier: str | None) -> str | None:
    conv = (conviction_tier or "").strip().upper()
    if conv in ("A", "B", "C"):
        return conv
    return _TIER_TO_GRADE.get((tier or "").strip().upper())


def _realized_pct(entry: Any, stop: Any, take_profit: Any, status: str) -> float | None:
    """Barrier-hit realized return (%): win → TP distance, loss → SL distance."""
    try:
        e = float(entry)
        if e <= 0:
            return None
        if status == "resolved_win" and take_profit:
            return (float(take_profit) - e) / e * 100.0
        if status == "resolved_loss" and stop:
            return (float(stop) - e) / e * 100.0
    except (TypeError, ValueError):
        return None
    return None


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)) or default)
    except ValueError:
        return default


def _overall_from_archive(con: sqlite3.Connection) -> dict[str, Any] | None:
    """All-time ungraded track record from signals_archive barrier labels.

    These historical rows carry realized barrier returns (resolved_pct_barrier)
    but no A/B/C grade, so they feed a single honest aggregate, not by_grade.
    """
    try:
        rows = con.execute(
            "SELECT resolved_status_barrier AS s, resolved_pct_barrier AS p "
            "FROM signals_archive "
            "WHERE resolved_status_barrier IN ('resolved_win', 'resolved_loss') "
            "  AND resolved_pct_barrier IS NOT NULL"
        ).fetchall()
    except sqlite3.Error:
        return None
    wins = [float(p) for s, p in rows if s == "resolved_win"]
    losses = [float(p) for s, p in rows if s == "resolved_loss"]
    n = len(wins) + len(losses)
    if n == 0:
        return None
    hit = len(wins) / n
    avg_win = sum(wins) / len(wins) if wins else 0.0
    avg_loss = sum(losses) / len(losses) if losses else 0.0
    return {
        "n": n,
        "hit_rate": round(hit, 3),
        "avg_win": round(avg_win, 3),
        "avg_loss": round(avg_loss, 3),
        "avg_pnl": round(hit * avg_win + (1 - hit) * avg_loss, 3),  # expectancy/trade
    }


def compute_karne_db(
    db_path: Path | str | None = None,
    days: int | None = None,
    maturity_days: int | None = None,
) -> dict[str, Any] | None:
    """Return karne dict or None when there is nothing honest to show.

    Shape: {
        "by_grade": {A/B/C: {"n", "hit_rate", "avg_pnl"}},   # matured graded
        "overall":  {"n", "hit_rate", "avg_win", "avg_loss", "avg_pnl"},  # all-time
        "tracked_total": int, "window": str, "raw": True, "source": "db",
    }
    Returns None only when BOTH by_grade and overall are empty.
    """
    if days is None:
        days = _env_int("FINPILOT_KARNE_WINDOW_DAYS", _WINDOW_DEFAULT)
    if maturity_days is None:
        maturity_days = _env_int("FINPILOT_KARNE_MATURITY_DAYS", _MATURITY_DEFAULT)
    path = Path(db_path) if db_path else DEFAULT_DB
    if not path.exists():
        logger.warning("karne db missing: %s", path)
        return None

    tracked_total = 0
    overall: dict[str, Any] | None = None
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
            overall = _overall_from_archive(con)
            rows = con.execute(
                """
                SELECT conviction_tier, tier, status_lifecycle,
                       entry_price, stop_loss, take_profit
                FROM   watchlist_signals
                WHERE  signal_date >= date('now', ?)
                  AND  signal_date <= date('now', ?)
                  AND  status_lifecycle IN ('resolved_win', 'resolved_loss')
                """,
                (f"-{int(days)} day", f"-{int(maturity_days)} day"),
            ).fetchall()
        finally:
            con.close()
    except sqlite3.Error as exc:
        logger.warning("karne db read failed: %s", exc)
        return None

    tallies: dict[str, dict[str, float]] = {}
    for conviction_tier, tier, status, entry, stop, take_profit in rows:
        grade = _grade_of_row(conviction_tier, tier)
        if grade is None:
            continue
        bucket = tallies.setdefault(grade, {"tp": 0, "stop": 0, "pnl_sum": 0.0, "pnl_n": 0})
        bucket["tp" if status == "resolved_win" else "stop"] += 1
        pnl = _realized_pct(entry, stop, take_profit, status)
        if pnl is not None:
            bucket["pnl_sum"] += pnl
            bucket["pnl_n"] += 1

    by_grade: dict[str, dict[str, Any]] = {}
    for grade in ("A", "B", "C"):
        bucket = tallies.get(grade)
        if not bucket:
            continue
        closed = int(bucket["tp"] + bucket["stop"])
        if closed == 0:
            continue
        avg_pnl = round(bucket["pnl_sum"] / bucket["pnl_n"], 3) if bucket["pnl_n"] else None
        by_grade[grade] = {
            "n": closed,
            "hit_rate": round(bucket["tp"] / closed, 3),
            "avg_pnl": avg_pnl,
        }

    if not by_grade and not overall:
        return None
    result: dict[str, Any] = {
        "by_grade": by_grade,
        "window": f"last {days}d, matured ≥{maturity_days}d",
        "raw": True,
        "source": "db",
        "tracked_total": tracked_total,
    }
    if overall:
        result["overall"] = overall
    return result
