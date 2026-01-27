"""
Unit tests for scanner.signals module.

Tests signal detection and scoring functions.
"""

import numpy as np
import pandas as pd
import pytest

from scanner.signals import (
    analyze_price_momentum,
    build_explanation,
    build_reason,
    check_momentum_confluence,
    check_price_momentum,
    check_timeframe_alignment,
    check_trend_strength,
    check_volume_spike,
    compute_recommendation_score,
    compute_recommendation_strength,
    safe_float,
    signal_score_row,
)


class TestSafeFloat:
    """Tests for safe_float helper function."""

    def test_safe_float_scalar(self):
        """safe_float should handle scalar values."""
        assert safe_float(10.5) == 10.5
        assert safe_float(100) == 100.0

    def test_safe_float_series(self):
        """safe_float should extract first value from Series."""
        s = pd.Series([1.5, 2.5, 3.5])
        assert safe_float(s) == 1.5

    def test_safe_float_empty_series(self):
        """safe_float should return 0.0 for empty Series."""
        s = pd.Series([], dtype=float)
        assert safe_float(s) == 0.0


class TestCheckVolumeSpike:
    """Tests for volume spike detection."""

    def test_volume_spike_detected(self):
        """Should detect volume spike above threshold."""
        df = pd.DataFrame(
            {"Volume": [100000] * 9 + [200000], "vol_avg10": [100000] * 10}  # Last is 2x average
        )

        assert check_volume_spike(df) is True

    def test_volume_spike_not_detected(self):
        """Should not detect spike for normal volume."""
        df = pd.DataFrame({"Volume": [100000] * 10, "vol_avg10": [100000] * 10})

        assert check_volume_spike(df) is False

    def test_volume_spike_insufficient_data(self):
        """Should return False for insufficient data."""
        df = pd.DataFrame({"Volume": [100000] * 5, "vol_avg10": [100000] * 5})

        assert check_volume_spike(df) is False


class TestCheckTrendStrength:
    """Tests for trend strength detection."""

    def test_trend_strength_strong_uptrend(self):
        """Should detect strong trend when EMA50 >> EMA200."""
        df = pd.DataFrame({"ema50": [105.0] * 200, "ema200": [100.0] * 200})  # 5% above EMA200

        assert check_trend_strength(df) is True

    def test_trend_strength_weak_trend(self):
        """Should not detect trend when gap is small."""
        df = pd.DataFrame({"ema50": [101.0] * 200, "ema200": [100.0] * 200})  # Only 1% above

        assert check_trend_strength(df) is False

    def test_trend_strength_insufficient_data(self):
        """Should return False for insufficient data."""
        df = pd.DataFrame({"ema50": [105.0] * 100, "ema200": [100.0] * 100})

        assert check_trend_strength(df) is False


class TestAnalyzePriceMomentum:
    """Tests for momentum analysis."""

    def test_momentum_uptrend(self):
        """Should detect positive momentum in uptrend."""
        prices = pd.Series(range(50, 100))
        df = pd.DataFrame({"Close": prices, "vol_avg10": [1000000] * len(prices)})

        result = analyze_price_momentum(df)

        assert result["dominant_return_pct"] > 0
        assert result["dominant_direction"] >= 0

    def test_momentum_downtrend(self):
        """Should detect negative momentum in downtrend."""
        prices = pd.Series(range(100, 50, -1))
        df = pd.DataFrame({"Close": prices, "vol_avg10": [1000000] * len(prices)})

        result = analyze_price_momentum(df)

        assert result["dominant_return_pct"] < 0

    def test_momentum_empty_data(self):
        """Should handle empty DataFrame gracefully."""
        result = analyze_price_momentum(None)

        assert result["metrics"] == []
        assert result["best"] is None
        assert result["positive"] is False


class TestCheckTimeframeAlignment:
    """Tests for multi-timeframe alignment."""

    def test_alignment_all_bullish(self):
        """Should detect alignment when all timeframes bullish."""
        # Need enough data for EMA calculations
        df_1h = pd.DataFrame({"Close": [110.0] * 30})
        df_4h = pd.DataFrame({"Close": [110.0] * 60, "ema50": [100.0] * 60})
        df_1d = pd.DataFrame({"Close": [110.0] * 210, "ema200": [100.0] * 210})

        aligned, ratio, alignments = check_timeframe_alignment(df_1h, df_4h, df_1d)

        # At least 2/3 should be aligned for this to work
        # Note: 1h uses EMA20 calculated on the fly, needs proper Close data
        assert ratio >= 0.66 or len(alignments) >= 2

    def test_alignment_mixed(self):
        """Should handle mixed alignment signals."""
        df_1h = pd.DataFrame({"Close": [90.0] * 30})  # Bearish
        df_4h = pd.DataFrame({"Close": [110.0] * 60, "ema50": [100.0] * 60})  # Bullish
        df_1d = pd.DataFrame({"Close": [110.0] * 210, "ema200": [100.0] * 210})  # Bullish

        aligned, ratio, alignments = check_timeframe_alignment(df_1h, df_4h, df_1d)

        # 2/3 bullish = 0.67
        assert ratio >= 0.66


