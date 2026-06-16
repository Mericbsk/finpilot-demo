"""Data Fetching Module

Contains all external data retrieval functions.
Extracted from scanner.py for modularity and reusability.

Performance Features:
- Parallel multi-timeframe fetching with ThreadPoolExecutor
- Smart caching with configurable TTL
- Batch symbol fetching for efficiency
"""

import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any

import pandas as pd

try:
    import streamlit as st

    HAS_STREAMLIT = True
except ImportError:
    st = None  # type: ignore
    HAS_STREAMLIT = False

try:
    import yfinance as yf
except ImportError:  # pragma: no cover
    yf = None  # type: ignore

from .config import SETTINGS
from .indicators import add_indicators

# Configure module logger
logger = logging.getLogger(__name__)


# ============================================
# 🧠 Cache Configuration
# ============================================
# Market-aware TTL: 5 min during trading hours, 60 min outside.
# This avoids stale data during market hours while eliminating
# unnecessary yfinance calls on nights/weekends.


def _market_aware_ttl() -> int:
    """Return appropriate cache TTL based on current time (UTC).

    - 300s  during NYSE trading hours (Mon-Fri 13:30–20:00 UTC)
    - 3600s outside trading hours / weekends
    """
    now = datetime.utcnow()
    weekday = now.weekday()  # 0=Mon … 6=Sun
    if weekday >= 5:  # Weekend
        return 3600
    market_open_h, market_open_m = 13, 30  # 09:30 ET = 13:30 UTC
    market_close_h, market_close_m = 20, 0  # 16:00 ET = 20:00 UTC
    total_min = now.hour * 60 + now.minute
    open_min = market_open_h * 60 + market_open_m
    close_min = market_close_h * 60 + market_close_m
    if open_min <= total_min <= close_min:
        return 300  # 5 min — market open
    return 3600  # 60 min — pre/post market or overnight


CACHE_TTL_SECONDS = _market_aware_ttl()
CACHE_TTL_MARKET_INDEX = CACHE_TTL_SECONDS

# In-memory fallback cache for non-Streamlit usage
_memory_cache: dict[str, tuple] = {}


def _get_cache_key(symbol: str, interval: str, days: int) -> str:
    """Generate a unique cache key for data requests."""
    today = datetime.now().strftime("%Y-%m-%d")
    return f"{symbol}_{interval}_{days}_{today}"


