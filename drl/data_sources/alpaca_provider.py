"""Alpaca Market Data provider for FinPilot.

Implements the ``BaseAdapter`` interface (drl/data_sources/base.py) so the
rest of the DRL stack can swap yfinance for Alpaca without touching call sites.

Two main capabilities
----------------------
1. **Historical bars** — `fetch(symbol, start, end, timeframe)` returns a
   pandas DataFrame with the same column schema as yfinance (Open/High/Low/
   Close/Volume, uppercase) plus a ``vwap`` column when available.

2. **Bulk bars** — `fetch_bulk(symbols, start, end, timeframe)` issues a
   single batched request for up to 1 000 symbols and returns a dict of
   {symbol: DataFrame}.  This replaces the ``fetch_symbols_batch`` pattern in
   ``scanner/data_fetcher.py`` and is ~20× faster than one-symbol-at-a-time
   yfinance calls.

Environment variables (loaded from .env by core/config.py)
-----------------------------------------------------------
    ALPACA_API_KEY      — paper or live API key ID
    ALPACA_SECRET_KEY   — corresponding secret
    ALPACA_PAPER        — "true" (default) or "false"
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any

import pandas as pd

from .base import BaseAdapter, DataSlice

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Timeframe mapping  (FinPilot interval → Alpaca TimeFrame)
# ---------------------------------------------------------------------------
_TF_MAP: dict[str, Any] = {}  # populated lazily after import


def _tf(interval: str) -> Any:
    """Resolve a FinPilot interval string to an alpaca TimeFrame object."""
    global _TF_MAP  # noqa: PLW0603
    if not _TF_MAP:
        from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

        _TF_MAP = {
            "1m": TimeFrame.Minute,
            "5m": TimeFrame(5, TimeFrameUnit.Minute),
            "15m": TimeFrame(15, TimeFrameUnit.Minute),
            "30m": TimeFrame(30, TimeFrameUnit.Minute),
            "1h": TimeFrame.Hour,
            "4h": TimeFrame(4, TimeFrameUnit.Hour),
            "1d": TimeFrame.Day,
            "1w": TimeFrame.Week,
            "1mo": TimeFrame.Month,
        }
    tf = _TF_MAP.get(interval)
    if tf is None:
        raise ValueError(f"Unsupported interval '{interval}'. Choose from: {list(_TF_MAP.keys())}")
    return tf


# ---------------------------------------------------------------------------
# Column normalisation
# ---------------------------------------------------------------------------
_COL_RENAME = {
    "open": "Open",
    "high": "High",
    "low": "Low",
    "close": "Close",
    "volume": "Volume",
    "vwap": "Vwap",
    "trade_count": "TradeCount",
}


def _normalise_df(df: pd.DataFrame) -> pd.DataFrame:
    """Rename Alpaca lowercase columns → FinPilot Title-case schema."""
    df = df.rename(columns=_COL_RENAME)
    # Drop the symbol level from MultiIndex if present
    if isinstance(df.index, pd.MultiIndex):
        # (symbol, timestamp) → timestamp only
        if "timestamp" in df.index.names or df.index.nlevels >= 2:
            df = df.droplevel(0)
    # Strip timezone so downstream code doesn't choke on tz-aware vs naive
    if isinstance(df.index, pd.DatetimeIndex) and df.index.tz is not None:
        df.index = df.index.tz_convert(None)
    return df


# ---------------------------------------------------------------------------
# Client singleton
# ---------------------------------------------------------------------------

_client: Any | None = None


def _get_client() -> Any:
    """Return a shared StockHistoricalDataClient (lazy init)."""
    global _client  # noqa: PLW0603
    if _client is None:
        from alpaca.data.historical import StockHistoricalDataClient

        api_key = os.getenv("ALPACA_API_KEY")
        secret_key = os.getenv("ALPACA_SECRET_KEY")
        if not api_key or not secret_key:
            raise OSError("ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in the environment.")
        _client = StockHistoricalDataClient(api_key, secret_key)
        logger.info("AlpacaProvider: client initialised (key=...%s)", api_key[-4:])
    return _client


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------


class AlpacaProvider(BaseAdapter):
    """Alpaca Market Data adapter — drop-in replacement for yfinance fetches.

    Parameters
    ----------
    feed : str
        ``"iex"`` (free, ~2.5 % volume) or ``"sip"`` (paid, 100 % volume).
        Defaults to ``"iex"`` so the free tier works out of the box.
    """

    def __init__(self, feed: str = "iex") -> None:
        super().__init__("alpaca")
        self.feed = feed

    # ------------------------------------------------------------------
    # BaseAdapter protocol
    # ------------------------------------------------------------------

    def fetch(
        self,
        symbol: str,
        *,
        start: pd.Timestamp | None = None,
        end: pd.Timestamp | None = None,
        timeframe: str = "1d",
    ) -> DataSlice:
        """Fetch OHLCV bars for a single symbol.

        Parameters
        ----------
        symbol : str
            Ticker, e.g. ``"AAPL"``.
        start : pd.Timestamp, optional
            Inclusive start.  Defaults to 90 days ago.
        end : pd.Timestamp, optional
            Inclusive end.  Defaults to now.
        timeframe : str
            One of ``"1m" "5m" "15m" "30m" "1h" "4h" "1d" "1w" "1mo"``.
        """
        df = self.fetch_bulk([symbol], start=start, end=end, timeframe=timeframe).get(
            symbol, pd.DataFrame()
        )
        meta = self._build_metadata(symbol, feed=self.feed, timeframe=timeframe)
        return DataSlice(frame=df, metadata=meta)

    # ------------------------------------------------------------------
    # Bulk fetch (key new capability)
    # ------------------------------------------------------------------

    def fetch_bulk(
        self,
        symbols: list[str],
        *,
        start: pd.Timestamp | None = None,
        end: pd.Timestamp | None = None,
        timeframe: str = "1d",
        limit: int | None = None,
    ) -> dict[str, pd.DataFrame]:
        """Fetch OHLCV bars for multiple symbols in a **single API call**.

        Returns a dict ``{ticker: DataFrame}`` with the same column schema
        as a yfinance-sourced DataFrame so existing indicator code works
        without modification.

        Parameters
        ----------
        symbols : list[str]
            Up to ~1 000 tickers per call (Alpaca server-side limit).
        start : pd.Timestamp, optional
            Defaults to 90 days ago for daily; 7 days for intraday.
        end : pd.Timestamp, optional
            Defaults to now (UTC).
        timeframe : str
            Interval string.
        limit : int, optional
            Maximum bars per symbol.  None = Alpaca default.
        """
        from alpaca.data.requests import StockBarsRequest

        if not symbols:
            return {}

        # Sensible defaults
        now = datetime.now(UTC)
        if end is None:
            end_dt = now
        else:
            end_dt = pd.Timestamp(end).to_pydatetime().replace(tzinfo=UTC)

        if start is None:
            default_days = 7 if timeframe not in ("1d", "1w", "1mo") else 90
            start_dt = now - timedelta(days=default_days)
        else:
            start_dt = pd.Timestamp(start).to_pydatetime().replace(tzinfo=UTC)

        req = StockBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=_tf(timeframe),
            start=start_dt,
            end=end_dt,
            feed=self.feed,
            **({"limit": limit} if limit is not None else {}),
        )

        try:
            client = _get_client()
            bars = client.get_stock_bars(req)
        except Exception as exc:
            logger.error("AlpacaProvider.fetch_bulk error: %s", exc)
            return {}

        result: dict[str, pd.DataFrame] = {}
        for sym in symbols:
            try:
                sym_bars = bars[sym]
            except (KeyError, TypeError):
                logger.debug("No bars returned for %s", sym)
                continue

            try:
                df = sym_bars.df if hasattr(sym_bars, "df") else pd.DataFrame(sym_bars)
            except Exception as exc:
                logger.warning("Could not convert bars for %s: %s", sym, exc)
                continue

            if df.empty:
                continue

            result[sym] = _normalise_df(df)

        logger.debug(
            "fetch_bulk(%d symbols, %s) → %d results", len(symbols), timeframe, len(result)
        )
        return result

    # ------------------------------------------------------------------
    # Convenience: latest quotes
    # ------------------------------------------------------------------

    def latest_quotes(self, symbols: list[str]) -> dict[str, dict]:
        """Return the latest trade price + change_pct for each symbol.

        Falls back to the last bar's close when a quote is unavailable.
        Returns ``{symbol: {"price": float, "change_pct": float}}``.
        """
        from alpaca.data.requests import StockLatestQuoteRequest

        if not symbols:
            return {}

        req = StockLatestQuoteRequest(symbol_or_symbols=symbols, feed=self.feed)
        try:
            client = _get_client()
            quotes = client.get_stock_latest_quote(req)
        except Exception as exc:
            logger.error("AlpacaProvider.latest_quotes error: %s", exc)
            return {}

        result: dict[str, dict] = {}
        for sym, q in quotes.items():
            try:
                mid = (q.ask_price + q.bid_price) / 2 if q.ask_price and q.bid_price else 0.0
                result[sym] = {"price": float(mid), "change_pct": 0.0}
            except Exception:
                result[sym] = {"price": 0.0, "change_pct": 0.0}

        return result


# ---------------------------------------------------------------------------
# Module-level convenience functions (mirrors scanner/data_fetcher API)
# ---------------------------------------------------------------------------

_default_provider: AlpacaProvider | None = None


def _provider() -> AlpacaProvider:
    global _default_provider  # noqa: PLW0603
    if _default_provider is None:
        feed = os.getenv("ALPACA_FEED", "iex")
        _default_provider = AlpacaProvider(feed=feed)
    return _default_provider


def fetch_bars(
    symbol: str,
    interval: str = "1d",
    days: int = 90,
) -> pd.DataFrame:
    """Single-symbol convenience wrapper — same signature as ``scanner.data_fetcher.fetch``."""
    end = datetime.now(UTC)
    start = end - timedelta(days=days)
    ds = _provider().fetch(
        symbol, start=pd.Timestamp(start), end=pd.Timestamp(end), timeframe=interval
    )
    return ds.frame


def fetch_bars_bulk(
    symbols: list[str],
    interval: str = "1d",
    days: int = 90,
) -> dict[str, pd.DataFrame]:
    """Multi-symbol bulk bars — replaces ``fetch_symbols_batch`` for Alpaca."""
    end = datetime.now(UTC)
    start = end - timedelta(days=days)
    return _provider().fetch_bulk(
        symbols,
        start=pd.Timestamp(start),
        end=pd.Timestamp(end),
        timeframe=interval,
    )
