"""Per-Regime Weight Set — Sprint 15

Three market regimes × 10 named weights.

Regime detection
----------------
Uses a simple SPY-based heuristic (can be replaced by ``regime_detection``
module later):
  - ``bull`` : SPY price > 200-day SMA
  - ``bear`` : SPY price < 200-day SMA AND 20d return < -5%
  - ``range``: everything else

Weight storage
--------------
``data/regime_weights.json`` — keys are "bull", "bear", "range".
Each value is a dict of 10 named weights matching
``research.lgbm_ranker.FEATURE_COLS`` semantics.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def is_enabled() -> bool:
    """Sprint 16 (S16-09): regime-weighted scoring feature flag.

    Disabled by default. Set ``FINPILOT_ENABLE_REGIME_WEIGHTS=1`` to enable.
    Until per-regime edge is demonstrated, scoring falls back to global
    champion weights. See ``docs/feature_flags.md``.
    """
    return os.getenv("FINPILOT_ENABLE_REGIME_WEIGHTS", "0").lower() in ("1", "true", "yes", "on")

_REGIME_WEIGHTS_PATH = Path("data/regime_weights.json")
_REGIME_SPY_CACHE: dict[str, Any] = {}
_REGIME_SPY_CACHE_TTL = 3600  # 1 hour

_lock = threading.Lock()

# Default weights per regime (sum doesn't need to equal 1; relative importance)
_DEFAULT_WEIGHTS: dict[str, dict[str, float]] = {
    "bull": {
        "score": 1.0,
        "rsi": 0.8,
        "macd_hist": 0.7,
        "volume_ratio": 0.5,
        "sector_rs": 0.9,
        "vol_regime": 0.3,
        "regime_encoded": 0.0,
        "p_win_calib": 1.2,
        "momentum_20d": 0.6,
        "earnings_proximity": -0.4,
    },
    "bear": {
        "score": 0.7,
        "rsi": 0.5,
        "macd_hist": 0.4,
        "volume_ratio": 0.6,
        "sector_rs": 1.1,
        "vol_regime": 0.8,
        "regime_encoded": 0.0,
        "p_win_calib": 1.4,
        "momentum_20d": -0.3,
        "earnings_proximity": -0.8,
    },
    "range": {
        "score": 0.9,
        "rsi": 1.0,
        "macd_hist": 0.6,
        "volume_ratio": 0.4,
        "sector_rs": 0.7,
        "vol_regime": 0.5,
        "regime_encoded": 0.0,
        "p_win_calib": 1.0,
        "momentum_20d": 0.2,
        "earnings_proximity": -0.5,
    },
}


def _load_regime_weights() -> dict[str, dict[str, float]]:
    if _REGIME_WEIGHTS_PATH.exists():
        try:
            with open(_REGIME_WEIGHTS_PATH) as fh:
                return json.load(fh)
        except Exception as exc:
            logger.warning("regime_weights: load failed: %s", exc)
    return {k: dict(v) for k, v in _DEFAULT_WEIGHTS.items()}


def _save_regime_weights(weights: dict[str, dict[str, float]]) -> None:
    _REGIME_WEIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_REGIME_WEIGHTS_PATH, "w") as fh:
        json.dump(weights, fh, indent=2)


def get_regime_weights(regime: str) -> dict[str, float]:
    """Return the weight dict for a given regime (bull/bear/range)."""
    with _lock:
        all_weights = _load_regime_weights()
    return all_weights.get(regime, dict(_DEFAULT_WEIGHTS["range"]))


def set_regime_weights(regime: str, weights: dict[str, float]) -> None:
    """Persist updated weights for a specific regime."""
    with _lock:
        all_weights = _load_regime_weights()
        all_weights[regime] = weights
        _save_regime_weights(all_weights)
    logger.info("regime_weights: updated regime=%s weights=%s", regime, list(weights.keys()))


def get_all_regime_weights() -> dict[str, dict[str, float]]:
    """Return all three regime weight dicts."""
    with _lock:
        return _load_regime_weights()


# ─────────────────────────────────────────────
# Regime detection (SPY heuristic)
# ─────────────────────────────────────────────

def detect_current_regime() -> str:
    """Detect market regime using SPY 200-day SMA heuristic.

    Returns ``"bull"``, ``"bear"``, or ``"range"``.
    Falls back to ``"range"`` on any error.
    """
    global _REGIME_SPY_CACHE
    now = time.time()
    cached = _REGIME_SPY_CACHE
    if cached.get("ts") and now - cached["ts"] < _REGIME_SPY_CACHE_TTL:
        return cached["regime"]  # type: ignore[return-value]

    try:
        import yfinance as yf  # type: ignore[import]
        import pandas as pd  # noqa: PLC0415

        spy = yf.download("SPY", period="1y", interval="1d", progress=False, auto_adjust=True)
        if spy.empty or len(spy) < 50:
            return "range"

        close = spy["Close"].squeeze()
        sma200 = close.rolling(min(200, len(close))).mean().iloc[-1]
        sma20 = close.rolling(20).mean().iloc[-1]
        price = float(close.iloc[-1])
        ret_20d = float((close.iloc[-1] - close.iloc[-21]) / close.iloc[-21]) if len(close) >= 21 else 0.0

        if price > float(sma200):
            regime = "bull"
        elif price < float(sma200) and ret_20d < -0.05:
            regime = "bear"
        else:
            regime = "range"

        _REGIME_SPY_CACHE = {"regime": regime, "ts": now, "price": price, "sma200": float(sma200)}
        logger.info("regime_detection: SPY=%.2f SMA200=%.2f ret20d=%.2f%% → %s", price, float(sma200), ret_20d * 100, regime)
        return regime
    except Exception as exc:
        logger.debug("regime_detection: failed: %s", exc)
        return "range"


def get_active_weights() -> dict[str, float]:
    """Return weight dict for the currently detected regime."""
    regime = detect_current_regime()
    return get_regime_weights(regime)
