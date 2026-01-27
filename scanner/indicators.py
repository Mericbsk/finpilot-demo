"""Technical Indicators Module

Contains all technical analysis indicator calculations.
Extracted from scanner.py for modularity and reusability.
"""

from typing import Tuple

import pandas as pd


def ema(series: pd.Series, window: int) -> pd.Series:
    """
    Calculate Exponential Moving Average.

    Args:
        series: Price series (typically Close prices)
        window: EMA period (e.g., 50, 200)

    Returns:
        EMA values as pandas Series
    """
    return series.ewm(span=window, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index.

    Args:
        series: Price series (typically Close prices)
        period: RSI period (default 14)

    Returns:
        RSI values as pandas Series (0-100 scale)
    """
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    roll_up = up.ewm(alpha=1 / period, adjust=False).mean()
    roll_down = down.ewm(alpha=1 / period, adjust=False).mean()
    rs = roll_up / (roll_down.replace(0, 1e-10))
    return 100 - (100 / (1 + rs))


def macd_hist(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.Series:
    """
    Calculate MACD Histogram.

    Args:
        close: Close price series
        fast: Fast EMA period (default 12)
        slow: Slow EMA period (default 26)
        signal: Signal line period (default 9)

    Returns:
        MACD histogram values as pandas Series
    """
    macd_line = (
        close.ewm(span=fast, adjust=False).mean() - close.ewm(span=slow, adjust=False).mean()
    )
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line - signal_line


def bbands(
    series: pd.Series, window: int = 20, ndev: float = 2
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands.

    Args:
        series: Price series (typically Close prices)
        window: Moving average period (default 20)
        ndev: Number of standard deviations (default 2)

    Returns:
        Tuple of (upper_band, middle_band, lower_band) as pandas Series
    """
    middle = series.rolling(window).mean()
    std = series.rolling(window).std()
    upper = middle + ndev * std
    lower = middle - ndev * std
    return upper, middle, lower


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range.

    Args:
        df: DataFrame with 'High', 'Low', 'Close' columns
        period: ATR period (default 14)

    Returns:
        ATR values as pandas Series
    """

    def _ensure_series(x):
        if isinstance(x, pd.DataFrame):
            return x.iloc[:, 0]
        return x

    high = _ensure_series(df["High"])
    low = _ensure_series(df["Low"])
    close = _ensure_series(df["Close"])
    prev_close = close.shift(1)

    tr = pd.concat(
        [(high - low).abs(), (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)

    return tr.ewm(alpha=1 / period, adjust=False).mean()


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all technical indicators to a price DataFrame.

    Args:
        df: DataFrame with OHLCV columns (Open, High, Low, Close, Volume)

    Returns:
        DataFrame with added indicator columns:
        - ema50, ema200: Exponential moving averages
        - rsi: Relative Strength Index
        - macd_hist: MACD Histogram
        - bb_upper, bb_middle, bb_lower: Bollinger Bands
        - atr: Average True Range
        - vol_med20: 20-day median volume
        - vol_avg10: 10-day average volume
    """
    df = df.copy()

    # Validate required columns
    required_cols = {"Open", "High", "Low", "Close", "Volume"}
    if not required_cols.issubset(set(df.columns)):
        return pd.DataFrame()

    # Ensure single Series for calculations
    close = df["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]  # type: ignore[arg-type]
    high = df["High"]
    if isinstance(high, pd.DataFrame):
        high = high.iloc[:, 0]  # type: ignore[arg-type]
    low = df["Low"]
    if isinstance(low, pd.DataFrame):
        low = low.iloc[:, 0]  # type: ignore[arg-type]
    vol = df["Volume"]
    if isinstance(vol, pd.DataFrame):
        vol = vol.iloc[:, 0]  # type: ignore[arg-type]

    # Moving averages
    df["ema50"] = ema(close, 50)
    df["ema200"] = ema(close, 200)

    # Momentum indicators
    df["rsi"] = rsi(close, 14)
    df["macd_hist"] = macd_hist(close)

    # Bollinger Bands
    upper, middle, lower = bbands(close, 20, 2)
    df["bb_upper"] = upper
    df["bb_middle"] = middle
    df["bb_lower"] = lower

    # Volatility
    df["atr"] = atr(pd.DataFrame({"High": high, "Low": low, "Close": close}))

    # Volume analysis
    df["vol_med20"] = vol.rolling(20).median()
    df["vol_avg10"] = vol.rolling(10).mean()

    return df
