"""
Unit tests for scanner.indicators module.

Tests technical indicator calculations with known values.
"""

import numpy as np
import pandas as pd
import pytest

from scanner.indicators import add_indicators, atr, bbands, ema, macd_hist, rsi


class TestEMA:
    """Tests for Exponential Moving Average calculation."""

    def test_ema_basic(self):
        """EMA should calculate correctly for simple series."""
        prices = pd.Series([10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20])
        result = ema(prices, 3)

        # EMA should exist for all values
        assert len(result) == len(prices)
        # Last EMA should be close to recent prices (uptrend)
        assert result.iloc[-1] > 18

    def test_ema_uptrend(self):
        """EMA should lag below price in uptrend."""
        prices = pd.Series(range(1, 21))  # 1 to 20
        result = ema(prices, 5)

        # In uptrend, EMA should be below current price
        assert result.iloc[-1] < prices.iloc[-1]

    def test_ema_downtrend(self):
        """EMA should lag above price in downtrend."""
        prices = pd.Series(range(20, 0, -1))  # 20 to 1
        result = ema(prices, 5)

        # In downtrend, EMA should be above current price
        assert result.iloc[-1] > prices.iloc[-1]

    def test_ema_flat(self):
        """EMA of constant series should equal that constant."""
        prices = pd.Series([50.0] * 20)
        result = ema(prices, 10)

        # EMA of flat line should equal the constant
        assert abs(result.iloc[-1] - 50.0) < 0.001


class TestRSI:
    """Tests for Relative Strength Index calculation."""

    def test_rsi_range(self):
        """RSI should always be between 0 and 100."""
        np.random.seed(42)
        prices = pd.Series(np.random.random(100) * 100 + 50)
        result = rsi(prices, 14)

        valid_rsi = result.dropna()
        assert all(valid_rsi >= 0)
        assert all(valid_rsi <= 100)

    def test_rsi_strong_uptrend(self):
        """RSI should be high (>70) in strong uptrend."""
        prices = pd.Series(range(50, 100))  # Strong uptrend
        result = rsi(prices, 14)

        # Should be overbought territory
        assert result.iloc[-1] > 70

    def test_rsi_strong_downtrend(self):
        """RSI should be low (<30) in strong downtrend."""
        prices = pd.Series(range(100, 50, -1))  # Strong downtrend
        result = rsi(prices, 14)

        # Should be oversold territory
        assert result.iloc[-1] < 30

    def test_rsi_neutral(self):
        """RSI should be around 50 for oscillating prices."""
        # Create oscillating price (up-down-up-down)
        prices = pd.Series([50 + (i % 2) * 2 for i in range(50)])
        result = rsi(prices, 14)

        # Should be near neutral
        assert 40 < result.iloc[-1] < 60


class TestMACD:
    """Tests for MACD Histogram calculation."""

    def test_macd_hist_uptrend(self):
        """MACD histogram should be positive in uptrend."""
        prices = pd.Series(range(50, 100))
        result = macd_hist(prices)

        # In strong uptrend, histogram should be positive
        assert result.iloc[-1] > 0

    def test_macd_hist_downtrend(self):
        """MACD histogram should be negative in downtrend."""
        prices = pd.Series(range(100, 50, -1))
        result = macd_hist(prices)

        # In strong downtrend, histogram should be negative
        assert result.iloc[-1] < 0

    def test_macd_hist_length(self):
        """MACD histogram should have same length as input."""
        prices = pd.Series(range(1, 51))
        result = macd_hist(prices)

        assert len(result) == len(prices)


