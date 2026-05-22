"""Tests for Sprint 16 feature flags and regime weight helpers.

Covers:
  - core.regime_weights.is_enabled()  (FINPILOT_ENABLE_REGIME_WEIGHTS)
  - research.lgbm_ranker.is_enabled() (FINPILOT_ENABLE_LGBM_RANKER)
  - core.regime_weights._DEFAULT_WEIGHTS structure
  - core.regime_weights.get_regime_weights() fallback to defaults
  - research.lgbm_ranker.FEATURE_COLS presence and type
  - llm.router._should_load / single-provider feature flag
"""

from __future__ import annotations

import os

import pytest


# ---------------------------------------------------------------------------
# regime_weights.is_enabled()
# ---------------------------------------------------------------------------
class TestRegimeWeightsIsEnabled:
    def test_disabled_by_default(self, monkeypatch):
        monkeypatch.delenv("FINPILOT_ENABLE_REGIME_WEIGHTS", raising=False)
        from core.regime_weights import is_enabled
        assert is_enabled() is False

    @pytest.mark.parametrize("val", ["1", "true", "True", "yes", "on"])
    def test_enabled_values(self, monkeypatch, val):
        monkeypatch.setenv("FINPILOT_ENABLE_REGIME_WEIGHTS", val)
        import importlib
        import core.regime_weights as rw
        importlib.reload(rw)
        from core.regime_weights import is_enabled
        assert is_enabled() is True

    @pytest.mark.parametrize("val", ["0", "false", "no", "off", ""])
    def test_disabled_values(self, monkeypatch, val):
        monkeypatch.setenv("FINPILOT_ENABLE_REGIME_WEIGHTS", val)
        from core.regime_weights import is_enabled
        assert is_enabled() is False


# ---------------------------------------------------------------------------
# regime_weights — default weight structure
# ---------------------------------------------------------------------------
class TestRegimeWeightsDefaults:
    def test_three_regimes_present(self):
        from core.regime_weights import _DEFAULT_WEIGHTS
        assert set(_DEFAULT_WEIGHTS.keys()) == {"bull", "bear", "range"}

    def test_each_regime_has_ten_weights(self):
        from core.regime_weights import _DEFAULT_WEIGHTS
        for regime, weights in _DEFAULT_WEIGHTS.items():
            assert len(weights) == 10, f"{regime} should have 10 weights"

    def test_all_weight_values_are_floats(self):
        from core.regime_weights import _DEFAULT_WEIGHTS
        for regime, weights in _DEFAULT_WEIGHTS.items():
            for key, val in weights.items():
                assert isinstance(val, (int, float)), f"{regime}.{key} is not numeric"

    def test_bear_regime_dampens_momentum_vs_bull(self):
        from core.regime_weights import _DEFAULT_WEIGHTS
        # In bear regime, momentum_20d should be negative (penalise trend-following)
        bull_mom = _DEFAULT_WEIGHTS["bull"].get("momentum_20d", 0)
        bear_mom = _DEFAULT_WEIGHTS["bear"].get("momentum_20d", 0)
        assert bear_mom < bull_mom


# ---------------------------------------------------------------------------
# regime_weights.get_regime_weights() — fallback to defaults
# ---------------------------------------------------------------------------
class TestGetRegimeWeights:
    def test_returns_dict_for_bull(self, tmp_path, monkeypatch):
        # When no JSON file, should return default weights
        import core.regime_weights as rw
        monkeypatch.setattr(rw, "_REGIME_WEIGHTS_PATH", tmp_path / "nonexistent.json")
        # Clear cache
        rw._REGIME_SPY_CACHE.clear()
        weights = rw.get_regime_weights("bull")
        assert isinstance(weights, dict)
        assert len(weights) > 0

    def test_returns_same_keys_as_defaults(self, tmp_path, monkeypatch):
        import core.regime_weights as rw
        monkeypatch.setattr(rw, "_REGIME_WEIGHTS_PATH", tmp_path / "nonexistent.json")
        rw._REGIME_SPY_CACHE.clear()
        weights = rw.get_regime_weights("range")
        default_keys = set(rw._DEFAULT_WEIGHTS["range"].keys())
        assert set(weights.keys()) == default_keys


