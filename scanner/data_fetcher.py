"""Data Fetching Module

Contains all external data retrieval functions.
Extracted from scanner.py for modularity and reusability.

Performance Features:
- Parallel multi-timeframe fetching with ThreadPoolExecutor
- Smart caching with configurable TTL
- Batch symbol fetching for efficiency
"""

import hashlib
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import yfinance as yf

try:
    import streamlit as st

    HAS_STREAMLIT = True
except ImportError:
    st = None  # type: ignore
    HAS_STREAMLIT = False

from .config import SETTINGS
from .indicators import add_indicators

# Configure module logger
logger = logging.getLogger(__name__)


# ============================================
# 🧠 Cache Configuration
# ============================================
# TTL: 5 dakika (300 saniye) - tüm modüllerde standart
# Bu değer tüm cache'ler için tek kaynak olarak kullanılır
CACHE_TTL_SECONDS = 300
CACHE_TTL_MARKET_INDEX = 300  # Market index için de aynı TTL (önceden 600 idi)

# In-memory fallback cache for non-Streamlit usage
_memory_cache: Dict[str, tuple] = {}


def _get_cache_key(symbol: str, interval: str, days: int) -> str:
    """Generate a unique cache key for data requests."""
    today = datetime.now().strftime("%Y-%m-%d")
    return f"{symbol}_{interval}_{days}_{today}"


def _cache_data(ttl_seconds: int = CACHE_TTL_SECONDS):
    """
    Decorator that uses Streamlit cache when available,
    falls back to simple TTL-based memory cache otherwise.
    """

    def decorator(func):
        if HAS_STREAMLIT and st is not None:
            # Use Streamlit's native caching
            return st.cache_data(ttl=ttl_seconds, show_spinner=False)(func)
        else:
            # Simple memory cache with TTL for non-Streamlit usage
            def wrapper(*args, **kwargs):
                key = f"{func.__name__}_{str(args)}_{str(kwargs)}"
                now = datetime.now().timestamp()

                if key in _memory_cache:
                    cached_time, cached_result = _memory_cache[key]
                    if now - cached_time < ttl_seconds:
                        return cached_result

                result = func(*args, **kwargs)
                _memory_cache[key] = (now, result)
                return result

            return wrapper

    return decorator


@_cache_data(ttl_seconds=CACHE_TTL_SECONDS)
def fetch(symbol: str, interval: str, days: int) -> pd.DataFrame:
    """
    Fetch OHLCV data from Yahoo Finance with indicators.

    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
        interval: Time interval ('15m', '1h', '4h', '1d')
        days: Number of days of history to fetch

    Returns:
        DataFrame with OHLCV data and technical indicators,
        or empty DataFrame on failure
    """
    interval_map = {"15m": "15m", "1h": "1h", "4h": "4h", "1d": "1d"}
    yf_interval = interval_map.get(interval, "1d")
    period_map = {"15m": f"{days}d", "1h": f"{days}d", "4h": f"{days}d", "1d": f"{days}d"}
    yf_period = period_map.get(interval, f"{days}d")

    try:
        tkr = yf.Ticker(symbol)
        df = tkr.history(
            period=yf_period,
            interval=yf_interval,
            auto_adjust=SETTINGS.get("auto_adjust", True),
            prepost=SETTINGS.get("prepost", False),
            actions=False,
            back_adjust=False,
        )

        if df is None or df.empty:
            print(f"[WARN] Veri yok: {symbol} {interval} {days}d")
            return pd.DataFrame()

        # Ensure required columns exist
        if "Close" not in df.columns and "Adj Close" in df.columns:
            df = df.rename(columns={"Adj Close": "Close"})

        # Validate required columns
        needed = {"Open", "High", "Low", "Close", "Volume"}
        if not needed.issubset(set(df.columns)):
            print(f"[WARN] Beklenen sütunlar eksik: {symbol} {interval} - var: {list(df.columns)}")
            return pd.DataFrame()

        # Normalize timezone to avoid tz-aware vs tz-naive issues
        try:
            if isinstance(df.index, pd.DatetimeIndex):
                if getattr(df.index, "tz", None) is not None:
                    df.index = df.index.tz_convert(None)
        except (TypeError, AttributeError):
            pass

        df = df.dropna()
        return df

    except ConnectionError as e:
        logger.error(
            "yfinance bağlantı hatası: %s %s %dd - Ağ bağlantınızı kontrol edin. Hata: %s",
            symbol,
            interval,
            days,
            e,
        )
        return pd.DataFrame()
    except ValueError as e:
        error_msg = str(e).lower()
        if "rate limit" in error_msg or "too many requests" in error_msg:
            logger.warning(
                "yfinance rate limit aşıldı: %s - Lütfen birkaç dakika bekleyin.", symbol
            )
        else:
            logger.warning("yfinance değer hatası: %s %s %dd - %s", symbol, interval, days, e)
        return pd.DataFrame()
    except KeyError as e:
        logger.warning(
            "yfinance veri yapısı hatası: %s %s %dd - Sembol geçersiz olabilir. Hata: %s",
            symbol,
            interval,
            days,
            e,
        )
        return pd.DataFrame()
    except Exception as e:
        # Beklenmeyen hatalar için güvenli fallback
        error_type = type(e).__name__
        logger.error(
            "yfinance beklenmeyen hata (%s): %s %s %dd - %s", error_type, symbol, interval, days, e
        )
        return pd.DataFrame()


