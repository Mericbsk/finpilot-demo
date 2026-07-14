"""EODHD News Sentiment factor (env-gated, cache-based — hot-path safe).

Mirrors scanner.catalyst: the scan hot-path only READS a scheduler-populated
cache (``data/sentiment_cache.json``); no per-symbol network call happens during
a scan. A scheduler job calls :func:`refresh_sentiment_cache` (which hits the
EODHD News Sentiment API) off the hot path, exactly like the catalyst cache.

The value is normalised to ``0.0–1.0`` with ``0.5 = neutral`` so it plugs
straight into score_engine's existing ±0.5 sentiment hook
(``compute_recommendation_score(..., sentiment_score=...)``). Missing data →
0.5 (neutral = no score effect).

Enable with both:
    FINPILOT_ENABLE_SENTIMENT=1
    EODHD_API_KEY=<your key>

Discipline note (audit): this is INTENTIONALLY cache-only on the hot path and
best-effort everywhere, so it can never become another "looks wired but silently
broken / slow per-symbol network" factor. Prove it helps via the weekly Edge
Report (bucket by sentiment) BEFORE trusting it in live decisions.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_CACHE_PATH = Path("data/sentiment_cache.json")
_EODHD_URL = "https://eodhd.com/api/sentiments"
_REQUEST_TIMEOUT = 10.0
_RATE_LIMIT_SLEEP = 0.05  # gentle pacing between symbols during refresh
_LOOKBACK_DAYS = 7
_NEUTRAL = 0.5


def _api_key() -> str:
    return os.environ.get("EODHD_API_KEY", "").strip()


def sentiment_enabled() -> bool:
    """True only when the flag is on AND an EODHD key is present."""
    return os.environ.get("FINPILOT_ENABLE_SENTIMENT", "0") == "1" and bool(_api_key())


def _normalise(raw: float) -> float:
    """Map EODHD 'normalized' sentiment (-1..1) to 0..1 (0.5 = neutral)."""
    try:
        v = (float(raw) + 1.0) / 2.0
        return round(max(0.0, min(1.0, v)), 4)
    except Exception:
        return _NEUTRAL


# ---------------------------------------------------------------------------
# Network path — scheduler only (NOT the scan hot path)
# ---------------------------------------------------------------------------
def _get(url: str, params: dict[str, Any]) -> Any:
    """GET returning parsed JSON, or None on any failure. Best-effort."""
    try:
        import requests  # noqa: PLC0415

        resp = requests.get(url, params=params, timeout=_REQUEST_TIMEOUT)
        if resp.status_code != 200:
            logger.debug("sentiment: EODHD %s -> HTTP %s", url, resp.status_code)
            return None
        return resp.json()
    except Exception as exc:  # noqa: BLE001
        logger.debug("sentiment: EODHD request failed: %s", exc)
        return None


def _latest_normalised_for(payload: Any, eodhd_symbol: str) -> float | None:
    """Extract the most recent 'normalized' value from an EODHD response.

    EODHD returns ``{"AAPL.US": [{"date": "...", "count": N, "normalized": x}, ...]}``.
    Defensive: tolerates dict-keyed or bare-list shapes and missing fields.
    """
    try:
        rows = None
        if isinstance(payload, dict):
            rows = payload.get(eodhd_symbol) or payload.get(eodhd_symbol.upper())
            if rows is None and len(payload) == 1:
                rows = next(iter(payload.values()))
        elif isinstance(payload, list):
            rows = payload
        if not rows:
            return None
        # Rows are date-ascending; take the last with a 'normalized' field.
        for row in reversed(rows):
            if isinstance(row, dict) and "normalized" in row:
                return float(row["normalized"])
        return None
    except Exception:
        return None


def refresh_sentiment_cache(symbols: list[str], days: int = _LOOKBACK_DAYS) -> dict[str, float]:
    """Fetch EODHD news sentiment for ``symbols`` and write the cache atomically.

    Intended to be called by a scheduler job (off the scan hot path). Returns
    the ``{symbol: factor_0_1}`` map it wrote. No-op returning {} when disabled.
    """
    if not sentiment_enabled():
        logger.info("sentiment: refresh skipped (flag off or no EODHD_API_KEY)")
        return {}

    from datetime import UTC, datetime, timedelta  # noqa: PLC0415

    to_d = datetime.now(tz=UTC).date()
    from_d = to_d - timedelta(days=days)
    key = _api_key()

    out: dict[str, float] = {}
    for sym in symbols:
        eodhd_symbol = sym if "." in sym else f"{sym}.US"
        payload = _get(
            _EODHD_URL,
            {
                "s": eodhd_symbol,
                "from": from_d.isoformat(),
                "to": to_d.isoformat(),
                "api_token": key,
                "fmt": "json",
            },
        )
        raw = _latest_normalised_for(payload, eodhd_symbol)
        out[sym] = _normalise(raw) if raw is not None else _NEUTRAL
        time.sleep(_RATE_LIMIT_SLEEP)

    try:
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = _CACHE_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
        tmp.replace(_CACHE_PATH)
        logger.info("sentiment: cached %d symbols → %s", len(out), _CACHE_PATH)
    except Exception as exc:  # noqa: BLE001
        logger.warning("sentiment: cache write failed (non-fatal): %s", exc)
    return out


# ---------------------------------------------------------------------------
# Hot path — cache read only (no network)
# ---------------------------------------------------------------------------
def _load_cache() -> dict[str, float]:
    try:
        if not _CACHE_PATH.exists():
            return {}
        data = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def compute_sentiment_factor(symbol: str) -> float:
    """Return the cached 0.0–1.0 sentiment factor for ``symbol`` (0.5 = neutral).

    Hot-path safe: reads only the scheduler-populated cache, never the network.
    Missing symbol / missing cache → 0.5 (neutral → no score effect).
    """
    try:
        return float(_load_cache().get(symbol, _NEUTRAL))
    except Exception:
        return _NEUTRAL
