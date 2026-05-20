"""FinPilot Outcome Reconciler — Sprint 5 (S5-1).

For every open signal in ``core.kpi_tracker`` whose age exceeds
``HOLD_BARS`` market-days, fetch the close at entry_ts + HOLD_BARS via
yfinance and call ``record_outcome`` so KPIs reflect real P/L.

In parallel, the paper portfolio is closed for the same signal so the
equity curve advances.

This is the *single most important* loop closure in Sprint 5 — without
real outcomes every other KPI is noise.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

HOLD_DAYS = 5  # outcome captured after T+5 calendar days
MIN_AGE_HOURS = 24  # never reconcile a signal younger than this


def _fetch_close_after(symbol: str, entry_ts_ms: int, hold_days: int) -> float | None:
    """Return the close N days after entry, or latest available if not yet reached."""
    try:
        import yfinance as yf
    except ImportError:
        logger.warning("outcome_reconciler: yfinance not installed")
        return None

    entry_dt = datetime.fromtimestamp(entry_ts_ms / 1000, tz=UTC)
    target_dt = entry_dt + timedelta(days=hold_days)
    end_dt = min(target_dt + timedelta(days=3), datetime.now(tz=UTC))  # buffer for weekends

    if end_dt <= entry_dt:
        return None

    try:
        df = yf.download(
            symbol,
            start=entry_dt.strftime("%Y-%m-%d"),
            end=end_dt.strftime("%Y-%m-%d"),
            progress=False,
            auto_adjust=True,
        )
    except Exception as exc:
        logger.debug("outcome_reconciler: yf.download(%s) failed: %s", symbol, exc)
        return None

    if df is None or df.empty:
        return None

    # Filter to bars on/after the target date; otherwise take the last available bar
    try:
        idx = df.index
        # yfinance index is tz-naive; treat as UTC date for comparison
        target_date = target_dt.date()
        after = df[idx.date >= target_date]
        bar = after.iloc[0] if not after.empty else df.iloc[-1]
        close = bar["Close"]
        # multi-ticker fallback (when df has MultiIndex columns)
        if hasattr(close, "iloc"):
            close = close.iloc[0]
        return float(close)
    except Exception as exc:
        logger.debug("outcome_reconciler: parse close for %s failed: %s", symbol, exc)
        return None


def reconcile_open_signals(
    hold_days: int = HOLD_DAYS,
    min_age_hours: int = MIN_AGE_HOURS,
    max_signals: int = 100,
) -> dict[str, Any]:
    """Walk all open signals and reconcile those past the holding window.

    Returns a summary dict suitable for logging / metrics:
        { "checked": N, "reconciled": M, "skipped": K, "errors": [...] }
    """
    from core.kpi_tracker import _load_all_signals, record_outcome

    signals = _load_all_signals()
    open_signals = [s for s in signals if s.get("outcome") is None]

    now_ms = int(time.time() * 1000)
    min_age_ms = min_age_hours * 3600 * 1000

    summary: dict[str, Any] = {
        "checked": len(open_signals),
        "reconciled": 0,
        "skipped_age": 0,
        "skipped_data": 0,
        "errors": [],
        "ran_at": datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC"),
    }

    for sig in open_signals[:max_signals]:
        try:
            entry_ts = int(sig.get("ts", 0))
            if now_ms - entry_ts < min_age_ms:
                summary["skipped_age"] += 1
                continue

            symbol = sig["symbol"]
            cycle = int(sig.get("cycle", 0))
            entry_price = float(sig.get("price", 0) or 0)
            if entry_price <= 0:
                summary["skipped_data"] += 1
                continue

            exit_price = _fetch_close_after(symbol, entry_ts, hold_days)
            if exit_price is None or exit_price <= 0:
                summary["skipped_data"] += 1
                continue

            direction = sig.get("direction", "BUY")
            sign = 1.0 if direction == "BUY" else -1.0
            profit_pct = sign * (exit_price - entry_price) / entry_price * 100.0

            record_outcome(symbol=symbol, cycle=cycle, profit_pct=profit_pct)

            # Also close paper portfolio position if it exists
            try:
                from core.paper_portfolio import close_position

                close_position(sig["id"], exit_price)
            except Exception as paper_exc:
                logger.debug("paper close failed for %s: %s", sig["id"], paper_exc)

            summary["reconciled"] += 1
        except Exception as exc:
            summary["errors"].append(f"{sig.get('symbol', '?')}: {exc}")
            logger.warning("outcome_reconciler error on %s: %s", sig.get("symbol"), exc)

    logger.info(
        "Outcome reconciler: checked=%d reconciled=%d skipped_age=%d skipped_data=%d errors=%d",
        summary["checked"],
        summary["reconciled"],
        summary["skipped_age"],
        summary["skipped_data"],
        len(summary["errors"]),
    )
    return summary
