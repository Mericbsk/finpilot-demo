from __future__ import annotations

import pandas as pd
import pytest
from scanner.features import (
    compute_dist_52w_high,
    compute_gap_pct,
    compute_rvol_daily,
)


@pytest.fixture
def known_daily_bars() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Open": [100.0, 104.0, 110.0],
            "High": [102.0, 106.0, 112.0],
            "Close": [101.0, 105.0, 111.0],
            "Volume": [1000.0, 2000.0, 4500.0],
        },
        index=pd.to_datetime(["2026-08-12", "2026-08-13", "2026-08-14"]),
    )


def test_dist_52w_high_uses_latest_close_and_252_bar_high(known_daily_bars):
    assert compute_dist_52w_high(known_daily_bars) == pytest.approx(111.0 / 112.0, abs=1e-4)


def test_gap_pct_uses_latest_open_and_previous_close(known_daily_bars):
    expected = round((110.0 - 105.0) / 105.0 * 100.0, 4)
    assert compute_gap_pct(known_daily_bars) == pytest.approx(expected)


def test_rvol_daily_uses_latest_volume_and_prior_20_day_average(known_daily_bars):
    assert compute_rvol_daily(known_daily_bars) == pytest.approx(4500.0 / 1500.0)


def test_daily_attention_features_return_zero_when_required_data_is_missing():
    assert compute_dist_52w_high(pd.DataFrame()) == 0.0
    assert compute_gap_pct(pd.DataFrame({"Open": [1.0], "Close": [1.0]})) == 0.0
    assert compute_rvol_daily(pd.DataFrame({"Volume": [100.0]})) == 0.0
