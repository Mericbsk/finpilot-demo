from pathlib import Path

import pandas as pd
from research.high_rvol_full_universe_2026_08_12 import run


def test_full_universe_uses_prior_dates_and_all_cohorts(tmp_path: Path):
    rows = []
    for day_index, day in enumerate(pd.date_range("2026-01-01", periods=12, freq="D")):
        for symbol_index in range(4):
            rows.append(
                {
                    "symbol": f"S{symbol_index}",
                    "scan_date": day.date(),
                    "entry_ok": symbol_index < 2,
                    "rvol": 10 if symbol_index in (0, 2) else 1,
                    "atr_pct_real": symbol_index + 1,
                    "c2c_5d": float(day_index + symbol_index),
                }
            )
    source = tmp_path / "export.csv"
    pd.DataFrame(rows).to_csv(source, index=False)

    result = run(source, min_history_dates=3)

    assert result["production_change"] is False
    assert result["dates"]["evaluated"] == 9
    assert "high_rvol_all" in result["cohort_summary"]
    assert "high_rvol_eligible" in result["cohort_summary"]
    assert "high_rvol_rejected" in result["cohort_summary"]
    assert result["protocol"]["locked_oos"] == "not_opened"
