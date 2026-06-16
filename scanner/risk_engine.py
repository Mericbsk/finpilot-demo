"""Scanner Risk Engine — Sprint 5 T3

ATR-based dynamic stop-loss, take-profit, and position sizing extracted
from scanner/evaluate.py so it can be unit-tested and adjusted without
touching the main evaluation pipeline.

Yang-Zhang volatility estimator added 2026-06-12 (Faz 1 P1):
  Reduces false-stop rate by using overnight gap + intraday range together,
  as documented in Yang & Zhang (2000) and Rogers-Satchell (1991).
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# Portfolio drawdown gate state file (resets daily)
_DD_STATE_PATH = Path(__file__).resolve().parents[1] / "data" / "portfolio_dd_state.json"


def daily_dd_breached(threshold: float = 0.03) -> bool:
    """Return True if today's realised portfolio drawdown >= threshold (fraction).

    Reads data/portfolio_dd_state.json:
        { "date": "YYYY-MM-DD", "start_equity": float, "current_equity": float }

    A missing/stale/malformed file is treated as "not breached" (fail-open so
    the scanner keeps running when state isn't initialised). Stale = date older
    than today (UTC); the file is logically reset on the first read of a new day.
    """
    try:
        if not _DD_STATE_PATH.exists():
            return False
        data = json.loads(_DD_STATE_PATH.read_text(encoding="utf-8"))
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        if str(data.get("date")) != today:
            return False  # stale: new day, no DD yet
        start = float(data.get("start_equity", 0) or 0)
        current = float(data.get("current_equity", 0) or 0)
        if start <= 0:
            return False
        dd = (start - current) / start
        return dd >= float(threshold)
    except Exception:
        return False


def record_equity_snapshot(equity: float) -> None:
    """Update the daily DD state file. Initialises start_equity on first call of the day."""
    try:
        _DD_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        state: dict[str, Any] = {}
        if _DD_STATE_PATH.exists():
            try:
                state = json.loads(_DD_STATE_PATH.read_text(encoding="utf-8"))
            except Exception:
                state = {}
        if state.get("date") != today:
            state = {"date": today, "start_equity": float(equity)}
        state["current_equity"] = float(equity)
        state["updated_at"] = datetime.now(UTC).isoformat()
        _DD_STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception:
        pass


# Suppress unused-import warnings if timedelta gets pruned by ruff later
_ = timedelta


# ── Yang-Zhang Volatility ─────────────────────────────────────────────────────


def yang_zhang_vol(df: pd.DataFrame, window: int = 20, k: float = 0.34) -> float:
    """Compute Yang-Zhang close-to-close volatility estimate (annualised daily σ).

    Yang-Zhang combines three components:
    - σ²_overnight : variance of overnight log-returns  (Close[t-1] → Open[t])
    - σ²_openclose : variance of open-to-close log-returns
    - σ²_rs        : Rogers-Satchell intraday variance (uses H, L, O, C)

    Formula:
        σ²_YZ = σ²_overnight + k·σ²_openclose + (1-k)·σ²_rs

    The result is the *daily* σ (not annualised), matching ATR units.

    Args:
        df:     DataFrame with columns Open, High, Low, Close (sorted oldest→newest).
        window: Number of bars to use (default 20 trading days ≈ 1 month).
        k:      Weighting parameter (Yang-Zhang optimal ≈ 0.34).

    Returns:
        Daily volatility estimate (same units as price, i.e. σ·Close_last).
        Falls back to ATR-proxy (0.01 × last_close) on any error.
    """
    try:
        needed = ["Open", "High", "Low", "Close"]
        for col in needed:
            if col not in df.columns:
                raise ValueError(f"Missing column: {col}")
        tail = df[needed].tail(window + 1).copy()
        if len(tail) < window + 1:
            raise ValueError("Insufficient rows")
        o = tail["Open"].astype(float).values
        h = tail["High"].astype(float).values
        lv = tail["Low"].astype(float).values
        c = tail["Close"].astype(float).values

        # Overnight returns: log(Open[t] / Close[t-1])
        log_oc = np.log(o[1:] / c[:-1])
        # Open-to-close returns: log(Close[t] / Open[t])
        log_co = np.log(c[1:] / o[1:])
        # Rogers-Satchell per-bar: log(H/C)*log(H/O) + log(L/C)*log(L/O)
        log_ho = np.log(h[1:] / o[1:])
        log_hc = np.log(h[1:] / c[1:])
        log_lo = np.log(lv[1:] / o[1:])
        log_lc = np.log(lv[1:] / c[1:])
        rs = log_ho * log_hc + log_lo * log_lc

        n = len(log_oc)
        mu_oc = log_oc.mean()
        mu_co = log_co.mean()
        var_overnight = ((log_oc - mu_oc) ** 2).sum() / (n - 1)
        var_openclose = ((log_co - mu_co) ** 2).sum() / (n - 1)
        var_rs = rs.mean()

        var_yz = var_overnight + k * var_openclose + (1.0 - k) * var_rs
        # σ in log-return space → convert to price units via last close
        sigma_log = math.sqrt(max(var_yz, 1e-12))
        last_close = float(c[-1])
        return sigma_log * last_close
    except Exception:
        try:
            return 0.01 * float(df["Close"].iloc[-1])
        except Exception:
            return 0.0


def calculate_risk_management_yz(
    price: float,
    df: pd.DataFrame,
    momentum_score: int,
    yz_window: int = 20,
) -> dict[str, Any]:
    """ATR-independent TP/SL using Yang-Zhang volatility.

    Drops-in as a replacement for calculate_risk_management() when a DataFrame
    with OHLC columns is available. The multipliers mirror the ATR version so
    the strategy_tag tiers remain unchanged.

    Args:
        price:          Current entry price.
        df:             Daily OHLC DataFrame (≥21 rows recommended).
        momentum_score: 0-100 composite momentum score.
        yz_window:      Number of bars for YZ estimation (default 20).

    Returns:
        Same dict shape as calculate_risk_management().
    """
    yz_val = yang_zhang_vol(df, window=yz_window)
    # YZ already in price units (σ × last_close); treat identically to ATR
    return calculate_risk_management(price=price, atr_val=yz_val, momentum_score=momentum_score)


def calculate_risk_management(price: float, atr_val: float, momentum_score: int) -> dict[str, Any]:
    """ATR-based dynamic stop-loss & take-profit.

    Multipliers are chosen by momentum tier:
      - Sniper  (score >= 70): tighter stop, aggressive targets
      - Normal  (50-69):       balanced
      - Defansif (score < 50): wider stop, conservative targets

    Args:
        price:          Current entry price
        atr_val:        Average True Range (same unit as price)
        momentum_score: 0-100 composite momentum score from evaluate_symbol

    Returns:
        Dict with stop_loss, take_profit, tp1/tp2/tp3, risk_reward_ratio,
        stop_loss_percent, position_size, strategy_tag.
    """
    if momentum_score >= 70:
        stop_mult, tp1_mult, tp2_mult, tp3_mult = 1.5, 3.0, 5.0, 8.0
        strategy_tag = "Sniper 🎯"
    elif momentum_score < 50:
        stop_mult, tp1_mult, tp2_mult, tp3_mult = 2.5, 4.5, 6.5, 0
        strategy_tag = "Defansif 🛡️"
    else:
        stop_mult, tp1_mult, tp2_mult, tp3_mult = 2.0, 3.5, 5.5, 7.5
        strategy_tag = "Normal 📈"

    stop_loss = price - (atr_val * stop_mult)
    tp1 = price + (atr_val * tp1_mult)
    tp2 = price + (atr_val * tp2_mult)
    tp3 = price + (atr_val * tp3_mult) if tp3_mult > 0 else 0
    take_profit = tp2
    position_size = 1000
    risk_reward_ratio = (
        (take_profit - price) / (price - stop_loss) if (price - stop_loss) != 0 else 0
    )
    stop_loss_percent = (price - stop_loss) / price * 100 if price != 0 else 0

    return {
        "stop_loss": round(stop_loss, 2),
        "take_profit": round(take_profit, 2),
        "tp1": round(tp1, 2),
        "tp2": round(tp2, 2),
        "tp3": round(tp3, 2) if tp3 > 0 else None,
        "strategy_tag": strategy_tag,
        "position_size": position_size,
        "risk_reward_ratio": round(risk_reward_ratio, 2),
        "stop_loss_percent": round(stop_loss_percent, 2),
    }