def _cache_data(ttl_seconds: int = CACHE_TTL_SECONDS):
    """
    Decorator providing layered caching:

    1. Streamlit ``cache_data`` if available (UI process only).
    2. Process-shared Redis cache via ``core.cache.cache_manager`` when Redis
       is configured — DataFrames serialized via to_dict / from_records to
       stay JSON-safe (Sprint 4 S4-1).
    3. Per-process in-memory TTL cache as last resort.
    """

    def decorator(func):
        # Attempt to use shared CacheManager (covers both Redis L2 and
        # in-process LRU L1, with safe DataFrame serialization).
        cache_manager = None
        try:
            from core.cache import cache_manager as _cm

            cache_manager = _cm
        except Exception:  # noqa: BLE001
            cache_manager = None

        if HAS_STREAMLIT and st is not None:
            return st.cache_data(ttl=ttl_seconds, show_spinner=False)(func)

        def wrapper(*args, **kwargs):
            key = f"finpilot:ohlcv:{func.__name__}:{args}:{sorted(kwargs.items())}"
            now = datetime.now().timestamp()

            entry = _memory_cache.get(key)
            if entry is not None:
                cached_time, cached_result = entry
                if now - cached_time < ttl_seconds:
                    return cached_result

            shared_payload = None
            if cache_manager is not None:
                try:
                    shared_payload = cache_manager.get(key)
                except Exception:  # noqa: BLE001
                    shared_payload = None
            if isinstance(shared_payload, dict) and "records" in shared_payload:
                try:
                    df = pd.DataFrame(shared_payload["records"])
                    if "index" in shared_payload and shared_payload["index"]:
                        df.index = pd.to_datetime(shared_payload["index"])
                    _memory_cache[key] = (now, df)
                    return df
                except Exception:  # noqa: BLE001
                    pass

            result = func(*args, **kwargs)
            _memory_cache[key] = (now, result)

            if cache_manager is not None and isinstance(result, pd.DataFrame) and not result.empty:
                try:
                    payload = {
                        "records": result.reset_index(drop=False).to_dict(orient="records"),
                        "index": [str(ix) for ix in result.index.tolist()],
                    }
                    cache_manager.set(key, payload, ttl=ttl_seconds)
                except Exception:  # noqa: BLE001
                    pass

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

    # S4-4: yfinance rate limit (default 4 req/s, burst 8). Non-fatal: if
    # bucket times out we proceed anyway — the existing retry path will
    # absorb 429s.
    try:
        from core.rate_limiter import get_bucket

        rate = float(os.environ.get("YFINANCE_RATE", "4"))
        burst = float(os.environ.get("YFINANCE_BURST", "8"))
        get_bucket("yfinance", rate=rate, capacity=burst).wait(timeout=5.0)
    except Exception:  # noqa: BLE001
        pass

    try:
        tkr = yf.Ticker(symbol)

        # Pre-validate: yfinance raises NoneType errors for delisted/invalid tickers
        try:
            info = tkr.fast_info if hasattr(tkr, "fast_info") else None
            if info is not None and getattr(info, "last_price", None) is None:
                logger.warning(
                    "yfinance fast_info boş: %s — delisted veya geçersiz sembol olabilir", symbol
                )
        except Exception:
            pass  # fast_info check is best-effort

        try:
            df = tkr.history(
                period=yf_period,
                interval=yf_interval,
                auto_adjust=SETTINGS.get("auto_adjust", True),
                prepost=SETTINGS.get("prepost", False),
                actions=False,
                back_adjust=False,
            )
        except TypeError:
            # yfinance MultiIndex/NoneType bug — retry without auto_adjust
            logger.debug(
                "yfinance TypeError on first attempt for %s, retrying with auto_adjust=False",
                symbol,
            )
            try:
                df = tkr.history(
                    period=yf_period,
                    interval=yf_interval,
                    auto_adjust=False,
                    prepost=False,
                    actions=False,
                )
            except Exception:
                return pd.DataFrame()

        if df is None or df.empty:
            print(f"[WARN] Veri yok: {symbol} {interval} {days}d")
            return pd.DataFrame()

        # Guard: yfinance MultiIndex None-column bug (some symbols return MultiIndex
        # with a None second level, causing "NoneType is not subscriptable" downstream)
        if isinstance(df.columns, pd.MultiIndex):
            try:
                df.columns = df.columns.droplevel(1)
            except Exception:
                df = df.loc[:, [c for c in df.columns if c is not None and c != ""]]
        df = df.loc[:, [c for c in df.columns if c is not None]]

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
            logger.debug(
                "Timezone conversion skipped for %s",
                symbol if "symbol" in dir() else "?",
                exc_info=True,
            )

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
# NOTE: yfinance does not reliably support "4h" as a native interval.
# The 4h DataFrame is derived by resampling the 1h data (fetched with 100-day window)
# inside fetch_multi_timeframe(), saving one network round-trip per symbol.
DEFAULT_TIMEFRAMES: list[tuple[str, int]] = [
    ("15m", 10),  # 15-minute, 10 days
    ("1h", 100),  # 1-hour, 100 days (also used to build 4h via resample)
    ("1d", 400),  # Daily, 400 days
]


