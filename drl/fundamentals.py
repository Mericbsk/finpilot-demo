"""Fundamental data provider for FinPilot.

Fetches key fundamental metrics via yfinance:
  - Valuation: P/E, Forward P/E, PEG, P/B, P/S
  - Growth: Revenue growth, earnings growth
  - Profitability: Profit margin, ROE, ROA
  - Analyst: Target price (mean/high/low), recommendation
  - Dividends: Yield, payout ratio

Usage:
    from drl.fundamentals import get_fundamentals, get_batch_fundamentals
    result = get_fundamentals("AAPL")
    print(result.pe_ratio, result.analyst_target_mean)
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Cache: symbol → (FundamentalResult, timestamp)
_CACHE: dict[str, tuple[FundamentalResult, float]] = {}
_CACHE_TTL = 3600  # 1 hour — fundamentals don't change intraday


@dataclass
class FundamentalResult:
    """Core fundamental metrics for a symbol."""

    symbol: str

    # Valuation
    pe_ratio: float | None = None
    forward_pe: float | None = None
    peg_ratio: float | None = None
    price_to_book: float | None = None
    price_to_sales: float | None = None
    market_cap: float | None = None

    # Growth
    revenue_growth: float | None = None  # YoY %
    earnings_growth: float | None = None  # YoY %

    # Profitability
    profit_margin: float | None = None
    roe: float | None = None  # Return on Equity
    roa: float | None = None  # Return on Assets

    # Analyst consensus
    analyst_target_mean: float | None = None
    analyst_target_high: float | None = None
    analyst_target_low: float | None = None
    recommendation: str | None = None  # "buy", "hold", "sell"
    number_of_analysts: int | None = None

    # Dividends
    dividend_yield: float | None = None

    # Meta
    sector: str | None = None
    industry: str | None = None
    fetched_at: float = 0.0

    @property
    def upside_pct(self) -> float | None:
        """Analyst target upside from current price (requires current_price)."""
        return None  # Calculated externally with current price

    @property
    def valuation_score(self) -> float:
        """Simple 0-100 score: lower P/E + higher growth = better."""
        score = 50.0
        if self.pe_ratio is not None:
            if self.pe_ratio < 15:
                score += 15
            elif self.pe_ratio < 25:
                score += 5
            elif self.pe_ratio > 40:
                score -= 15
        if self.peg_ratio is not None:
            if self.peg_ratio < 1.0:
                score += 15
            elif self.peg_ratio < 2.0:
                score += 5
            elif self.peg_ratio > 3.0:
                score -= 10
        if self.earnings_growth is not None:
            if self.earnings_growth > 0.20:
                score += 10
            elif self.earnings_growth > 0.10:
                score += 5
            elif self.earnings_growth < 0:
                score -= 10
        if self.profit_margin is not None and self.profit_margin > 0.20:
            score += 5
        if self.recommendation:
            rec = self.recommendation.lower()
            if "buy" in rec or "strong" in rec:
                score += 5
            elif "sell" in rec or "under" in rec:
                score -= 10
        return max(0.0, min(100.0, score))

    def to_dict(self) -> dict:
        """Serialize for JSON / Streamlit display."""
        return {
            "symbol": self.symbol,
            "pe_ratio": self.pe_ratio,
            "forward_pe": self.forward_pe,
            "peg_ratio": self.peg_ratio,
            "price_to_book": self.price_to_book,
            "market_cap": self.market_cap,
            "revenue_growth": self.revenue_growth,
            "earnings_growth": self.earnings_growth,
            "profit_margin": self.profit_margin,
            "roe": self.roe,
            "analyst_target_mean": self.analyst_target_mean,
            "analyst_target_high": self.analyst_target_high,
            "analyst_target_low": self.analyst_target_low,
            "recommendation": self.recommendation,
            "number_of_analysts": self.number_of_analysts,
            "dividend_yield": self.dividend_yield,
            "sector": self.sector,
            "industry": self.industry,
            "valuation_score": round(self.valuation_score, 1),
        }


def _safe_get(info: dict, key: str) -> float | None:
    """Safely get a numeric value from yfinance info dict."""
    val = info.get(key)
    if val is None or val == "Infinity" or val == "NaN":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def get_fundamentals(symbol: str) -> FundamentalResult:
    """Fetch fundamental data for a single symbol via yfinance."""
    # Check cache
    if symbol in _CACHE:
        cached, ts = _CACHE[symbol]
        if time.time() - ts < _CACHE_TTL:
            return cached

    try:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        info = ticker.info or {}

        result = FundamentalResult(
            symbol=symbol,
            pe_ratio=_safe_get(info, "trailingPE"),
            forward_pe=_safe_get(info, "forwardPE"),
            peg_ratio=_safe_get(info, "pegRatio"),
            price_to_book=_safe_get(info, "priceToBook"),
            price_to_sales=_safe_get(info, "priceToSalesTrailing12Months"),
            market_cap=_safe_get(info, "marketCap"),
            revenue_growth=_safe_get(info, "revenueGrowth"),
            earnings_growth=_safe_get(info, "earningsGrowth"),
            profit_margin=_safe_get(info, "profitMargins"),
            roe=_safe_get(info, "returnOnEquity"),
            roa=_safe_get(info, "returnOnAssets"),
            analyst_target_mean=_safe_get(info, "targetMeanPrice"),
            analyst_target_high=_safe_get(info, "targetHighPrice"),
            analyst_target_low=_safe_get(info, "targetLowPrice"),
            recommendation=info.get("recommendationKey"),
            number_of_analysts=int(info.get("numberOfAnalystOpinions", 0)) or None,
            dividend_yield=_safe_get(info, "dividendYield"),
            sector=info.get("sector"),
            industry=info.get("industry"),
            fetched_at=time.time(),
        )

        _CACHE[symbol] = (result, time.time())
        logger.info(
            "Fundamentals: %s PE=%.1f FwdPE=%.1f Target=$%.0f Rec=%s",
            symbol,
            result.pe_ratio or 0,
            result.forward_pe or 0,
            result.analyst_target_mean or 0,
            result.recommendation or "N/A",
        )
        return result

    except Exception as e:
        logger.warning("Fundamentals error for %s: %s", symbol, e)
        return FundamentalResult(symbol=symbol, fetched_at=time.time())


def get_batch_fundamentals(
    symbols: list[str], max_workers: int = 6
) -> dict[str, FundamentalResult]:
    """Fetch fundamentals for multiple symbols in parallel."""
    results: dict[str, FundamentalResult] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(get_fundamentals, s): s for s in symbols}
        for fut in as_completed(futures):
            symbol = futures[fut]
            try:
                results[symbol] = fut.result()
            except Exception as e:
                logger.warning("Batch fundamental error for %s: %s", symbol, e)
                results[symbol] = FundamentalResult(symbol=symbol)
    return results
