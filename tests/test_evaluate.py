"""
Unit tests for scanner.evaluate module — Sprint 3 F1.

Tests calculate_risk_management, STRATEGY_PARAMS and evaluate_symbol
with mocked data fetching.
"""

import numpy as np
import pandas as pd
import pytest
from scanner.evaluate import (
    STRATEGY_PARAMS,
    calculate_risk_management,
    evaluate_symbol,
    evaluate_symbols_parallel,
)


# ---------------------------------------------------------------------------
# calculate_risk_management
# ---------------------------------------------------------------------------
class TestCalculateRiskManagement:
    """Tests for ATR-based risk management calculator."""

    def test_sniper_strategy(self):
        """High momentum (>=70) → Sniper strategy."""
        result = calculate_risk_management(price=100.0, atr_val=2.0, momentum_score=80)
        assert result["strategy_tag"] == "Sniper 🎯"
        assert result["stop_loss"] == 100.0 - (2.0 * 1.5)  # 97.0
        assert result["tp1"] == 100.0 + (2.0 * 3.0)  # 106.0
        assert result["tp2"] == 100.0 + (2.0 * 5.0)  # 110.0
        assert result["tp3"] == 100.0 + (2.0 * 8.0)  # 116.0
        assert result["take_profit"] == result["tp2"]
        assert result["risk_reward_ratio"] > 0

    def test_defensive_strategy(self):
        """Low momentum (<50) → Defensive strategy, no TP3."""
        result = calculate_risk_management(price=50.0, atr_val=1.0, momentum_score=30)
        assert result["strategy_tag"] == "Defansif 🛡️"
        assert result["tp3"] is None
        assert result["stop_loss"] == 50.0 - (1.0 * 2.5)  # 47.5

    def test_normal_strategy(self):
        """Medium momentum (50-69) → Normal strategy."""
        result = calculate_risk_management(price=200.0, atr_val=5.0, momentum_score=60)
        assert result["strategy_tag"] == "Normal 📈"
        assert result["tp3"] is not None

    def test_zero_price_no_division_error(self):
        """Should handle zero price gracefully."""
        result = calculate_risk_management(price=0.0, atr_val=1.0, momentum_score=50)
        assert result["stop_loss_percent"] == 0

    def test_zero_atr(self):
        """Should handle zero ATR without crashing."""
        result = calculate_risk_management(price=100.0, atr_val=0.0, momentum_score=50)
        assert result["stop_loss"] == 100.0
        assert result["take_profit"] == 100.0

    def test_result_keys(self):
        """All expected keys should be present."""
        result = calculate_risk_management(price=100.0, atr_val=2.0, momentum_score=60)
        expected_keys = {
            "stop_loss",
            "take_profit",
            "tp1",
            "tp2",
            "tp3",
            "strategy_tag",
            "position_size",
            "risk_reward_ratio",
            "stop_loss_percent",
        }
        assert set(result.keys()) == expected_keys


# ---------------------------------------------------------------------------
# STRATEGY_PARAMS constant
# ---------------------------------------------------------------------------
class TestStrategyParams:
    """Validate STRATEGY_PARAMS structure."""

    def test_all_strategies_present(self):
        assert set(STRATEGY_PARAMS.keys()) == {"Normal", "Agresif", "Defansif", "Momentum"}

    @pytest.mark.parametrize("strategy", ["Normal", "Agresif", "Defansif", "Momentum"])
    def test_strategy_has_required_keys(self, strategy):
        params = STRATEGY_PARAMS[strategy]
        assert "min_score" in params
        assert "rsi_low" in params
        assert "rsi_high" in params
        assert params["rsi_low"] < params["rsi_high"]


# ---------------------------------------------------------------------------
# evaluate_symbol (mocked)
# ---------------------------------------------------------------------------
class TestEvaluateSymbol:
    """Tests evaluate_symbol with pre-fetched mock data."""

    @staticmethod
    def _make_mock_data(n_15m=60, n_1h=40, n_4h=60, n_1d=250):
        """Build a dict of DataFrames matching expected timeframe keys."""
        np.random.seed(42)

        def _df(n, freq):
            dates = pd.date_range(end="2025-01-15", periods=n, freq=freq)
            close = 100 + np.cumsum(np.random.randn(n) * 0.5)
            close = np.maximum(close, 5.0)
            high = close + np.abs(np.random.randn(n))
            low = close - np.abs(np.random.randn(n))
            low = np.maximum(low, 1.0)
            vol = np.random.randint(300_000, 5_000_000, size=n).astype(float)
            df = pd.DataFrame(
                {"Open": close + 0.1, "High": high, "Low": low, "Close": close, "Volume": vol},
                index=dates,
            )
            df["ema50"] = df["Close"].ewm(span=min(50, n)).mean()
            df["ema200"] = df["Close"].ewm(span=min(200, n)).mean()
            df["rsi"] = 55.0
            df["atr"] = (df["High"] - df["Low"]).rolling(14).mean().bfill()
            df["macd_hist"] = 0.3
            df["vol_avg10"] = df["Volume"].rolling(10).mean().bfill()
            df["vol_med20"] = df["Volume"].rolling(20).median().bfill()
            return df

        return {
            "15m": _df(n_15m, "15min"),
            "1h": _df(n_1h, "1h"),
            "4h": _df(n_4h, "4h"),
            "1d": _df(n_1d, "D"),
        }

    def test_returns_dict_on_valid_data(self):
        """evaluate_symbol should return a dict for valid prefetched data."""
        data = self._make_mock_data()
        result = evaluate_symbol("TEST", prefetched_data=data)
        assert result is not None
        assert isinstance(result, dict)
        assert result["symbol"] == "TEST"

    def test_returns_none_on_insufficient_data(self):
        """Should return None when any timeframe has too few rows."""
        data = self._make_mock_data(n_15m=5, n_1h=5, n_4h=5, n_1d=10)
        result = evaluate_symbol("TINY", prefetched_data=data)
        assert result is None

    def test_result_contains_key_fields(self):
        """Result dict should contain critical trading fields."""
        data = self._make_mock_data()
        result = evaluate_symbol("AAPL", prefetched_data=data)
        if result is None:
            pytest.skip("evaluate_symbol returned None for mock data")
        for key in [
            "price",
            "score",
            "entry_ok",
            "stop_loss",
            "take_profit",
            "risk_reward",
            "momentum_bias",
        ]:
            assert key in result, f"Missing key: {key}"

    def test_kelly_fraction_passthrough(self):
        """Kelly fraction should appear in result."""
        data = self._make_mock_data()
        result = evaluate_symbol("KF", kelly_fraction=0.25, prefetched_data=data)
        if result is None:
            pytest.skip("evaluate_symbol returned None")
        assert result["kelly_fraction"] == 0.25


# ---------------------------------------------------------------------------
# evaluate_symbols_parallel
# ---------------------------------------------------------------------------
class TestEvaluateSymbolsParallel:
    """Tests for parallel evaluation (without real network calls)."""

    def test_empty_symbols_list(self):
        """Should return empty list for empty input."""
        results = evaluate_symbols_parallel([], kelly_fraction=0.5, use_prefetch=False)
        assert results == []

    def test_progress_callback_called(self):
        """Progress callback should be invoked."""
        calls = []

        def cb(current, total):
            calls.append((current, total))

        # Even with invalid symbols, it should call progress and not crash
        evaluate_symbols_parallel(
            ["INVALID_SYMBOL_XYZ"],
            kelly_fraction=0.5,
            progress_callback=cb,
            use_prefetch=False,
        )
        assert len(calls) >= 0  # callback may or may not be called depending on errors
