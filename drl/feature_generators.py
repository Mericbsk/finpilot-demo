"""Feature generation utilities for alternative data sources."""

from __future__ import annotations

from collections.abc import Iterable, MutableMapping, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class WeightedSentimentConfig:
    sentiment_col: str = "sentiment_score"
    weight_col: str | None = "news_volume"
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
        momentum = series.pct_change(periods=period) if pct else series.diff(periods=period)
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
    base: pd.DataFrame | None = None,
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
    "calculate_alpha158_features",
]


def calculate_alpha158_features(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate Qlib Alpha158-inspired features for DRL training (INT-6).

    Adds 25 new features to the input DataFrame:
    - ROC series: roc_5, roc_10, roc_20, roc_30, roc_60 (5)
    - STD series: std_5, std_10, std_20, std_30 (4)
    - Multi-period RSI: rsi_5, rsi_10, rsi_20, rsi_30 (4)
    - Price-volume correlation: corr_pv_5, corr_pv_10, corr_pv_20 (3)
    - Candlestick: kmid, klen, kmid2, kup, kdn (5)
    - Multi-period EMA ratios: close_ema5_ratio, close_ema10_ratio, close_ema30_ratio, close_ema60_ratio (4)

    All values are normalised to be scale-free and clipped to [-10, 10].

    Args:
        df: DataFrame with OHLCV columns (Open, High, Low, Close, Volume).

    Returns:
        DataFrame with Alpha158 feature columns appended.
    """
    if df.empty:
        return df

    required = {"Open", "High", "Low", "Close", "Volume"}
    missing = required - set(df.columns)
    if missing:
        return df

    result = df.copy()

    def _s(col: str) -> pd.Series:
        s = result[col]
        return s.iloc[:, 0] if isinstance(s, pd.DataFrame) else s

    close = _s("Close")
    high = _s("High")
    low = _s("Low")
    open_ = _s("Open")
    vol = _s("Volume")

    # ── ROC Series ────────────────────────────────────────────────────────────
    for d in (5, 10, 20, 30, 60):
        result[f"roc_{d}"] = close.pct_change(d)

    # ── STD Series ────────────────────────────────────────────────────────────
    ret = close.pct_change()
    for d in (5, 10, 20, 30):
        result[f"std_{d}"] = ret.rolling(d).std()

    # ── Multi-period RSI ──────────────────────────────────────────────────────
    def _rsi(s: pd.Series, p: int) -> pd.Series:
        delta = s.diff()
        up = delta.clip(lower=0)
        dn = -delta.clip(upper=0)
        rs = up.ewm(alpha=1 / p, adjust=False).mean() / dn.ewm(
            alpha=1 / p, adjust=False
        ).mean().replace(0, 1e-10)
        return 100 - (100 / (1 + rs))

    for d in (5, 10, 20, 30):
        result[f"rsi_{d}"] = _rsi(close, d)

    # ── Price-Volume Correlation ──────────────────────────────────────────────
    log_vol = vol.apply(lambda x: float(np.log(x + 1)) if x > 0 else 0.0)
    for d in (5, 10, 20):
        result[f"corr_pv_{d}"] = ret.rolling(d).corr(log_vol)

    # ── Candlestick Features ──────────────────────────────────────────────────
    day_range = (high - low).replace(0, float("nan"))
    result["kmid"] = ((close - open_) / day_range).fillna(0.0)
    result["klen"] = ((high - low) / open_.replace(0, float("nan"))).fillna(0.0)
    result["kmid2"] = ((close - open_) / (open_.replace(0, float("nan")) * 2)).fillna(0.0)
    result["kup"] = ((high - pd.concat([open_, close], axis=1).max(axis=1)) / day_range).fillna(0.0)
    result["kdn"] = ((pd.concat([open_, close], axis=1).min(axis=1) - low) / day_range).fillna(0.0)

    # ── Extended EMA Ratios ───────────────────────────────────────────────────
    for d in (5, 10, 30, 60):
        ema = close.ewm(span=d, adjust=False).mean()
        result[f"close_ema{d}_ratio"] = (close / ema - 1.0).replace(
            [float("inf"), float("-inf")], 0.0
        )

    # ── Clip ──────────────────────────────────────────────────────────────────
    alpha_cols = (
        [f"roc_{d}" for d in (5, 10, 20, 30, 60)]
        + [f"std_{d}" for d in (5, 10, 20, 30)]
        + [f"rsi_{d}" for d in (5, 10, 20, 30)]
        + [f"corr_pv_{d}" for d in (5, 10, 20)]
        + ["kmid", "klen", "kmid2", "kup", "kdn"]
        + [f"close_ema{d}_ratio" for d in (5, 10, 30, 60)]
    )
    for col in alpha_cols:
        if col in result.columns:
            result[col] = result[col].clip(-10.0, 10.0)

    return result
