"""Alpha Feature Engineering — Sprint 15

Provides two new features for the LightGBM Layer-2 ranker:

1. ``sector_rs`` — sector ETF return vs SPY over the last 20 trading days.
   Higher = sector outperforming the market.

2. ``vol_regime`` — realised volatility regime for a symbol:
   0 = low vol  (σ < 0.15 annualised)
   1 = normal   (0.15 ≤ σ < 0.30)
   2 = high vol (σ ≥ 0.30)

Both features are cached per symbol with a 1-hour TTL to avoid
redundant yfinance calls during scanner cycles.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

# ─── Sector → ETF map (GICS-aligned) ────────────────────────────────────────
SECTOR_ETF: dict[str, str] = {
    "Technology": "XLK",
    "Health Care": "XLV",
    "Financials": "XLF",
    "Consumer Discretionary": "XLY",
    "Consumer Staples": "XLP",
    "Energy": "XLE",
    "Industrials": "XLI",
    "Materials": "XLB",
    "Real Estate": "XLRE",
    "Communication Services": "XLC",
    "Utilities": "XLU",
}

# Cache: symbol → {"sector_rs": float, "vol_regime": int, "ts": float}
_FEATURE_CACHE: dict[str, dict[str, Any]] = {}
_CACHE_TTL = 3600.0  # seconds


def _fetch_returns(ticker: str, period: str = "3mo") -> Any:
    """Return a pandas Series of daily close prices, or None on failure."""
    try:
        import yfinance as yf  # type: ignore[import]

        data = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=True)
        if data.empty:
            return None
        return data["Close"].squeeze()
    except Exception as exc:
        logger.debug("features: fetch_returns(%s) failed: %s", ticker, exc)
        return None


def compute_sector_rs(sector: str) -> float:
    """Return the sector ETF 20-day return minus SPY 20-day return.

    Positive values mean the sector is outperforming the broad market.
    Returns 0.0 if data is unavailable.
    """
    etf = SECTOR_ETF.get(sector)
    if not etf:
        return 0.0

    spy_close = _fetch_returns("SPY")
    etf_close = _fetch_returns(etf)

    if spy_close is None or etf_close is None or len(spy_close) < 21 or len(etf_close) < 21:
        return 0.0

    spy_ret = float((spy_close.iloc[-1] - spy_close.iloc[-21]) / spy_close.iloc[-21])
    etf_ret = float((etf_close.iloc[-1] - etf_close.iloc[-21]) / etf_close.iloc[-21])
    return round(etf_ret - spy_ret, 4)


def compute_vol_regime(symbol: str) -> int:
    """Return vol regime bucket for symbol (0=low, 1=normal, 2=high).

    Uses 20-day realised vol annualised (×√252).
    Returns 1 (normal) on failure.
    """
    close = _fetch_returns(symbol, period="2mo")
    if close is None or len(close) < 21:
        return 1

    daily_rets = close.pct_change().dropna()
    if len(daily_rets) < 20:
        return 1
    rv = float(daily_rets.iloc[-20:].std() * (252**0.5))

    if rv < 0.15:
        return 0
    if rv < 0.30:
        return 1
    return 2


# ─── Float / Short squeeze factor ───────────────────────────────────────────
# Low float + high short interest = squeeze fuel. This data is already fetched
# from yfinance for display (api/routers/market_data.py) but never reached the
# scoring engine. The factor is a normalised 0.0–1.0 squeeze-potential score.
#
# Reference float pivot: 50M shares (below this, supply is tight enough to
# matter). Reference short-interest pivot: 20% of float (above this, covering
# pressure can drive >30% moves).
_SQUEEZE_FLOAT_PIVOT: float = 50e6
_SQUEEZE_SHORT_PIVOT: float = 0.20


def compute_squeeze_factor(symbol: str) -> float:
    """Return a 0.0–1.0 short-squeeze potential score for ``symbol``.

    Combines two yfinance fundamentals:
      * ``shortPercentOfFloat`` — short interest as a fraction of float.
      * ``floatShares`` — tradable share count (lower = tighter supply).

    The two components are equally weighted. Returns 0.0 when the
    fundamentals are unavailable (the factor is then a no-op in scoring).
    """
    try:
        import yfinance as yf  # noqa: PLC0415

        info = yf.Ticker(symbol).info or {}
    except Exception as exc:
        logger.debug("features: squeeze info(%s) failed: %s", symbol, exc)
        return 0.0

    short_pct = info.get("shortPercentOfFloat")
    float_shares = info.get("floatShares")

    # Short-interest component: scales 0→1 as short% rises toward the pivot.
    short_comp = 0.0
    if isinstance(short_pct, int | float) and short_pct > 0:
        short_comp = min(1.0, float(short_pct) / _SQUEEZE_SHORT_PIVOT)

    # Float-tightness component: scales 1→0 as float rises toward the pivot.
    float_comp = 0.0
    if isinstance(float_shares, int | float) and float_shares > 0:
        float_comp = max(0.0, 1.0 - float(float_shares) / _SQUEEZE_FLOAT_PIVOT)

    squeeze = 0.5 * short_comp + 0.5 * float_comp
    return round(max(0.0, min(1.0, squeeze)), 4)


def get_alpha_features(symbol: str, sector: str | None = None) -> dict[str, Any]:
    """Return cached ``sector_rs``, ``vol_regime`` and ``squeeze_factor``.

    Uses a 1-hour in-memory cache to avoid redundant fetches. The squeeze
    factor is only computed when ``FINPILOT_ENABLE_SQUEEZE_FACTOR=1`` so the
    extra yfinance ``.info`` call is skipped while the factor is disabled.
    """
    now = time.time()
    cache_key = f"{symbol}:{sector or ''}"
    cached = _FEATURE_CACHE.get(cache_key)
    if cached and now - cached["ts"] < _CACHE_TTL:
        return {k: v for k, v in cached.items() if k != "ts"}

    sector_rs = compute_sector_rs(sector or "") if sector else 0.0
    vol_regime = compute_vol_regime(symbol)

    squeeze_factor = 0.0
    if os.environ.get("FINPILOT_ENABLE_SQUEEZE_FACTOR", "0") == "1":
        squeeze_factor = compute_squeeze_factor(symbol)

    entry: dict[str, Any] = {
        "sector_rs": sector_rs,
        "vol_regime": vol_regime,
        "squeeze_factor": squeeze_factor,
        "ts": now,
    }
    _FEATURE_CACHE[cache_key] = entry
    return {
        "sector_rs": sector_rs,
        "vol_regime": vol_regime,
        "squeeze_factor": squeeze_factor,
    }