def _resample_4h(df_1h: pd.DataFrame) -> pd.DataFrame:
    """Derive a 4-hour OHLCV DataFrame from 1-hour data via resample.

    This avoids a separate yfinance network call for the 4h interval
    (which yfinance does not support reliably anyway).
    """
    if df_1h.empty:
        return pd.DataFrame()
    try:
        df = df_1h[["Open", "High", "Low", "Close", "Volume"]].copy()
        df4 = (
            df.resample("4h")
            .agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"})
            .dropna()
        )
        return df4
    except Exception:
        return pd.DataFrame()


def fetch_multi_timeframe(
    symbol: str,
    timeframes: list[tuple[str, int]] | None = None,
    with_indicators: bool = True,
    max_workers: int = 4,
) -> dict[str, pd.DataFrame]:
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

    results: dict[str, pd.DataFrame] = {}

    def _fetch_single(interval: str, days: int) -> tuple[str, pd.DataFrame]:
        """Fetch single timeframe with optional indicators."""
        if with_indicators:
            df = fetch_with_indicators(symbol, interval, days)
        else:
            df = fetch(symbol, interval, days)
        return interval, df

    # Parallel fetch (only real timeframes — 4h is derived from 1h below)
    real_timeframes = [(iv, d) for iv, d in timeframes if iv != "4h"]
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(_fetch_single, interval, days) for interval, days in real_timeframes
        ]

        for future in as_completed(futures):
            try:
                interval, df = future.result()
                results[interval] = df
            except Exception as e:
                logger.warning("Paralel fetch hatası: %s %s - %s", symbol, str(e), type(e).__name__)

    # Derive 4h from 1h to avoid an extra yfinance round-trip
    df_1h = results.get("1h", pd.DataFrame())
    df_4h_raw = _resample_4h(df_1h)
    if not df_4h_raw.empty:
        results["4h"] = add_indicators(df_4h_raw) if with_indicators else df_4h_raw
    else:
        results["4h"] = pd.DataFrame()

    return results


def fetch_symbols_batch(
    symbols: list[str],
    interval: str = "1d",
    days: int = 100,
    with_indicators: bool = True,
    max_workers: int = 8,
    use_alpaca: bool | None = None,
) -> dict[str, pd.DataFrame]:
    """Fetch OHLCV + indicators for multiple symbols.

    Uses Alpaca bulk-bars when available (single HTTP call per batch of up to
    1 000 symbols, ~20× faster than sequential yfinance).  Falls back to
    parallel yfinance ThreadPoolExecutor when Alpaca credentials are missing.

    Parameters
    ----------
    symbols : list[str]
        Tickers to fetch.
    interval : str
        FinPilot interval string (``"15m"``, ``"1h"``, ``"1d"`` …).
    days : int
        Look-back window in calendar days.
    with_indicators : bool
        Apply ``add_indicators()`` to each DataFrame.
    max_workers : int
        Thread count used only for the yfinance fallback path.
    use_alpaca : bool | None
        ``True`` forces Alpaca, ``False`` forces yfinance, ``None``
        auto-detects (Alpaca when env vars are present).
    """
    if not symbols:
        return {}

    # --- Auto-detect Alpaca availability ---
    if use_alpaca is None:
        use_alpaca = bool(os.environ.get("ALPACA_API_KEY"))

    results: dict[str, pd.DataFrame] = {}

    if use_alpaca:
        try:
            from drl.data_sources.alpaca_provider import fetch_bars_bulk

            logger.info(
                "fetch_symbols_batch: Alpaca bulk path (%d symbols, %s, %dd)",
                len(symbols),
                interval,
                days,
            )
            raw = fetch_bars_bulk(symbols, interval=interval, days=days)

            for sym, df in raw.items():
                if df.empty:
                    results[sym] = df
                    continue
                if with_indicators:
                    try:
                        df = add_indicators(df)
                    except Exception:
                        pass
                results[sym] = df

            # Fill missing symbols with empty frames
            for sym in symbols:
                if sym not in results:
                    results[sym] = pd.DataFrame()

            logger.info(
                "fetch_symbols_batch: Alpaca returned %d/%d non-empty",
                sum(1 for v in results.values() if not v.empty),
                len(symbols),
            )
            return results

        except Exception as exc:
            logger.warning("Alpaca bulk fetch failed (%s) — falling back to yfinance", exc)

    # --- yfinance fallback (original implementation) ---
    def _fetch_symbol(symbol: str) -> tuple[str, pd.DataFrame]:
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


