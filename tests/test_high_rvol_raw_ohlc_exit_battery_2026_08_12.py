import json

import pandas as pd
import pytest
from research.high_rvol_raw_ohlc_exit_battery_2026_08_12 import _first_touch_exit, run


def test_first_touch_exit_prefers_stop_on_same_bar():
    item = {
        "entry": 100.0,
        "atr_pct": 2.0,
        "highs": [103.0],
        "lows": [97.0],
        "opens": [100.0],
        "close_returns": [0.0],
    }
    value, event = _first_touch_exit(item, horizon=1, target_pct=2.0, stop_multiple=1.0)
    assert event == "stop"
    assert value == pytest.approx(-2.0)


def test_raw_ohlc_horizon_and_stop(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    bars = []
    for day in range(8):
        close = 100 + day
        bars.append(
            {
                "date": f"2026-01-{day + 1:02d}",
                "open": close,
                "high": close + 2,
                "low": close - 2,
                "close": close,
                "volume": 1000,
            }
        )
    (cache / "A.json").write_text(json.dumps(bars), encoding="utf-8")
    rows = [
        {"symbol": "A", "scan_date": f"2026-01-{day + 1:02d}", "entry_ok": True, "rvol": 10.0}
        for day in range(5)
    ]
    path = tmp_path / "rows.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    result = run(path, cache, min_history_dates=1, max_horizon=3, random_runs=2)
    summary = result["cohort_summary"]["high_rvol_eligible"]["horizon_close_to_close"]
    assert summary["1"]["rows"] > 0
    assert summary["2"]["median_pct"] > 0
    assert "1.0" in result["cohort_summary"]["high_rvol_eligible"]["atr_stop_grid"]["1"]
    fixed = result["cohort_summary"]["high_rvol_eligible"]["fixed_target_grid"]["1"]
    assert fixed["1.0"]["1.0"]["target_mode"] == "fixed_pct"
    assert (
        sum(
            fixed["1.0"]["1.0"][key]
            for key in ("target_hit_share", "stop_hit_share", "time_exit_share")
        )
        == 1
    )
