"""Tests for the FRED macro-regime classifier (env-gated, default OFF)."""

from __future__ import annotations

import json

import pytest
import scanner.score_engine as se

import core.macro_regime as mr


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    mr._MEMO.clear()
    monkeypatch.setenv("FINPILOT_ENABLE_FRED_MACRO", "1")
    monkeypatch.setenv("FRED_API_KEY", "test-key")
    yield
    mr._MEMO.clear()


def test_fred_disabled_without_key(monkeypatch):
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    assert mr.fred_enabled() is False


def test_fred_disabled_without_flag(monkeypatch):
    monkeypatch.setenv("FINPILOT_ENABLE_FRED_MACRO", "0")
    assert mr.fred_enabled() is False


def test_classify_risk_off_high_vix():
    assert mr.classify_regime(30.0, 0.5) == "risk_off"


def test_classify_risk_off_inverted_curve_elevated_vix():
    assert mr.classify_regime(22.0, -0.2) == "risk_off"


def test_classify_risk_on_low_vix_positive_spread():
    assert mr.classify_regime(14.0, 0.5) == "risk_on"


def test_classify_neutral_mid_vix():
    assert mr.classify_regime(18.0, 0.3) == "neutral"


def test_classify_neutral_when_vix_missing():
    assert mr.classify_regime(None, -1.0) == "neutral"


def test_macro_multiplier_risk_off(monkeypatch):
    monkeypatch.setattr(mr, "get_macro_regime", lambda: "risk_off")
    assert mr.macro_factor_multiplier() == 0.5


def test_macro_multiplier_neutral(monkeypatch):
    monkeypatch.setattr(mr, "get_macro_regime", lambda: "neutral")
    assert mr.macro_factor_multiplier() == 1.0


def test_macro_multiplier_disabled_is_one(monkeypatch):
    monkeypatch.setenv("FINPILOT_ENABLE_FRED_MACRO", "0")
    assert mr.macro_factor_multiplier() == 1.0


def test_refresh_writes_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(mr, "_CACHE_PATH", tmp_path / "macro_regime.json")
    series = {"VIXCLS": 30.0, "T10Y2Y": -0.1}
    monkeypatch.setattr(mr, "_fetch_latest", lambda sid: series.get(sid))
    payload = mr.refresh_macro_regime()
    assert payload["regime"] == "risk_off"
    saved = json.loads((tmp_path / "macro_regime.json").read_text(encoding="utf-8"))
    assert saved["regime"] == "risk_off"


def test_get_macro_regime_reads_cache(monkeypatch, tmp_path):
    cache = tmp_path / "macro_regime.json"
    cache.write_text(json.dumps({"regime": "risk_off"}), encoding="utf-8")
    monkeypatch.setattr(mr, "_CACHE_PATH", cache)
    mr._MEMO.clear()
    assert mr.get_macro_regime() == "risk_off"


def test_score_engine_macro_dampens_squeeze(monkeypatch):
    monkeypatch.setenv("FINPILOT_ENABLE_SQUEEZE_FACTOR", "1")
    monkeypatch.setenv("FINPILOT_ENABLE_FRED_MACRO", "1")
    monkeypatch.setattr(se, "_macro_mult", lambda: 0.5)
    base = se.compute_recommendation_score({"score": 3, "squeeze_factor": 0.0})
    boosted = se.compute_recommendation_score({"score": 3, "squeeze_factor": 1.0})
    # squeeze boost halved by risk-off macro multiplier
    assert boosted - base == pytest.approx(se._SQUEEZE_WEIGHT * 0.5)


def test_score_engine_macro_neutral_full_squeeze(monkeypatch):
    monkeypatch.setenv("FINPILOT_ENABLE_SQUEEZE_FACTOR", "1")
    monkeypatch.setattr(se, "_macro_mult", lambda: 1.0)
    base = se.compute_recommendation_score({"score": 3, "squeeze_factor": 0.0})
    boosted = se.compute_recommendation_score({"score": 3, "squeeze_factor": 1.0})
    assert boosted - base == pytest.approx(se._SQUEEZE_WEIGHT)
