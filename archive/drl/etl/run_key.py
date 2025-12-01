"""Utilities for constructing deterministic ETL run keys."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import pandas as pd


@dataclass(frozen=True)
class RunKeyInputs:
    source: str
    symbol: str
    start: Optional[pd.Timestamp]
    end: Optional[pd.Timestamp]

    def serialise(self) -> str:
        def _norm(ts: Optional[pd.Timestamp]) -> str:
            if ts is None:
                return ""
            if isinstance(ts, datetime):
                ts = pd.Timestamp(ts)
            if not isinstance(ts, pd.Timestamp):
                ts = pd.Timestamp(ts)
            ts = ts.tz_convert("UTC") if ts.tzinfo else ts.tz_localize("UTC")
            return ts.isoformat()

        return "|".join([self.source.lower(), self.symbol.upper(), _norm(self.start), _norm(self.end)])


def build_run_key(source: str, symbol: str, *, start: Optional[pd.Timestamp], end: Optional[pd.Timestamp]) -> str:
    """Return a deterministic run key combining source, symbol and window."""

    inputs = RunKeyInputs(source=source, symbol=symbol, start=start, end=end)
    payload = inputs.serialise().encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()[:16]
    return f"{inputs.source.lower()}-{inputs.symbol.lower()}-{digest}"  # noqa: E501


__all__ = ["build_run_key", "RunKeyInputs"]