def _prefetch_alpaca_bulk(
    symbols: list[str],
    timeframes: list[tuple[str, int]],
    with_indicators: bool,
) -> dict[str, dict[str, pd.DataFrame]] | None:
    """Try Alpaca bulk bars for all timeframes.  Returns None on failure.

    Issues one HTTP call per (interval, days) pair — O(timeframes) requests
    instead of O(symbols × timeframes), giving ~20× speedup for large lists.

    Uses BarSet.df directly to get properly-named columns (Open/High/Low/Close/Volume).
    The fetch_bars_bulk wrapper returns integer-indexed columns when the Alpaca SDK
    converts Pydantic Bar objects via pd.DataFrame(), so we bypass it here.
    """
    if not os.environ.get("ALPACA_API_KEY"):
        return None
    try:
        from datetime import UTC
        from datetime import timedelta as _timedelta

        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

        _TF_MAP: dict[str, Any] = {
            "15m": TimeFrame(15, TimeFrameUnit.Minute),
            "1h": TimeFrame.Hour,
            "4h": TimeFrame(4, TimeFrameUnit.Hour),
            "1d": TimeFrame.Day,
        }
        _COL_RENAME = {
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
            "vwap": "Vwap",
            "trade_count": "TradeCount",
        }

        api_key = os.environ["ALPACA_API_KEY"]
        secret_key = os.environ.get("ALPACA_SECRET_KEY", "")
        client = StockHistoricalDataClient(api_key, secret_key)

        result: dict[str, dict[str, pd.DataFrame]] = {s: {} for s in symbols}
        real_tfs = [(iv, d) for iv, d in timeframes if iv != "4h"]

        for interval, days in real_tfs:
            tf_obj = _TF_MAP.get(interval)
            if tf_obj is None:
                logger.warning("Alpaca: unknown interval %s", interval)
                continue

            end_dt = datetime.now(UTC)
            start_dt = end_dt - _timedelta(days=days)

            req = StockBarsRequest(
                symbol_or_symbols=symbols,
                timeframe=tf_obj,
                start=start_dt,
                end=end_dt,
                feed="iex",
                limit=10000,
            )

            try:
                bars = client.get_stock_bars(req)
                # BarSet.df returns MultiIndex (symbol, timestamp) with lowercase columns
                full_df = bars.df
            except Exception as exc:
                logger.warning("Alpaca bulk bars failed for %s/%dd: %s", interval, days, exc)
                return None  # Fall back entirely to yfinance

            for sym in symbols:
                try:
                    if isinstance(full_df.index, pd.MultiIndex):
                        lvl0 = full_df.index.get_level_values(0)
                        df = full_df.loc[sym].copy() if sym in lvl0 else pd.DataFrame()
                    else:
                        df = full_df.copy()

                    if not df.empty:
                        df = df.rename(columns=_COL_RENAME)
                        if isinstance(df.index, pd.DatetimeIndex) and df.index.tz is not None:
                            df.index = df.index.tz_convert(None)
                        if with_indicators:
                            try:
                                df = add_indicators(df)
                            except Exception:
                                pass
                    result[sym][interval] = df
                except KeyError:
                    result[sym][interval] = pd.DataFrame()

        # Derive 4h from 1h
        for sym in symbols:
            df_1h = result[sym].get("1h", pd.DataFrame())
            df_4h_raw = _resample_4h(df_1h)
            if not df_4h_raw.empty:
                result[sym]["4h"] = add_indicators(df_4h_raw) if with_indicators else df_4h_raw
            else:
                result[sym]["4h"] = pd.DataFrame()

        logger.info(
            "Alpaca bulk prefetch: %d symbols × %d timeframes complete",
            len(symbols),
            len(real_tfs) + 1,
        )
        return result
    except Exception as exc:
        logger.warning("Alpaca bulk prefetch error: %s — falling back to yfinance", exc)
        return None


