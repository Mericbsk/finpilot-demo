"""Generate stock_presets.json dynamically from FinanceDatabase (INT-1).

Usage::

    python scripts/generate_presets.py                  # Write data/stock_presets.json
    python scripts/generate_presets.py --dry-run        # Print without writing
    python scripts/generate_presets.py --out custom.json

The generated file keeps the same schema as the existing static
``data/stock_presets.json`` so the rest of the application is unchanged.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Paths ────────────────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent
_OUT_DEFAULT = _ROOT / "data" / "stock_presets.json"


# ── FinanceDatabase availability guard ───────────────────────────────────────
try:
    import financedatabase as fd  # type: ignore[import]

    _FD_AVAILABLE = True
    logger.info("financedatabase %s loaded", getattr(fd, "__version__", "?"))
except ImportError:
    _FD_AVAILABLE = False
    logger.warning(
        "financedatabase not installed — "
        "run `pip install financedatabase>=0.3` to enable dynamic presets"
    )


# ── Symbol normalisation ─────────────────────────────────────────────────────
def _clean_symbols(symbols: list[str]) -> list[str]:
    """Remove empty, NaN and overly long tickers."""
    out: list[str] = []
    for s in symbols:
        if not isinstance(s, str):
            continue
        s = s.strip()
        if s and len(s) <= 10 and s not in out:
            out.append(s)
    return sorted(out)


# ── FinanceDatabase preset builders ─────────────────────────────────────────


def _fd_equities(
    sector: str | None = None,
    country: str | None = None,
    exchange: str | None = None,
    only_primary: bool = True,
    limit: int | None = None,
) -> list[str]:
    """Query FinanceDatabase for equities matching the given filters."""
    if not _FD_AVAILABLE:
        return []
    try:
        eq = fd.Equities()
        kwargs: dict = {"only_primary_listing": only_primary}
        if sector:
            kwargs["sector"] = sector
        if country:
            kwargs["country"] = country
        if exchange:
            kwargs["exchange"] = exchange

        df = eq.select(**kwargs)
        if df is None or df.empty:
            return []
        symbols = list(df.index)
        if limit:
            symbols = symbols[:limit]
        return _clean_symbols(symbols)
    except Exception as exc:
        logger.warning("financedatabase query failed (%s, %s): %s", sector, country, exc)
        return []


def _fd_etfs(country: str = "United States", limit: int = 200) -> list[str]:
    if not _FD_AVAILABLE:
        return []
    try:
        etfs = fd.ETFs()
        df = etfs.select(country=country)
        if df is None or df.empty:
            return []
        return _clean_symbols(list(df.index))[:limit]
    except Exception as exc:
        logger.warning("financedatabase ETF query failed: %s", exc)
        return []


# ── Static fallbacks (keeps existing high-quality curated lists) ─────────────
_STATIC_BIST_STARS = [
    "AKBNK.IS",
    "ARCLK.IS",
    "ASELS.IS",
    "BIMAS.IS",
    "DOHOL.IS",
    "EKGYO.IS",
    "EREGL.IS",
    "FROTO.IS",
    "GARAN.IS",
    "HALKB.IS",
    "ISCTR.IS",
    "KCHOL.IS",
    "KOZAA.IS",
    "KOZAL.IS",
    "KRDMD.IS",
    "PGSUS.IS",
    "SAHOL.IS",
    "SASA.IS",
    "SISE.IS",
    "TAVHL.IS",
    "TCELL.IS",
    "THYAO.IS",
    "TKFEN.IS",
    "TOASO.IS",
    "TTKOM.IS",
    "TTRAK.IS",
    "TUPRS.IS",
    "VAKBN.IS",
    "VESTL.IS",
    "YKBNK.IS",
]

_STATIC_US_MEGA = [
    "AAPL",
    "MSFT",
    "NVDA",
    "GOOGL",
    "AMZN",
    "META",
    "TSLA",
    "BRK-B",
    "AVGO",
    "JPM",
    "UNH",
    "V",
    "MA",
    "XOM",
    "COST",
    "HD",
    "ORCL",
    "BAC",
    "AMD",
    "LLY",
]

_STATIC_NASDAQ_CORE = [
    "AAPL",
    "MSFT",
    "NVDA",
    "GOOGL",
    "AMZN",
    "META",
    "TSLA",
    "AVGO",
    "COST",
    "AMD",
    "QCOM",
    "INTC",
    "TXN",
    "NFLX",
    "ADBE",
    "ASML",
    "ISRG",
    "ADP",
    "PANW",
    "SNPS",
    "CDNS",
    "KLAC",
    "LRCX",
    "MRVL",
    "AMAT",
    "FTNT",
    "CRWD",
    "ZS",
    "TEAM",
    "DDOG",
]


# ── Preset builder ────────────────────────────────────────────────────────────
def build_presets() -> list[dict]:
    """Return the complete preset list using FinanceDatabase + static fallbacks."""
    presets: list[dict] = []

    # ── 1. BIST Stars (Türkiye) ───────────────────────────────────────────────
    bist = _fd_equities(country="Turkey", only_primary=True, limit=100)
    if not bist:
        bist = _STATIC_BIST_STARS
        logger.info("preset[BIST Stars]: using static fallback (%d symbols)", len(bist))
    else:
        logger.info("preset[BIST Stars]: FinanceDatabase (%d symbols)", len(bist))
    presets.append({"name": "BIST Stars", "symbols": bist})

    # ── 2. US Mega Caps ───────────────────────────────────────────────────────
    presets.append({"name": "US Mega Caps", "symbols": _STATIC_US_MEGA})

    # ── 3. Nasdaq Tech (dynamic) ─────────────────────────────────────────────
    nasdaq_tech = _fd_equities(
        sector="Information Technology",
        country="United States",
        exchange="NMS",
        limit=400,
    )
    if not nasdaq_tech:
        nasdaq_tech = _STATIC_NASDAQ_CORE
        logger.info("preset[Nasdaq Tech]: using static fallback (%d symbols)", len(nasdaq_tech))
    else:
        logger.info("preset[Nasdaq Tech]: FinanceDatabase (%d symbols)", len(nasdaq_tech))
    presets.append({"name": "Nasdaq Tech", "symbols": nasdaq_tech})

    # ── 4. US Healthcare ─────────────────────────────────────────────────────
    healthcare = _fd_equities(
        sector="Healthcare",
        country="United States",
        only_primary=True,
        limit=300,
    )
    if not healthcare:
        healthcare = [
            "UNH",
            "JNJ",
            "LLY",
            "ABBV",
            "MRK",
            "TMO",
            "ABT",
            "DHR",
            "ISRG",
            "BSX",
            "MDT",
            "AMGN",
            "GILD",
            "CVS",
            "CI",
            "ELV",
            "HUM",
            "DXCM",
            "BIIB",
            "REGN",
        ]
    logger.info("preset[US Healthcare]: %d symbols", len(healthcare))
    presets.append({"name": "US Healthcare", "symbols": healthcare})

    # ── 5. US Financials ─────────────────────────────────────────────────────
    financials = _fd_equities(
        sector="Financial Services",
        country="United States",
        only_primary=True,
        limit=300,
    )
    if not financials:
        financials = [
            "JPM",
            "BAC",
            "WFC",
            "GS",
            "MS",
            "BLK",
            "SCHW",
            "C",
            "AXP",
            "BX",
            "KKR",
            "CB",
            "MMC",
            "AON",
            "PGR",
            "TRV",
            "ALL",
            "MET",
            "PRU",
            "AFL",
        ]
    logger.info("preset[US Financials]: %d symbols", len(financials))
    presets.append({"name": "US Financials", "symbols": financials})

    # ── 6. US Energy ─────────────────────────────────────────────────────────
    energy = _fd_equities(
        sector="Energy",
        country="United States",
        only_primary=True,
        limit=200,
    )
    if not energy:
        energy = [
            "XOM",
            "CVX",
            "COP",
            "EOG",
            "SLB",
            "MPC",
            "PSX",
            "VLO",
            "HAL",
            "DVN",
            "OXY",
            "HES",
            "CTRA",
            "FANG",
            "APA",
            "MRO",
            "BKR",
            "NOV",
            "RIG",
            "HP",
        ]
    logger.info("preset[US Energy]: %d symbols", len(energy))
    presets.append({"name": "US Energy", "symbols": energy})

    # ── 7. US Industrials ────────────────────────────────────────────────────
    industrials = _fd_equities(
        sector="Industrials",
        country="United States",
        only_primary=True,
        limit=250,
    )
    if not industrials:
        industrials = [
            "CAT",
            "RTX",
            "HON",
            "UPS",
            "LMT",
            "GE",
            "DE",
            "MMM",
            "ITW",
            "EMR",
            "ETN",
            "PH",
            "ROK",
            "CMI",
            "DOV",
            "XYL",
            "CARR",
            "OTIS",
            "GD",
            "NOC",
        ]
    logger.info("preset[US Industrials]: %d symbols", len(industrials))
    presets.append({"name": "US Industrials", "symbols": industrials})

    # ── 8. US Consumer Discretionary ─────────────────────────────────────────
    consumer = _fd_equities(
        sector="Consumer Cyclical",
        country="United States",
        only_primary=True,
        limit=250,
    )
    if not consumer:
        consumer = [
            "AMZN",
            "TSLA",
            "HD",
            "MCD",
            "NKE",
            "LOW",
            "SBUX",
            "BKNG",
            "MAR",
            "HLT",
            "CMG",
            "ORLY",
            "AZO",
            "BBY",
            "ROST",
            "TJX",
            "DG",
            "DLTR",
            "GPS",
            "FL",
        ]
    logger.info("preset[US Consumer]: %d symbols", len(consumer))
    presets.append({"name": "US Consumer Disc.", "symbols": consumer})

    # ── 9. ETFs Core ─────────────────────────────────────────────────────────
    etfs = _fd_etfs(country="United States", limit=150)
    if not etfs:
        etfs = [
            "SPY",
            "QQQ",
            "IWM",
            "DIA",
            "VTI",
            "VOO",
            "ARKK",
            "XLK",
            "XLV",
            "XLF",
            "XLE",
            "XLI",
            "XLB",
            "XLRE",
            "XLC",
            "XLU",
            "GLD",
            "SLV",
            "USO",
            "TLT",
        ]
    logger.info("preset[ETFs Core]: %d symbols", len(etfs))
    presets.append({"name": "ETFs Core", "symbols": etfs})

    # ── 10. Low Volatility US (strategy preset) ───────────────────────────────
    # Quality companies — manually curated for low-vol strategy
    low_vol = [
        "JNJ",
        "PG",
        "KO",
        "PEP",
        "WMT",
        "MCD",
        "MMM",
        "JCI",
        "ADP",
        "CL",
        "COST",
        "SYY",
        "GIS",
        "CPB",
        "HRL",
        "TSN",
        "MKC",
        "SJM",
        "CAG",
        "K",
        "KHC",
        "VZ",
        "T",
        "BCE",
        "TMUS",
        "ED",
        "SO",
        "DUK",
        "NEE",
        "AEP",
        "EXC",
        "XEL",
        "WEC",
        "DTE",
        "PPL",
        "ETR",
        "ES",
        "FE",
        "AES",
        "NI",
    ]
    logger.info("preset[Low Vol US]: %d symbols", len(low_vol))
    presets.append({"name": "Low Vol US (Strategy)", "symbols": low_vol})

    # ── 11. Short-Term Reversal Universe (strategy preset) ────────────────────
    # Broad liquid universe for reversal scanning
    reversal_universe = _fd_equities(
        country="United States",
        exchange="NMS",
        only_primary=True,
        limit=600,
    )
    if not reversal_universe:
        reversal_universe = _STATIC_NASDAQ_CORE + [
            "SPY",
            "QQQ",
            "IWM",
            "BA",
            "CAT",
            "JPM",
            "GS",
            "MS",
            "XOM",
            "CVX",
        ]
    logger.info("preset[Reversal Universe]: %d symbols", len(reversal_universe))
    presets.append({"name": "Reversal Universe", "symbols": reversal_universe})

    return presets


# ── Entry point ───────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Generate stock_presets.json from FinanceDatabase")
    parser.add_argument("--out", type=Path, default=_OUT_DEFAULT, help="Output JSON path")
    parser.add_argument("--dry-run", action="store_true", help="Print without writing")
    args = parser.parse_args()

    presets = build_presets()

    total_symbols = sum(len(p["symbols"]) for p in presets)
    logger.info("Total: %d presets, %d symbol entries", len(presets), total_symbols)

    payload = json.dumps(presets, indent=2, ensure_ascii=False)

    if args.dry_run:
        print(payload)
        return

    out_path: Path = args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(payload, encoding="utf-8")
    logger.info("Written to %s", out_path)


if __name__ == "__main__":
    main()
