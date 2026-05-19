"""Research Agent — web news search per symbol using DuckDuckGo.

Input  : AgentContext.symbols (list of tickers)
Process: DuckDuckGo news search for each symbol → top 5 headlines + snippets
Output : AgentResult.data = dict[symbol, list[{title, url, body, date}]]

Falls back gracefully when duckduckgo-search is not installed.
"""

from __future__ import annotations

import logging
from typing import Any

from agents.base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)

_MAX_RESULTS_PER_SYMBOL = 5
_SEARCH_TIMEOUT_S = 10


class ResearchAgent(BaseAgent):
    """Fetch recent news headlines for each symbol via DuckDuckGo."""

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

        news: dict[str, list[dict[str, Any]]] = {}
        errors: list[str] = []

        ddgs = DDGS(timeout=_SEARCH_TIMEOUT_S)

        for sym in context.symbols:
            # Strip exchange suffix for cleaner searches (THYAO.IS → THYAO)
            clean = sym.split(".")[0]
            query = f"{clean} hisse senedi haber analiz 2025"
            try:
                results = list(
                    ddgs.news(
                        query,
                        max_results=_MAX_RESULTS_PER_SYMBOL,
                        safesearch="off",
                    )
                )
                news[sym] = [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "body": r.get("body", "")[:300],
                        "date": r.get("date", ""),
                        "source": r.get("source", ""),
                    }
                    for r in results
                ]
                logger.info("ResearchAgent: %s → %d news items", sym, len(news[sym]))
            except Exception as exc:
                logger.warning("ResearchAgent: %s search failed: %s", sym, exc)
                errors.append(f"{sym}: {exc}")
                news[sym] = []

        duration = (time.perf_counter() - t0) * 1000
        if not news and errors:
            return AgentResult(
                agent=self.name,
                success=False,
                error="; ".join(errors),
                duration_ms=duration,
            )

        return AgentResult(agent=self.name, success=True, data=news, duration_ms=duration)
