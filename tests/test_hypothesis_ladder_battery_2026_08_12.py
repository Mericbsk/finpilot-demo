import numpy as np
import pandas as pd
from research.hypothesis_ladder_battery_2026_08_12 import (
    _paired_date_median_diff,
    _partial_spearman,
)


def _frame():
    rng = np.random.default_rng(1)
    rows = []
    for i, day in enumerate(pd.date_range("2026-01-01", periods=8).strftime("%Y-%m-%d")):
        for j in range(10):
            rows.append(
                {"symbol": f"S{j}", "scan_date": day, "v": rng.normal(1.0 if j < 5 else -1.0, 0.5)}
            )
    return pd.DataFrame(rows)


def test_paired_date_median_diff_detects_direction():
    df = _frame()
    a = df[df["symbol"].isin([f"S{j}" for j in range(5)])]
    b = df[~df["symbol"].isin([f"S{j}" for j in range(5)])]
    out = _paired_date_median_diff(a, b, "v", seed=7)
    assert out["paired_dates"] == 8
    assert out["median_diff_pp"] > 0
    assert out["ci_lo"] > 0


def test_partial_spearman_removes_confound():
    rng = np.random.default_rng(2)
    n = 500
    c = rng.normal(size=n)
    x = c + rng.normal(scale=0.01, size=n)  # x is almost entirely the confound
    y = c + rng.normal(scale=0.01, size=n)
    df = pd.DataFrame({"x": x, "y": y, "c": c})
    raw = df["x"].corr(df["y"], method="spearman")
    part = _partial_spearman(df["x"], df["y"], df[["c"]])
    assert raw > 0.9
    assert abs(part) < 0.2
