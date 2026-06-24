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


# ─── Lottery / MAX fade factor (Faz 1) ──────────────────────────────────────
# Bali-Cakici-Whitelaw (2011): stocks with high MAX (best single-day return),
# high idiosyncratic vol, and positive return skew have systematically NEGATIVE
# expected returns — investors overpay for lottery-like payoffs.
#
# The factor is 0.0–1.0 where 1.0 = maximum lottery character = FADE signal.
# It is computed from the already-fetched df_1d so no extra network call.
#
# Component weights: MAX 30%, IVOL 30%, skew 25%, low-price 15%.
# Reference caps: 15% max single-day gain, 80% annualised IVOL, 2σ skew, $50 price.
_MAX_WINDOW: int = 21  # days for MAX / IVOL / skew window
_LOTTERY_PRICE_CAP: float = 50.0  # above this price, lottery character diminishes


def compute_lottery_factor(df: Any) -> float:
    """Return 0.0–1.0 lottery-spike score from daily OHLC DataFrame.

    Higher score = more lottery-like = stronger fade expectation.

    Args:
        df: Daily OHLC DataFrame with at least a ``Close`` column.

    Returns:
        0.0 when fewer than 22 daily bars are available.
    """
    try:
        if not hasattr(df, "iloc") or len(df) < _MAX_WINDOW + 1 or "Close" not in df.columns:
            return 0.0
        close = df["Close"].iloc[-(_MAX_WINDOW + 1) :].astype(float)
        rets = close.pct_change().dropna()
        if len(rets) < 10:
            return 0.0

        # MAX: best single-day gain in window, normalised via 15% cap
        max_ret = float(rets.max())
        max_comp = min(1.0, max(0.0, max_ret / 0.15))

        # IVOL: annualised daily-return std, normalised via 80% annual vol cap
        ivol = float(rets.std() * (252**0.5))
        ivol_comp = min(1.0, max(0.0, ivol / 0.80))

        # Skewness: positive skew = right-tail lottery-like payoff
        skew_val = float(rets.skew())
        skew_comp = min(1.0, max(0.0, skew_val / 2.0))

        # Price: lower price → more lottery character
        last_price = float(df["Close"].iloc[-1])
        price_comp = max(0.0, 1.0 - min(1.0, last_price / _LOTTERY_PRICE_CAP))

        lottery = 0.30 * max_comp + 0.30 * ivol_comp + 0.25 * skew_comp + 0.15 * price_comp
        return round(max(0.0, min(1.0, lottery)), 4)
    except Exception as exc:
        logger.debug("features: compute_lottery_factor failed: %s", exc)
        return 0.0


# ─── Overnight gap reversal factor (Faz 4) ──────────────────────────────────
# Large overnight gaps (open_t / close_{t-1} − 1) create short-term
# mean-reversion pressure (gap-and-fade). The factor is 0.0–1.0 where
# 1.0 = extreme recent gap-up = strong reversal/fade expectation.
#
# Reference gap cap: 8% overnight gap → component saturates at 1.0.
# Looks back over the last 3 trading days; blends max single gap (60%)
# with average positive gap (40%).
_OVERNIGHT_WINDOW: int = 3  # look-back trading days
_OVERNIGHT_GAP_CAP: float = 0.08  # 8% gap → full factor (1.0)


def compute_overnight_gap_factor(df: Any) -> float:
    """Return 0.0–1.0 overnight-gap reversal pressure from daily OHLC DataFrame.

    Args:
        df: Daily OHLC DataFrame with ``Open`` and ``Close`` columns.

    Returns:
        0.0 when Open column is unavailable or fewer than 4 bars.
    """
    try:
        if (
            not hasattr(df, "iloc")
            or len(df) < _OVERNIGHT_WINDOW + 1
            or "Open" not in df.columns
            or "Close" not in df.columns
        ):
            return 0.0
        recent = df.iloc[-(_OVERNIGHT_WINDOW + 1) :].reset_index(drop=True)
        gaps: list[float] = []
        for i in range(1, len(recent)):
            prev_close = float(recent["Close"].iloc[i - 1])
            today_open = float(recent["Open"].iloc[i])
            if prev_close > 0:
                gaps.append((today_open - prev_close) / prev_close)

        if not gaps:
            return 0.0

        # Only positive gaps (gap-ups) drive reversal pressure
        max_pos_gap = max(0.0, max(gaps))
        avg_pos_gap = sum(max(0.0, g) for g in gaps) / len(gaps)

        gap_comp = min(1.0, max_pos_gap / _OVERNIGHT_GAP_CAP)
        avg_comp = min(1.0, avg_pos_gap / (_OVERNIGHT_GAP_CAP / 2.0))

        factor = 0.6 * gap_comp + 0.4 * avg_comp
        return round(max(0.0, min(1.0, factor)), 4)
    except Exception as exc:
        logger.debug("features: compute_overnight_gap_factor failed: %s", exc)
        return 0.0