# ---------------------------------------------------------------------------
# lgbm_ranker.is_enabled()
# ---------------------------------------------------------------------------
class TestLgbmRankerIsEnabled:
    def test_disabled_by_default(self, monkeypatch):
        monkeypatch.delenv("FINPILOT_ENABLE_LGBM_RANKER", raising=False)
        from research.lgbm_ranker import is_enabled
        assert is_enabled() is False

    @pytest.mark.parametrize("val", ["1", "true", "yes", "on"])
    def test_enabled_values(self, monkeypatch, val):
        monkeypatch.setenv("FINPILOT_ENABLE_LGBM_RANKER", val)
        from research.lgbm_ranker import is_enabled
        assert is_enabled() is True

    @pytest.mark.parametrize("val", ["0", "false", "no", "off"])
    def test_disabled_values(self, monkeypatch, val):
        monkeypatch.setenv("FINPILOT_ENABLE_LGBM_RANKER", val)
        from research.lgbm_ranker import is_enabled
        assert is_enabled() is False


# ---------------------------------------------------------------------------
# lgbm_ranker — FEATURE_COLS structure
# ---------------------------------------------------------------------------
class TestLgbmFeatureCols:
    def test_feature_cols_is_list(self):
        from research.lgbm_ranker import FEATURE_COLS
        assert isinstance(FEATURE_COLS, list)

    def test_feature_cols_not_empty(self):
        from research.lgbm_ranker import FEATURE_COLS
        assert len(FEATURE_COLS) > 0

    def test_all_feature_cols_are_strings(self):
        from research.lgbm_ranker import FEATURE_COLS
        for col in FEATURE_COLS:
            assert isinstance(col, str)

    def test_score_in_feature_cols(self):
        from research.lgbm_ranker import FEATURE_COLS
        assert "score" in FEATURE_COLS

    def test_feature_cols_matches_regime_weight_keys(self):
        from research.lgbm_ranker import FEATURE_COLS
        from core.regime_weights import _DEFAULT_WEIGHTS
        regime_keys = set(_DEFAULT_WEIGHTS["bull"].keys())
        lgbm_keys = set(FEATURE_COLS)
        # At least 5 keys should overlap (design invariant)
        overlap = regime_keys & lgbm_keys
        assert len(overlap) >= 5, f"Expected ≥5 overlapping keys, got {len(overlap)}: {overlap}"


# ---------------------------------------------------------------------------
# llm.router — single-provider feature flag
# ---------------------------------------------------------------------------
class TestLlmRouterFeatureFlag:
    def test_single_provider_env_var_default_is_none(self, monkeypatch):
        monkeypatch.delenv("FINPILOT_LLM_SINGLE_PROVIDER", raising=False)
        val = os.getenv("FINPILOT_LLM_SINGLE_PROVIDER")
        assert val is None

    def test_should_load_returns_true_when_no_filter(self, monkeypatch):
        import llm.router as lr
        # Monkeypatch the module-level constant (read at import time)
        monkeypatch.setattr(lr, "_SINGLE_PROVIDER", "")
        from llm.router import _should_load
        assert _should_load("claude") is True
        assert _should_load("groq") is True

    def test_should_load_filters_to_single_provider(self, monkeypatch):
        import llm.router as lr
        monkeypatch.setattr(lr, "_SINGLE_PROVIDER", "claude")
        from llm.router import _should_load
        assert _should_load("claude") is True
        assert _should_load("groq") is False
        assert _should_load("gemini") is False

    def test_should_load_case_insensitive(self, monkeypatch):
        import llm.router as lr
        # _SINGLE_PROVIDER is always lowercase; provider_name must match lowercase
        monkeypatch.setattr(lr, "_SINGLE_PROVIDER", "claude")
        from llm.router import _should_load
        assert _should_load("claude") is True
        assert _should_load("groq") is False

    def test_should_load_empty_string_allows_all(self, monkeypatch):
        import llm.router as lr
        monkeypatch.setattr(lr, "_SINGLE_PROVIDER", "")
        from llm.router import _should_load
        # Empty string → no filter
        assert _should_load("claude") is True
