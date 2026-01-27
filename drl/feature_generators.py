"""Feature generation utilities for alternative data sources."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, MutableMapping, Optional, Sequence

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class WeightedSentimentConfig:
    sentiment_col: str = "sentiment_score"
    weight_col: Optional[str] = "news_volume"
    decay: float = 0.35
    min_periods: int = 1
    result_col: str = "wtd_sentiment_score"

    def __post_init__(self) -> None:
        if not (0.0 < self.decay <= 1.0):
            raise ValueError("decay must be within (0, 1]")
        if self.min_periods < 1:
            raise ValueError("min_periods must be >= 1")


def calculate_weighted_sentiment(
    frame: pd.DataFrame, config: WeightedSentimentConfig = WeightedSentimentConfig()
) -> pd.Series:
    """Compute exponentially weighted sentiment scores.

    Parameters
    ----------
    frame:
        DataFrame sorted by timestamp index containing sentiment columns.
    config:
        Configuration for column names and EWMA decay.
    """

    if frame.empty or config.sentiment_col not in frame.columns:
        return pd.Series(dtype=float, name=config.result_col)

    df = frame.sort_index()
    sentiment = df[config.sentiment_col].astype(float).fillna(0.0)

    if config.weight_col and config.weight_col in df.columns:
        weights = df[config.weight_col].astype(float).clip(lower=0.0).fillna(0.0)
        weighted_values = (
            (sentiment * weights)
            .ewm(alpha=config.decay, adjust=False, min_periods=config.min_periods)
            .mean()
        )
        normaliser = weights.ewm(
            alpha=config.decay, adjust=False, min_periods=config.min_periods
        ).mean()
        result = weighted_values / normaliser.replace(to_replace=0.0, value=np.nan)
    else:
        result = sentiment.ewm(
            alpha=config.decay, adjust=False, min_periods=config.min_periods
        ).mean()

    return result.rename(config.result_col)


def calculate_momentum(
    frame: pd.DataFrame,
    column: str,
    periods: Sequence[int],
    *,
    pct: bool = True,
    suffix: str = "momentum",
) -> pd.DataFrame:
    """Calculate momentum features for a numeric column.

    Parameters
    ----------
    frame:
        Input DataFrame containing the target column.
    column:
        Column name to compute momentum on.
    periods:
        Iterable of lag periods (in rows) to evaluate.
    pct:
        When True, use percentage change; otherwise raw difference.
    suffix:
        Suffix to append to generated column names.
    """

    if frame.empty or column not in frame.columns:
        return pd.DataFrame(index=frame.index)

    series = frame[column].astype(float)
    data: MutableMapping[str, pd.Series] = {}
    for period in periods:
        if period <= 0:
            raise ValueError("periods must contain positive integers")
        if pct:
            momentum = series.pct_change(periods=period)
        else:
            momentum = series.diff(periods=period)
        col_name = f"{column}_{suffix}_{period}"
        data[col_name] = momentum
    return pd.DataFrame(data, index=frame.index).sort_index()


def create_lag_features(
    frame: pd.DataFrame,
    columns: Sequence[str],
    lags: Sequence[int],
    *,
    prefix: str = "lag",
) -> pd.DataFrame:
    """Produce lagged versions of specified columns."""

    if frame.empty:
        return pd.DataFrame(index=frame.index)

    data: MutableMapping[str, pd.Series] = {}
    for column in columns:
        if column not in frame.columns:
            continue
        for lag in lags:
            if lag <= 0:
                raise ValueError("lags must contain positive integers")
            lagged = frame[column].shift(lag)
            col_name = f"{column}_{prefix}_{lag}"
            data[col_name] = lagged
    return pd.DataFrame(data, index=frame.index).sort_index()


def assemble_feature_frame(
    *frames: Iterable[pd.Series | pd.DataFrame],
    base: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Concatenate feature pieces into a single DataFrame.

    Parameters
    ----------
    frames:
        Series/DataFrames aligned on the same index.
    base:
        Optional starting DataFrame. When provided, its columns will be included first.
    """

    pieces = []
    if base is not None:
        pieces.append(base)
    for frame in frames:
        if isinstance(frame, pd.Series):
            pieces.append(frame.to_frame())
        else:
            pieces.append(frame)
    if not pieces:
        return pd.DataFrame()
    return pd.concat(pieces, axis=1).sort_index()


__all__ = [
    "WeightedSentimentConfig",
    "calculate_weighted_sentiment",
    "calculate_momentum",
    "create_lag_features",
    "assemble_feature_frame",
]
