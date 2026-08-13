from __future__ import annotations

import pandas as pd
from research.pre_rise_path_battery_2026_08_11 import compute_path_features, temporal_feature_tests


def test_path_features_capture_expansion_and_reversal():
    bars = [
        {"open": 100.0, "high": 101.0, "low": 99.5, "close": 100.5},
        {"open": 100.5, "high": 101.0, "low": 100.0, "close": 100.8},
        {"open": 100.8, "high": 104.0, "low": 100.5, "close": 103.5},
        {"open": 103.5, "high": 105.0, "low": 102.0, "close": 102.5},
    ]

    features = compute_path_features(bars)

    assert features is not None
    assert features["path_range_expansion_ratio"] > 1
    assert features["path_reversal_pct"] > 0


def test_temporal_feature_threshold_is_learned_without_future_dates():
    frame = pd.DataFrame(
        {
            "scan_date": ["2026-01-01"] * 4 + ["2026-01-02"] * 4,
            "c2c_1d": [-1, 0, 1, 2, -2, 0, 1, 3],
            "path_range_expansion_ratio": [1, 2, 3, 4, 1, 2, 3, 4],
        }
    )

    result = temporal_feature_tests(frame, "c2c_1d")

    assert result["train_dates"] == 1
    assert result["validation_dates"] == 1
    assert result["features"]["path_range_expansion_ratio"]["threshold_train"] == 3.7
