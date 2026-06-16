"""Yahoo Finance Screener — INT-2 (yfinance >=1.4.1)

EquityQuery / Screener API wrapper.  Falls back gracefully when
yfinance < 1.4.1 or when the screener endpoint is unavailable.

Usage::

    from scanner.screener import build_query, run_screener, quick_universe

    # Screener-based symbol list
    symbols = run_screener(
        sector="Technology",
        min_volume=500_000,
        min_price=5.0,
        max_results=200,
    )

    # Quick preset universe by name
    symbols = quick_universe("nasdaq_tech_large")
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# yfinance version detection
# ─────────────────────────────────────────────────────────────────────────────

_YF_SCREENER_AVAILABLE = False
_YF_VERSION = "0.0.0"

try:
    import yfinance as yf

    _YF_VERSION = getattr(yf, "__version__", "0.0.0")
    _major, _minor, *_ = (_YF_VERSION + ".0.0").split(".")
    if (int(_major), int(_minor)) >= (1, 4):
        from yfinance import EquityQuery, screen  # type: ignore[attr-defined]

        _YF_SCREENER_AVAILABLE = True
        logger.info("screener: yfinance %s — EquityQuery/Screener available", _YF_VERSION)
    else:
        logger.info("screener: yfinance %s — EquityQuery not available (need >=1.4.1)", _YF_VERSION)
except Exception as _exc:
    logger.debug("screener: yfinance import failed: %s", _exc)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

# GICS sector → Yahoo Finance sector name mapping
_SECTOR_MAP: dict[str, str] = {
    "Technology": "Technology",
    "Information Technology": "Technology",
    "Health Care": "Healthcare",
    "Healthcare": "Healthcare",
    "Financials": "Financial Services",
    "Financial Services": "Financial Services",
    "Consumer Discretionary": "Consumer Cyclical",
    "Consumer Staples": "Consumer Defensive",
    "Energy": "Energy",
    "Industrials": "Industrials",
    "Materials": "Basic Materials",
    "Real Estate": "Real Estate",
    "Communication Services": "Communication Services",
    "Utilities": "Utilities",
}

# Pre-built query presets
_PRESET_QUERIES: dict[str, dict[str, Any]] = {
    "nasdaq_tech_large": {
        "sector": "Technology",
        "exchange": "NMS",
        "min_volume": 1_000_000,
        "min_price": 10.0,
        "max_results": 300,
    },
    "sp500_core": {
        "min_market_cap": 10_000_000_000,
        "min_volume": 500_000,
        "min_price": 5.0,
        "max_results": 500,
    },
    "us_momentum": {
        "min_volume": 1_000_000,
        "min_price": 10.0,
        "max_results": 400,
    },
    "healthcare_growth": {
        "sector": "Healthcare",
        "min_volume": 500_000,
        "min_price": 5.0,
        "max_results": 200,
    },
    "energy_sector": {
        "sector": "Energy",
        "min_volume": 300_000,
        "min_price": 3.0,
        "max_results": 150,
    },
    "financials": {
        "sector": "Financial Services",
        "min_volume": 500_000,
        "min_price": 5.0,
        "max_results": 200,
    },
}


def build_query(
    sector: str | None = None,
    exchange: str | None = None,
    min_volume: int = 0,
    min_price: float = 0.0,
    min_market_cap: int = 0,
) -> Any:
    """Build a yfinance EquityQuery from filter parameters.

    Returns None if EquityQuery is unavailable.
    """
    if not _YF_SCREENER_AVAILABLE:
        return None

    try:
        conditions: list[Any] = []

        if min_volume > 0:
            conditions.append(EquityQuery("gt", ["avgdailyvol3m", min_volume]))

        if min_price > 0:
            conditions.append(EquityQuery("gt", ["intradayprice", min_price]))

        if sector:
            yahoo_sector = _SECTOR_MAP.get(sector, sector)
            conditions.append(EquityQuery("eq", ["sector", yahoo_sector]))

        if exchange:
            conditions.append(EquityQuery("eq", ["exchange", exchange]))

        if min_market_cap > 0:
            conditions.append(EquityQuery("gt", ["intradaymarketcap", min_market_cap]))

        if not conditions:
            return None

        # Chain AND conditions
        query = conditions[0]
        for cond in conditions[1:]:
            query = EquityQuery("and", [query, cond])

        return query

    except Exception as exc:
        logger.debug("screener: build_query failed: %s", exc)
        return None


def run_screener(
    sector: str | None = None,
    exchange: str | None = None,
    min_volume: int = 500_000,
    min_price: float = 2.0,
    min_market_cap: int = 0,
    max_results: int = 200,
    sort_by: str = "percentchange",
    sort_asc: bool = False,
) -> list[str]:
    """Run Yahoo Finance screener and return a list of ticker symbols.

    Falls back to empty list (not an error) when:
    - yfinance < 1.4.1
    - Screener endpoint is unavailable / rate-limited

    Args:
        sector:         GICS sector name (e.g. "Technology")
        exchange:       Exchange code (e.g. "NMS" for NASDAQ, "NYQ" for NYSE)
        min_volume:     Minimum 3-month average daily volume
        min_price:      Minimum current price
        min_market_cap: Minimum market cap in USD
        max_results:    Maximum symbols to return
        sort_by:        Field to sort by (percentchange, marketCap, etc.)
        sort_asc:       Sort ascending if True

    Returns:
        List of ticker strings, empty on failure.
    """
    if not _YF_SCREENER_AVAILABLE:
        logger.debug("screener: yfinance EquityQuery not available — returning empty list")
        return []

    query = build_query(
        sector=sector,
        exchange=exchange,
        min_volume=min_volume,
        min_price=min_price,
        min_market_cap=min_market_cap,
    )

    if query is None:
        logger.debug("screener: no query conditions — returning empty list")
        return []

    try:
        response = screen(query, size=min(max_results, 500), sortField=sort_by, sortAsc=sort_asc)
        if response is None:
            return []

        quotes = response.get("quotes", [])
        symbols = [q["symbol"] for q in quotes if q.get("symbol")]
        logger.info(
            "screener: returned %d symbols (sector=%s, exchange=%s)",
            len(symbols),
            sector,
            exchange,
        )
        return symbols[:max_results]

    except Exception as exc:
        logger.debug("screener: screen() failed: %s", exc)
        return []


def quick_universe(preset: str) -> list[str]:
    """Return symbols for a named preset using the screener.

    If the screener is unavailable, returns an empty list (caller should
    fall back to static ``stock_presets.json``).
    """
    params = _PRESET_QUERIES.get(preset)
    if not params:
        logger.warning("screener: unknown preset '%s'", preset)
        return []
    return run_screener(**params)  # type: ignore[arg-type]


def is_available() -> bool:
    """Return True if the screener API is functional."""
    return _YF_SCREENER_AVAILABLE


__all__ = [
    "build_query",
    "run_screener",
    "quick_universe",
    "is_available",
    "_YF_VERSION",
    "_YF_SCREENER_AVAILABLE",
]
