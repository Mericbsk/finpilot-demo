"""FRED macro-regime classifier (env-gated, default OFF).

FinPilot's regime gate is price-only (SPY vs EMA200). It has no view of the
macro backdrop, so it sizes small-cap squeeze/catalyst plays the same in a
risk-on melt-up and a risk-off VIX spike — exactly when those plays fail.

This module pulls a handful of daily FRED series and classifies the market into
``risk_on`` / ``neutral`` / ``risk_off``. The classification drives
:func:`macro_factor_multiplier`, which dampens the squeeze and catalyst factors
when conditions are hostile.

Series used (all free, daily):
  * ``VIXCLS``  — CBOE volatility index.
  * ``T10Y2Y``  — 10y minus 2y Treasury spread (negative = inverted curve).

Requires a free ``FRED_API_KEY``. When the key or flag is absent the module is
a complete no-op (multiplier 1.0).
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_FRED_URL = "https://api.stlouisfed.org/fred/series/observations"
_REQUEST_TIMEOUT = 10.0
_CACHE_PATH = Path("data/macro_regime.json")
_MEMO_TTL = 3600.0  # re-read the on-disk classification at most hourly

# Classification thresholds.
_VIX_HIGH = 25.0
_VIX_ELEVATED = 20.0
_VIX_LOW = 16.0

# Factor multipliers per regime (applied to squeeze/catalyst additive terms).
_MULTIPLIER = {"risk_on": 1.0, "neutral": 1.0, "risk_off": 0.5}

# In-memory memo: {"regime": str, "ts": float}.
_MEMO: dict[str, Any] = {}


def fred_enabled() -> bool:
    return os.environ.get("FINPILOT_ENABLE_FRED_MACRO", "0") == "1" and bool(
        os.environ.get("FRED_API_KEY")
    )


def _fetch_latest(series_id: str) -> float | None:
    """Return the most recent numeric observation for ``series_id`` from FRED."""
    api_key = os.environ.get("FRED_API_KEY", "")
    if not api_key:
        return None
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 100,
    }
    try:
        import requests  # noqa: PLC0415

        resp = requests.get(_FRED_URL, params=params, timeout=_REQUEST_TIMEOUT)
        resp.raise_for_status()
        for obs in resp.json().get("observations", []):
            val = obs.get("value")
            if val not in (None, ".", ""):
                return float(val)
    except Exception as exc:
        logger.debug("macro_regime: fetch %s failed: %s", series_id, exc)
    return None


def classify_regime(vix: float | None, spread: float | None) -> str:
    """Classify the macro regime from VIX and the 10y-2y spread."""
    if vix is None:
        return "neutral"
    if vix >= _VIX_HIGH or (vix >= _VIX_ELEVATED and spread is not None and spread < 0):
        return "risk_off"
    if vix <= _VIX_LOW and (spread is None or spread > 0):
        return "risk_on"
    return "neutral"


def refresh_macro_regime() -> dict[str, Any]:
    """Fetch FRED series, classify, and persist ``data/macro_regime.json``.

    Intended to be called from a daily scheduler job. No-op (returns neutral)
    when the feature is disabled.
    """
    if not fred_enabled():
        return {"regime": "neutral", "vix": None, "spread": None}

    vix = _fetch_latest("VIXCLS")
    spread = _fetch_latest("T10Y2Y")
    regime = classify_regime(vix, spread)
    payload = {
        "regime": regime,
        "vix": vix,
        "spread": spread,
        "updated": datetime.now(tz=UTC).isoformat(),
    }
    try:
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = _CACHE_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        tmp.replace(_CACHE_PATH)
    except OSError as exc:
        logger.warning("macro_regime: cache write failed: %s", exc)

    _MEMO["regime"] = regime
    _MEMO["ts"] = time.time()
    logger.info("macro_regime: %s (vix=%s, spread=%s)", regime, vix, spread)
    return payload


def get_macro_regime() -> str:
    """Return the cached macro regime ('risk_on'/'neutral'/'risk_off')."""
    now = time.time()
    if _MEMO.get("regime") and now - _MEMO.get("ts", 0.0) < _MEMO_TTL:
        return str(_MEMO["regime"])
    regime = "neutral"
    try:
        payload = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        regime = str(payload.get("regime", "neutral"))
    except (OSError, ValueError):
        regime = "neutral"
    _MEMO["regime"] = regime
    _MEMO["ts"] = now
    return regime


def macro_factor_multiplier() -> float:
    """Return the multiplier applied to squeeze/catalyst factors.

    1.0 when disabled or in a benign regime; 0.5 in a risk-off regime.
    """
    if not fred_enabled():
        return 1.0
    return _MULTIPLIER.get(get_macro_regime(), 1.0)