class TestBollingerBands:
    """Tests for Bollinger Bands calculation."""

    def test_bbands_structure(self):
        """Bollinger Bands should return upper, middle, lower."""
        prices = pd.Series(np.random.random(50) * 10 + 100)
        upper, middle, lower = bbands(prices, 20, 2)

        assert len(upper) == len(prices)
        assert len(middle) == len(prices)
        assert len(lower) == len(prices)

    def test_bbands_order(self):
        """Upper band should be above middle, middle above lower."""
        np.random.seed(42)
        prices = pd.Series(np.random.random(50) * 10 + 100)
        upper, middle, lower = bbands(prices, 20, 2)

        # Check last valid values
        valid_idx = upper.dropna().index[-1]
        assert upper.loc[valid_idx] > middle.loc[valid_idx]
        assert middle.loc[valid_idx] > lower.loc[valid_idx]

    def test_bbands_width_with_volatility(self):
        """Higher volatility should result in wider bands."""
        # Low volatility
        low_vol = pd.Series([100 + (i % 2) * 0.1 for i in range(50)])
        upper_low, middle_low, lower_low = bbands(low_vol, 20, 2)

        # High volatility
        high_vol = pd.Series([100 + (i % 2) * 10 for i in range(50)])
        upper_high, middle_high, lower_high = bbands(high_vol, 20, 2)

        # High volatility should have wider bands
        width_low = upper_low.iloc[-1] - lower_low.iloc[-1]
        width_high = upper_high.iloc[-1] - lower_high.iloc[-1]

        assert width_high > width_low


class TestATR:
    """Tests for Average True Range calculation."""

    def test_atr_positive(self):
        """ATR should always be positive."""
        df = pd.DataFrame(
            {
                "High": [105, 107, 106, 108, 110],
                "Low": [100, 102, 101, 103, 105],
                "Close": [103, 105, 104, 106, 108],
            }
        )
        result = atr(df, 3)

        valid_atr = result.dropna()
        assert all(valid_atr > 0)

    def test_atr_high_volatility(self):
        """ATR should be higher with more volatile data."""
        # Low volatility
        df_low = pd.DataFrame(
            {
                "High": [101, 102, 101, 102, 101],
                "Low": [99, 100, 99, 100, 99],
                "Close": [100, 101, 100, 101, 100],
            }
        )

        # High volatility
        df_high = pd.DataFrame(
            {
                "High": [110, 120, 110, 120, 110],
                "Low": [90, 80, 90, 80, 90],
                "Close": [100, 100, 100, 100, 100],
            }
        )

        atr_low = atr(df_low, 3).iloc[-1]
        atr_high = atr(df_high, 3).iloc[-1]

        assert atr_high > atr_low


class TestAddIndicators:
    """Tests for the add_indicators composite function."""

    def test_add_indicators_columns(self):
        """add_indicators should add all expected columns."""
        df = pd.DataFrame(
            {
                "Open": np.random.random(250) * 10 + 100,
                "High": np.random.random(250) * 10 + 105,
                "Low": np.random.random(250) * 10 + 95,
                "Close": np.random.random(250) * 10 + 100,
                "Volume": np.random.random(250) * 1000000,
            }
        )

        result = add_indicators(df)

        expected_cols = [
            "ema50",
            "ema200",
            "rsi",
            "macd_hist",
            "bb_upper",
            "bb_middle",
            "bb_lower",
            "atr",
            "vol_med20",
            "vol_avg10",
        ]

        for col in expected_cols:
            assert col in result.columns, f"Missing column: {col}"

    def test_add_indicators_missing_columns(self):
        """add_indicators should return empty DataFrame if columns missing."""
        df = pd.DataFrame(
            {
                "Open": [100, 101],
                "High": [105, 106],
                # Missing Low, Close, Volume
            }
        )

        result = add_indicators(df)
        assert result.empty

    def test_add_indicators_preserves_original(self):
        """add_indicators should not modify original DataFrame."""
        df = pd.DataFrame(
            {
                "Open": [100, 101, 102],
                "High": [105, 106, 107],
                "Low": [95, 96, 97],
                "Close": [102, 103, 104],
                "Volume": [1000000, 1100000, 1200000],
            }
        )

        original_cols = set(df.columns)
        _ = add_indicators(df)

        # Original should be unchanged
        assert set(df.columns) == original_cols


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
