"""GET /api/v1/news/{symbol}  &  GET /api/v1/fundamentals/{symbol}
Real market data via yfinance — used by the AI Analysis page.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

import yfinance as yf
from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["market_data"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# News
# ---------------------------------------------------------------------------


@router.get("/news/{symbol}")
async def get_news(symbol: str):
    """Return the latest news items for a ticker via yfinance."""
    sym = symbol.upper().strip()
    if not sym or len(sym) > 10:
        raise HTTPException(status_code=400, detail="Invalid symbol")
    try:
        ticker = yf.Ticker(sym)
        raw = ticker.news or []
        items = []
        for n in raw[:10]:
            content = n.get("content", {})
            # yfinance ≥0.2.x wraps everything in content{}
            title = content.get("title") or n.get("title", "")
            provider = (content.get("provider", {}) or {}).get("displayName") or n.get(
                "publisher", ""
            )
            pub_ts = content.get("pubDate") or n.get("providerPublishTime")
            # Normalise timestamp → human string
            if isinstance(pub_ts, (int, float)):
                from datetime import datetime

                dt = datetime.fromtimestamp(pub_ts, tz=UTC)
                time_str = dt.strftime("%b %d, %H:%M")
            elif isinstance(pub_ts, str):
                time_str = pub_ts[:16]
            else:
                time_str = "—"
            # Rough sentiment from title keywords
            title_l = title.lower()
            if any(
                w in title_l
                for w in [
                    "beat",
                    "surge",
                    "rally",
                    "upgrade",
                    "buy",
                    "profit",
                    "gain",
                    "rise",
                    "soar",
                    "record",
                    "strong",
                ]
            ):
                sentiment = "Bullish"
            elif any(
                w in title_l
                for w in [
                    "miss",
                    "drop",
                    "fall",
                    "downgrade",
                    "sell",
                    "loss",
                    "decline",
                    "warn",
                    "cut",
                    "concern",
                    "risk",
                ]
            ):
                sentiment = "Bearish"
            else:
                sentiment = "Neutral"
            if title:
                items.append(
                    {
                        "title": title,
                        "source": provider,
                        "time": time_str,
                        "sentiment": sentiment,
                    }
                )
        return {"symbol": sym, "items": items, "count": len(items)}
    except Exception as exc:
        logger.warning("news fetch failed for %s: %s", sym, exc)
        raise HTTPException(status_code=502, detail="News fetch failed") from exc


# ---------------------------------------------------------------------------
# Fundamentals
# ---------------------------------------------------------------------------

_FUNDAMENTAL_KEYS = [
    ("marketCap", "Market Cap", "cap"),
    ("trailingPE", "P/E (TTM)", "number"),
    ("forwardPE", "P/E (Fwd)", "number"),
    ("trailingEps", "EPS (TTM)", "currency"),
    ("revenueGrowth", "Revenue Growth", "pct"),
    ("earningsGrowth", "Earnings Growth", "pct"),
    ("debtToEquity", "Debt/Equity", "number"),
    ("dividendYield", "Div Yield", "pct"),
    ("fiftyTwoWeekHigh", "52W High", "currency"),
    ("fiftyTwoWeekLow", "52W Low", "currency"),
    ("beta", "Beta", "number"),
    ("floatShares", "Float", "shares"),
    ("averageVolume", "Avg Volume", "volume"),
    ("returnOnEquity", "ROE", "pct"),
    ("grossMargins", "Gross Margin", "pct"),
    ("operatingMargins", "Op Margin", "pct"),
    ("currentRatio", "Current Ratio", "number"),
    ("priceToBook", "P/B Ratio", "number"),
    ("enterpriseToEbitda", "EV/EBITDA", "number"),
    ("shortRatio", "Short Ratio", "number"),
]


def _fmt(value: float | None, fmt: str) -> str:
    if value is None:
        return "—"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "—"
    if fmt == "cap":
        if v >= 1e12:
            return f"${v/1e12:.2f}T"
        if v >= 1e9:
            return f"${v/1e9:.1f}B"
        if v >= 1e6:
            return f"${v/1e6:.1f}M"
        return f"${v:,.0f}"
    if fmt == "shares":
        if v >= 1e9:
            return f"{v/1e9:.1f}B"
        if v >= 1e6:
            return f"{v/1e6:.1f}M"
        return f"{v:,.0f}"
    if fmt == "volume":
        if v >= 1e6:
            return f"{v/1e6:.1f}M"
        return f"{v:,.0f}"
    if fmt == "pct":
        return f"{v*100:.1f}%"
    if fmt == "currency":
        return f"${v:.2f}"
    if fmt == "number":
        return f"{v:.2f}"
    return str(v)


@router.get("/fundamentals/{symbol}")
async def get_fundamentals(symbol: str):
    """Return fundamental data for a ticker via yfinance."""
    sym = symbol.upper().strip()
    if not sym or len(sym) > 10:
        raise HTTPException(status_code=400, detail="Invalid symbol")
    try:
        info = yf.Ticker(sym).info or {}
        rows = []
        for key, label, fmt in _FUNDAMENTAL_KEYS:
            raw = info.get(key)
            rows.append(
                {
                    "label": label,
                    "value": _fmt(raw, fmt),
                    "raw": raw,
                }
            )
        return {
            "symbol": sym,
            "name": info.get("longName") or info.get("shortName") or sym,
            "sector": info.get("sector", "—"),
            "industry": info.get("industry", "—"),
            "summary": (info.get("longBusinessSummary") or "")[:300],
            "rows": rows,
            "fetched_at": datetime.now(UTC).isoformat(),
        }
    except Exception as exc:
        logger.warning("fundamentals fetch failed for %s: %s", sym, exc)
        raise HTTPException(status_code=502, detail="Fundamentals fetch failed") from exc