def fetch_with_indicators(symbol: str, interval: str, days: int) -> pd.DataFrame:
    """
    Fetch data and add technical indicators.

    Convenience function combining fetch() and add_indicators().

    Args:
        symbol: Stock ticker symbol
        interval: Time interval
        days: Number of days of history

    Returns:
        DataFrame with OHLCV data and all technical indicators
    """
    df = fetch(symbol, interval, days)
    if df.empty:
        return pd.DataFrame()
    return add_indicators(df)


# ============================================
# 🚀 Parallel Multi-Timeframe Fetching
# ============================================

# Default timeframes for multi-timeframe analysis
DEFAULT_TIMEFRAMES: List[Tuple[str, int]] = [
    ("15m", 10),  # 15-minute, 10 days
    ("1h", 60),  # 1-hour, 60 days
    ("4h", 100),  # 4-hour, 100 days
    ("1d", 400),  # Daily, 400 days
]


def fetch_multi_timeframe(
    symbol: str,
    timeframes: Optional[List[Tuple[str, int]]] = None,
    with_indicators: bool = True,
    max_workers: int = 4,
) -> Dict[str, pd.DataFrame]:
    """
    Fetch multiple timeframes for a symbol in parallel.

    This function significantly improves performance by fetching
    all timeframe data concurrently instead of sequentially.

    Args:
        symbol: Stock ticker symbol
        timeframes: List of (interval, days) tuples.
                   Defaults to DEFAULT_TIMEFRAMES if None.
        with_indicators: Whether to add technical indicators
        max_workers: Maximum parallel threads

    Returns:
        Dictionary mapping interval to DataFrame:
        {'15m': df_15m, '1h': df_1h, '4h': df_4h, '1d': df_1d}

    Example:
        >>> data = fetch_multi_timeframe('AAPL')
        >>> df_daily = data['1d']
        >>> df_hourly = data['1h']
    """
    if timeframes is None:
        timeframes = DEFAULT_TIMEFRAMES

    results: Dict[str, pd.DataFrame] = {}

    def _fetch_single(interval: str, days: int) -> Tuple[str, pd.DataFrame]:
        """Fetch single timeframe with optional indicators."""
        if with_indicators:
            df = fetch_with_indicators(symbol, interval, days)
        else:
            df = fetch(symbol, interval, days)
        return interval, df

    # Parallel fetch
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_fetch_single, interval, days) for interval, days in timeframes]

        for future in as_completed(futures):
            try:
                interval, df = future.result()
                results[interval] = df
            except Exception as e:
                logger.warning("Paralel fetch hatası: %s %s - %s", symbol, str(e), type(e).__name__)

    return results


def fetch_symbols_batch(
    symbols: List[str],
    interval: str = "1d",
    days: int = 100,
    with_indicators: bool = True,
    max_workers: int = 8,
) -> Dict[str, pd.DataFrame]:
    """
    Fetch data for multiple symbols in parallel.

    Optimized for batch operations like scanning large symbol lists.

    Args:
        symbols: List of stock ticker symbols
        interval: Time interval for all symbols
        days: Number of days of history
        with_indicators: Whether to add technical indicators
        max_workers: Maximum parallel threads (default 8 for batch)

    Returns:
        Dictionary mapping symbol to DataFrame:
        {'AAPL': df_aapl, 'GOOGL': df_googl, ...}

    Example:
        >>> symbols = ['AAPL', 'GOOGL', 'MSFT']
        >>> data = fetch_symbols_batch(symbols)
        >>> df_apple = data['AAPL']
    """
    results: Dict[str, pd.DataFrame] = {}

    def _fetch_symbol(symbol: str) -> Tuple[str, pd.DataFrame]:
        """Fetch single symbol."""
        if with_indicators:
            df = fetch_with_indicators(symbol, interval, days)
        else:
            df = fetch(symbol, interval, days)
        return symbol, df

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_fetch_symbol, symbol): symbol for symbol in symbols}

        for future in as_completed(futures):
            symbol = futures[future]
            try:
                _, df = future.result()
                results[symbol] = df
            except Exception as e:
                logger.warning("Batch fetch hatası: %s - %s", symbol, e)
                results[symbol] = pd.DataFrame()

    return results


