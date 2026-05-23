"""FinPilot Outcome Reconciler — Sprint 5 (S5-1), extended in Sprint 9.

For every open signal in ``core.kpi_tracker`` whose age exceeds the holding
period, fetch the close via yfinance and call ``record_outcome`` so KPIs
reflect real P/L.

Sprint 9 addition: multi-horizon reconciliation (T+1, T+5, T+20). Each
horizon is stored as a separate field on the signal so calibration can later
weight short-term vs long-term predictive accuracy independently.

Primary horizon (T+1) drives the main KPI win_rate/profit_factor.
T+5 and T+20 are stored as ``outcome_t5`` and ``outcome_t20`` for future use.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

HOLD_DAYS = 1  # T+1: primary horizon for KPI tracking
MIN_AGE_HOURS = 24  # never reconcile a signal younger than this

# Horizon config: (horizon_label, hold_days, min_age_hours)
# T+1 drives primary KPIs; T+3 / T+5 / T+10 are stored in the
# outcomes_horizon SQLite table (task 26) for decay analysis.
HORIZONS: list[tuple[str, int, int]] = [
    ("t1", 1, 24),
    ("t3", 3, 3 * 24),
    ("t5", 5, 5 * 24),
    ("t10", 10, 10 * 24),
]


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


def _compute_profit_pct(direction: str, entry_price: float, exit_price: float) -> float:
    sign = 1.0 if direction == "BUY" else -1.0
    return sign * (exit_price - entry_price) / entry_price * 100.0


def reconcile_open_signals(
    hold_days: int = HOLD_DAYS,
    min_age_hours: int = MIN_AGE_HOURS,
    max_signals: int = 100,
) -> dict[str, Any]:
    """Walk all open signals and reconcile those past the T+1 holding window.

    This is the primary reconciler that drives KPIs. For full multi-horizon
    reconciliation use ``reconcile_all_horizons()`` instead.

    Returns a summary dict:
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
            profit_pct = _compute_profit_pct(direction, entry_price, exit_price)

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
        "Outcome reconciler (T+%d): checked=%d reconciled=%d skipped_age=%d skipped_data=%d errors=%d",
        hold_days,
        summary["checked"],
        summary["reconciled"],
        summary["skipped_age"],
        summary["skipped_data"],
        len(summary["errors"]),
    )
    return summary


def _record_horizon_outcome(
    signals_store: Any,
    signal_id: str,
    horizon_key: str,
    profit_pct: float,
) -> bool:
    """Update a signal's horizon-specific outcome field (outcome_t5, outcome_t20).

    Works directly on the in-memory store or Redis list. Returns True if updated.
    The primary ``outcome`` field (used for KPIs) is NOT touched here.
    """
    import json

    r: Any
    try:
        r = signals_store  # may be None
    except Exception:
        r = None

    outcome_val = "win" if profit_pct > 0 else "loss"
    field = f"outcome_{horizon_key}"

    if r is not None:
        try:
            from core.kpi_tracker import MAX_SIGNALS, SIGNALS_KEY

            raw = r.lrange(SIGNALS_KEY, 0, MAX_SIGNALS - 1)
            new_list = []
            updated = False
            for item in raw:
                sig = json.loads(item)
                if sig.get("id") == signal_id and sig.get(field) is None:
                    sig[field] = outcome_val
                    sig[f"profit_pct_{horizon_key}"] = round(profit_pct, 4)
                    updated = True
                new_list.append(json.dumps(sig))
            if updated:
                pipe = r.pipeline()
                pipe.delete(SIGNALS_KEY)
                for item in new_list:
                    pipe.rpush(SIGNALS_KEY, item)
                pipe.execute()
            return updated
        except Exception as exc:
            logger.debug("_record_horizon_outcome Redis error: %s", exc)

    # In-memory fallback (import _mem_signals directly)
    try:
        from core import kpi_tracker as _kt

        for sig in _kt._mem_signals:
            if sig.get("id") == signal_id and sig.get(field) is None:
                sig[field] = outcome_val
                sig[f"profit_pct_{horizon_key}"] = round(profit_pct, 4)
                return True
    except Exception as exc:
        logger.debug("_record_horizon_outcome mem error: %s", exc)

    return False


