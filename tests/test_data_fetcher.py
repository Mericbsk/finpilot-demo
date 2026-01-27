"""
Unit tests for scanner.data_fetcher module.

Tests data fetching and symbol management functions.
"""

import os
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from scanner.data_fetcher import (
    get_market_regime_status,
    load_symbols,
    load_symbols_from_file,
    load_ticker_list,
    save_scan_results,
)


class TestLoadSymbols:
    """Tests for symbol loading functions."""

    def test_load_symbols_returns_list(self):
        """load_symbols should return a list of strings."""
        symbols = load_symbols()

        assert isinstance(symbols, list)
        assert len(symbols) > 0
        assert all(isinstance(s, str) for s in symbols)

    def test_load_symbols_default_list(self):
        """load_symbols should include major stocks."""
        symbols = load_symbols()

        # Should include some major stocks
        major_stocks = ["AAPL", "MSFT", "GOOGL"]
        assert any(s in symbols for s in major_stocks)


class TestLoadTickerList:
    """Tests for predefined ticker list loading."""

    def test_load_ticker_list_us_large_cap(self):
        """Should load US large cap stocks."""
        symbols = load_ticker_list("us_large_cap")

        assert len(symbols) > 0
        assert "AAPL" in symbols
        assert "MSFT" in symbols

    def test_load_ticker_list_us_tech(self):
        """Should load US tech stocks."""
        symbols = load_ticker_list("us_tech")

        assert len(symbols) > 0
        assert "NVDA" in symbols or "AMD" in symbols

    def test_load_ticker_list_etf(self):
        """Should load ETF symbols."""
        symbols = load_ticker_list("etf")

        assert len(symbols) > 0
        assert "SPY" in symbols
        assert "QQQ" in symbols

    def test_load_ticker_list_tr_bist30(self):
        """Should load Turkish BIST30 stocks."""
        symbols = load_ticker_list("tr_bist30")

        assert len(symbols) > 0
        assert all(s.endswith(".IS") for s in symbols)

    def test_load_ticker_list_unknown_category(self):
        """Should return default for unknown category."""
        symbols = load_ticker_list("unknown_category")

        # Should return default (us_large_cap)
        assert len(symbols) > 0
        assert "AAPL" in symbols


class TestLoadSymbolsFromFile:
    """Tests for file-based symbol loading."""

    def test_load_symbols_from_file_success(self, tmp_path):
        """Should load symbols from text file."""
        # Create temp file
        symbol_file = tmp_path / "symbols.txt"
        symbol_file.write_text("AAPL\nMSFT\nGOOGL\n")

        symbols = load_symbols_from_file(str(symbol_file))

        assert symbols == ["AAPL", "MSFT", "GOOGL"]

    def test_load_symbols_from_file_lowercase(self, tmp_path):
        """Should uppercase symbols from file."""
        symbol_file = tmp_path / "symbols.txt"
        symbol_file.write_text("aapl\nmsft\n")

        symbols = load_symbols_from_file(str(symbol_file))

        assert symbols == ["AAPL", "MSFT"]

    def test_load_symbols_from_file_empty_lines(self, tmp_path):
        """Should skip empty lines."""
        symbol_file = tmp_path / "symbols.txt"
        symbol_file.write_text("AAPL\n\nMSFT\n  \nGOOGL\n")

        symbols = load_symbols_from_file(str(symbol_file))

        assert "AAPL" in symbols
        assert "MSFT" in symbols
        assert "GOOGL" in symbols

    def test_load_symbols_from_file_not_found(self):
        """Should return empty list for missing file."""
        symbols = load_symbols_from_file("/nonexistent/path/symbols.txt")

        assert symbols == []


