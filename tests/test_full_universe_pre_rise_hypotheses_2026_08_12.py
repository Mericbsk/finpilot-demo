from __future__ import annotations

import pandas as pd
import pytest
from research.full_universe_pre_rise_hypotheses_2026_08_12 import (
    _paired_inference,
    daily_path_features,
    feature_selection,
)


def _bar(
    date: str, close: float, high: float | None = None, low: float | None = None
) -> dict[str, object]:
    return {
        "date": date,
        "open": close,
        "high": high or close + 1,
        "low": low or close - 1,
        "close": close,
    }


def test_daily_features_use_only_bars_before_scan_date():
    bars = [
        _bar(f"2026-01-{day:02d}", 100 + day, high=101 + day, low=99 + day) for day in range(1, 12)
    ]
    bars[-1]["close"] = bars[-1]["high"]
    benchmark = [_bar(f"2026-01-{day:02d}", 100) for day in range(1, 13)]

    features = daily_path_features(bars, "2026-01-12", benchmark, benchmark)

    assert features is not None
    assert features["daily_close_location"] > 0.5
    assert features["daily_trend_consistency_5d"] == 1.0


def test_combination_threshold_is_learned_on_train_dates_only():
    rows = []
    for date, values in [
        ("2026-01-01", [0.1, 0.2, 0.3, 1.0]),
        ("2026-01-02", [0.9, 0.9, 0.9, 0.8]),
    ]:
        for index, value in enumerate(values):
            rows.append(
                {
                    "symbol": f"S{index}",
                    "scan_date": date,
                    "c2c_1d": value,
                    "daily_close_location": value,
                    "daily_trend_consistency_5d": value,
                    "daily_relative_strength_5d_spy": value,
                    "daily_range_expansion_ratio": value,
                }
            )

    result = feature_selection(pd.DataFrame(rows), "c2c_1d")

    assert result["train_dates"] == 1
    assert result["validation_dates"] == 1
    assert result["combination"]["thresholds_learned_on_train"][
        "daily_close_location"
    ] == pytest.approx(0.37)


def test_paired_inference_is_reproducible_and_reports_interval_and_null():
    result = _paired_inference([1.0, 1.0, -0.5, 0.5, 2.0], seed=7)

    assert result["iterations"] == 2000
    assert result["observed_median_difference_pct"] == 1.0
    assert len(result["bootstrap_median_ci_95_pct"]) == 2
    assert len(result["null_median_ci_95_pct"]) == 2
    assert 0.0 <= result["two_sided_permutation_p_value"] <= 1.0
    assert result == _paired_inference([1.0, 1.0, -0.5, 0.5, 2.0], seed=7)
