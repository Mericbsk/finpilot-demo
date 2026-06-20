"""Tests for the Float/Short squeeze factor (env-gated, default OFF).

Covers:
  * ``scanner.features.compute_squeeze_factor`` normalisation (yfinance mocked).
  * ``scanner.features.get_alpha_features`` env-gating.
  * ``scanner.score_engine`` additive contribution and normalisation ceiling.
"""

from __future__ import annotations

import sys
import types

import pytest
import scanner.features as features
import scanner.score_engine as se


def _install_fake_yfinance(monkeypatch, info: dict) -> None:
    """Install a fake ``yfinance`` module returning ``info`` from Ticker().info."""

    class _FakeTicker:
        def __init__(self, symbol):
            self.symbol = symbol

        @property
        def info(self):
            return info

    fake = types.ModuleType("yfinance")
    fake.Ticker = _FakeTicker  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "yfinance", fake)


def test_squeeze_factor_high_short_low_float(monkeypatch):
    # short% at pivot (0.20) and tiny float → both components ~max.
    _install_fake_yfinance(monkeypatch, {"shortPercentOfFloat": 0.20, "floatShares": 5e6})
    val = features.compute_squeeze_factor("XYZ")
    assert val == pytest.approx(0.95, abs=0.02)


def test_squeeze_factor_low_short_high_float(monkeypatch):
    _install_fake_yfinance(monkeypatch, {"shortPercentOfFloat": 0.01, "floatShares": 500e6})
    val = features.compute_squeeze_factor("XYZ")
    assert val == pytest.approx(0.025, abs=0.02)


def test_squeeze_factor_missing_fields_is_zero(monkeypatch):
    _install_fake_yfinance(monkeypatch, {})
    assert features.compute_squeeze_factor("XYZ") == 0.0


def test_squeeze_factor_clamped_above_pivot(monkeypatch):
    # short% well above pivot must not exceed 1.0 short component.
    _install_fake_yfinance(monkeypatch, {"shortPercentOfFloat": 0.60, "floatShares": 1e6})
    val = features.compute_squeeze_factor("XYZ")
    assert 0.0 <= val <= 1.0


def test_get_alpha_features_skips_squeeze_when_disabled(monkeypatch):
    monkeypatch.delenv("FINPILOT_ENABLE_SQUEEZE_FACTOR", raising=False)
    features._FEATURE_CACHE.clear()
    monkeypatch.setattr(features, "compute_sector_rs", lambda *_: 0.0)
    monkeypatch.setattr(features, "compute_vol_regime", lambda *_: 1)

    def _boom(_symbol):
        raise AssertionError("squeeze should not be called when disabled")

    monkeypatch.setattr(features, "compute_squeeze_factor", _boom)
    out = features.get_alpha_features("XYZ")
    assert out["squeeze_factor"] == 0.0


def test_get_alpha_features_computes_squeeze_when_enabled(monkeypatch):
    monkeypatch.setenv("FINPILOT_ENABLE_SQUEEZE_FACTOR", "1")
    features._FEATURE_CACHE.clear()
    monkeypatch.setattr(features, "compute_sector_rs", lambda *_: 0.0)
    monkeypatch.setattr(features, "compute_vol_regime", lambda *_: 1)
    monkeypatch.setattr(features, "compute_squeeze_factor", lambda _s: 0.7)
    out = features.get_alpha_features("XYZ")
    assert out["squeeze_factor"] == 0.7


def test_score_engine_squeeze_off_by_default(monkeypatch):
    monkeypatch.delenv("FINPILOT_ENABLE_SQUEEZE_FACTOR", raising=False)
    row = {"score": 3, "squeeze_factor": 1.0}
    assert se.compute_recommendation_score(row) == 3.0
    assert se.effective_max_reco_score() == se.MAX_RECO_SCORE


def test_score_engine_squeeze_adds_when_enabled(monkeypatch):
    monkeypatch.setenv("FINPILOT_ENABLE_SQUEEZE_FACTOR", "1")
    base = se.compute_recommendation_score({"score": 3, "squeeze_factor": 0.0})
    boosted = se.compute_recommendation_score({"score": 3, "squeeze_factor": 1.0})
    assert boosted - base == pytest.approx(se._SQUEEZE_WEIGHT)
    # Ceiling stays fixed so non-squeeze signals are unaffected.
    assert se.effective_max_reco_score() == se.MAX_RECO_SCORE


def test_score_engine_squeeze_no_data_is_noop(monkeypatch):
    """A symbol with no squeeze data scores identically on/off (normalisation)."""
    monkeypatch.delenv("FINPILOT_ENABLE_SQUEEZE_FACTOR", raising=False)
    row = {"regime": True, "score": 3, "squeeze_factor": 0.0}
    off = se.compute_recommendation_strength(row)
    monkeypatch.setenv("FINPILOT_ENABLE_SQUEEZE_FACTOR", "1")
    on = se.compute_recommendation_strength(row)
    assert off == on