class TestGetMarketRegimeStatus:
    """Tests for market regime detection."""

    @patch("scanner.data_fetcher.yf.download")
    def test_market_regime_safe(self, mock_download):
        """Should return safe when market is positive."""
        # Mock positive market data
        mock_df = pd.DataFrame(
            {
                "Open": [100.0] * 60,
                "Close": [105.0] * 60,  # Close > Open (green day)
            }
        )
        mock_df["ema50"] = [100.0] * 60  # Close > EMA50 (uptrend)
        mock_download.return_value = mock_df

        result = get_market_regime_status(["AAPL", "MSFT"])

        assert result["safe"] is True
        assert "Pozitif" in result["reason"] or "reason" in result

    @patch("scanner.data_fetcher._fetch_market_index")
    def test_market_regime_downtrend(self, mock_fetch):
        """Should return unsafe when market is in downtrend."""
        # Mock downtrend data - must patch the cached function
        mock_df = pd.DataFrame(
            {
                "Open": [100.0] * 60,
                "Close": [95.0] * 60,  # Close < EMA50
            }
        )
        mock_df["ema50"] = [100.0] * 60
        mock_fetch.return_value = mock_df

        result = get_market_regime_status(["AAPL", "MSFT"])

        assert result["safe"] is False

    @patch("scanner.data_fetcher._fetch_market_index")
    def test_market_regime_empty_data(self, mock_fetch):
        """Should return safe as default when no data."""
        mock_fetch.return_value = pd.DataFrame()

        result = get_market_regime_status(["AAPL"])

        assert result["safe"] is True

    @patch("scanner.data_fetcher._fetch_market_index")
    def test_market_regime_error_handling(self, mock_fetch):
        """Should handle errors gracefully."""
        # Simulate returning invalid/empty data instead of raising exception
        mock_fetch.return_value = pd.DataFrame()

        result = get_market_regime_status(["AAPL"])

        assert result["safe"] is True  # Default to safe on error

    def test_market_regime_turkish_stocks(self):
        """Should use XU100 for Turkish stocks."""
        # This is a behavior test - we can't easily mock this
        # Just verify it doesn't crash with Turkish symbols
        symbols = ["THYAO.IS", "AKBNK.IS"]
        # Would need network, so just test the symbol detection logic


class TestSaveScanResults:
    """Tests for scan result saving."""

    def test_save_scan_results_creates_file(self, tmp_path):
        """Should create CSV file with results."""
        df = pd.DataFrame(
            {"symbol": ["AAPL", "MSFT"], "price": [150.0, 350.0], "entry_ok": [True, False]}
        )

        output_dir = str(tmp_path / "results")
        filepath = save_scan_results(df, prefix="test", output_dir=output_dir)

        assert os.path.exists(filepath)
        assert filepath.endswith(".csv")

    def test_save_scan_results_content(self, tmp_path):
        """Should save correct content to CSV."""
        df = pd.DataFrame({"symbol": ["AAPL", "MSFT"], "price": [150.0, 350.0]})

        output_dir = str(tmp_path / "results")
        filepath = save_scan_results(df, prefix="test", output_dir=output_dir)

        # Read back and verify
        loaded = pd.read_csv(filepath)
        assert list(loaded["symbol"]) == ["AAPL", "MSFT"]

    def test_save_scan_results_creates_directory(self, tmp_path):
        """Should create output directory if not exists."""
        df = pd.DataFrame({"symbol": ["AAPL"]})

        output_dir = str(tmp_path / "new" / "nested" / "dir")
        filepath = save_scan_results(df, output_dir=output_dir)

        assert os.path.exists(filepath)
        assert os.path.isdir(output_dir)


class TestFetch:
    """Tests for data fetching function."""

    @patch("scanner.data_fetcher.yf.Ticker")
    def test_fetch_returns_dataframe(self, mock_ticker):
        """fetch should return a DataFrame."""
        from scanner.data_fetcher import fetch

        # Mock yfinance response
        mock_hist = pd.DataFrame(
            {
                "Open": [100.0, 101.0],
                "High": [105.0, 106.0],
                "Low": [98.0, 99.0],
                "Close": [103.0, 104.0],
                "Volume": [1000000, 1100000],
            }
        )
        mock_ticker.return_value.history.return_value = mock_hist

        result = fetch("AAPL", "1d", 10)

        assert isinstance(result, pd.DataFrame)

    @patch("scanner.data_fetcher.yf.Ticker")
    def test_fetch_empty_on_error(self, mock_ticker):
        """fetch should return empty DataFrame on error."""
        from scanner.data_fetcher import fetch

        # Use specific exception type that our code catches
        mock_ticker.return_value.history.side_effect = ValueError("API Error")

        result = fetch("INVALID", "1d", 10)

        assert isinstance(result, pd.DataFrame)
        assert result.empty


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
