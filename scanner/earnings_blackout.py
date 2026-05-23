"""Earnings Blackout Filter — Sprint 15

Suppresses or discounts signals for stocks within N days of an earnings
announcement to avoid high-IV / gap risk.

Usage
-----
    from scanner.earnings_blackout import is_earnings_blackout, earnings_proximity

    if is_earnings_blackout("AAPL", days_before=2, days_after=1):
        ...  # skip signal

    prox = earnings_proximity("AAPL")  # float: 0.0 = far away, 1.0 = earnings today
"""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

# In-memory cache: symbol → {"next_earnings": epoch | None, "ts": float}
_EARNINGS_CACHE: dict[str, dict[str, Any]] = {}
_CACHE_TTL = 6 * 3600.0  # 6 hours

_SECONDS_PER_DAY = 86400


def _fetch_next_earnings(symbol: str) -> float | None:
    """Return epoch of next earnings date (midnight UTC), or None."""
    try:
        import yfinance as yf  # type: ignore[import]

        ticker = yf.Ticker(symbol)
        cal = ticker.calendar
        if cal is None:
            return None

        # yfinance returns calendar as dict or DataFrame depending on version
        if hasattr(cal, "iloc"):
            # DataFrame: columns are dates, rows are items
            try:
                earn_dates = cal.loc["Earnings Date"] if "Earnings Date" in cal.index else None
                if earn_dates is not None:
                    import pandas as pd  # noqa: PLC0415

                    dt = pd.to_datetime(earn_dates.iloc[0])
                    return dt.timestamp()
            except Exception:
                pass
            return None

        # Dict form
        earn_date = cal.get("Earnings Date")
        if earn_date is None:
            return None

        import pandas as pd  # noqa: PLC0415

        if hasattr(earn_date, "__iter__") and not isinstance(earn_date, str):
            earn_date = list(earn_date)[0]
        dt = pd.to_datetime(earn_date)
        return float(dt.timestamp())
    except Exception as exc:
        logger.debug("earnings_blackout: fetch(%s) failed: %s", symbol, exc)
        return None


def _get_next_earnings_cached(symbol: str) -> float | None:
    now = time.time()
    cached = _EARNINGS_CACHE.get(symbol)
    if cached and now - cached["ts"] < _CACHE_TTL:
        return cached["next_earnings"]
    next_ts = _fetch_next_earnings(symbol)
    _EARNINGS_CACHE[symbol] = {"next_earnings": next_ts, "ts": now}
    return next_ts


def is_earnings_blackout(
    symbol: str,
    days_before: int = 2,
    days_after: int = 1,
) -> bool:
    """Return True if *symbol* is within the earnings blackout window.

    Parameters
    ----------
    symbol:       Ticker symbol
    days_before:  Suppress signals this many days *before* earnings
    days_after:   Suppress signals this many days *after* earnings
    """
    next_ts = _get_next_earnings_cached(symbol)
    if next_ts is None:
        return False
    now = time.time()
    days_until = (next_ts - now) / _SECONDS_PER_DAY
    # Within [−days_after, +days_before] window
    return -days_after <= days_until <= days_before


def earnings_proximity(symbol: str, decay_days: int = 7) -> float:
    """Return a [0, 1] proximity score where 1.0 = earnings is today/imminent.

    Used as a penalty feature (``earnings_proximity``) in the LightGBM ranker.
    Returns 0.0 if no upcoming earnings found or if earnings are > decay_days away.
    """
    next_ts = _get_next_earnings_cached(symbol)
    if next_ts is None:
        return 0.0
    now = time.time()
    days_until = (next_ts - now) / _SECONDS_PER_DAY
    if days_until < 0 or days_until > decay_days:
        return 0.0
    return round(1.0 - days_until / decay_days, 4)