def prefetch_symbols_multi_timeframe(
    symbols: list[str],
    timeframes: list[tuple[str, int]] | None = None,
    with_indicators: bool = True,
    max_workers: int = 10,
    progress_callback: Any | None = None,
) -> dict[str, dict[str, pd.DataFrame]]:
    """
    Prefetch all timeframe data for multiple symbols.

    Fast path: Alpaca bulk bars (1 HTTP call per timeframe, ~3-5s for 50 symbols).
    Fallback:  Parallel yfinance ThreadPoolExecutor (original implementation).

    Returns:
        Nested dictionary: {symbol: {interval: DataFrame}}
    """
    if timeframes is None:
        timeframes = DEFAULT_TIMEFRAMES

    total = len(symbols)

    # ── Fast path: Alpaca bulk ──────────────────────────────────────────────
    alpaca_result = _prefetch_alpaca_bulk(symbols, timeframes, with_indicators)
    if alpaca_result is not None:
        if progress_callback:
            try:
                progress_callback(total, total)
            except Exception:
                pass
        return alpaca_result

    # ── Fallback: parallel yfinance ─────────────────────────────────────────
    results: dict[str, dict[str, pd.DataFrame]] = {}
    completed = 0

    def _fetch_all_timeframes(symbol: str) -> tuple[str, dict[str, pd.DataFrame]]:
        data = fetch_multi_timeframe(
            symbol,
            timeframes=timeframes,
            with_indicators=with_indicators,
            max_workers=min(4, len(timeframes)),
        )
        return symbol, data

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_fetch_all_timeframes, symbol): symbol for symbol in symbols}

        for future in as_completed(futures, timeout=180):
            symbol = futures[future]
            try:
                _, data = future.result(timeout=30)
                results[symbol] = data
            except TimeoutError:
                logger.warning("Prefetch timeout: %s — atlanıyor", symbol)
                results[symbol] = {tf[0]: pd.DataFrame() for tf in timeframes}
            except Exception as e:
                logger.warning("Multi-timeframe prefetch hatası: %s - %s", symbol, e)
                results[symbol] = {tf[0]: pd.DataFrame() for tf in timeframes}

            completed += 1
            if progress_callback:
                try:
                    progress_callback(completed, total)
                except Exception:
                    logger.debug("Progress callback failed", exc_info=True)

    for sym in symbols:
        if sym not in results:
            logger.warning("Prefetch incomplete: %s — boş veri", sym)
            results[sym] = {tf[0]: pd.DataFrame() for tf in timeframes}

    return results


