from __future__ import annotations

import pandas as pd
from research.winner_anatomy_2026_08_11 import build_report


def test_winner_profiles_are_descriptive_and_capture_high_volatility(tmp_path):
    frame = pd.DataFrame(
        {
            "symbol": ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"],
            "scan_date": ["2026-01-01"] * 3 + ["2026-01-02"] * 3,
            "c2c_1d": [-2, -1, 0, 1, 2, 10],
            "c2c_5d": [-4, -2, 0, 2, 4, 20],
            "gap_pct": [0, 0, 0, 0, 0, 0],
            "rvol": [0.5, 0.6, 0.7, 0.8, 0.9, 2.0],
            "atr_pct_real": [2, 2, 3, 3, 4, 8],
            "sentiment": [0, 0, 0, 0, 0, 0],
            "overnight_gap_factor": [0, 0, 0, 0, 0, 0],
            "score": [1, 1, 1, 1, 1, 1],
            "entry_ok": [0, 0, 0, 0, 0, 0],
            "catalyst_factor": [0, 0, 0, 0, 0, 0],
        }
    )

    report = build_report(frame, source=__file__, root=tmp_path)

    profile = report["profiles"]["c2c_5d"]
    assert profile["winner_rows"] == 1
    assert profile["features"]["rvol"]["winner_median"] > profile["features"]["rvol"]["all_median"]
    assert "not causal" in profile["interpretation"]
    assert report["same_date_controls"]["c2c_1d"]["days"] == 1
    assert report["temporal_predictive_check"]["c2c_1d"]["train"]["rows"] > 0
    assert report["pre_scan_feature_selection"]["c2c_1d"]["rvol"]["validation"]["selected_n"] > 0
    assert "train_threshold" in report["pre_scan_feature_selection"]["c2c_1d"]["atr_pct_real"]
