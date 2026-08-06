"""Research protocol controls for reproducible, research-only experiments.

These controls do not select signals or change production behavior. They make
the minimum metadata and access rules explicit before a research run can be
reported as valid.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any


class ProtocolError(ValueError):
    """Raised when a research protocol record is incomplete or inconsistent."""


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ProtocolError(f"invalid ISO date: {value!r}") from exc


@dataclass(frozen=True)
class TemporalSplit:
    """Non-overlapping chronological train/validation/locked-OOS split."""

    train_end: str
    validation_end: str
    locked_oos_end: str

    def validate(self) -> None:
        train_end = _parse_date(self.train_end)
        validation_end = _parse_date(self.validation_end)
        locked_oos_end = _parse_date(self.locked_oos_end)
        if not train_end < validation_end < locked_oos_end:
            raise ProtocolError(
                "temporal split must satisfy train_end < validation_end < locked_oos_end"
            )

    def as_dict(self) -> dict[str, str]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class CostModel:
    """Versioned round-trip cost declaration in basis points."""

    version: str
    commission_bps: float | None
    spread_bps: float | None
    slippage_bps: float | None
    impact_bps: float | None

    def validate(self) -> None:
        if not self.version.strip():
            raise ProtocolError("cost model version is required")
        fields = (
            self.commission_bps,
            self.spread_bps,
            self.slippage_bps,
            self.impact_bps,
        )
        if any(value is None for value in fields):
            raise ProtocolError("missing cost fields must remain insufficient_data")
        if any(value < 0 for value in fields if value is not None):
            raise ProtocolError("cost fields cannot be negative")

    def round_trip_bps(self) -> float:
        self.validate()
        return sum(
            value
            for value in (
                self.commission_bps,
                self.spread_bps,
                self.slippage_bps,
                self.impact_bps,
            )
            if value is not None
        )


@dataclass(frozen=True)
class FERRecord:
    """Minimum FinPilot Experiment Registry record."""

    experiment_id: str
    hypothesis: str
    economic_rationale: str
    data_snapshot: str
    date_range: str
    split: TemporalSplit
    factors: tuple[str, ...]
    pairwise_tests: int
    triple_tests: int
    max_interaction_order: int
    cost_model: CostModel
    n_trials: int
    status: str
    reviewer: str | None = None
    decision: str | None = None
    evidence_path: str | None = None

    def validate(self) -> None:
        required_text = (
            self.experiment_id,
            self.hypothesis,
            self.economic_rationale,
            self.data_snapshot,
            self.date_range,
        )
        if any(not value.strip() for value in required_text):
            raise ProtocolError("FER requires hypothesis, rationale, data, and date range")
        if not self.factors:
            raise ProtocolError("FER requires at least one factor")
        if self.pairwise_tests < 0 or self.pairwise_tests > 25:
            raise ProtocolError("pairwise interaction tests must be between 0 and 25")
        if self.triple_tests < 0 or self.triple_tests > 10:
            raise ProtocolError("triple interaction tests must be between 0 and 10")
        if self.max_interaction_order > 3:
            raise ProtocolError("four-way interactions are not permitted")
        if self.max_interaction_order < 1:
            raise ProtocolError("interaction order must be at least one")
        if self.n_trials < 1:
            raise ProtocolError("FER requires at least one recorded trial")
        if self.status not in {"proposed", "completed", "rejected", "insufficient_data"}:
            raise ProtocolError(f"unsupported FER status: {self.status}")
        self.split.validate()
        self.cost_model.validate()

    def as_dict(self) -> dict[str, Any]:
        self.validate()
        result = asdict(self)
        result["split"] = self.split.as_dict()
        result["cost_model"] = asdict(self.cost_model)
        result["factors"] = list(self.factors)
        return result


class LockedHoldoutGuard:
    """Persist a one-time locked holdout opening event."""

    def __init__(self, state_path: Path):
        self.state_path = state_path

    def open_once(self, experiment_id: str) -> dict[str, str]:
        if self.state_path.exists():
            raise ProtocolError("locked holdout has already been opened")
        if not experiment_id.strip():
            raise ProtocolError("experiment_id is required to open locked holdout")
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "experiment_id": experiment_id,
            "opened_at": datetime.now(UTC).isoformat(),
        }
        self.state_path.write_text(json.dumps(event, indent=2), encoding="utf-8")
        return event


def file_sha256(path: Path) -> str:
    """Return a stable SHA-256 hash for a research input artifact."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