def prefetch_symbols_multi_timeframe(
    symbols: List[str],
    timeframes: Optional[List[Tuple[str, int]]] = None,
    with_indicators: bool = True,
    max_workers: int = 10,
    progress_callback: Optional[Any] = None,
) -> Dict[str, Dict[str, pd.DataFrame]]:
    """
    Prefetch all timeframe data for multiple symbols in parallel.

    This is the most efficient way to prepare data for scanning
    large symbol lists. Uses nested parallelism for maximum throughput.

    Args:
        symbols: List of stock ticker symbols
        timeframes: List of (interval, days) tuples
        with_indicators: Whether to add technical indicators
        max_workers: Maximum parallel threads
        progress_callback: Optional callback(current, total) for progress

    Returns:
        Nested dictionary: {symbol: {interval: DataFrame}}
        Example: data['AAPL']['1d'] returns daily DataFrame for Apple

    Example:
        >>> symbols = ['AAPL', 'GOOGL']
        >>> data = prefetch_symbols_multi_timeframe(symbols)
        >>> aapl_daily = data['AAPL']['1d']
        >>> googl_hourly = data['GOOGL']['1h']
    """
    if timeframes is None:
        timeframes = DEFAULT_TIMEFRAMES

    results: Dict[str, Dict[str, pd.DataFrame]] = {}
    total = len(symbols)
    completed = 0

    def _fetch_all_timeframes(symbol: str) -> Tuple[str, Dict[str, pd.DataFrame]]:
        """Fetch all timeframes for a symbol."""
        data = fetch_multi_timeframe(
            symbol,
            timeframes=timeframes,
            with_indicators=with_indicators,
            max_workers=min(4, len(timeframes)),  # Nested parallelism limit
        )
        return symbol, data

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_fetch_all_timeframes, symbol): symbol for symbol in symbols}

        for future in as_completed(futures):
            symbol = futures[future]
            try:
                _, data = future.result()
                results[symbol] = data
            except Exception as e:
                logger.warning("Multi-timeframe prefetch hatası: %s - %s", symbol, e)
                results[symbol] = {tf[0]: pd.DataFrame() for tf in timeframes}

            completed += 1
            if progress_callback:
                try:
                    progress_callback(completed, total)
                except Exception:
                    pass

    return results


def load_symbols() -> List[str]:
    """
    Load list of symbols to scan.

    Currently returns a basic list. In production, this should
    read from a configuration file or database.

    Returns:
        List of stock ticker symbols
    """
    # Basic symbol list - extend as needed
    return ["AAPL", "MSFT", "GOOGL", "NVDA", "SPY", "QQQ"]


def load_symbols_from_file(filepath: str) -> List[str]:
    """
    Load symbols from a text file (one symbol per line).

    Args:
        filepath: Path to symbols file

    Returns:
        List of stock ticker symbols
    """
    try:
        with open(filepath, "r") as f:
            symbols = [line.strip().upper() for line in f if line.strip()]
        return symbols
    except (FileNotFoundError, IOError, PermissionError) as e:
        logger.warning("Sembol dosyası okunamadı: %s - %s", filepath, e)
        return []


@_cache_data(ttl_seconds=CACHE_TTL_MARKET_INDEX)  # Standardized TTL
def _fetch_market_index(index_symbol: str) -> pd.DataFrame:
    """
    Fetch market index data (cached).

    Args:
        index_symbol: Index ticker (e.g., '^IXIC', 'XU100.IS')

    Returns:
        DataFrame with index OHLCV data
    """
    try:
        result = yf.download(index_symbol, period="1y", interval="1d", progress=False)
        if result is None or result.empty:
            logger.warning("Market index verisi alınamadı: %s", index_symbol)
            return pd.DataFrame()
        return result
    except ConnectionError as e:
        logger.error("Market index bağlantı hatası: %s - %s", index_symbol, e)
        return pd.DataFrame()
    except Exception as e:
        logger.error("Market index beklenmeyen hata: %s - %s", index_symbol, e)
        return pd.DataFrame()


