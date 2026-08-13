from pathlib import Path

import pandas as pd
from research.high_rvol_opportunity_battery_2026_08_12 import run


def test_opportunity_battery_reports_clipped_and_one_day_views(tmp_path: Path):
    rows = []
    for day_index, day in enumerate(pd.date_range("2026-01-01", periods=12, freq="D")):
        for symbol_index in range(4):
            rows.append(
                {
                    "symbol": f"S{symbol_index}",
                    "scan_date": day.date(),
                    "entry_ok": symbol_index < 2,
                    "rvol": 10 if symbol_index in (0, 2) else 1,
                    "c2c_1d": float(day_index),
                    "c2c_5d": float(day_index * 10),
                }
            )
    source = tmp_path / "export.csv"
    pd.DataFrame(rows).to_csv(source, index=False)

    result = run(source, min_history_dates=3)

    summary = result["cohort_summary"]["high_rvol_rejected"]
    assert summary["five_day_clip_50"]["dates"] == 9
    assert summary["one_day_non_overlapping"]["dates"] == 9
    assert result["protocol"]["five_day_warning"] == "c2c_5d windows overlap"
    assert result["same_date_random_control"]["high_rvol_rejected"]["runs"] == 100
    assert "2.0" in summary["cost_sensitivity"]
