from pathlib import Path

import pandas as pd
from research.high_rvol_deep_audit_2026_08_12 import run


def test_high_rvol_audit_reports_date_and_outlier_sensitivity(tmp_path: Path):
    rows = []
    for day_index, day in enumerate(pd.date_range("2026-01-01", periods=12, freq="D")):
        for symbol_index in range(4):
            rows.append(
                {
                    "symbol": f"S{symbol_index}",
                    "scan_date": day.date(),
                    "entry_ok": symbol_index < 2,
                    "gap_pct": 0,
                    "rvol": 5,
                    "atr_pct_real": symbol_index + 1,
                    "finpilot_score": 50,
                    "c2c_5d": 1000.0 if day_index == 8 and symbol_index == 0 else 1.0,
                }
            )
    source = tmp_path / "export.csv"
    pd.DataFrame(rows).to_csv(source, index=False)

    result = run(source)

    assert result["production_change"] is False
    assert result["equal_weight"]["top_contribution"]
    assert "without_top_four_dates" in result["equal_weight"]
    assert result["equal_weight"]["row_outlier_sensitivity"]["row_outcomes_above_50_pct"] == 1
