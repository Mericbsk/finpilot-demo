"""Feature engineering pipeline for the DRL engine.

The module exposes ``FeaturePipeline`` which:

1. Validates the incoming feature frame against :mod:`drl.config` specs.
2. Learns per-column statistics (mean/std or median/IQR) during ``fit``.
3. Transforms observations into ordered numpy arrays to be consumed by
   :class:`drl.market_env.MarketEnv`.

The implementation intentionally avoids external ML libraries so it can execute
inside Streamlit, batch workers, and notebooks without additional dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import (
    Dict,
    Iterable,
    List,
    Literal,
    Mapping,
    Optional,
    Sequence,
    TypedDict,
    Union,
    cast,
)

import numpy as np
import pandas as pd

from .config import FeatureSpec, MarketEnvConfig


class _ZScoreStats(TypedDict):
    type: Literal["zscore"]
    mean: float
    std: float


class _RobustStats(TypedDict):
    type: Literal["robust"]
    median: float
    iqr: float


class _MinMaxStats(TypedDict):
    type: Literal["minmax"]
    min: float
    span: float


class _NoneStats(TypedDict):
    type: Literal["none"]


ColumnStats = Union[_ZScoreStats, _RobustStats, _MinMaxStats, _NoneStats]
ScalerStats = Dict[str, Dict[str, ColumnStats]]


@dataclass
class FeatureFrame:
    """Canonical structure consumed by the pipeline."""

    data: pd.DataFrame

    @classmethod
    def from_records(cls, records: Sequence[Mapping[str, float]]) -> FeatureFrame:
        return cls(pd.DataFrame.from_records(records))


class FeaturePipeline:
    """Transforms raw feature frames into agent-ready tensors."""

    def __init__(self, config: MarketEnvConfig):
        self.config = config
        self._stats: ScalerStats = {}
        self._ordered_columns: List[str] = list(config.feature_columns)

    # ------------------------------------------------------------------
    # Fitting & transformation
    # ------------------------------------------------------------------
    def fit(self, frame: FeatureFrame) -> None:
        """Learn scaling statistics from the supplied frame.

        Parameters
        ----------
        frame:
            FeatureFrame containing at least the columns described in the
            configuration. Extra columns are ignored.
        """

        df = frame.data
        missing = [col for col in self._ordered_columns if col not in df.columns]
        if missing:
            required_missing = [
                col
                for spec in self.config.feature_specs
                if spec.required
                for col in spec.columns
                if col in missing
            ]
            if required_missing:
                raise KeyError("Missing required feature columns: " + ", ".join(required_missing))

        stats: ScalerStats = {}
        for spec in self.config.feature_specs:
            spec_stats: Dict[str, ColumnStats] = {}
            for column in spec.columns:
                if column not in df.columns:
                    continue
                series = df[column].astype(float)
                if spec.scaler == "zscore":
                    mean = float(series.mean())
                    std = float(series.std(ddof=0)) or 1.0
                    spec_stats[column] = cast(
                        ColumnStats,
                        {"type": "zscore", "mean": mean, "std": std},
                    )
                elif spec.scaler == "robust":
                    median = float(series.median())
                    q1 = float(series.quantile(0.25))
                    q3 = float(series.quantile(0.75))
                    iqr = (q3 - q1) or 1.0
                    spec_stats[column] = cast(
                        ColumnStats,
                        {
                            "type": "robust",
                            "median": median,
                            "iqr": iqr,
                        },
                    )
                elif spec.scaler == "minmax":
                    min_val = float(series.min())
                    max_val = float(series.max())
                    span = (max_val - min_val) or 1.0
                    spec_stats[column] = cast(
                        ColumnStats,
                        {
                            "type": "minmax",
                            "min": min_val,
                            "span": span,
                        },
                    )
                else:  # "none" or unsupported
                    spec_stats[column] = cast(ColumnStats, {"type": "none"})
            if spec_stats:
                stats[spec.name] = spec_stats
        self._stats = stats

    def transform(self, frame: FeatureFrame) -> np.ndarray:
        """Transform the frame into an ordered numpy array."""

        if not self._stats:
            raise RuntimeError("FeaturePipeline must be fitted before calling transform().")

        df = frame.data
        rows: List[np.ndarray] = []
        for _, row in df.iterrows():
            rows.append(self._transform_row(row))
        return np.vstack(rows).astype(self.config.target_dtype)

    def transform_row(self, row: Mapping[str, float]) -> np.ndarray:
        """Transform a single observation mapping into the feature vector."""

        if not self._stats:
            raise RuntimeError("FeaturePipeline must be fitted before calling transform_row().")
        pandas_row = pd.Series(row, dtype=float)
        return self._transform_row(pandas_row).astype(self.config.target_dtype)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _transform_row(self, row: pd.Series) -> np.ndarray:
        values: List[float] = []
        stats = self._stats
        for spec in self.config.feature_specs:
            spec_stats = stats.get(spec.name)
            for column in spec.columns:
                if spec_stats is None or column not in spec_stats:
                    # Missing optional feature → fall back to zero.
                    values.append(0.0)
                    continue
                val = float(row.get(column, 0.0))
                info = spec_stats[column]
                if info["type"] == "zscore":
                    typed = cast(_ZScoreStats, info)
                    norm = (val - typed["mean"]) / typed["std"]
                elif info["type"] == "robust":
                    typed = cast(_RobustStats, info)
                    norm = (val - typed["median"]) / typed["iqr"]
                elif info["type"] == "minmax":
                    typed = cast(_MinMaxStats, info)
                    norm = (val - typed["min"]) / typed["span"]
                else:  # "none"
                    norm = val
                values.append(norm * spec.weight)
        return np.asarray(values, dtype=float)

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def export_state(self) -> ScalerStats:
        """Serialize scaling statistics for storage in MLflow/W&B."""

        return self._stats

    def load_state(self, state: ScalerStats) -> None:
        """Load previously exported scaling statistics."""

        self._stats = state


__all__ = ["FeaturePipeline", "FeatureFrame", "ScalerStats"]
