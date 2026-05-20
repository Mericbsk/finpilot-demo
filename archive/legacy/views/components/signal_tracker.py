"""
Signal Tracker — Sprint 22 (simplified).

Provides:
  - log_signals / log_signals_to_csv: Persist scan results (DB-first, CSV fallback)
  - load_signal_log: Read signals from DB or CSV
  - render_signal_performance_tab: Delegates to daily_signals module
"""

from __future__ import annotations

import csv
import logging
import os
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DB Integration (Sprint 20)
# ---------------------------------------------------------------------------
try:
    from auth.database import SignalRepository, get_database

    _SIGNAL_DB_AVAILABLE = True
except ImportError:
    _SIGNAL_DB_AVAILABLE = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SIGNAL_LOG_PATH = os.path.join(os.getcwd(), "data", "logs", "signal_log.csv")

SIGNAL_LOG_COLUMNS = [
    "timestamp",
    "symbol",
    "price",
    "stop_loss",
    "take_profit",
    "score",
    "strength",
    "regime",
    "sentiment",
    "onchain",
    "entry_ok",
    "summary",
    "reason",
]


# ---------------------------------------------------------------------------
# Signal Logging (Write) — DB-first, CSV fallback
# ---------------------------------------------------------------------------
def log_signals(df: pd.DataFrame) -> int:
    """Persist scan results to SQLite (primary) and CSV (backup)."""
    if df is None or df.empty:
        return 0

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    signals = []
    for _, row in df.iterrows():
        signals.append(
            {
                "timestamp": now,
                "symbol": row.get("symbol", ""),
                "price": row.get("price"),
                "stop_loss": row.get("stop_loss"),
                "take_profit": row.get("take_profit"),
                "score": row.get("recommendation_score", row.get("score")),
                "strength": row.get("strength", row.get("filter_score")),
                "regime": row.get("regime"),
                "sentiment": row.get("sentiment"),
                "onchain": str(row.get("onchain_metric", row.get("onchain", ""))),
                "entry_ok": row.get("entry_ok", False),
                "summary": row.get("why", row.get("summary", "")),
                "reason": row.get("reason", ""),
            }
        )

    count = 0

    # Primary: SQLite
    if _SIGNAL_DB_AVAILABLE:
        try:
            db = get_database()
            repo = SignalRepository(db)
            count = repo.save_batch(signals)
            logger.info(f"Logged {count} signals to DB")
        except Exception as e:
            logger.error(f"DB signal write failed, falling back to CSV: {e}")
            count = 0

    # Fallback: CSV
    if count == 0:
        count = _write_signals_csv(signals)

    return count


# Legacy alias
log_signals_to_csv = log_signals


def _write_signals_csv(signals: list[dict]) -> int:
    """Write signals to CSV (legacy fallback)."""
    os.makedirs(os.path.dirname(SIGNAL_LOG_PATH), exist_ok=True)
    count = 0
    try:
        with open(SIGNAL_LOG_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for s in signals:
                writer.writerow(
                    [
                        s["timestamp"],
                        s["symbol"],
                        s.get("price", ""),
                        s.get("stop_loss", ""),
                        s.get("take_profit", ""),
                        s.get("score", ""),
                        s.get("strength", ""),
                        s.get("regime", ""),
                        s.get("sentiment", ""),
                        s.get("onchain", ""),
                        s.get("entry_ok", ""),
                        s.get("summary", ""),
                        s.get("reason", ""),
                    ]
                )
                count += 1
        logger.info(f"Logged {count} signals to CSV: {SIGNAL_LOG_PATH}")
    except Exception as e:
        logger.error(f"CSV signal write also failed: {e}")
    return count


# ---------------------------------------------------------------------------
# Signal Reading
# ---------------------------------------------------------------------------
def load_signal_log() -> pd.DataFrame:
    """Load signals from DB (primary) or CSV (fallback)."""
    if _SIGNAL_DB_AVAILABLE:
        try:
            db = get_database()
            repo = SignalRepository(db)
            rows = repo.get_recent(limit=5000)
            if rows:
                df = pd.DataFrame(rows)
                for col in SIGNAL_LOG_COLUMNS:
                    if col not in df.columns:
                        df[col] = None
                df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
                for num_col in ("price", "stop_loss", "take_profit", "score", "strength"):
                    if num_col in df.columns:
                        df[num_col] = pd.to_numeric(df[num_col], errors="coerce")
                df["entry_ok"] = df["entry_ok"].astype(bool)
                df = df.dropna(subset=["timestamp", "symbol", "price"])
                df = df.sort_values("timestamp", ascending=False)
                return df
        except Exception as e:
            logger.warning(f"DB signal read failed, falling back to CSV: {e}")

    return _load_signal_log_csv()


def _load_signal_log_csv() -> pd.DataFrame:
    """Legacy CSV-based signal reading."""
    if not os.path.exists(SIGNAL_LOG_PATH):
        return pd.DataFrame(columns=SIGNAL_LOG_COLUMNS)
    try:
        df = pd.read_csv(SIGNAL_LOG_PATH, header=None, names=SIGNAL_LOG_COLUMNS)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df["stop_loss"] = pd.to_numeric(df["stop_loss"], errors="coerce")
        df["take_profit"] = pd.to_numeric(df["take_profit"], errors="coerce")
        df["score"] = pd.to_numeric(df["score"], errors="coerce")
        df["strength"] = pd.to_numeric(df["strength"], errors="coerce")
        df["entry_ok"] = (
            df["entry_ok"].astype(str).str.lower().isin({"1", "true", "evet", "al", "yes"})
        )
        df = df.dropna(subset=["timestamp", "symbol", "price"])
        df = df.sort_values("timestamp", ascending=False)
        return df
    except Exception as e:
        logger.error(f"Failed to load signal log CSV: {e}")
        return pd.DataFrame(columns=SIGNAL_LOG_COLUMNS)


# ---------------------------------------------------------------------------
# Rendering — delegates to daily_signals
# ---------------------------------------------------------------------------
def render_signal_performance_tab():
    """Render the full Signal Performance tab — daily signal tracker."""
    from views.components.daily_signals import render_daily_signals_tab

    render_daily_signals_tab()
