from pathlib import Path

import pandas as pd
from research.production_candidate_validation_2026_08_12 import run


def _frame() -> pd.DataFrame:
    rows = []
    for day in pd.date_range("2026-01-01", periods=12, freq="D"):
        for index in range(6):
            rows.append(
                {
                    "symbol": f"S{index}",
                    "scan_date": day.date(),
                    "entry_ok": index < 2,
                    "atr_pct_real": 2 + index,
                    "gap_pct": -4 if index == 0 else index,
                    "rvol": 3 if index == 1 else 1,
                    "c2c_5d": float(index - 2),
                }
            )
    return pd.DataFrame(rows)


def test_candidate_validation_keeps_production_boundary_closed(tmp_path: Path):
    csv_path = tmp_path / "export.csv"
    _frame().to_csv(csv_path, index=False)

    result = run(csv_path, random_runs=5)

    assert result["production_change"] is False
    assert result["locked_oos"] == "not_opened"
    assert "eligible" in result["atr_parity"]["groups"]
    assert "rejected" in result["atr_parity"]["groups"]
    assert result["abstention_independent_split"]["dates"]["validation"] > 0
    assert set(result["gap_rvol_context"]["features"]) == {"gap_pct", "rvol"}
