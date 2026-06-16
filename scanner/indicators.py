"""Technical Indicators Module

Contains all technical analysis indicator calculations.
Extracted from scanner.py for modularity and reusability.
"""

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
) -> tuple[pd.Series, pd.Series, pd.Series]:
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


def add_alpha_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add Alpha158-inspired indicators (INT-6: Qlib Alpha158 port).

    Extends add_indicators() output with:
    - ROC series (Rate of Change): roc_5, roc_10, roc_20, roc_30, roc_60
    - STD series (Rolling volatility): std_5, std_10, std_20, std_30
    - Multi-period RSI: rsi_5, rsi_10, rsi_20, rsi_30
    - Price-volume correlation: corr_pv_5, corr_pv_10, corr_pv_20
    - Candlestick features: kmid, klen, kmid2, kup, kdn

    Args:
        df: DataFrame with at minimum OHLCV columns (add_indicators() already called recommended)

    Returns:
        DataFrame with additional Alpha158 columns appended.
    """
    import numpy as np  # noqa: PLC0415

    df = df.copy()

    required_cols = {"Open", "High", "Low", "Close", "Volume"}
    if not required_cols.issubset(set(df.columns)):
        return df

    # Ensure single Series
    close = df["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    high = df["High"]
    if isinstance(high, pd.DataFrame):
        high = high.iloc[:, 0]
    low = df["Low"]
    if isinstance(low, pd.DataFrame):
        low = low.iloc[:, 0]
    open_ = df["Open"]
    if isinstance(open_, pd.DataFrame):
        open_ = open_.iloc[:, 0]
    vol = df["Volume"]
    if isinstance(vol, pd.DataFrame):
        vol = vol.iloc[:, 0]

    # ── ROC Series (Rate of Change) ──────────────────────────────────────────
    for d in (5, 10, 20, 30, 60):
        df[f"roc_{d}"] = close.pct_change(d)

    # ── STD Series (Rolling realised vol, normalised by close) ───────────────
    for d in (5, 10, 20, 30):
        df[f"std_{d}"] = close.pct_change().rolling(d).std()

    # ── Multi-period RSI ─────────────────────────────────────────────────────
    for d in (5, 10, 20, 30):
        if d != 14:  # rsi(14) already in add_indicators()
            df[f"rsi_{d}"] = rsi(close, d)

    # ── Price-Volume Correlation ─────────────────────────────────────────────
    log_ret = close.pct_change()
    log_vol = vol.apply(lambda x: float(np.log(x + 1)) if x > 0 else 0.0)
    for d in (5, 10, 20):
        df[f"corr_pv_{d}"] = log_ret.rolling(d).corr(log_vol)

    # ── Candlestick Features (Qlib KMID / KLEN / KMID2 / KUP / KDN) ─────────
    day_range = (high - low).replace(0, float("nan"))
    # KMID: (close - open) / (high - low)  — body relative to range
    df["kmid"] = ((close - open_) / day_range).fillna(0.0)
    # KLEN: (high - low) / open           — range relative to open
    df["klen"] = ((high - low) / open_.replace(0, float("nan"))).fillna(0.0)
    # KMID2: (close - open) / (open * 2)  — body relative to open price
    df["kmid2"] = ((close - open_) / (open_.replace(0, float("nan")) * 2)).fillna(0.0)
    # KUP: (high - max(open, close)) / (high - low)  — upper wick fraction
    df["kup"] = ((high - pd.concat([open_, close], axis=1).max(axis=1)) / day_range).fillna(0.0)
    # KDN: (min(open, close) - low) / (high - low)   — lower wick fraction
    df["kdn"] = ((pd.concat([open_, close], axis=1).min(axis=1) - low) / day_range).fillna(0.0)

    # Clip extreme values (guard against overnight gaps, splits)
    alpha_cols = (
        [f"roc_{d}" for d in (5, 10, 20, 30, 60)]
        + [f"std_{d}" for d in (5, 10, 20, 30)]
        + [f"rsi_{d}" for d in (5, 10, 20, 30)]
        + [f"corr_pv_{d}" for d in (5, 10, 20)]
        + ["kmid", "klen", "kmid2", "kup", "kdn"]
    )
    for col in alpha_cols:
        if col in df.columns:
            df[col] = df[col].clip(-10.0, 10.0)

    return df
