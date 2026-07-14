"""Regression tests for the scanner end-to-end fixes (2026-06-12 audit).

Covers:
  * compute_vol_regime_from_df — hot-path vol-regime with NO network fetch,
    matching the old yfinance-based buckets.
  * The archived legacy modules (regime_detection / altdata) are genuinely
    NOT importable — proving the old per-scan imports were dead (the fix
    removed them). This test documents the honest-neutral decision.

Pure / deterministic; no network.
"""

from __future__ import annotations

import importlib.util

import numpy as np
import pandas as pd
from scanner.features import compute_vol_regime_from_df


def _daily(closes):
    closes = np.asarray(closes, dtype=float)
    n = len(closes)
    idx = pd.bdate_range(end=pd.Timestamp.now(), periods=n)
    return pd.DataFrame(
        {
            "Open": closes,
            "High": closes * 1.01,
            "Low": closes * 0.99,
            "Close": closes,
            "Volume": np.full(n, 1_000_000.0),
        },
        index=idx,
    )


# ── vol_regime from df (no network) ──────────────────────────────────────────
def test_vol_regime_low_when_calm():
    # Tiny daily moves → annualised vol well under 15% → bucket 0.
    rs = np.random.RandomState(0)
    closes = 100 * np.cumprod(1 + rs.randn(40) * 0.002)  # ~0.2%/day
    assert compute_vol_regime_from_df(_daily(closes)) == 0


def test_vol_regime_high_when_wild():
    # Large daily moves → annualised vol well over 30% → bucket 2.
    rs = np.random.RandomState(1)
    closes = 100 * np.cumprod(1 + rs.randn(40) * 0.05)  # ~5%/day
    assert compute_vol_regime_from_df(_daily(closes)) == 2


def test_vol_regime_insufficient_data_defaults_normal():
    assert compute_vol_regime_from_df(_daily(np.full(10, 100.0))) == 1


def test_vol_regime_bad_input_defaults_normal():
    assert compute_vol_regime_from_df(None) == 1
    assert compute_vol_regime_from_df(pd.DataFrame({"X": [1, 2, 3]})) == 1


def test_vol_regime_matches_manual_formula():
    # The function must reproduce: std(last 20 daily returns) * sqrt(252) bucketed.
    rs = np.random.RandomState(2)
    closes = 100 * np.cumprod(1 + rs.randn(60) * 0.012)
    df = _daily(closes)
    daily = df["Close"].pct_change().dropna()
    rv = float(daily.iloc[-20:].std() * (252**0.5))
    expected = 0 if rv < 0.15 else (1 if rv < 0.30 else 2)
    assert compute_vol_regime_from_df(df) == expected


# ── honest-neutral: legacy modules really are gone ───────────────────────────
def test_legacy_regime_and_altdata_not_importable():
    # The scanner used to `from regime_detection import ...` / `from altdata
    # import ...` on every symbol; both live only under archive/scripts_legacy
    # and are NOT importable. The fix removed those dead imports. This asserts
    # the premise stays true (if someone re-adds a real module, update the fix).
    assert importlib.util.find_spec("regime_detection") is None
    assert importlib.util.find_spec("altdata") is None


# ── slippage cost model: broken import fixed ─────────────────────────────────
def test_slippage_real_api_resolves_and_estimate_stub_is_gone():
    """_compute_cost_labels used ``from core.slippage_tracker import
    estimate_round_trip_cost`` — a function that does NOT exist, so the import
    raised on every call and cost silently fell back to a flat 0.20% (one side
    only). The fix uses the real RealisticBacktestCosts model. This test proves
    (a) the stub function is genuinely absent, and (b) the real API yields a
    sane round-trip cost fraction (~0.55%, a truer, higher cost than 0.20%).
    """
    import sys
    import types

    core_pkg = types.ModuleType("core")
    core_pkg.__path__ = ["core"]
    sys.modules.setdefault("core", core_pkg)
    spec = importlib.util.spec_from_file_location(
        "core.slippage_tracker", "core/slippage_tracker.py"
    )
    m = importlib.util.module_from_spec(spec)
    sys.modules["core.slippage_tracker"] = m
    spec.loader.exec_module(m)

    assert not hasattr(m, "estimate_round_trip_cost")  # the broken import target
    cost_frac = m.RealisticBacktestCosts().round_trip_cost_pct() / 100.0
    assert 0.0 < cost_frac < 0.05  # sane round-trip cost as a fraction
    assert cost_frac > 0.0020  # truer cost than the old flat one-side fallback
