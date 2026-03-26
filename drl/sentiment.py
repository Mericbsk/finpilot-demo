"""Sentiment NLP pipeline for FinPilot DRL agents.

Sprint 13 — Item #5: Wire DDG news headlines through VADER sentiment
analysis to produce ``news_sentiment`` and ``sentiment_score`` features
consumed by the feature pipeline and inference engine.

Key functions:
    ``get_news_sentiment(symbol)`` → float in [−1, 1]
    ``get_batch_sentiment(symbols)`` → dict[symbol, SentimentResult]
    ``enrich_dataframe_sentiment(df, symbol)`` → df with sentiment columns

The module is self-contained: it fetches news via DuckDuckGo, scores each
headline with VADER, and aggregates into a single compound sentiment.  A
small LRU cache + TTL prevents hammering the API on every call.
"""

from __future__ import annotations

import contextlib
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional imports (graceful degradation)
# ---------------------------------------------------------------------------
try:
    from tavily import TavilyClient  # type: ignore[import-untyped]

    _TAVILY_KEY = os.environ.get("TAVILY_API_KEY", "")
    _HAS_TAVILY = bool(_TAVILY_KEY)
except ImportError:
    TavilyClient = None  # type: ignore[assignment,misc]
    _TAVILY_KEY = ""
    _HAS_TAVILY = False

try:
    from duckduckgo_search import DDGS

    _HAS_DDG = True
except ImportError:
    DDGS = None  # type: ignore[assignment,misc]
    _HAS_DDG = False

try:
    import nltk
    from nltk.sentiment.vader import SentimentIntensityAnalyzer

    # Download lexicon once (silent)
    nltk.download("vader_lexicon", quiet=True)
    _VADER = SentimentIntensityAnalyzer()
    _HAS_VADER = True
except Exception:
    _VADER = None  # type: ignore[assignment]
    _HAS_VADER = False

# ---------------------------------------------------------------------------
# Financial keyword lexicon (fallback when VADER isn't available)
# ---------------------------------------------------------------------------
_POSITIVE_KEYWORDS = frozenset(
    {
        "surge",
        "surges",
        "rally",
        "gain",
        "gains",
        "profit",
        "profits",
        "beat",
        "beats",
        "strong",
        "bullish",
        "upgrade",
        "upgraded",
        "outperform",
        "buy",
        "growth",
        "record",
        "breakout",
        "rise",
        "rises",
        "soar",
        "soars",
        "boom",
        "positive",
        "exceeds",
        "exceeded",
        "up",
        "higher",
        "high",
    }
)

