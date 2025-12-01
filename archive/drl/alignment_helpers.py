"""Alignment utilities for combining multi-frequency time series."""
from __future__ import annotations

from typing import Dict, Mapping, MutableMapping, Optional, Literal

import pandas as pd


FillMethod = Literal["ffill", "bfill", "nearest"]


def resample_frame(
    frame: pd.DataFrame,
    *,
    frequency: str,
    agg: str = "mean",
    fill_method: Optional[FillMethod] = None,
    limit: Optional[int] = None,
) -> pd.DataFrame:
    """Resample a frame to the requested frequency."""

    if frame.empty:
        return frame.copy()

    resampled = frame.sort_index().resample(frequency).agg(agg)
    if fill_method == "ffill":
        resampled = resampled.ffill(limit=limit)
    elif fill_method == "bfill":
        resampled = resampled.bfill(limit=limit)
    elif fill_method == "nearest":
        resampled = resampled.interpolate(method="nearest", limit=limit)
    return resampled


def forward_fill(frame: pd.DataFrame, *, limit: Optional[int] = None) -> pd.DataFrame:
    """Forward fill missing values respecting optional limit."""

    if frame.empty:
        return frame.copy()
    return frame.sort_index().ffill(limit=limit)


def align_frames(
    frames: Mapping[str, pd.DataFrame],
    *,
    frequency: str,
    join: Literal["inner", "outer"] = "outer",
    fill_method: Optional[FillMethod] = "ffill",
    fill_limit: Optional[int] = None,
    agg: str = "first",
) -> pd.DataFrame:
    """Align multiple frames to a shared frequency and merge columns."""

    if not frames:
        return pd.DataFrame()

    non_empty_frames = [frame for frame in frames.values() if not frame.empty]
    if not non_empty_frames:
        resampled = {
            name: resample_frame(frame, frequency=frequency, fill_method=None, agg=agg).add_prefix(f"{name}__")
            for name, frame in frames.items()
        }
        return pd.concat(list(resampled.values()), axis=1, join=join)

    anchor = min(frame.index.min() for frame in non_empty_frames).floor(frequency)
    horizon_end = max(frame.index.max() for frame in non_empty_frames)
    natural_range = pd.date_range(anchor, horizon_end, freq=frequency)
    natural_periods = len(natural_range) if len(natural_range) else 1
    longest_input = max(len(frame) for frame in non_empty_frames)
    target_periods = max(natural_periods, longest_input)
    target_index = pd.date_range(anchor, periods=target_periods, freq=frequency)

    resampled: MutableMapping[str, pd.DataFrame] = {}
    for name, frame in frames.items():
        resampled_frame = resample_frame(frame, frequency=frequency, fill_method=None, agg=agg)
        resampled[name] = resampled_frame.add_prefix(f"{name}__")

    combined = pd.concat(list(resampled.values()), axis=1, join=join).sort_index()

    if join == "outer":
        combined = combined.reindex(target_index)

    if fill_method == "ffill":
        combined = combined.ffill(limit=fill_limit)
    elif fill_method == "bfill":
        combined = combined.bfill(limit=fill_limit)
    elif fill_method == "nearest":
        combined = combined.interpolate(method="nearest", limit=fill_limit)

    combined = combined.loc[~combined.index.duplicated(keep="last")]
    return combined


__all__ = ["resample_frame", "forward_fill", "align_frames"]
