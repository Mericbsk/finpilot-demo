"""Tests for scanner.backtest_metrics — the full-universe edge-measurement layer.

Deterministic, no I/O. Verifies the four statistics used to reproduce and
stress-test the developer's alpha-v2 / conviction claims:
decile_lift, atr_barrier_params, spy_relative, median_split_ablation,
conviction_bucket_hitrate.
"""

from __future__ import annotations

from scanner.backtest_metrics import (
    atr_barrier_params,
    conviction_bucket_hitrate,
    decile_lift,
    median_split_ablation,
    spy_relative,
)


def _obs(factor, ret, f_key="f", mfe=None, bench=None, **extra):
    o = {f_key: factor, "ret": ret, "win": 1 if ret > 0 else 0}
    if mfe is not None:
        o["mfe_pct"] = mfe
    if bench is not None:
        o["bench_ret"] = bench
    o.update(extra)
    return o


# ── decile_lift ──────────────────────────────────────────────────────────────
def test_decile_lift_monotone_factor_wins_top_bucket():
    # factor perfectly ranks winners: high factor → win, low factor → loss.
    obs = [_obs(i, ret=(0.10 if i >= 50 else -0.05)) for i in range(100)]
    dl = decile_lift(obs, "f", metric="win")
    assert dl["n"] == 100 and dl["n_per_bucket"] == 10
    assert dl["base"] == 0.5  # half win overall
    assert dl["top_bucket"] == 1.0  # top decile all winners
    assert dl["lift"] == 2.0  # 1.0 / 0.5


def test_decile_lift_ret_metric_is_additive_excess():
    obs = [_obs(i, ret=(0.08 if i >= 50 else -0.02)) for i in range(100)]
    dl = decile_lift(obs, "f", metric="ret")
    assert dl["top_bucket"] == 0.08
    assert dl["base"] == 0.03  # (0.08*50 + -0.02*50)/100
    assert abs(dl["lift"] - 0.05) < 1e-9


def test_decile_lift_drops_missing_factor_and_handles_small_n():
    obs = [{"ret": 0.1, "win": 1}, {"f": 0.5, "ret": -0.1, "win": 0}]
    dl = decile_lift(obs, "f", metric="win")
    assert dl["n"] == 1  # one dropped for missing factor
    assert dl["lift"] is None  # n < n_buckets → no lift


def test_decile_lift_no_edge_factor_lift_near_one():
    # factor uncorrelated with outcome (alternating) → top decile ≈ base.
    obs = [_obs(i, ret=(0.1 if i % 2 == 0 else -0.1)) for i in range(100)]
    dl = decile_lift(obs, "f", metric="win")
    assert 0.8 <= dl["lift"] <= 1.2


# ── atr_barrier_params ───────────────────────────────────────────────────────
def test_atr_barrier_scales_with_volatility():
    tp, sl = atr_barrier_params(4.0, k_tp=2.0, k_sl=1.0)
    assert tp == 0.08 and sl == 0.04  # 2*4% , 1*4%
    tp2, sl2 = atr_barrier_params(8.0, k_tp=2.0, k_sl=1.0)
    assert tp2 == 0.16 and sl2 == 0.08


def test_atr_barrier_floors_quiet_names():
    tp, sl = atr_barrier_params(0.1, min_tp=0.02, min_sl=0.01)
    assert tp == 0.02 and sl == 0.01  # floored, not near-zero


# ── spy_relative ─────────────────────────────────────────────────────────────
def test_spy_relative_strips_beta():
    # raw +5% but benchmark also +5% → excess ≈ 0 → all beta.
    obs = [_obs(0.5, ret=0.05, bench=0.05) for _ in range(10)]
    out = spy_relative(obs)
    assert abs(out["raw_expectancy"] - 0.05) < 1e-9
    assert abs(out["excess_expectancy"]) < 1e-9
    assert out["beta_share"] == 1.0


def test_spy_relative_keeps_real_edge():
    obs = [_obs(0.5, ret=0.06, bench=0.01) for _ in range(10)]
    out = spy_relative(obs)
    assert abs(out["excess_expectancy"] - 0.05) < 1e-9
    assert out["beta_share"] is not None and out["beta_share"] < 0.3


# ── median_split_ablation ────────────────────────────────────────────────────
def test_median_split_fills_both_buckets_and_detects_edge():
    # even a factor whose values never reach a fixed 55 cut still splits at median
    obs = [_obs(v, ret=(0.1 if v >= 30 else -0.1)) for v in range(20, 41)]
    out = median_split_ablation(obs, "f", metric="ret")
    assert out["hi"]["n"] > 0 and out["lo"]["n"] > 0  # both non-empty (fixes n_hi=0)
    assert out["separates"] is True
    assert out["lift"] > 0


def test_median_split_no_separation():
    obs = [_obs(v, ret=(0.1 if v % 2 == 0 else -0.1)) for v in range(20)]
    out = median_split_ablation(obs, "f", metric="ret")
    assert out["hi"] is not None and out["lo"] is not None
    assert abs(out["lift"]) < 1e-9


# ── conviction_bucket_hitrate ────────────────────────────────────────────────
def test_conviction_bucket_hitrate_replicates_claim():
    # 5 conviction names (squeeze & gap high) that all reach +10%;
    # 15 others that never do → bucket hit-rate 100%, base 25%.
    conv = [_obs(0.9, ret=0.12, mfe=0.12, f_key="squeeze_factor", gap_factor=0.8) for _ in range(5)]
    rest = [
        _obs(0.1, ret=-0.02, mfe=0.0, f_key="squeeze_factor", gap_factor=0.1) for _ in range(15)
    ]
    out = conviction_bucket_hitrate(conv + rest)
    assert out["n_bucket"] == 5
    t10 = out["thresholds"][">=10%"]
    assert t10["bucket_hitrate"] == 1.0
    assert t10["base_hitrate"] == 0.25
    assert t10["lift"] == 4.0


def test_conviction_bucket_empty_when_no_names_qualify():
    obs = [_obs(0.1, ret=0.1, f_key="squeeze_factor", gap_factor=0.1) for _ in range(10)]
    out = conviction_bucket_hitrate(obs)
    assert out["n_bucket"] == 0
    assert out["thresholds"][">=5%"]["bucket_hitrate"] == 0.0