def reconcile_horizon(
    horizon_key: str,
    hold_days: int,
    min_age_hours: int,
    max_signals: int = 100,
) -> dict[str, Any]:
    """Reconcile open signals for a single extended horizon (t5 or t20).

    Unlike the primary reconciler, this writes ``outcome_t5`` / ``outcome_t20``
    fields on signals that haven't been reconciled for this horizon yet.
    The main ``outcome`` field and KPI metrics are not modified.
    """
    from core.kpi_tracker import _get_redis, _load_all_signals

    outcome_field = f"outcome_{horizon_key}"
    signals = _load_all_signals()
    # Candidates: old enough AND not yet reconciled for this horizon
    now_ms = int(time.time() * 1000)
    min_age_ms = min_age_hours * 3600 * 1000

    candidates = [
        s
        for s in signals
        if s.get(outcome_field) is None
        and (now_ms - int(s.get("ts", now_ms))) >= min_age_ms
        and float(s.get("price", 0) or 0) > 0
    ]

    summary: dict[str, Any] = {
        "horizon": horizon_key,
        "hold_days": hold_days,
        "checked": len(candidates),
        "reconciled": 0,
        "skipped_data": 0,
        "errors": [],
        "ran_at": datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC"),
    }

    r = _get_redis()

    for sig in candidates[:max_signals]:
        try:
            entry_ts = int(sig.get("ts", 0))
            symbol = sig["symbol"]
            entry_price = float(sig["price"])
            direction = sig.get("direction", "BUY")

            exit_price = _fetch_close_after(symbol, entry_ts, hold_days)
            if exit_price is None or exit_price <= 0:
                summary["skipped_data"] += 1
                continue

            profit_pct = _compute_profit_pct(direction, entry_price, exit_price)
            updated = _record_horizon_outcome(r, sig["id"], horizon_key, profit_pct)
            # Also persist to the relational outcomes_horizon table (task 26)
            try:
                from core.horizon_outcomes_db import record_horizon_outcome

                record_horizon_outcome(
                    signal_id=str(sig.get("id", "")),
                    horizon_days=int(hold_days),
                    pct=float(profit_pct),
                )
            except Exception as db_exc:
                logger.debug("outcomes_horizon persist failed: %s", db_exc)
            if updated:
                summary["reconciled"] += 1
        except Exception as exc:
            summary["errors"].append(f"{sig.get('symbol', '?')}: {exc}")
            logger.warning(
                "reconcile_horizon(%s) error on %s: %s", horizon_key, sig.get("symbol"), exc
            )

    logger.info(
        "Outcome reconciler (%s): checked=%d reconciled=%d skipped_data=%d errors=%d",
        horizon_key,
        summary["checked"],
        summary["reconciled"],
        summary["skipped_data"],
        len(summary["errors"]),
    )
    return summary


def reconcile_all_horizons(max_signals: int = 100) -> dict[str, Any]:
    """Run T+1, T+5, and T+20 reconciliation in a single pass.

    T+1 drives primary KPI metrics; T+5 and T+20 store extended outcome
    fields for calibration and dashboard use.

    Returns aggregated summary across all horizons.
    """
    results: dict[str, Any] = {
        "ran_at": datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC"),
        "horizons": {},
    }

    for label, hold_days, min_age_hours in HORIZONS:
        if label == "t1":
            summary = reconcile_open_signals(
                hold_days=hold_days,
                min_age_hours=min_age_hours,
                max_signals=max_signals,
            )
        else:
            summary = reconcile_horizon(
                horizon_key=label,
                hold_days=hold_days,
                min_age_hours=min_age_hours,
                max_signals=max_signals,
            )
        results["horizons"][label] = summary

    total_reconciled = sum(h.get("reconciled", 0) for h in results["horizons"].values())
    results["total_reconciled"] = total_reconciled
    logger.info("reconcile_all_horizons: total_reconciled=%d", total_reconciled)
    return results