class TestCheckMomentumConfluence:
    """Tests for momentum confluence detection."""

    def test_confluence_strong_momentum(self):
        """Should detect confluence with strong momentum indicators."""
        df_15m = pd.DataFrame(
            {"rsi": [55.0] * 30, "macd_hist": [0.1] * 30}  # Healthy range  # Strong positive
        )
        df_4h = pd.DataFrame({"rsi": [55.0] * 30, "macd_hist": [0.1] * 30})

        has_confluence, ratio = check_momentum_confluence(df_15m, df_4h)

        assert ratio > 0


class TestSignalScoreRow:
    """Tests for signal scoring."""

    def test_signal_score_bullish_signals(self):
        """Should score bullish signals."""
        df = pd.DataFrame(
            {
                "Close": [99.0, 101.0],  # Bounced above BB
                "bb_lower": [100.0, 100.0],
                "rsi": [28.0, 35.0],  # Recovering from oversold
                "macd_hist": [-0.1, 0.1],  # Crossed positive
                "Volume": [1000000, 1500000],  # Volume spike
                "vol_med20": [1000000, 1000000],
            }
        )

        score = signal_score_row(df)

        assert score >= 0
        assert score <= 4


class TestRecommendationScore:
    """Tests for recommendation scoring."""

    def test_recommendation_score_strong_signal(self):
        """Should give high score for strong signals."""
        row = {
            "regime": True,
            "direction": True,
            "score": 3,
            "filter_score": 3,
            "alignment_ratio": 1.0,
            "momentum_ratio": 0.8,
            "volume_spike": True,
            "price_momentum": True,
            "trend_strength": True,
            "is_premium_symbol": True,
        }

        score = compute_recommendation_score(row)

        assert score > 10  # Strong signal

    def test_recommendation_score_weak_signal(self):
        """Should give low score for weak signals."""
        row = {
            "regime": False,
            "direction": False,
            "score": 0,
            "filter_score": 0,
            "alignment_ratio": 0.0,
            "momentum_ratio": 0.0,
            "volume_spike": False,
            "price_momentum": False,
            "trend_strength": False,
            "is_premium_symbol": False,
        }

        score = compute_recommendation_score(row)

        assert score < 2  # Weak signal


class TestRecommendationStrength:
    """Tests for recommendation strength scaling."""

    def test_strength_range(self):
        """Strength should be 0-100."""
        weak_row = {"regime": False, "direction": False, "score": 0}
        strong_row = {
            "regime": True,
            "direction": True,
            "score": 3,
            "filter_score": 3,
            "alignment_ratio": 1.0,
            "momentum_ratio": 1.0,
        }

        weak_strength = compute_recommendation_strength(weak_row)
        strong_strength = compute_recommendation_strength(strong_row)

        assert 0 <= weak_strength <= 100
        assert 0 <= strong_strength <= 100
        assert strong_strength > weak_strength


class TestBuildExplanation:
    """Tests for explanation builder."""

    def test_explanation_uptrend(self):
        """Should build uptrend explanation."""
        row = {
            "regime": True,
            "direction": True,
            "alignment_ratio": 0.8,
            "momentum_ratio": 0.6,
            "filter_score": 2,
        }

        explanation = build_explanation(row)

        assert "Up" in explanation
        assert "Filtre" in explanation

    def test_explanation_downtrend(self):
        """Should build downtrend explanation."""
        row = {
            "regime": False,
            "direction": False,
            "alignment_ratio": 0.3,
            "momentum_ratio": 0.2,
            "filter_score": 0,
        }

        explanation = build_explanation(row)

        assert "Down" in explanation


class TestBuildReason:
    """Tests for reason builder."""

    def test_reason_entry_ok(self):
        """Should build positive reason for entry_ok signals."""
        row = {"entry_ok": True, "risk_reward": 2.5, "stop_loss": 95.0, "take_profit": 110.0}

        reason = build_reason(row)

        assert "Alınır" in reason
        assert "R/R" in reason

    def test_reason_entry_not_ok(self):
        """Should list missing criteria for non-entry signals."""
        row = {
            "entry_ok": False,
            "risk_reward": 1.5,
            "volume_spike": False,
            "price_momentum": False,
            "trend_strength": True,
            "timeframe_aligned": True,
            "momentum_confluence": True,
        }

        reason = build_reason(row)

        assert "Bekleyin" in reason
        assert "Eksik" in reason


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
