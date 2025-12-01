"""Adapters for ingesting on-chain analytics."""
from __future__ import annotations

from typing import Callable, Iterable, Mapping, Optional

import pandas as pd

from .base import BaseAdapter, DataSlice

RawOnChainFetcher = Callable[[str, Optional[pd.Timestamp], Optional[pd.Timestamp]], Iterable[Mapping[str, object]]]


def normalize_onchain_rows(rows: Iterable[Mapping[str, object]]) -> pd.DataFrame:
    rows_list = list(rows)
    columns = ["timestamp", "onchain_active_addresses", "onchain_tx_volume", "stablecoin_ratio"]
    if not rows_list:
        frame = pd.DataFrame(columns=columns)
    else:
        frame = pd.DataFrame(rows_list)
        for column in columns:
            if column not in frame.columns:
                frame[column] = 0.0 if column != "timestamp" else pd.NaT
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
        frame = frame.set_index("timestamp", drop=True)
        frame = frame[["onchain_active_addresses", "onchain_tx_volume", "stablecoin_ratio"]]
    return frame.sort_index()


class OnChainAdapter(BaseAdapter):
    """Normalises on-chain metrics for downstream feature consumption."""

    def __init__(self, fetcher: RawOnChainFetcher, *, provider: str = "onchain") -> None:
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
        frame = normalize_onchain_rows(rows)
        metadata = self._build_metadata(symbol, rows=len(frame))
        return DataSlice(frame=frame, metadata=metadata)


__all__ = ["OnChainAdapter", "RawOnChainFetcher", "normalize_onchain_rows"]
