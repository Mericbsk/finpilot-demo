"""Shared fixtures for FinPilot test suite."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture(autouse=True)
def _isolate_llm_state():
    """Ensure LLM cache and rate-limiter state is per-test (Sprint 4 isolation)."""
    try:
        from core.cache import cache_manager

        cache_manager.clear()
    except Exception:
        pass
    try:
        from core.rate_limiter import reset_buckets

        reset_buckets()
    except Exception:
        pass
    yield


@pytest.fixture
def sample_ohlcv():
    """Generate a realistic OHLCV DataFrame for testing."""
    np.random.seed(42)
    n = 250
    dates = pd.bdate_range(end=pd.Timestamp.now(), periods=n, freq="D")
    close = 100 + np.cumsum(np.random.randn(n) * 1.5)
    close = np.maximum(close, 5)  # keep prices positive
    high = close + np.abs(np.random.randn(n)) * 2
    low = close - np.abs(np.random.randn(n)) * 2
    low = np.maximum(low, 1)
    opn = close + np.random.randn(n) * 0.5
    volume = np.random.randint(100_000, 5_000_000, size=n).astype(float)

    df = pd.DataFrame(
        {"Open": opn, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=dates,
    )
    return df


@pytest.fixture
def sample_ohlcv_with_indicators(sample_ohlcv):
    """OHLCV with common indicator columns pre-populated."""
    df = sample_ohlcv.copy()
    df["ema50"] = df["Close"].ewm(span=50).mean()
    df["ema200"] = df["Close"].ewm(span=200).mean()
    df["rsi"] = 50.0  # neutral RSI
    df["atr"] = (df["High"] - df["Low"]).rolling(14).mean()
    df["macd_hist"] = np.random.randn(len(df)) * 0.5
    df["vol_avg10"] = df["Volume"].rolling(10).mean()
    df["vol_med20"] = df["Volume"].rolling(20).median()
    return df
