import pandas as pd
from research.high_rvol_horizon_battery_2026_08_12 import run


def test_horizons_compound_daily_returns(tmp_path):
    rows = []
    for day in range(8):
        for symbol, rvol, entry_ok in (("A", 10.0, True), ("B", 1.0, False)):
            rows.append(
                {
                    "symbol": symbol,
                    "scan_date": f"2026-01-{day + 1:02d}",
                    "entry_ok": entry_ok,
                    "rvol": rvol,
                    "c2c_1d": 1.0,
                }
            )
    path = tmp_path / "input.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    result = run(path, min_history_dates=2, max_horizon=3)
    horizon = result["cohort_summary"]["high_rvol_eligible"]
    assert horizon["1"]["rows"] > 0
    assert abs(horizon["2"]["mean_pct"] - 2.01) < 1e-9
    assert abs(horizon["3"]["mean_pct"] - 3.0301) < 1e-9
