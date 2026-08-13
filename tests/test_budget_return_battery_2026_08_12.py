from pathlib import Path

import pandas as pd
from research.budget_return_battery_2026_08_12 import run


def test_budget_battery_reports_capital_and_keeps_production_closed(tmp_path: Path):
    rows = []
    for day in pd.date_range("2026-01-01", periods=12, freq="D"):
        for index in range(4):
            rows.append(
                {
                    "symbol": f"S{index}",
                    "scan_date": day.date(),
                    "entry_ok": index < 2,
                    "gap_pct": -3 if index == 0 else index,
                    "rvol": 3 if index == 1 else 1,
                    "atr_pct_real": index + 1,
                    "finpilot_score": 50 + index,
                    "c2c_5d": float(index - 1),
                }
            )
    source = tmp_path / "export.csv"
    pd.DataFrame(rows).to_csv(source, index=False)

    result = run(source, capital=10_000.0, cost_pct=0.55)

    assert result["production_change"] is False
    assert result["protocol"]["starting_capital_usd"] == 10_000.0
    assert result["protocol"]["locked_oos"] == "not_opened"
    assert result["strategies"]["entry_ok"]["equal_weight"]["final_capital_usd"] is not None
