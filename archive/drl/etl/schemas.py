"""Pydantic models describing alternative data records."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Mapping, Optional, Tuple

import pandas as pd

try:  # pragma: no cover - graceful fallback when optional deps missing
    from pydantic import BaseModel, Field, ValidationError
except ImportError:  # pragma: no cover
    BaseModel = object  # type: ignore[misc, assignment]

    def Field(*args, **kwargs):  # type: ignore[override]
        return None

    class ValidationError(Exception):  # type: ignore[misc]
        ...

    _PYDANTIC_AVAILABLE = False
else:  # pragma: no cover - will be exercised in real environment
    _PYDANTIC_AVAILABLE = True


def _require_pydantic() -> None:
    if not _PYDANTIC_AVAILABLE:  # pragma: no cover - executed when dependency missing
        raise RuntimeError("pydantic>=2 is required for ETL schema validation. Install it via requirements-etl.txt.")


class NewsRecordModel(BaseModel):
    timestamp: pd.Timestamp = Field(..., description="UTC timestamp of the news event")
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    news_volume: float = Field(..., ge=0.0)
    source: str = Field(..., min_length=1)

    class Config:
        arbitrary_types_allowed = True


class OnChainRecordModel(BaseModel):
    timestamp: pd.Timestamp = Field(...)
    onchain_active_addresses: float = Field(..., ge=0.0)
    onchain_tx_volume: float = Field(..., ge=0.0)
    stablecoin_ratio: float = Field(...)

    class Config:
        arbitrary_types_allowed = True


@dataclass
class ValidationReport:
    passed: bool
    errors: List[str]


def _frame_records(frame: pd.DataFrame) -> Iterable[Mapping[str, object]]:
    if frame.index.name == "timestamp":
        frame = frame.reset_index()
    elif "timestamp" not in frame.columns:
        frame = frame.reset_index(drop=False)
        if "timestamp" not in frame.columns:
            raise KeyError("DataFrame must expose a 'timestamp' column for validation")
    records = frame.to_dict(orient="records")
    return records


def validate_dataframe(frame: pd.DataFrame, source: str) -> Tuple[pd.DataFrame, ValidationReport]:
    """Validate a DataFrame against source-specific schema."""

    _require_pydantic()
    if source.lower().startswith("news"):
        model = NewsRecordModel
    else:
        model = OnChainRecordModel

    records = _frame_records(frame)
    errors: List[str] = []
    valid_rows: List[Mapping[str, object]] = []
    for row in records:
        try:
            instance = model.model_validate(row)
        except ValidationError as exc:
            errors.append(str(exc))
        else:
            valid_rows.append(instance.model_dump())

    validated = pd.DataFrame(valid_rows)
    if not validated.empty:
        validated["timestamp"] = pd.to_datetime(validated["timestamp"], utc=True)
        validated = validated.set_index("timestamp", drop=True).sort_index()

    report = ValidationReport(passed=len(errors) == 0, errors=errors)
    return validated, report


__all__ = [
    "NewsRecordModel",
    "OnChainRecordModel",
    "ValidationReport",
    "validate_dataframe",
]
