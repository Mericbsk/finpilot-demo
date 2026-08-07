"""Canonical evidence records for reproducible research experiments.

The ledger identifies one decision-time observation and keeps data, label and
cost provenance together. It is research-only and does not select signals or
change production behavior.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Any


class EvidenceError(ValueError):
    """Raised when a research evidence record is incomplete or inconsistent."""


def _parse_date(value: str, field_name: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise EvidenceError(f"{field_name} must be an ISO date") from exc


def _parse_timestamp(value: str, field_name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise EvidenceError(f"{field_name} must be an ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise EvidenceError(f"{field_name} must include a timezone")
    return parsed


@dataclass(frozen=True)
class EvidenceEvent:
    """One canonical decision-time observation and its outcome metadata."""

    symbol: str
    scan_date: str
    snapshot_id: str
    feature_as_of: str
    label_version: str
    cost_model_version: str
    outcome_status: str = "unresolved"
    outcome_as_of: str | None = None
    source_snapshot: str | None = None

    @property
    def event_id(self) -> str:
        """Return a stable ID independent of JSON field ordering."""
        payload = {
            "symbol": self.symbol.strip().upper(),
            "scan_date": self.scan_date,
            "snapshot_id": self.snapshot_id,
            "feature_as_of": self.feature_as_of,
            "label_version": self.label_version,
            "cost_model_version": self.cost_model_version,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()[:24]

    def validate(self) -> None:
        text_fields = (
            (self.symbol, "symbol"),
            (self.snapshot_id, "snapshot_id"),
            (self.label_version, "label_version"),
            (self.cost_model_version, "cost_model_version"),
        )
        for value, field_name in text_fields:
            if not value or not value.strip():
                raise EvidenceError(f"{field_name} is required")

        scan_date = _parse_date(self.scan_date, "scan_date")
        feature_as_of = _parse_timestamp(self.feature_as_of, "feature_as_of")
        if feature_as_of.date() > scan_date:
            raise EvidenceError("feature_as_of cannot be after scan_date")

        if self.outcome_status not in {"unresolved", "resolved", "insufficient_data"}:
            raise EvidenceError(f"unsupported outcome_status: {self.outcome_status}")
        if self.outcome_status == "resolved" and not self.outcome_as_of:
            raise EvidenceError("resolved evidence requires outcome_as_of")
        if self.outcome_as_of:
            _parse_timestamp(self.outcome_as_of, "outcome_as_of")

    def as_dict(self) -> dict[str, Any]:
        self.validate()
        result = asdict(self)
        result["event_id"] = self.event_id
        return result
