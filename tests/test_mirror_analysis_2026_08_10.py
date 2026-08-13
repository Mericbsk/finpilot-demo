"""Focused tests for the mirror-thesis deep analysis battery."""

from __future__ import annotations

import numpy as np
import pandas as pd
from research import mirror_analysis_2026_08_10 as ma


def _frame(n=4000, seed=1, **cols) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    base = {
        "scan_date": np.repeat(
            pd.bdate_range("2026-01-01", periods=60).strftime("%Y-%m-%d"), (n + 59) // 60
        )[:n],
        "symbol": [f"S{i}" for i in range(n)],
        "entry_ok": False,
        "finpilot_score": rng.uniform(0, 100, n),
        "fwd_5d_pct": rng.normal(0.3, 3, n),
        "fwd_1d_pct": rng.normal(0.1, 1, n),
        "fwd_2d_pct": rng.normal(0.15, 1.5, n),
        "fwd_3d_pct": rng.normal(0.2, 2, n),
        "fwd_10d_pct": rng.normal(0.6, 4, n),
        "dist_52w_high": rng.uniform(0, 1, n),
        "past_5d_pct": rng.normal(0, 4, n),
        "gap_pct": rng.normal(0, 2, n),
        "rvol": rng.uniform(0.3, 4, n),
        "atr_pct_real": rng.uniform(0.5, 6, n),
        "squeeze_factor": rng.uniform(0, 1, n),
        "lottery_factor": rng.uniform(0, 1, n),
        "overnight_gap_factor": rng.uniform(0, 1, n),
    }
    base.update(cols)
    return pd.DataFrame(base)


def test_l1_detects_extension_encoding() -> None:
    rng = np.random.default_rng(2)
    n = 4000
    dist = rng.uniform(0, 1, n)
    past = rng.normal(0, 4, n)
    score = 60 * dist + rng.normal(0, 0.5, n)  # score is almost purely extension
    df = _frame(n=n, dist_52w_high=dist, past_5d_pct=past, finpilot_score=score)
    res = ma.exp_l1_encoding(df)
    assert res["status"] == "COMPLETED"
    assert res["encodes"]["dist_52w_high"] > 0.9
    assert res["rank_r2_from_extension_alone"] > 0.8


def test_l2_detects_reversal() -> None:
    rng = np.random.default_rng(3)
    n = 5000
    dist = rng.uniform(0, 1, n)
    fwd = -3 * dist + rng.normal(0, 1, n)  # more extended -> worse forward
    df = _frame(n=n, dist_52w_high=dist, fwd_5d_pct=fwd)
    res = ma.exp_l2_extension_reversal(df)
    assert res["status"] == "COMPLETED"
    assert res["dist_52w_high"]["spearman_vs_fwd"] < -0.5


def test_l3_partial_spearman_removes_mirror() -> None:
    rng = np.random.default_rng(4)
    n = 5000
    dist = rng.uniform(0, 1, n)
    past = rng.normal(0, 4, n)
    score = 60 * dist + 5 * past + rng.normal(0, 1, n)
    fwd = -3 * dist + rng.normal(0, 1, n)  # fwd depends only on extension
    df = _frame(n=n, dist_52w_high=dist, past_5d_pct=past, finpilot_score=score, fwd_5d_pct=fwd)
    res = ma.exp_l3_score_beyond_extension(df)
    assert res["status"] == "COMPLETED"
    assert abs(res["spearman_score_raw"]) > 0.3  # raw looks informative
    assert abs(res["spearman_score_given_extension"]) < 0.05  # but it's all the mirror


def test_l4_selection_vs_score_band() -> None:
    rng = np.random.default_rng(5)
    n = 4000
    score = rng.uniform(0, 100, n)
    fwd = -0.05 * score + rng.normal(0, 1, n)  # outcome driven by score band
    entry_ok = rng.random(n) < 0.2  # eligibility unrelated to outcome
    df = _frame(n=n, finpilot_score=score, fwd_5d_pct=fwd, entry_ok=entry_ok)
    res = ma.exp_l4_score_vs_selection(df)
    assert res["status"] == "COMPLETED"
    top = res["top_quintile"]
    # eligibility should NOT separate outcomes within the top band
    diff = abs((top["eligible"]["median"] or 0) - (top["not_eligible"]["median"] or 0))
    assert diff < 0.5


def test_a1_clean_vs_dirty() -> None:
    rng = np.random.default_rng(6)
    n = 4000
    past = rng.normal(0, 4, n)
    score = 10 * past + rng.normal(0, 1, n)
    fwd = rng.normal(0, 2, n)
    df = _frame(n=n, past_5d_pct=past, finpilot_score=score, fwd_5d_pct=fwd)
    df.attrs["flagged"] = {"S0", "S1"}  # only 2 dirty symbols
    res = ma.exp_a1_artifact_robustness(df)
    assert res["status"] == "COMPLETED"
    assert res["clean"]["spearman_score_vs_past"] > 0.9


def test_a2_day_concentration_counts_days() -> None:
    df = _frame(n=6000)
    res = ma.exp_a2_day_concentration(df)
    assert res["status"] == "COMPLETED"
    assert res["n_days"] >= 20


def test_synthesis_fade_beats_follow_when_mirror() -> None:
    rng = np.random.default_rng(7)
    n = 5000
    dist = rng.uniform(0, 1, n)
    score = 90 * dist + rng.normal(0, 1, n)  # score ~ extension
    fwd = -3 * dist + rng.normal(0, 1, n)  # extension reverses
    df = _frame(n=n, dist_52w_high=dist, finpilot_score=score, fwd_5d_pct=fwd)
    res = ma.exp_synthesis_mirror_vs_forward(df)
    assert res["status"] == "COMPLETED"
    assert res["spearman_fade_the_mirror"] > res["spearman_score"]
