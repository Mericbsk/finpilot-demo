"""Tests for the early-detection layer: contraction + RVOL acceleration
features, the WATCH→CONFIRM ladder, and triple-barrier labeling.

These cover the P0/early-detection work from
docs/audit-2026-06-12/10-scanner-analiz-ve-arastirma-degerlendirme.md.
All units are additive and pure — no live behaviour is exercised here.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scanner.features import (
    compute_contraction_factor,
    compute_rvol_acceleration,
)
from scanner.labeling import summarize_labels, triple_barrier_label
from scanner.watch_tier import TIER_ORDER, classify_tier


# ── helpers ──────────────────────────────────────────────────────────────────
def _ohlc(closes, vols=None, rng=0.02):
    """Build an OHLC(V) frame from a close path with a given relative range."""
    closes = np.asarray(closes, dtype=float)
    n = len(closes)
    high = closes * (1 + rng)
    low = closes * (1 - rng)
    opn = closes
    if vols is None:
        vols = np.full(n, 1_000_000.0)
    idx = pd.bdate_range(end=pd.Timestamp.now(), periods=n)
    return pd.DataFrame(
        {"Open": opn, "High": high, "Low": low, "Close": closes, "Volume": np.asarray(vols, float)},
        index=idx,
    )


# ── contraction factor ───────────────────────────────────────────────────────
def test_contraction_high_when_range_tightens():
    # Volatile 60-bar baseline, then a ~20-bar tight consolidation (the
    # research framework's >=14-day coil) → high contraction on both
    # the NTR (fast) and Bollinger-width (slow) components.
    rs = np.random.RandomState(0)
    base = 100 + np.cumsum(rs.randn(60) * 1.5)
    tight = np.full(20, base[-1])
    closes = np.concatenate([base, tight])
    df = _ohlc(closes, rng=0.05)
    # Squeeze the intrabar range of the consolidation stretch.
    df.iloc[-20:, df.columns.get_loc("High")] = closes[-20:] * 1.003
    df.iloc[-20:, df.columns.get_loc("Low")] = closes[-20:] * 0.997
    factor = compute_contraction_factor(df)
    assert factor >= 0.6, f"expected coiled (>=0.6), got {factor}"


def test_contraction_low_when_range_expands():
    closes = np.full(80, 100.0)
    df = _ohlc(closes, rng=0.01)  # baseline: tight
    # Blow out the last 5 bars (expansion).
    df.iloc[-5:, df.columns.get_loc("High")] = closes[-5:] * 1.10
    df.iloc[-5:, df.columns.get_loc("Low")] = closes[-5:] * 0.90
    factor = compute_contraction_factor(df)
    assert factor <= 0.4, f"expected expanding (<=0.4), got {factor}"


def test_contraction_insufficient_data_is_zero():
    df = _ohlc(np.full(10, 100.0))
    assert compute_contraction_factor(df) == 0.0


# ── RVOL acceleration ────────────────────────────────────────────────────────
def test_rvol_acceleration_positive_when_volume_builds():
    n = 40
    vols = np.full(n, 1_000_000.0)
    vols[-3:] = 3_000_000.0  # recent surge from flat base
    df = _ohlc(np.full(n, 100.0), vols=vols)
    assert compute_rvol_acceleration(df) > 0.3


def test_rvol_acceleration_zero_when_flat():
    df = _ohlc(np.full(40, 100.0), vols=np.full(40, 1_000_000.0))
    assert compute_rvol_acceleration(df) == 0.0


def test_rvol_acceleration_insufficient_data_is_zero():
    df = _ohlc(np.full(5, 100.0))
    assert compute_rvol_acceleration(df) == 0.0


# ── tier ladder ──────────────────────────────────────────────────────────────
def test_tier_none_when_nothing():
    r = classify_tier()
    assert r.tier == "NONE"
    assert r.suggested_size_fraction == 0.0


def test_tier_watch_on_coil_plus_volume():
    r = classify_tier(contraction_factor=0.8, rvol_acceleration=0.5)
    assert r.tier == "WATCH"


def test_tier_setup_on_catalyst_plus_coil():
    r = classify_tier(contraction_factor=0.7, catalyst_factor=0.5)
    assert r.tier == "SETUP"
    assert r.suggested_size_fraction == 0.25


def test_tier_trigger_on_breakout_plus_volume():
    r = classify_tier(breakout_confirmed=True, volume_multiple=3.0, rvol_acceleration=0.4)
    assert r.tier == "TRIGGER"
    assert r.suggested_size_fraction == 0.50


def test_tier_confirm_when_entry_ok():
    r = classify_tier(entry_ok=True, contraction_factor=0.5, rvol_acceleration=0.5)
    assert r.tier == "CONFIRM"
    assert r.suggested_size_fraction == 1.0


def test_tier_ordering_monotonic():
    assert TIER_ORDER["WATCH"] < TIER_ORDER["SETUP"] < TIER_ORDER["TRIGGER"] < TIER_ORDER["CONFIRM"]


def test_tier_does_not_change_entry_ok():
    # Classifying must be pure: no entry_ok input given → never CONFIRM.
    r = classify_tier(
        contraction_factor=0.99,
        rvol_acceleration=0.99,
        catalyst_factor=0.99,
        breakout_confirmed=True,
        volume_multiple=9.0,
    )
    assert r.tier != "CONFIRM"  # CONFIRM requires explicit entry_ok


# ── triple-barrier labeling ──────────────────────────────────────────────────
def test_barrier_take_profit_hit_first():
    # Price climbs to +12% by bar 3 → tp (10%) before sl.
    closes = [101, 105, 112, 108]
    lab = triple_barrier_label(closes, entry_price=100.0, tp_pct=0.10, sl_pct=0.05)
    assert lab.label == "tp"
    assert lab.bars_to_hit == 3
    assert lab.ret_pct > 0


def test_barrier_stop_loss_hit_first():
    closes = [99, 96, 94, 110]  # drops to -6% before any +10%
    lab = triple_barrier_label(closes, entry_price=100.0, tp_pct=0.10, sl_pct=0.05)
    assert lab.label == "sl"
    assert lab.ret_pct < 0


def test_barrier_time_exit_when_neither_touched():
    closes = [100.5, 101, 100, 102, 101]  # stays inside ±band
    lab = triple_barrier_label(closes, entry_price=100.0, tp_pct=0.10, sl_pct=0.05, max_horizon=5)
    assert lab.label == "time"
    assert lab.bars_to_hit == 5


def test_barrier_conservative_tie_breaks_to_stop():
    # Single bar whose HIGH crosses tp AND LOW crosses sl → stop assumed first.
    lab = triple_barrier_label(
        [100.0],
        entry_price=100.0,
        tp_pct=0.10,
        sl_pct=0.05,
        forward_highs=[115.0],
        forward_lows=[94.0],
    )
    assert lab.label == "sl"


def test_barrier_short_side():
    # Short: price falls 12% → tp for a short.
    lab = triple_barrier_label(
        [95, 90, 88], entry_price=100.0, tp_pct=0.10, sl_pct=0.05, side="short"
    )
    assert lab.label == "tp"
    assert lab.ret_pct > 0


def test_summarize_labels_rates_sum_to_one():
    labels = [
        triple_barrier_label(
            [112],
            entry_price=100,
            tp_pct=0.10,
            sl_pct=0.05,
            forward_highs=[112],
            forward_lows=[111],
        ),
        triple_barrier_label(
            [93], entry_price=100, tp_pct=0.10, sl_pct=0.05, forward_highs=[94], forward_lows=[93]
        ),
        triple_barrier_label([101, 102], entry_price=100, tp_pct=0.10, sl_pct=0.05, max_horizon=2),
    ]
    s = summarize_labels(labels)
    assert s["n"] == 3
    assert abs(s["tp_rate"] + s["sl_rate"] + s["time_rate"] - 1.0) < 1e-3


def test_summarize_empty():
    s = summarize_labels([])
    assert s["n"] == 0 and s["expectancy"] == 0.0


# ── end-to-end glue: df → tier dict ──────────────────────────────────────────
def test_compute_early_tier_end_to_end_watch():
    from scanner.watch_tier import compute_early_tier

    rs = np.random.RandomState(1)
    base = 100 + np.cumsum(rs.randn(60) * 1.5)
    tight = np.full(20, base[-1])
    closes = np.concatenate([base, tight])
    vols = np.full(80, 1_000_000.0)
    vols[-3:] = 2_500_000.0  # late volume build → rising rvol
    df = _ohlc(closes, vols=vols, rng=0.05)
    df.iloc[-20:, df.columns.get_loc("High")] = closes[-20:] * 1.003
    df.iloc[-20:, df.columns.get_loc("Low")] = closes[-20:] * 0.997
    out = compute_early_tier(df, volume_multiple=1.2)
    assert out["tier"] in {"WATCH", "SETUP", "TRIGGER"}
    assert "contraction_factor" in out and "rvol_acceleration" in out
    assert out["tier"] != "CONFIRM"  # entry_ok not passed


def test_compute_early_tier_handles_bad_input():
    from scanner.watch_tier import compute_early_tier

    out = compute_early_tier(None)
    assert out["tier"] == "NONE"
