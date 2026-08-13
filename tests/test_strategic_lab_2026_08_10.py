"""Focused tests for the Strategic Thinking Lab experiment battery.

Synthetic-data contract tests only; no production behavior is exercised.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from research import strategic_lab_2026_08_10 as lab


def _bars(closes: list[float], start: str = "2026-01-01") -> list[dict]:
    dates = pd.bdate_range(start, periods=len(closes)).strftime("%Y-%m-%d")
    return [
        {
            "date": d,
            "open": c * 0.99,
            "high": c * 1.05,
            "low": c * 0.95,
            "close": c,
            "volume": 1000,
        }
        for d, c in zip(dates, closes, strict=False)
    ]


def _write_cache(tmp_path: Path, symbol: str, bars: list[dict]) -> None:
    (tmp_path / f"{symbol}.json").write_text(json.dumps(bars), encoding="utf-8")


def _export_row(symbol: str, scan_date: str, **overrides) -> dict:
    row = {
        "source_file": "synthetic",
        "symbol": symbol,
        "scan_ts": f"{scan_date}T00:00:00",
        "scan_date": scan_date,
        "price": 100.0,
        "score": 2.0,
        "composite_score": 50.0,
        "regime": True,
        "direction": True,
        "entry_ok": True,
        "liquidity_ok": True,
        "risk_reward": 2.0,
        "tier": "A",
        "tier_score": 1.0,
        "conviction_tier": "high",
        "squeeze_factor": 1.0,
        "catalyst_factor": 1.0,
        "lottery_factor": 1.0,
        "overnight_gap_factor": 1.0,
        "sentiment": 0.0,
        "vol_regime": 1.0,
        "atr": 2.0,
        "finpilot_score": 50.0,
        "resolved_pct_t5": 1.0,
        "resolved_pct_1d": 0.2,
        "gap_pct": 0.0,
        "rvol": 1.5,
        "atr_pct_real": 2.0,
        "dist_52w_high": 5.0,
    }
    row.update(overrides)
    return row


def test_path_metrics_forward_and_mfe_mfe(tmp_path: Path) -> None:
    closes = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111]
    _write_cache(tmp_path, "AAA", _bars(closes))
    scan_date = str(pd.bdate_range("2026-01-01", periods=1)[0].date())
    rows = pd.DataFrame([_export_row("AAA", scan_date)])
    enriched = lab.compute_path_metrics(rows, tmp_path)
    row = enriched.iloc[0]
    # Entry close = 100; fwd 5d close = 105 -> +5%
    assert row["fwd_5d_pct"] == pytest.approx(5.0, abs=1e-6)
    # MFE window = bars entry+1..entry+5, highs = close*1.05 -> max close 105 -> 110.25 -> +10.25%
    assert abs(row["mfe_5d_pct"] - 10.25) < 1e-6
    # MAE window lows = close*0.95 -> min close 101 -> 95.95 -> -4.05%
    assert abs(row["mae_5d_pct"] - (-4.05)) < 1e-6
    assert row["time_to_mfe_5d"] == 5.0
    assert row["time_to_mae_5d"] == 1.0


def test_path_metrics_missing_symbol(tmp_path: Path) -> None:
    rows = pd.DataFrame([_export_row("NOPE", "2026-01-01")])
    enriched = lab.compute_path_metrics(rows, tmp_path)
    assert enriched.iloc[0]["cache_close"] != enriched.iloc[0]["cache_close"]  # NaN


def test_block_bootstrap_respects_date_blocks() -> None:
    # Two dates with wildly different medians; block bootstrap CI must stay wide.
    rows = []
    for date, value in (("2026-01-01", -50.0), ("2026-01-02", 50.0)):
        for _ in range(50):
            rows.append({"scan_date": date, "v": value + np.random.default_rng(1).normal(0, 0.01)})
    df = pd.DataFrame(rows)
    ci = lab.block_bootstrap_ci(df, "v", draws=200, seed=7)
    assert ci["n_dates"] == 2
    assert ci["ci_hi"] - ci["ci_lo"] > 50  # wide because whole days move together


def test_decile_monotonicity_detects_monotone_relation() -> None:
    rng = np.random.default_rng(3)
    n = 5000
    score = rng.uniform(0, 100, n)
    fwd = score * 0.1 + rng.normal(0, 1, n)
    df = pd.DataFrame(
        {
            "finpilot_score": score,
            "fwd_5d_pct": fwd,
            "scan_date": "2026-01-01",
            "symbol": [f"S{i}" for i in range(n)],
            "entry_ok": False,
        }
    )
    result = lab.exp_r3_decile_monotonicity(df)
    assert result["status"] == "COMPLETED"
    assert result["spearman_decile_vs_median"] > 0.9


def test_counterfactual_portfolio_detects_no_selection_value() -> None:
    rng = np.random.default_rng(11)
    rows = []
    dates = pd.bdate_range("2026-01-01", periods=60).strftime("%Y-%m-%d")
    for d in dates:
        for i in range(30):
            rows.append(
                {
                    "scan_date": d,
                    "symbol": f"S{i}",
                    "entry_ok": i < 3,
                    "fwd_5d_pct": rng.normal(0, 2),  # same distribution: no selection value
                }
            )
    df = pd.DataFrame(rows)
    result = lab.exp_p1_counterfactual_portfolio(df)
    assert result["status"] == "COMPLETED"
    share = result["selected_minus_counterfactual"]["share_positive"]
    assert 0.2 < share < 0.8  # centered around zero


def test_drift_budget_filters_high_drift_rows() -> None:
    df = pd.DataFrame(
        {
            "scan_date": ["2026-01-01"] * 4,
            "symbol": ["A", "B", "C", "D"],
            "entry_ok": [True] * 4,
            "drift_pct": [0.5, 2.0, 4.0, 10.0],
            "fwd_5d_pct": [1.0, 1.0, 1.0, 1.0],
        }
    )
    result = lab.exp_e2_drift_budget(df)
    assert result["budgets"]["1.0"]["kept_n"] == 1
    assert result["budgets"]["3.0"]["kept_n"] == 2
    assert result["budgets"]["5.0"]["kept_n"] == 3


def test_rank_stability_detects_sticky_ranks() -> None:
    rows = []
    dates = pd.bdate_range("2026-01-01", periods=10).strftime("%Y-%m-%d")
    for d in dates:
        for i in range(60):
            rows.append(
                {
                    "scan_date": d,
                    "symbol": f"S{i}",
                    "finpilot_score": float(i),  # identical ranking every day
                    "entry_ok": False,
                }
            )
    df = pd.DataFrame(rows)
    result = lab.exp_r4_rank_stability(df)
    assert result["status"] == "COMPLETED"
    assert result["spearman_rank_stability"] > 0.95


def test_effective_sample_size_shrinks_under_clustering() -> None:
    rows = []
    rng = np.random.default_rng(5)
    dates = pd.bdate_range("2026-01-01", periods=40).strftime("%Y-%m-%d")
    for d in dates:
        day_shock = rng.normal(0, 5)  # all rows in a day share a shock
        for i in range(20):
            rows.append({"scan_date": d, "v": day_shock + rng.normal(0, 0.1)})
    df = pd.DataFrame(rows)
    result = lab.effective_sample_size(df, "v")
    assert result["ratio"] < 0.5
    assert result["n_eff_approx"] < result["n_rows"] * 0.5