def get_market_regime_status(symbols: List[str]) -> Dict[str, Any]:
    """
    Check global market index for trend and momentum.

    Analyzes the appropriate index (XU100 for Turkish stocks,
    NASDAQ for US stocks) to determine if market conditions
    are favorable for trading.

    Args:
        symbols: List of symbols being scanned (used to determine market)

    Returns:
        Dictionary with:
        - safe: bool - Whether market conditions are favorable
        - reason: str - Explanation of market status
    """
    # Determine index based on symbol types
    if any(s.endswith(".IS") for s in symbols[:5]):
        index_symbol = "XU100.IS"
    else:
        index_symbol = "^IXIC"  # NASDAQ Composite

    print(f"📊 Piyasa Analizi Yapılıyor: {index_symbol}")

    try:
        # Download enough data for EMA50
        df = _fetch_market_index(index_symbol)
        if df is None or df.empty:
            return {"safe": True, "reason": "Veri yok"}

        # Calculate EMA50
        df["ema50"] = df["Close"].ewm(span=50, adjust=False).mean()

        last_row = df.iloc[-1]
        close_val = float(last_row["Close"])
        open_val = float(last_row["Open"])
        ema_val = float(last_row["ema50"])

        # 1. Trend Filter
        if close_val < ema_val:
            return {
                "safe": False,
                "reason": f"Düşüş Trendi (Fiyat < EMA50). {index_symbol} @ {close_val:.2f} < {ema_val:.2f}",
            }

        # 2. Red Day Filter
        if close_val < open_val:
            return {
                "safe": False,
                "reason": f"Kırmızı Gün (Close < Open). {index_symbol} bugün satıcılı.",
            }

        return {"safe": True, "reason": "Piyasa Pozitif (Trend Yukarı + Yeşil Mum)"}

    except (KeyError, ValueError, IndexError) as e:
        logger.warning("Piyasa analizi hatası: %s", e)
        return {"safe": True, "reason": "Hata oluştu, varsayılan güvenli"}


def load_ticker_list(category: str = "us_large_cap") -> List[str]:
    """
    Load predefined ticker lists by category.

    Args:
        category: Category name:
            - 'us_large_cap': Major US stocks
            - 'us_tech': Tech-focused stocks
            - 'tr_bist30': Turkish BIST30 stocks
            - 'etf': Major ETFs

    Returns:
        List of stock ticker symbols
    """
    categories = {
        "us_large_cap": [
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "META",
            "NVDA",
            "TSLA",
            "BRK-B",
            "JPM",
            "JNJ",
            "V",
            "PG",
            "UNH",
            "HD",
            "MA",
            "DIS",
            "PYPL",
            "NFLX",
        ],
        "us_tech": [
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "META",
            "NVDA",
            "AMD",
            "INTC",
            "CRM",
            "ADBE",
            "ORCL",
            "CSCO",
            "IBM",
            "QCOM",
            "TXN",
            "AVGO",
        ],
        "tr_bist30": [
            "AKBNK.IS",
            "ARCLK.IS",
            "ASELS.IS",
            "BIMAS.IS",
            "EKGYO.IS",
            "EREGL.IS",
            "GARAN.IS",
            "HEKTS.IS",
            "KCHOL.IS",
            "KOZAL.IS",
            "KRDMD.IS",
            "MGROS.IS",
            "PETKM.IS",
            "PGSUS.IS",
            "SAHOL.IS",
            "SASA.IS",
            "SISE.IS",
            "TAVHL.IS",
            "TCELL.IS",
            "THYAO.IS",
            "TKFEN.IS",
            "TOASO.IS",
            "TUPRS.IS",
            "VESTL.IS",
            "YKBNK.IS",
        ],
        "etf": [
            "SPY",
            "QQQ",
            "IWM",
            "DIA",
            "VTI",
            "VOO",
            "VGT",
            "XLK",
            "XLF",
            "XLE",
            "XLV",
            "GLD",
            "SLV",
            "TLT",
            "HYG",
            "EEM",
        ],
    }

    return categories.get(category, categories["us_large_cap"])


def save_scan_results(
    df: pd.DataFrame, prefix: str = "shortlist", output_dir: str = "data/shortlists"
) -> str:
    """
    Save scan results to CSV file with timestamp.

    Args:
        df: DataFrame with scan results
        prefix: Filename prefix
        output_dir: Output directory path

    Returns:
        Path to saved CSV file
    """
    from datetime import datetime

    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    out_csv = os.path.join(output_dir, f"{prefix}_{ts}.csv")
    df.to_csv(out_csv, index=False)

    return out_csv