_NEGATIVE_KEYWORDS = frozenset(
    {
        "crash",
        "crashes",
        "plunge",
        "plunges",
        "loss",
        "losses",
        "miss",
        "misses",
        "weak",
        "bearish",
        "downgrade",
        "downgraded",
        "underperform",
        "sell",
        "decline",
        "recession",
        "bankruptcy",
        "layoff",
        "layoffs",
        "warning",
        "risk",
        "negative",
        "down",
        "lower",
        "low",
        "fall",
        "falls",
        "drop",
        "drops",
    }
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class HeadlineSentiment:
    """Sentiment for a single headline."""

    title: str
    source: str
    score: float  # −1 → 1
    method: str  # "vader" | "keyword"


@dataclass
class SentimentResult:
    """Aggregated sentiment for a symbol."""

    symbol: str
    compound: float  # overall −1 → 1
    n_headlines: int
    avg_positive: float
    avg_negative: float
    headlines: list[HeadlineSentiment] = field(default_factory=list)
    fetched_at: float = 0.0  # time.time()

    @property
    def news_sentiment(self) -> float:
        """Alias for the compound score (used as feature column)."""
        return self.compound

    @property
    def sentiment_score(self) -> float:
        """Scaled compound biased toward magnitude (used as feature column)."""
        # Amplify signal: double the compound, clip to [-1, 1]
        return float(np.clip(self.compound * 1.5, -1.0, 1.0))


# ---------------------------------------------------------------------------
# Internal: DDG news fetch
# ---------------------------------------------------------------------------


def _ddg_news(
    query: str, region: str = "wt-wt", timelimit: str | None = "w", max_results: int = 5
) -> list[dict]:
    """Fetch news headlines from DuckDuckGo (thread-safe)."""
    if not _HAS_DDG or DDGS is None:
        return []
    try:
        with DDGS() as ddgs:
            res = list(
                ddgs.news(
                    query,
                    region=region,
                    safesearch="off",
                    timelimit=timelimit,
                    max_results=max_results,
                )
            )
            if res:
                return res
            # Fallback: remove time constraint
            if timelimit:
                return list(
                    ddgs.news(
                        query,
                        region=region,
                        safesearch="off",
                        timelimit=None,
                        max_results=max_results,
                    )
                )
    except Exception as e:
        logger.debug("DDG news error (%s): %s", query, e)
    return []


def _tavily_search(symbol: str, max_results: int = 10) -> list[dict]:
    """Sprint — Tavily AI-ranked financial news search (primary source)."""
    if not _HAS_TAVILY or TavilyClient is None:
        return []
    try:
        client = TavilyClient(api_key=_TAVILY_KEY)
        resp = client.search(
            query=f"{symbol} stock market news analysis",
            search_depth="basic",
            topic="news",
            max_results=max_results,
            include_answer=False,
        )
        results = []
        for r in resp.get("results", []):
            results.append(
                {
                    "title": r.get("title", ""),
                    "body": r.get("content", ""),
                    "url": r.get("url", ""),
                    "source": r.get("url", "").split("/")[2] if r.get("url") else "tavily",
                }
            )
        logger.info("Tavily: %d results for %s", len(results), symbol)
        return results
    except Exception as e:
        logger.warning("Tavily search error for %s: %s", symbol, e)
        return []


def _fetch_headlines(symbol: str) -> list[dict]:
    """Fetch headlines: Tavily (primary) → DDG (fallback)."""
    # Try Tavily first (AI-ranked, higher quality)
    results = _tavily_search(symbol, max_results=10)

    # Fallback to DDG if Tavily unavailable or returned too few
    if len(results) < 3:
        queries = [
            (f"{symbol} stock news", "wt-wt", "w", 5),
            (f"{symbol} earnings report", "wt-wt", "m", 3),
            (f"{symbol} analyst rating", "wt-wt", "m", 3),
        ]
        with ThreadPoolExecutor(max_workers=3) as pool:
            futs = {pool.submit(_ddg_news, q, r, t, m): q for q, r, t, m in queries}
            for fut in as_completed(futs):
                with contextlib.suppress(Exception):
                    results.extend(fut.result())

    # Dedup by title
    seen: set[str] = set()
    unique = []
    for item in results:
        title = item.get("title", "")
        if title and title not in seen:
            unique.append(item)
            seen.add(title)
    return unique[:15]


# ---------------------------------------------------------------------------
# Internal: sentiment scoring
# ---------------------------------------------------------------------------


def _score_headline_vader(text: str) -> float:
    """Score a single headline using VADER (−1 → 1)."""
    if _VADER is None:
        return _score_headline_keywords(text)
    try:
        return _VADER.polarity_scores(text)["compound"]
    except Exception:
        return 0.0


def _score_headline_keywords(text: str) -> float:
    """Simple keyword-based sentiment (fallback)."""
    words = set(text.lower().split())
    pos = len(words & _POSITIVE_KEYWORDS)
    neg = len(words & _NEGATIVE_KEYWORDS)
    total = pos + neg
    if total == 0:
        return 0.0
    return (pos - neg) / total


def _score_headline(text: str) -> tuple[float, str]:
    """Return (score, method) for a headline."""
    if _HAS_VADER:
        return _score_headline_vader(text), "vader"
    return _score_headline_keywords(text), "keyword"


# ---------------------------------------------------------------------------
# TTL-aware caching
# ---------------------------------------------------------------------------
_CACHE: dict[str, SentimentResult] = {}
_CACHE_TTL = 900  # 15 min


def _get_cached(symbol: str) -> SentimentResult | None:
    result = _CACHE.get(symbol)
    if result and (time.time() - result.fetched_at) < _CACHE_TTL:
        return result
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_news_sentiment(symbol: str) -> float:
    """Return a single compound sentiment score for *symbol* (−1 → 1).

    This is the simplest API — returns 0.0 if news cannot be fetched.
    """
    result = analyze_sentiment(symbol)
    return result.compound


def analyze_sentiment(symbol: str) -> SentimentResult:
    """Full sentiment analysis for a single symbol."""
    cached = _get_cached(symbol)
    if cached:
        return cached

    headlines = _fetch_headlines(symbol)

    if not headlines:
        result = SentimentResult(
            symbol=symbol,
            compound=0.0,
            n_headlines=0,
            avg_positive=0.0,
            avg_negative=0.0,
            fetched_at=time.time(),
        )
        _CACHE[symbol] = result
        return result

    scored: list[HeadlineSentiment] = []
    for item in headlines:
        title = item.get("title", "")
        source = item.get("source", "")
        score, method = _score_headline(title)
        scored.append(HeadlineSentiment(title=title, source=source, score=score, method=method))

    scores = [h.score for h in scored]
    pos_scores = [s for s in scores if s > 0]
    neg_scores = [s for s in scores if s < 0]

    result = SentimentResult(
        symbol=symbol,
        compound=float(np.mean(scores)) if scores else 0.0,
        n_headlines=len(scored),
        avg_positive=float(np.mean(pos_scores)) if pos_scores else 0.0,
        avg_negative=float(np.mean(neg_scores)) if neg_scores else 0.0,
        headlines=scored,
        fetched_at=time.time(),
    )
    _CACHE[symbol] = result
    logger.info(
        "Sentiment %s: compound=%.3f  n=%d (pos=%.3f neg=%.3f)",
        symbol,
        result.compound,
        result.n_headlines,
        result.avg_positive,
        result.avg_negative,
    )
    return result


def get_batch_sentiment(symbols: list[str], max_workers: int = 4) -> dict[str, SentimentResult]:
    """Fetch sentiment for multiple symbols in parallel."""
    results: dict[str, SentimentResult] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futs = {pool.submit(analyze_sentiment, s): s for s in symbols}
        for fut in as_completed(futs):
            sym = futs[fut]
            try:
                results[sym] = fut.result()
            except Exception as e:
                logger.warning("Sentiment error %s: %s", sym, e)
                results[sym] = SentimentResult(
                    symbol=sym,
                    compound=0.0,
                    n_headlines=0,
                    avg_positive=0.0,
                    avg_negative=0.0,
                    fetched_at=time.time(),
                )
    return results


if TYPE_CHECKING:
    import pandas as pd


def enrich_dataframe_sentiment(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Add ``news_sentiment`` and ``sentiment_score`` columns to *df*.

    Fetches live sentiment and broadcasts to all rows (point-in-time
    approximation for the latest sentiment window).
    """

    result = analyze_sentiment(symbol)
    df = df.copy()
    df["news_sentiment"] = result.news_sentiment
    df["sentiment_score"] = result.sentiment_score
    return df


__all__ = [
    "get_news_sentiment",
    "analyze_sentiment",
    "get_batch_sentiment",
    "enrich_dataframe_sentiment",
    "SentimentResult",
    "HeadlineSentiment",
]
