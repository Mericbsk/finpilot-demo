"""Async adapter for generic news sentiment providers."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

import pandas as pd

from ..async_base import (
    AsyncHTTPAdapter,
    AsyncHTTPClient,
    CircuitBreakerConfig,
    RateLimitConfig,
    RetryConfig,
)
from ..base import DataSlice
from ..exceptions import AdapterResponseError
from ..news import normalize_news_rows


def _to_iso(ts: Optional[pd.Timestamp | str | int | float]) -> Optional[str]:
    if ts is None:
        return None
    stamp = pd.Timestamp(ts)
    if stamp.tzinfo is None:
        stamp = stamp.tz_localize("UTC")
    else:
        stamp = stamp.tz_convert("UTC")
    return stamp.isoformat()


class NewsAPIAdapter(AsyncHTTPAdapter):
    """Adapter for REST-style news APIs returning article JSON payloads."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        endpoint: str = "/v2/everything",
        language: Optional[str] = "en",
        page_size: int = 100,
        extra_filters: Optional[Mapping[str, Any]] = None,
        provider: str = "newsapi",
        rate_limit: Optional[RateLimitConfig] = None,
        retry: Optional[RetryConfig] = None,
        circuit_breaker: Optional[CircuitBreakerConfig] = None,
        timeout: Optional[float] = 10.0,
    ) -> None:
        headers = {"Authorization": f"Bearer {api_key}"}
        client = AsyncHTTPClient(
            base_url=base_url,
            provider=provider,
            timeout=timeout,
            default_headers=headers,
            rate_limit=rate_limit,
            retry=retry,
            circuit_breaker=circuit_breaker,
        )
        super().__init__(client=client, provider=provider)
        self._endpoint = endpoint
        self._language = language
        self._page_size = page_size
        self._extra_filters = dict(extra_filters or {})

    async def fetch_async(
        self,
        symbol: str,
        *,
        start: Optional[pd.Timestamp] = None,
        end: Optional[pd.Timestamp] = None,
    ) -> DataSlice:
        params: dict[str, Any] = {
            "q": symbol,
            "pageSize": self._page_size,
        }
        if self._language:
            params["language"] = self._language
        params.update(self._extra_filters)
        start_iso = _to_iso(start)
        end_iso = _to_iso(end)
        if start_iso:
            params["from"] = start_iso
        if end_iso:
            params["to"] = end_iso

        payload = await self.client.get_json(self._endpoint, params=params)
        articles = payload.get("articles") if isinstance(payload, Mapping) else None
        if not isinstance(articles, Sequence):
            raise AdapterResponseError(
                "Provider response missing 'articles' array", provider=self.provider
            )

        rows = []
        for article in articles:
            if not isinstance(article, Mapping):
                continue
            source_entry = article.get("source")
            if isinstance(source_entry, Mapping):
                source_name = source_entry.get("name", self.provider)
            else:
                source_name = source_entry or self.provider
            rows.append(
                {
                    "timestamp": article.get("publishedAt"),
                    "sentiment": article.get("sentiment") or article.get("sentiment_score"),
                    "relevance": article.get("relevance") or article.get("volume", 1.0),
                    "source": source_name,
                    "headline": article.get("title"),
                    "metadata": {
                        "url": article.get("url"),
                        "tickers": article.get("tickers"),
                    },
                }
            )

        frame = normalize_news_rows(rows)
        metadata = self._build_metadata(symbol, rows=len(frame))
        return DataSlice(frame=frame, metadata=metadata)


__all__ = ["NewsAPIAdapter"]
