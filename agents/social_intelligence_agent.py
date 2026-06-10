"""Social Intelligence Agent — Reddit, HN and Polymarket sentiment per symbol.

Input  : AgentContext.symbols (list of tickers)
Process: For each symbol fetch:
           - Reddit public JSON (r/investing+stocks+wallstreetbets, last 30 days)
           - HN Algolia (last 30 days, epoch filtered)
           - Polymarket gamma API (active prediction markets mentioning the symbol)
Output : AgentResult.data = dict[symbol, SocialData]

SocialData shape:
    {
        "reddit_posts":       list[{title, score, url, subreddit}],
        "hn_posts":           list[{title, points, url}],
        "polymarket_markets": list[{question, yes_probability, volume}],
        "sentiment_score":    float,   # 0.0 (very negative) – 1.0 (very positive)
        "buzz_level":         str,     # "low" | "medium" | "high"
        "post_count":         int,
    }

All sources are free and require no authentication.
Controlled by SOCIAL_SENTIMENT_ENABLED env var (checked by _node_social in ceo.py).
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime, timedelta
from typing import Any

import requests

from agents.base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)

_HTTP_TIMEOUT_S = 8
_REDDIT_HEADERS = {
    "User-Agent": "FinPilot/1.0 (social intelligence; contact: finpilot@example.com)"
}

# Negative keywords used for simple sentiment scoring
_NEGATIVE_WORDS = {
    "crash",
    "dump",
    "sell",
    "short",
    "fraud",
    "scam",
    "overvalued",
    "bearish",
    "decline",
    "fall",
    "drop",
    "loss",
    "risk",
    "warning",
    "danger",
    "manipul",
    "düşüş",
    "sat",
    "kayıp",
    "tehlike",
    "tehdit",
    "çöküş",
}
_POSITIVE_WORDS = {
    "buy",
    "bull",
    "moon",
    "growth",
    "strong",
    "profit",
    "breakout",
    "undervalued",
    "rally",
    "rise",
    "gain",
    "bullish",
    "opportunity",
    "long",
    "calls",
    "al",
    "yükseliş",
    "kazanç",
    "fırsat",
    "güçlü",
    "büyüme",
}


def _simple_sentiment(texts: list[str]) -> float:
    """Return a 0-1 sentiment score based on keyword frequency."""
    if not texts:
        return 0.5
    pos = neg = 0
    for text in texts:
        low = text.lower()
        pos += sum(1 for w in _POSITIVE_WORDS if w in low)
        neg += sum(1 for w in _NEGATIVE_WORDS if w in low)
    total = pos + neg
    if total == 0:
        return 0.5
    return round(pos / total, 3)


def _buzz_level(post_count: int) -> str:
    if post_count >= 10:
        return "high"
    if post_count >= 4:
        return "medium"
    return "low"


def _fetch_reddit_30d(symbol: str, clean: str, limit: int = 10) -> list[dict[str, Any]]:
    """Top Reddit posts from the last 30 days via public JSON API."""
    is_bist = "." in symbol
    query = f"{clean} hisse senedi" if is_bist else clean
    url = (
        f"https://www.reddit.com/r/investing+stocks+wallstreetbets+StockMarket/search.json"
        f"?q={requests.utils.quote(query)}&sort=top&t=month&limit={limit}"
    )
    try:
        resp = requests.get(url, headers=_REDDIT_HEADERS, timeout=_HTTP_TIMEOUT_S)
        resp.raise_for_status()
        children = resp.json().get("data", {}).get("children", [])
        return [
            {
                "title": c["data"].get("title", ""),
                "score": c["data"].get("score", 0),
                "url": f"https://reddit.com{c['data'].get('permalink', '')}",
                "subreddit": c["data"].get("subreddit", ""),
            }
            for c in children
            if c.get("data")
        ]
    except Exception as exc:
        logger.debug("SocialAgent reddit %s: %s", symbol, exc)
        return []


def _fetch_hn_30d(symbol: str, clean: str, limit: int = 5) -> list[dict[str, Any]]:
    """Recent HN stories from the last 30 days via Algolia API."""
    is_bist = "." in symbol
    query = f"{clean} hisse senedi" if is_bist else f"{clean} stock"
    epoch_30d_ago = int((datetime.now(tz=UTC) - timedelta(days=30)).timestamp())
    url = (
        f"https://hn.algolia.com/api/v1/search"
        f"?query={requests.utils.quote(query)}&tags=story"
        f"&numericFilters=created_at_i>{epoch_30d_ago}&hitsPerPage={limit}"
    )
    try:
        resp = requests.get(url, timeout=_HTTP_TIMEOUT_S)
        resp.raise_for_status()
        hits = resp.json().get("hits", [])
        return [
            {
                "title": h.get("title", ""),
                "points": h.get("points", 0),
                "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
            }
            for h in hits
            if h.get("title")
        ]
    except Exception as exc:
        logger.debug("SocialAgent HN %s: %s", symbol, exc)
        return []


def _fetch_polymarket(symbol: str, clean: str, limit: int = 5) -> list[dict[str, Any]]:
    """Fetch active Polymarket prediction markets mentioning the symbol."""
    url = (
        f"https://gamma-api.polymarket.com/markets"
        f"?q={requests.utils.quote(clean)}&status=active&limit={limit}"
    )
    try:
        resp = requests.get(url, timeout=_HTTP_TIMEOUT_S)
        resp.raise_for_status()
        markets = resp.json()
        if not isinstance(markets, list):
            return []
        return [
            {
                "question": m.get("question", ""),
                "yes_probability": round(float(m.get("outcomePrices", [0.5])[0]), 3)
                if m.get("outcomePrices")
                else None,
                "volume": m.get("volume", 0),
            }
            for m in markets
            if m.get("question")
        ]
    except Exception as exc:
        logger.debug("SocialAgent Polymarket %s: %s", symbol, exc)
        return []


class SocialIntelligenceAgent(BaseAgent):
    """Aggregate social sentiment data for each symbol.

    Sources (all free, no auth, parallel fetch):
    - Reddit public JSON (r/investing+stocks+wallstreetbets, last 30 days)
    - HN Algolia (last 30 days)
    - Polymarket prediction markets (active only)
    """

    name = "social_intel"

    def run(self, context: AgentContext, **kwargs: object) -> AgentResult:  # noqa: D102
        t0 = time.perf_counter()
        results: dict[str, Any] = {}

        for sym in context.symbols:
            clean = sym.split(".")[0]

            reddit_posts: list[dict[str, Any]] = []
            hn_posts: list[dict[str, Any]] = []
            polymarket_markets: list[dict[str, Any]] = []

            with ThreadPoolExecutor(max_workers=3) as pool:
                futures = {
                    pool.submit(_fetch_reddit_30d, sym, clean): "reddit",
                    pool.submit(_fetch_hn_30d, sym, clean): "hn",
                    pool.submit(_fetch_polymarket, sym, clean): "polymarket",
                }
                for future in as_completed(futures, timeout=15):
                    key = futures[future]
                    try:
                        value = future.result()
                        if key == "reddit":
                            reddit_posts = value
                        elif key == "hn":
                            hn_posts = value
                        elif key == "polymarket":
                            polymarket_markets = value
                    except Exception as exc:
                        logger.debug("SocialAgent %s %s: %s", sym, key, exc)

            all_titles = (
                [p["title"] for p in reddit_posts]
                + [p["title"] for p in hn_posts]
                + [m["question"] for m in polymarket_markets]
            )
            post_count = len(reddit_posts) + len(hn_posts)
            sentiment_score = _simple_sentiment(all_titles)

            results[sym] = {
                "reddit_posts": reddit_posts,
                "hn_posts": hn_posts,
                "polymarket_markets": polymarket_markets,
                "sentiment_score": sentiment_score,
                "buzz_level": _buzz_level(post_count),
                "post_count": post_count,
            }

            logger.info(
                "SocialAgent: %s — reddit=%d hn=%d poly=%d sentiment=%.2f buzz=%s",
                sym,
                len(reddit_posts),
                len(hn_posts),
                len(polymarket_markets),
                sentiment_score,
                results[sym]["buzz_level"],
            )

        duration = (time.perf_counter() - t0) * 1000
        return AgentResult(agent=self.name, success=True, data=results, duration_ms=duration)
