"""Focused tests for the Ten-Perspectives Lab battery.

Synthetic-data contract tests only; no production behavior is exercised.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from research import ten_perspectives_lab_2026_08_10 as tpl


def _frame(n: int = 3000, seed: int = 1, **columns) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    base = {
        "scan_date": np.repeat(
            pd.bdate_range("2026-01-01", periods=60).strftime("%Y-%m-%d"), (n + 59) // 60
        )[:n],
        "symbol": [f"S{i}" for i in range(n)],
        "entry_ok": False,
        "finpilot_score": rng.uniform(0, 100, n),
        "fwd_5d_pct": rng.normal(0.3, 3, n),
        "mae_5d_pct": -np.abs(rng.normal(4, 2, n)),
        "mfe_5d_pct": np.abs(rng.normal(4, 2, n)),
        "time_to_mfe_5d": rng.integers(1, 6, n).astype(float),
        "time_to_mae_5d": rng.integers(1, 6, n).astype(float),
        "atr": 2.0,
        "cache_close": 100.0,
        "gap_pct": rng.normal(0, 2, n),
        "rvol": rng.uniform(0.3, 4, n),
        "atr_pct_real": rng.uniform(0.5, 6, n),
        "dist_52w_high": rng.uniform(0, 40, n),
        "past_5d_pct": rng.normal(0, 4, n),
        "squeeze_factor": rng.uniform(0, 1, n),
        "lottery_factor": rng.uniform(0, 1, n),
        "overnight_gap_factor": rng.uniform(0, 1, n),
        "sentiment": rng.normal(0, 0.1, n),
    }
    base.update(columns)
    return pd.DataFrame(base)


def test_adverse_movement_detects_protective_score() -> None:
    rng = np.random.default_rng(2)
    n = 4000
    score = rng.uniform(0, 100, n)
    # Higher score -> smaller (less negative) MAE, crossing the -1 ATR (-2%) threshold
    mae = -(6 - score / 20.0) + rng.normal(0, 0.3, n)
    df = _frame(n=n, finpilot_score=score, mae_5d_pct=mae)
    result = tpl.exp_adverse_movement_target(df)
    assert result["status"] == "COMPLETED"
    assert result["spearman_score_vs_adverse"] < -0.3


def test_failure_prediction_ranks_informative_feature_first() -> None:
    rng = np.random.default_rng(4)
    n = 5000
    gap = rng.normal(0, 3, n)
    fwd = -0.8 * gap + rng.normal(0, 2, n)  # big gaps fail
    df = _frame(n=n, gap_pct=gap, fwd_5d_pct=fwd)
    result = tpl.exp_failure_prediction(df)
    assert result["status"] == "COMPLETED"
    assert result["best_feature"] == "gap_pct"
    assert result["spearman_with_failure"]["gap_pct"] > 0.3


def test_null_feature_injection_bounds_real_noise() -> None:
    df = _frame(n=6000)  # all features independent of outcome
    result = tpl.exp_null_feature_injection(df)
    assert result["status"] == "COMPLETED"
    assert result["null_abs_spearman_p95"] < 0.05
    assert result["features_above_null_p95"] == []


def test_first_passage_counts_mfe_first() -> None:
    df = _frame(n=2000, time_to_mfe_5d=np.ones(2000), time_to_mae_5d=np.full(2000, 4.0))
    df.loc[df.index[:500], "entry_ok"] = True
    result = tpl.exp_first_passage(df)
    assert result["status"] == "COMPLETED"
    assert result["eligible_p_mfe_first"] == 1.0


def test_calibration_beats_base_rate_when_score_informs() -> None:
    rng = np.random.default_rng(6)
    n = 8000
    score = rng.uniform(0, 100, n)
    p = 0.2 + 0.5 * (score / 100.0)
    fwd = np.where(rng.random(n) < p, 2.0, -2.0)
    dates = pd.bdate_range("2026-01-01", periods=80).strftime("%Y-%m-%d")
    df = _frame(
        n=n, finpilot_score=score, fwd_5d_pct=fwd, scan_date=np.repeat(dates, (n + 79) // 80)[:n]
    )
    result = tpl.exp_calibration_reliability(df)
    assert result["status"] == "COMPLETED"
    skill = result["events"]["positive"]["brier_skill_vs_base"]
    assert skill is not None and skill > 0.05


def test_correlation_cluster_selection_deduplicates() -> None:
    rng = np.random.default_rng(8)
    rows = []
    dates = pd.bdate_range("2026-01-01", periods=40).strftime("%Y-%m-%d")
    for d in dates:
        shared = rng.normal(0, 1, 20)  # two candidates share the same return path
        for i in range(4):
            series = shared if i < 2 else rng.normal(0, 1, 20)
            rows.append(
                {
                    "scan_date": d,
                    "symbol": f"S{i}",
                    "entry_ok": True,
                    "finpilot_score": float(100 - i),
                    "fwd_5d_pct": rng.normal(0.5, 2),
                    "past20_ret": series.tolist(),
                }
            )
    df = pd.DataFrame(rows)
    result = tpl.exp_correlation_cluster_selection(df)
    assert result["status"] == "COMPLETED"
    assert result["n_dates"] == 40


def test_sizing_comparison_produces_three_schemes() -> None:
    n = 3000
    df = _frame(n=n)
    df.loc[df.index[:400], "entry_ok"] = True
    result = tpl.exp_sizing_comparison(df)
    assert result["status"] == "COMPLETED"
    assert set(result["schemes"]) == {"equal", "atr_parity", "score_weighted"}
    for scheme in result["schemes"].values():
        assert scheme["max_drawdown_pct"] <= 0


def test_unsupervised_regimes_find_separation() -> None:
    rng = np.random.default_rng(9)
    n = 4000
    atr = np.concatenate([rng.uniform(0.5, 1.5, n // 2), rng.uniform(4, 6, n // 2)])
    fwd = np.concatenate([rng.normal(1.5, 1, n // 2), rng.normal(-1.5, 1, n // 2)])
    df = _frame(
        n=n,
        atr_pct_real=atr,
        fwd_5d_pct=fwd,
        rvol=np.ones(n),
        gap_pct=np.zeros(n),
        past_5d_pct=np.zeros(n),
    )
    result = tpl.exp_unsupervised_regimes(df)
    assert result["status"] == "COMPLETED"
    assert result["median_spread_across_clusters"] > 1.0


def test_tail_metrics_cvar_ordering() -> None:
    rng = np.random.default_rng(10)
    n = 4000
    fwd = rng.normal(0, 2, n)
    df = _frame(n=n, fwd_5d_pct=fwd)
    df.loc[df.index[:800], "entry_ok"] = True
    df.loc[df.index[:800], "fwd_5d_pct"] = rng.normal(-1, 4, 800)  # fatter left tail
    result = tpl.exp_tail_metrics(df)
    assert result["status"] == "COMPLETED"
    assert result["eligible"]["cvar5_pct"] < result["rejected"]["cvar5_pct"]


def test_gap_conditioning_buckets_cover_all() -> None:
    df = _frame(n=3000)
    result = tpl.exp_gap_conditioning(df)
    assert result["status"] == "COMPLETED"
    total = sum(c["n"] for c in result["all_rows"].values())
    assert total == 3000
