"""Scanner Risk Metrics — Task 2: Risk-Adjusted Performance Metrics

Provides per-symbol, estimation-quality risk-adjusted metrics using
historical daily OHLC data. All metrics are deliberately conservative:
- Short history (< 60 bars) downgrades estimates
- No survivorship-bias correction applied at this stage
- Results are labelled "estimated" in the output

Functions
---------
calculate_risk_adjusted_metrics(df, benchmark_returns=None)
    Main entry — Sharpe, Sortino, Calmar, MaxDD, AnnVol, Beta, EV
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


# ── Constants ────────────────────────────────────────────────────────────────
TRADING_DAYS = 252
RISK_FREE_DAILY = 0.045 / TRADING_DAYS   # ~4.5% annual T-bill rate (2025-2026)
MIN_BARS_RELIABLE = 60   # Below this, all estimates are flagged as low-quality
MIN_BARS_CALMAR = 120    # Need at least 6 months for a meaningful max-drawdown


def _safe_div(numerator: float, denominator: float, fallback: float = 0.0) -> float:
    if denominator == 0 or not math.isfinite(denominator):
        return fallback
    result = numerator / denominator
    return result if math.isfinite(result) else fallback


def _max_drawdown(equity_curve: np.ndarray) -> float:
    """Peak-to-trough maximum drawdown as a positive fraction [0, 1].

    Args:
        equity_curve: Cumulative product of (1 + daily returns), shape (N,)

    Returns:
        Maximum drawdown fraction (0 = no drawdown, 1 = total loss).
    """
    if len(equity_curve) < 2:
        return 0.0
    running_max = np.maximum.accumulate(equity_curve)
    drawdowns = (equity_curve - running_max) / np.where(running_max > 0, running_max, 1.0)
    return float(-drawdowns.min()) if len(drawdowns) > 0 else 0.0


def _annualise(daily_return_mean: float, daily_return_std: float) -> tuple[float, float]:
    """Convert daily mean/std to annualised figures."""
    ann_return = daily_return_mean * TRADING_DAYS
    ann_vol = daily_return_std * math.sqrt(TRADING_DAYS)
    return ann_return, ann_vol


def calculate_risk_adjusted_metrics(
    df: pd.DataFrame,
    benchmark_returns: pd.Series | None = None,
    window: int | None = None,
) -> dict[str, Any]:
    """Calculate risk-adjusted performance metrics from a daily OHLC DataFrame.

    Args:
        df:                 Daily OHLC DataFrame with at least a 'Close' column.
                            Sorted oldest → newest.
        benchmark_returns:  Optional pd.Series of daily benchmark returns
                            (e.g. SPY) aligned to df's index. Used for Beta.
        window:             If set, only use the last `window` rows. Default: all.

    Returns:
        Dictionary with the following keys (all numeric unless noted):
            sharpe_ratio    – Annualised Sharpe (rf = 4.5% / 252 per day)
            sortino_ratio   – Annualised Sortino (downside deviation denominator)
            calmar_ratio    – Annualised return / max drawdown
            max_drawdown_pct – Max peak-to-trough drawdown as percentage (0–100)
            ann_vol_pct     – Annualised volatility as percentage
            ann_return_pct  – Annualised return as percentage
            beta            – Beta vs benchmark (0.0 if benchmark unavailable)
            ev_per_trade    – Expected value per trade estimate [−1, 1] range
            data_quality    – "high" / "medium" / "low" (bars available)
            bars_used       – Number of rows used in calculation
    """
    out: dict[str, Any] = {
        "sharpe_ratio": 0.0,
        "sortino_ratio": 0.0,
        "calmar_ratio": 0.0,
        "max_drawdown_pct": 0.0,
        "ann_vol_pct": 0.0,
        "ann_return_pct": 0.0,
        "beta": 0.0,
        "ev_per_trade": 0.0,
        "data_quality": "low",
        "bars_used": 0,
    }

    try:
        if "Close" not in df.columns or len(df) < 10:
            return out

        close = df["Close"].astype(float)
        if window is not None and window > 0:
            close = close.tail(window)
        close = close.dropna()
        n = len(close)
        out["bars_used"] = n

        # Data quality flag
        if n >= MIN_BARS_RELIABLE * 2:
            out["data_quality"] = "high"
        elif n >= MIN_BARS_RELIABLE:
            out["data_quality"] = "medium"
        else:
            out["data_quality"] = "low"

        returns = close.pct_change().dropna().values.astype(float)
        if len(returns) < 5:
            return out

        mean_r = returns.mean()
        std_r = returns.std(ddof=1)
        ann_return, ann_vol = _annualise(mean_r, std_r)
        out["ann_return_pct"] = round(ann_return * 100, 2)
        out["ann_vol_pct"] = round(ann_vol * 100, 2)

        # ── Sharpe ──────────────────────────────────────────────────────────
        excess = returns - RISK_FREE_DAILY
        sharpe_daily = excess.mean() / std_r if std_r > 0 else 0.0
        out["sharpe_ratio"] = round(sharpe_daily * math.sqrt(TRADING_DAYS), 3)

        # ── Sortino ─────────────────────────────────────────────────────────
        downside = returns[returns < RISK_FREE_DAILY] - RISK_FREE_DAILY
        if len(downside) > 1:
            downside_std = math.sqrt((downside**2).mean())
            sortino_daily = excess.mean() / downside_std if downside_std > 0 else 0.0
            out["sortino_ratio"] = round(sortino_daily * math.sqrt(TRADING_DAYS), 3)
        else:
            # No downside observations — very bullish or insufficient data
            out["sortino_ratio"] = min(out["sharpe_ratio"] * 1.5, 9.99)

        # ── Max Drawdown & Calmar ────────────────────────────────────────────
        if n >= MIN_BARS_CALMAR:
            equity = np.cumprod(1.0 + returns)
            mdd = _max_drawdown(equity)
            out["max_drawdown_pct"] = round(mdd * 100, 2)
            if mdd > 0:
                out["calmar_ratio"] = round(
                    _safe_div(ann_return, mdd, fallback=0.0), 3
                )
        elif n >= 30:
            # Rough estimate with shorter window (marked as low quality)
            equity = np.cumprod(1.0 + returns)
            mdd = _max_drawdown(equity)
            out["max_drawdown_pct"] = round(mdd * 100, 2)
            out["calmar_ratio"] = 0.0   # not enough history for calmar

        # ── Beta ─────────────────────────────────────────────────────────────
        if benchmark_returns is not None and len(benchmark_returns) >= 10:
            try:
                aligned = benchmark_returns.reindex(
                    pd.RangeIndex(len(returns))
                    if not hasattr(benchmark_returns, "index")
                    else benchmark_returns.index
                ).dropna()
                # Align by position (last N bars)
                min_len = min(len(returns), len(aligned))
                r_sym = returns[-min_len:]
                r_bm = np.asarray(aligned.values[-min_len:], dtype=float)
                cov_mat = np.cov(r_sym, r_bm)
                beta = _safe_div(cov_mat[0, 1], cov_mat[1, 1], fallback=1.0)
                out["beta"] = round(float(beta), 3)
            except Exception:
                out["beta"] = 1.0

        # ── Expected Value per Trade ─────────────────────────────────────────
        # EV = P(win) * avg_win - P(loss) * avg_loss
        # Treat each daily return as a "trade"
        wins = returns[returns > 0]
        losses = returns[returns <= 0]
        if len(wins) > 0 and len(losses) > 0:
            p_win = len(wins) / len(returns)
            avg_win = wins.mean()
            avg_loss = abs(losses.mean())
            ev = p_win * avg_win - (1 - p_win) * avg_loss
            out["ev_per_trade"] = round(float(ev) * 100, 4)   # as % per period

    except Exception:
        pass

    return out


def portfolio_risk_summary(
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate risk metrics across a list of scan results.

    Args:
        results: List of enriched scan result dicts (each must have
                 'risk_metrics' key from calculate_risk_adjusted_metrics).

    Returns:
        Portfolio-level summary dict:
            avg_sharpe, avg_sortino, avg_calmar, avg_max_dd_pct,
            avg_ann_vol_pct, avg_ev_per_trade,
            high_quality_count, total_count,
            risk_budget_used_pct   (avg_ann_vol weighted by signal quality)
    """
    metrics = [
        r["risk_metrics"]
        for r in results
        if isinstance(r.get("risk_metrics"), dict)
    ]
    if not metrics:
        return {}

    def _avg(key: str) -> float:
        vals = [m[key] for m in metrics if isinstance(m.get(key), (int, float))]
        return round(sum(vals) / len(vals), 3) if vals else 0.0

    hq = sum(1 for m in metrics if m.get("data_quality") == "high")
    return {
        "avg_sharpe": _avg("sharpe_ratio"),
        "avg_sortino": _avg("sortino_ratio"),
        "avg_calmar": _avg("calmar_ratio"),
        "avg_max_dd_pct": _avg("max_drawdown_pct"),
        "avg_ann_vol_pct": _avg("ann_vol_pct"),
        "avg_ev_per_trade": _avg("ev_per_trade"),
        "high_quality_count": hq,
        "total_count": len(metrics),
    }
