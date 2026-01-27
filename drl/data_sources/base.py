"""Base abstractions for alternative data feeds.

Real-world deployments need to aggregate data from multiple providers
(news, on-chain analytics, macro indicators).  The classes here define
a minimal set of interfaces adapters should satisfy so the rest of the
DRL stack can remain agnostic of the underlying transport.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Dict, Mapping, Optional, Protocol, Sequence

import pandas as pd


@dataclass
class DataSlice:
    """Represents a time-indexed frame returned by a data adapter."""

    frame: pd.DataFrame
    metadata: Mapping[str, object]

    def ensure_columns(self, expected: Sequence[str]) -> pd.DataFrame:
        missing = [col for col in expected if col not in self.frame.columns]
        if missing:
            raise KeyError(f"Missing columns in data slice: {missing}")
        return self.frame


class DataAdapter(Protocol):
    """Protocol implemented by all data source adapters."""

    def fetch(
        self, symbol: str, *, start: Optional[pd.Timestamp], end: Optional[pd.Timestamp]
    ) -> DataSlice:
        """Retrieve the requested time window for ``symbol``."""
        ...


class BaseAdapter(abc.ABC):
    """Convenience base class providing shared utilities."""

    provider: str

    def __init__(self, provider: str) -> None:
        self.provider = provider

    def _build_metadata(self, symbol: str, **extra: object) -> Mapping[str, object]:
        base: Dict[str, object] = {"symbol": symbol, "provider": self.provider}
        base.update(extra)
        return base

    @abc.abstractmethod
    def fetch(
        self,
        symbol: str,
        *,
        start: Optional[pd.Timestamp] = None,
        end: Optional[pd.Timestamp] = None,
    ) -> DataSlice:
        raise NotImplementedError


__all__ = ["DataSlice", "DataAdapter", "BaseAdapter"]