# ─── Early-detection features (pre-event / "coiled spring") ──────────────────
_CONTRACTION_WINDOW: int = 60
_CONTRACTION_RECENT: int = 5
_RVOL_BASELINE: int = 20
_RVOL_ACCEL_CAP: float = 1.5


def _percentile_rank(series: Any, value: float) -> float:
    """Fraction of ``series`` values <= ``value`` (0.0-1.0). Empty -> 0.5."""
    try:
        n = len(series)
        if n == 0:
            return 0.5
        return float((series <= value).sum()) / float(n)
    except Exception:
        return 0.5


def compute_contraction_factor(df: Any, window: int = _CONTRACTION_WINDOW) -> float:
    """Return a 0.0-1.0 volatility-contraction ("coiled spring") score."""
    try:
        if (
            not hasattr(df, "iloc")
            or len(df) < window + 1
            or not {"High", "Low", "Close"}.issubset(df.columns)
        ):
            return 0.0
        close = df["Close"].astype(float)
        high = df["High"].astype(float)
        low = df["Low"].astype(float)

        ntr = ((high - low) / close.replace(0, float("nan"))).dropna()
        if len(ntr) < window:
            return 0.0
        ntr_window = ntr.iloc[-window:]
        ntr_current = float(ntr.iloc[-_CONTRACTION_RECENT:].mean())
        ntr_contraction = 1.0 - _percentile_rank(ntr_window, ntr_current)

        roll_std = close.rolling(20).std()
        roll_mean = close.rolling(20).mean()
        bb_width = (roll_std / roll_mean.replace(0, float("nan"))).dropna()
        if len(bb_width) >= window:
            bbw_window = bb_width.iloc[-window:]
            bbw_current = float(bb_width.iloc[-_CONTRACTION_RECENT:].mean())
            bbw_contraction = 1.0 - _percentile_rank(bbw_window, bbw_current)
        else:
            bbw_contraction = ntr_contraction

        factor = 0.6 * ntr_contraction + 0.4 * bbw_contraction
        return round(max(0.0, min(1.0, factor)), 4)
    except Exception as exc:
        logger.debug("features: compute_contraction_factor failed: %s", exc)
        return 0.0


def compute_rvol_acceleration(df: Any, baseline: int = _RVOL_BASELINE) -> float:
    """Return a 0.0–1.0 *relative-volume acceleration* score.

    Leading volume signal: measures whether relative volume is RISING
    (recent RVOL > prior RVOL), not whether a spike has already printed.

      rvol_t       = Volume_t / SMA(Volume, baseline)
      acceleration = mean(rvol last 3 bars) − mean(rvol prior 3 bars)
      factor       = clamp(acceleration / cap, 0, 1)

    1.0 = volume building fast from a low base (early interest).
    0.0 = volume flat or fading. Pure pandas; 0.0 when insufficient data.
    """
    try:
        if not hasattr(df, "iloc") or len(df) < baseline + 6 or "Volume" not in df.columns:
            return 0.0
        vol = df["Volume"].astype(float)
        vol_sma = vol.rolling(baseline).mean()
        rvol = (vol / vol_sma.replace(0, float("nan"))).dropna()
        if len(rvol) < 6:
            return 0.0
        recent = float(rvol.iloc[-3:].mean())
        prior = float(rvol.iloc[-6:-3].mean())
        accel = recent - prior
        factor = accel / _RVOL_ACCEL_CAP
        return round(max(0.0, min(1.0, factor)), 4)
    except Exception as exc:
        logger.debug("features: compute_rvol_acceleration failed: %s", exc)
        return 0.0
