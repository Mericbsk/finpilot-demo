"""Adapters for ingesting news and sentiment feeds into the DRL pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Iterable, List, Mapping, Optional

import pandas as pd

from .base import BaseAdapter, DataSlice

RawNewsFetcher = Callable[[str, Optional[pd.Timestamp], Optional[pd.Timestamp]], Iterable[Mapping[str, object]]]


@dataclass
class NewsRecord:
    """Canonical representation of a single news datapoint."""

    timestamp: pd.Timestamp
    sentiment: float
    volume: float
    source: str
    headline: Optional[str] = None
    metadata: Mapping[str, object] = field(default_factory=dict)


def _coerce_float(value: object, default: float) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def normalize_news_rows(rows: Iterable[Mapping[str, object]]) -> pd.DataFrame:
    records: List[NewsRecord] = []
    for row in rows:
        timestamp_raw = row.get("timestamp")
        if timestamp_raw is None:
            continue
        if isinstance(timestamp_raw, (pd.Timestamp, datetime, str, int, float)):
            ts = pd.to_datetime(timestamp_raw, utc=True)
        else:
            continue
        sentiment = _coerce_float(row.get("sentiment"), 0.0)
        volume = _coerce_float(row.get("relevance"), 1.0)
        source = str(row.get("source", "unknown"))
        headline = row.get("headline")
        extra = {k: v for k, v in row.items() if k not in {"timestamp", "sentiment", "relevance", "source", "headline"}}
        records.append(
            NewsRecord(
                timestamp=ts,
                sentiment=sentiment,
                volume=volume,
                source=source,
                headline=headline if isinstance(headline, str) else None,
                metadata=extra,
            )
        )

    if not records:
        frame = pd.DataFrame(columns=["sentiment_score", "news_volume", "source"])
    else:
        frame = pd.DataFrame(
            {
                "sentiment_score": [rec.sentiment for rec in records],
                "news_volume": [rec.volume for rec in records],
                "source": [rec.source for rec in records],
            },
            index=[rec.timestamp for rec in records],
        )
    return frame.sort_index()


class NewsAdapter(BaseAdapter):
    """Transforms raw news API payloads into FeaturePipeline-ready frames."""

    def __init__(self, fetcher: RawNewsFetcher, *, provider: str = "news") -> None:
        super().__init__(provider=provider)
        self._fetcher = fetcher

    def fetch(
        self,
        symbol: str,
        *,
        start: Optional[pd.Timestamp] = None,
        end: Optional[pd.Timestamp] = None,
    ) -> DataSlice:
        rows = list(self._fetcher(symbol, start, end))
        frame = normalize_news_rows(rows)
        metadata = self._build_metadata(symbol, rows=len(frame))
        return DataSlice(frame=frame, metadata=metadata)


__all__ = ["NewsAdapter", "NewsRecord", "RawNewsFetcher", "normalize_news_rows"]
