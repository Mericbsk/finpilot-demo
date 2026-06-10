"""Research Agent — web news search per symbol using DuckDuckGo + Reddit + HN + Jina.

Input  : AgentContext.symbols (list of tickers)
Process: DuckDuckGo news + Reddit public JSON + HN Algolia + Jina Reader (parallel)
Output : AgentResult.data = dict[symbol, {
    "news": list[{title, url, body, date, source}],        # DuckDuckGo
    "reddit": list[{title, score, url, subreddit}],        # Reddit public JSON
    "hacker_news": list[{title, points, url}],             # HN Algolia
    "jina_articles": list[{url, text}],                    # Full article text
}]

All sources fall back gracefully when unavailable.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import requests

from agents.base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)

_MAX_RESULTS_PER_SYMBOL = 5
_SEARCH_TIMEOUT_S = 10
_HTTP_TIMEOUT_S = 8
_REDDIT_HEADERS = {"User-Agent": "FinPilot/1.0 (research agent; contact: finpilot@example.com)"}


def _fetch_reddit_public(symbol: str, clean: str, limit: int = 5) -> list[dict[str, Any]]:
    """Fetch top Reddit posts for a symbol via public JSON API (no auth required)."""
    is_bist = "." in symbol
    query = f"{clean} hisse senedi" if is_bist else clean
    url = (
        f"https://www.reddit.com/r/investing+stocks+wallstreetbets/search.json"
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
        logger.debug("ResearchAgent reddit %s: %s", symbol, exc)
        return []


def _fetch_hn(symbol: str, clean: str, limit: int = 3) -> list[dict[str, Any]]:
    """Fetch recent HN stories for a symbol via Algolia API (no auth required)."""
    is_bist = "." in symbol
    query = f"{clean} hisse senedi" if is_bist else f"{clean} stock"
    url = (
        f"https://hn.algolia.com/api/v1/search"
        f"?query={requests.utils.quote(query)}&tags=story&hitsPerPage={limit}"
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
        logger.debug("ResearchAgent HN %s: %s", symbol, exc)
        return []


def _jina_read_url(url: str) -> str:
    """Read a URL via Jina Reader and return clean markdown text (no auth required)."""
    try:
        resp = requests.get(
            f"https://r.jina.ai/{url}",
            headers={"Accept": "text/plain"},
            timeout=_HTTP_TIMEOUT_S,
        )
        resp.raise_for_status()
        return resp.text[:1500]  # cap to avoid oversized prompts
    except Exception as exc:
        logger.debug("ResearchAgent jina %s: %s", url, exc)
        return ""


class ResearchAgent(BaseAgent):
    """Fetch recent news + social data for each symbol.

    Sources (all parallel, all graceful on failure):
    - DuckDuckGo news
    - Reddit public JSON (r/investing+stocks+wallstreetbets)
    - HN Algolia search
    - Jina Reader (full text of top news URLs)
    """

    name = "research"

    def run(self, context: AgentContext, **kwargs: object) -> AgentResult:  # noqa: D102
        import time

        t0 = time.perf_counter()

        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return AgentResult(
                agent=self.name,
                success=False,
                error="duckduckgo-search not installed. Run: pip install duckduckgo-search",
            )

        results: dict[str, dict[str, Any]] = {}
        errors: list[str] = []
        ddgs = DDGS(timeout=_SEARCH_TIMEOUT_S)

        for sym in context.symbols:
            clean = sym.split(".")[0]
            is_bist = "." in sym
            ddg_query = (
                f"{clean} hisse senedi haber analiz 2026"
                if is_bist
                else f"{clean} stock news analysis 2026"
            )

            # --- DuckDuckGo (synchronous, already fast) ---
            ddg_news: list[dict[str, Any]] = []
            top_urls: list[str] = []
            try:
                ddg_raw = list(
                    ddgs.news(ddg_query, max_results=_MAX_RESULTS_PER_SYMBOL, safesearch="off")
                )
                ddg_news = [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "body": r.get("body", "")[:300],
                        "date": r.get("date", ""),
                        "source": r.get("source", ""),
                    }
                    for r in ddg_raw
                ]
                top_urls = [r.get("url", "") for r in ddg_raw[:2] if r.get("url")]
                logger.info("ResearchAgent: %s → %d DDG news", sym, len(ddg_news))
            except Exception as exc:
                logger.warning("ResearchAgent: %s DDG failed: %s", sym, exc)
                errors.append(f"{sym} DDG: {exc}")

            # --- Parallel fetch: Reddit + HN + Jina ---
            reddit_posts: list[dict[str, Any]] = []
            hn_posts: list[dict[str, Any]] = []
            jina_articles: list[dict[str, Any]] = []

            with ThreadPoolExecutor(max_workers=4) as pool:
                futures = {
                    pool.submit(_fetch_reddit_public, sym, clean): "reddit",
                    pool.submit(_fetch_hn, sym, clean): "hn",
                }
                for url in top_urls:
                    futures[pool.submit(_jina_read_url, url)] = f"jina:{url}"

                for future in as_completed(futures, timeout=12):
                    key = futures[future]
                    try:
                        value = future.result()
                        if key == "reddit":
                            reddit_posts = value
                        elif key == "hn":
                            hn_posts = value
                        elif key.startswith("jina:") and value:
                            jina_articles.append({"url": key[5:], "text": value})
                    except Exception as exc:
                        logger.debug("ResearchAgent parallel %s %s: %s", sym, key, exc)

            logger.info(
                "ResearchAgent: %s — reddit=%d hn=%d jina=%d",
                sym,
                len(reddit_posts),
                len(hn_posts),
                len(jina_articles),
            )

            results[sym] = {
                "news": ddg_news,
                "reddit": reddit_posts,
                "hacker_news": hn_posts,
                "jina_articles": jina_articles,
            }

        duration = (time.perf_counter() - t0) * 1000
        if not results and errors:
            return AgentResult(
                agent=self.name, success=False, error="; ".join(errors), duration_ms=duration
            )

        return AgentResult(agent=self.name, success=True, data=results, duration_ms=duration)