def load_symbols(
    tradable_only: bool = True,
    exchanges: list[str] | None = None,
    limit: int | None = None,
    universe: str | None = None,
    market_cap_min: int | None = None,
    market_cap_max: int | None = None,
) -> list[str]:
    """Load tradable US equity symbols from the local DB.

    Falls back to a minimal hardcoded list when the table doesn't exist yet
    (i.e. before ``scripts/sync_symbols.py`` has been run).

    Parameters
    ----------
    tradable_only:
        When True (default) only returns symbols Alpaca marks as tradable.
    exchanges:
        Optional filter, e.g. ``["NASDAQ", "NYSE"]``.  None = all.
    limit:
        Cap the number of symbols returned (useful for quick dev runs).
    universe:
        Named universe from the ``symbol_lists`` table, e.g.
        ``"preset_1500"``, ``"iwm_300m"``, ``"combined_2026"``.
        When set, the query joins against that list instead of scanning
        the full symbols table.  If the list doesn't exist the function
        falls back to the regular symbols table query.
    market_cap_min:
        Include only symbols with ``market_cap >= market_cap_min``.
        Symbols with NULL market_cap are excluded when this is set.
    market_cap_max:
        Include only symbols with ``market_cap <= market_cap_max``.
        Symbols with NULL market_cap are excluded when this is set.
    """
    try:
        import sqlite3

        from core.config import DB_PATH

        with sqlite3.connect(str(DB_PATH)) as conn:
            # Confirm symbols table exists
            if not conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='symbols'"
            ).fetchone():
                raise RuntimeError("symbols table not found")

            clauses: list[str] = []
            params: list[object] = []

            # --- universe (symbol_lists join) ---
            use_universe = False
            if universe:
                lists_exist = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='symbol_lists'"
                ).fetchone()
                list_count = (
                    conn.execute(
                        "SELECT COUNT(*) FROM symbol_lists WHERE list_name=?", (universe,)
                    ).fetchone()[0]
                    if lists_exist
                    else 0
                )
                if list_count > 0:
                    use_universe = True
                else:
                    logger.warning(
                        "load_symbols: universe '%s' not found in symbol_lists — using full table",
                        universe,
                    )

            if tradable_only:
                clauses.append("s.tradable = 1")
            if exchanges:
                placeholders = ",".join("?" * len(exchanges))
                clauses.append(f"s.exchange IN ({placeholders})")
                params.extend(exchanges)
            if market_cap_min is not None:
                clauses.append("s.market_cap >= ?")
                params.append(market_cap_min)
            if market_cap_max is not None:
                clauses.append("s.market_cap <= ?")
                params.append(market_cap_max)
            if market_cap_min is not None or market_cap_max is not None:
                clauses.append("s.market_cap IS NOT NULL")

            where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

            if use_universe:
                # Join to symbol_lists to restrict to the named universe
                # user input is parameterised (universe, *params); clauses
                # contain only static strings — safe against injection.
                extra = ("AND " + " AND ".join(clauses) + " ") if clauses else ""
                sql = f"SELECT s.ticker FROM symbols s JOIN symbol_lists sl ON sl.ticker = s.ticker WHERE sl.list_name = ? {extra}ORDER BY s.ticker"  # noqa: S608
                query_params: list[object] = [universe, *params]
            else:
                sql = f"SELECT s.ticker FROM symbols s {where} ORDER BY s.ticker"  # noqa: S608
                query_params = params  # type: ignore[assignment]

            if limit:
                sql += f" LIMIT {int(limit)}"  # noqa: S608

            rows = conn.execute(sql, query_params).fetchall()

        symbols = [r[0] for r in rows]
        logger.info(
            "load_symbols: %d symbols (universe=%s, tradable=%s, cap=%s–%s)",
            len(symbols),
            universe,
            tradable_only,
            market_cap_min,
            market_cap_max,
        )
        return symbols

    except Exception as exc:
        logger.warning("load_symbols DB fallback: %s — returning hardcoded list", exc)
        return [
            "AAPL",
            "MSFT",
            "GOOGL",
            "NVDA",
            "AMZN",
            "META",
            "TSLA",
            "SPY",
            "QQQ",
            "NVDA",
            "AMD",
            "INTC",
        ]


def load_symbols_from_file(filepath: str) -> list[str]:
    """
    Load symbols from a text file (one symbol per line).

    Args:
        filepath: Path to symbols file

    Returns:
        List of stock ticker symbols
    """
    try:
        with open(filepath) as f:
            symbols = [line.strip().upper() for line in f if line.strip()]
        return symbols
    except (OSError, FileNotFoundError, PermissionError) as e:
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


def get_market_regime_status(symbols: list[str]) -> dict[str, Any]:
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


def load_ticker_list(category: str = "us_large_cap") -> list[str]:
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
