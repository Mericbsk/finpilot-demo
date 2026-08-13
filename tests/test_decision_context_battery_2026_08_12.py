from pathlib import Path

import pandas as pd
from research.decision_context_battery_2026_08_12 import classify_states, run_battery


def _frame() -> pd.DataFrame:
    rows = []
    for day in pd.date_range("2026-01-01", periods=10, freq="D"):
        for index in range(4):
            rows.append(
                {
                    "symbol": f"S{index}",
                    "scan_date": day.date(),
                    "gap_pct": -4 if index == 0 else 0.2 * index,
                    "rvol": 3 if index == 1 else 1,
                    "atr_pct_real": 8 if index == 1 else 2,
                    "dist_52w_high": 0.9 if index == 2 else 0.2,
                    "finpilot_score": 50 + index,
                    "c2c_1d": float(index - 1),
                    "c2c_5d": float(index - 1) * 2,
                }
            )
    return pd.DataFrame(rows)


def test_classify_states_marks_gap_down():
    frame = _frame().iloc[:4]
    thresholds = {
        feature: {"q10": -1, "q25": 0, "q75": 1, "q90": 2}
        for feature in ("gap_pct", "rvol", "atr_pct_real", "dist_52w_high", "finpilot_score")
    }

    states = classify_states(frame, thresholds)

    assert states.iloc[0] == "gap_down"


def test_battery_uses_train_only_dates_and_returns_context_metrics(tmp_path: Path):
    csv_path = tmp_path / "export.csv"
    _frame().to_csv(csv_path, index=False)

    result = run_battery(csv_path, k=5)

    assert result["production_change"] is False
    assert result["protocol"]["locked_oos"] == "not_opened"
    assert result["rows"]["train"] > 0
    assert result["rows"]["validation"] > 0
    assert "similar_case_mae_5d_pct" in result["similar_case_validation"]
    assert 0 <= result["abstention_validation"]["abstain_rate"] <= 1
