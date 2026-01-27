from __future__ import annotations

import numpy as np
import pandas as pd

from drl.feature_generators import (
    WeightedSentimentConfig,
    assemble_feature_frame,
    calculate_momentum,
    calculate_weighted_sentiment,
    create_lag_features,
)


def test_calculate_weighted_sentiment_matches_manual_ewm():
    dates = pd.date_range("2025-01-01", periods=5, freq="D", tz="UTC")
    frame = pd.DataFrame(
        {
            "sentiment_score": [0.1, 0.2, -0.5, 0.3, 0.6],
            "news_volume": [1.0, 2.0, 1.0, 3.0, 4.0],
        },
        index=dates,
    )
    config = WeightedSentimentConfig(decay=0.4, min_periods=1)
    result = calculate_weighted_sentiment(frame, config=config)

    weighted_values = (
        (frame["sentiment_score"] * frame["news_volume"])
        .ewm(
            alpha=config.decay,
            adjust=False,
            min_periods=config.min_periods,
        )
        .mean()
    )
    normaliser = (
        frame["news_volume"]
        .ewm(
            alpha=config.decay,
            adjust=False,
            min_periods=config.min_periods,
        )
        .mean()
    )
    expected = weighted_values / normaliser

    pd.testing.assert_series_equal(result, expected.rename(config.result_col))


def test_calculate_weighted_sentiment_handles_missing_columns():
    frame = pd.DataFrame(index=pd.date_range("2025-01-01", periods=3, freq="D", tz="UTC"))
    result = calculate_weighted_sentiment(frame)
    assert result.empty
    assert result.name == "wtd_sentiment_score"


def test_calculate_momentum_percentage():
    frame = pd.DataFrame(
        {"onchain_active_addresses": [100.0, 110.0, 121.0, 90.0]},
        index=pd.date_range("2025-01-01", periods=4, freq="D", tz="UTC"),
    )
    features = calculate_momentum(frame, "onchain_active_addresses", periods=[1, 2])
    expected_cols = {"onchain_active_addresses_momentum_1", "onchain_active_addresses_momentum_2"}
    assert set(features.columns) == expected_cols
    np.testing.assert_allclose(features.iloc[2, 0], 0.1, atol=1e-8)
    np.testing.assert_allclose(features.iloc[3, 1], -0.1818181818, atol=1e-8)


def test_create_lag_features_multiple_columns():
    frame = pd.DataFrame(
        {
            "sentiment_score": [0.1, 0.2, 0.3, 0.4],
            "news_volume": [1, 2, 3, 4],
        },
        index=pd.date_range("2025-01-01", periods=4, freq="D", tz="UTC"),
    )
    lags = create_lag_features(frame, ["sentiment_score", "news_volume"], lags=[1, 2])
    expected_cols = {
        "sentiment_score_lag_1",
        "sentiment_score_lag_2",
        "news_volume_lag_1",
        "news_volume_lag_2",
    }
    assert set(lags.columns) == expected_cols
    assert pd.isna(lags.loc[frame.index[0], "sentiment_score_lag_1"])
    assert lags.loc[frame.index[2], "news_volume_lag_2"] == 1


def test_assemble_feature_frame_combines_series_and_frames():
    base = pd.DataFrame(
        {"base_col": [1, 2, 3]},
        index=pd.date_range("2025-01-01", periods=3, freq="D", tz="UTC"),
    )
    series = pd.Series([0.5, 0.1, -0.2], index=base.index, name="extra")
    additional = pd.DataFrame({"more": [10, 11, 12]}, index=base.index)
    assembled = assemble_feature_frame(series, additional, base=base)
    assert list(assembled.columns) == ["base_col", "extra", "more"]
