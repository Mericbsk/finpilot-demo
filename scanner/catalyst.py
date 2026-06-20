"""SEC EDGAR catalyst feed (env-gated, default OFF).

FinPilot has news-based sentiment but no primary-document feed. Material
events surface first in SEC filings:

  * **8-K**  — material event (M&A, guidance, contracts) → bullish catalyst.
  * **4**    — insider transaction → mild positive presence signal.
  * **S-1 / 424B** — securities offering / shelf takedown → dilution, bearish.

This module pulls the *submissions* feed (no API key, only a ``User-Agent`` is
required by SEC) and converts recent filings into a signed ``catalyst_factor``
in ``[-1.0, 1.0]``.

Hot-path safety: per-symbol live fetches would hit SEC's 10 req/s limit during
a scan, so :func:`refresh_catalyst_cache` pre-populates ``data/catalyst_cache.json``
from a scheduler job and :func:`compute_catalyst_factor` reads only from cache.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────
# SEC requires a descriptive User-Agent with contact info. Override via env.
_DEFAULT_UA = "FinPilot/1.0 (contact: set SEC_EDGAR_USER_AGENT)"
_SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:0>10}.json"
_REQUEST_TIMEOUT = 10.0
_RATE_LIMIT_SLEEP = 0.15  # ~6.6 req/s, under SEC's 10 req/s ceiling

_CACHE_PATH = Path("data/catalyst_cache.json")
_LOOKBACK_DAYS = 7

# Signed weights per form type. 8-K is the primary bullish catalyst; offerings
# are dilutive (bearish). Form 4 buy/sell direction is not available from the
# submissions feed, so it carries a small direction-agnostic positive weight.
_CATALYST_WEIGHTS: dict[str, float] = {
    "8-K": 0.6,
    "4": 0.3,
    "S-1": -0.5,
    "424B5": -0.5,
    "424B3": -0.5,
    "424B4": -0.5,
}

# In-memory caches.
_TICKER_CIK_MAP: dict[str, str] | None = None
_FACTOR_CACHE: dict[str, float] | None = None


def _user_agent() -> str:
    return os.environ.get("SEC_EDGAR_USER_AGENT", _DEFAULT_UA)


def edgar_enabled() -> bool:
    return os.environ.get("FINPILOT_ENABLE_EDGAR_CATALYST", "0") == "1"


def _get(url: str) -> Any:
    """GET ``url`` with the SEC-required User-Agent. Returns parsed JSON or None."""
    try:
        import requests  # noqa: PLC0415

        resp = requests.get(url, headers={"User-Agent": _user_agent()}, timeout=_REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.debug("catalyst: GET %s failed: %s", url, exc)
        return None


def _load_ticker_cik_map(force: bool = False) -> dict[str, str]:
    """Return a ``{TICKER: zero-padded-CIK}`` map, cached in memory."""
    global _TICKER_CIK_MAP
    if _TICKER_CIK_MAP is not None and not force:
        return _TICKER_CIK_MAP

    data = _get(_SEC_TICKERS_URL)
    mapping: dict[str, str] = {}
    if isinstance(data, dict):
        for row in data.values():
            try:
                ticker = str(row["ticker"]).upper()
                mapping[ticker] = str(int(row["cik_str"]))
            except (KeyError, TypeError, ValueError):
                continue
    _TICKER_CIK_MAP = mapping
    return mapping


def fetch_recent_filings(symbol: str, days: int = _LOOKBACK_DAYS) -> list[dict[str, str]]:
    """Return recent filings ``[{form, date}]`` for ``symbol`` within ``days``."""
    cik = _load_ticker_cik_map().get(symbol.upper())
    if not cik:
        return []

    data = _get(_SEC_SUBMISSIONS_URL.format(cik=cik))
    recent = (data or {}).get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    if not forms or not dates:
        return []

    cutoff = (datetime.now(tz=UTC) - timedelta(days=days)).date()
    out: list[dict[str, str]] = []
    for form, date_str in zip(forms, dates, strict=False):
        try:
            filed = datetime.strptime(date_str, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            continue
        if filed >= cutoff:
            out.append({"form": str(form), "date": date_str})
    return out


def _score_filings(filings: list[dict[str, str]]) -> float:
    """Convert a filing list into a signed catalyst factor in [-1.0, 1.0]."""
    seen: set[str] = set()
    total = 0.0
    for f in filings:
        form = f.get("form", "")
        weight = _CATALYST_WEIGHTS.get(form)
        if weight is None or form in seen:
            continue
        seen.add(form)  # count each catalyst type at most once
        total += weight
    return round(max(-1.0, min(1.0, total)), 4)


def refresh_catalyst_cache(symbols: list[str], days: int = _LOOKBACK_DAYS) -> dict[str, float]:
    """Refresh the on-disk catalyst factor cache for ``symbols``.

    Intended to be called from a scheduler job. Respects SEC's rate limit with a
    short sleep between requests. Writes ``data/catalyst_cache.json`` atomically.
    """
    global _FACTOR_CACHE
    if not symbols:
        return {}

    _load_ticker_cik_map(force=True)
    factors: dict[str, float] = {}
    for sym in symbols:
        try:
            filings = fetch_recent_filings(sym, days=days)
            factors[sym.upper()] = _score_filings(filings)
        except Exception as exc:
            logger.debug("catalyst: refresh(%s) failed: %s", sym, exc)
            factors[sym.upper()] = 0.0
        time.sleep(_RATE_LIMIT_SLEEP)

    payload = {"updated": datetime.now(tz=UTC).isoformat(), "factors": factors}
    try:
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = _CACHE_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        tmp.replace(_CACHE_PATH)
    except OSError as exc:
        logger.warning("catalyst: cache write failed: %s", exc)

    _FACTOR_CACHE = factors
    logger.info("catalyst: refreshed %d symbols", len(factors))
    return factors


def _load_factor_cache() -> dict[str, float]:
    """Load the catalyst factor cache from disk (memoised)."""
    global _FACTOR_CACHE
    if _FACTOR_CACHE is not None:
        return _FACTOR_CACHE
    try:
        payload = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        _FACTOR_CACHE = dict(payload.get("factors", {}))
    except (OSError, ValueError):
        _FACTOR_CACHE = {}
    return _FACTOR_CACHE


def compute_catalyst_factor(symbol: str) -> float:
    """Return the cached signed catalyst factor for ``symbol`` (0.0 if unknown).

    Reads only from the cache populated by :func:`refresh_catalyst_cache`, so it
    is safe to call from the scanner hot path without hitting SEC.
    """
    if not edgar_enabled():
        return 0.0
    return float(_load_factor_cache().get(symbol.upper(), 0.0))
