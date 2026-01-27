from __future__ import annotations

import pandas as pd

from drl.alignment_helpers import align_frames, forward_fill, resample_frame


def _build_df(values):
    return pd.DataFrame(
        {"value": values},
        index=pd.date_range("2025-01-01", periods=len(values), freq="12h", tz="UTC"),
    )


def test_resample_frame_to_daily_mean():
    frame = _build_df([1, 2, 3, 4])
    resampled = resample_frame(frame, frequency="1D", agg="sum")
    assert len(resampled) == 2
    assert resampled.iloc[0, 0] == 3
    assert resampled.iloc[1, 0] == 7


def test_forward_fill_respects_limit():
    frame = pd.DataFrame(
        {"value": [1.0, None, None, 4.0]},
        index=pd.date_range("2025-01-01", periods=4, freq="D", tz="UTC"),
    )
    filled = forward_fill(frame, limit=1)
    assert filled.iloc[1, 0] == 1.0
    assert pd.isna(filled.iloc[2, 0])


def test_align_frames_resamples_and_merges():
    news = _build_df([1, 2, 3])
    onchain = _build_df([10, 20, 30, 40])
    aligned = align_frames({"news": news, "onchain": onchain}, frequency="1D", join="outer")
    assert "news__value" in aligned.columns and "onchain__value" in aligned.columns
    assert aligned.shape[0] == 4
    assert aligned.iloc[0, 0] == 1
