"""GET /api/v1/prices/stream/{symbol} — Server-Sent Events real-time price feed.
GET /api/v1/quotes?symbols=AAPL,MSFT   — Batch real-time quote endpoint.

Quote fetch strategy (fastest first):
  1. Alpaca StockLatestTrade  — ~300 ms for 30 symbols (requires ALPACA_API_KEY)
  2. yf.download fallback     — ~3-8 s (no key needed)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from datetime import UTC, datetime

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["prices"])

_SYMBOL_RE = re.compile(r"^[A-Z0-9.]{1,10}$")
_POLL_INTERVAL = 3.0
_MAX_DURATION = 600  # 10 min max per connection

# ── In-process quote cache (30 s TTL) ────────────────────────────────────────
import time as _time

_QUOTE_CACHE: dict[str, dict] = {}
_QUOTE_TTL = 30  # seconds

# ── Alpaca client singleton ───────────────────────────────────────────────────
_alpaca_client = None
_alpaca_available: bool | None = None  # None = not yet checked


def _get_alpaca_client():
    """Return shared StockHistoricalDataClient or None if keys not set."""
    global _alpaca_client, _alpaca_available  # noqa: PLW0603
    if _alpaca_available is False:
        return None
    if _alpaca_client is not None:
        return _alpaca_client
    try:
        from alpaca.data.historical import StockHistoricalDataClient

        api_key = os.getenv("ALPACA_API_KEY")
        secret = os.getenv("ALPACA_SECRET_KEY")
        if not api_key or not secret:
            _alpaca_available = False
            return None
        _alpaca_client = StockHistoricalDataClient(api_key, secret)
        _alpaca_available = True
        logger.info("quotes: Alpaca client ready (key=...%s)", api_key[-4:])
        return _alpaca_client
    except Exception as exc:
        logger.warning("quotes: Alpaca SDK unavailable — %s", exc)
        _alpaca_available = False
        return None


def _fetch_price_sync(symbol: str) -> dict:
    """Single-symbol price via Alpaca latest trade, fallback to yfinance."""
    batch = _fetch_batch_sync([symbol])
    if symbol in batch:
        d = batch[symbol]
        return {
            "symbol": symbol,
            "price": d["price"],
            "change_pct": d["change"],
            "ts": datetime.now(UTC).isoformat(),
        }
    return {"symbol": symbol, "price": 0.0, "change_pct": 0.0, "ts": datetime.now(UTC).isoformat()}


def _fetch_batch_alpaca(symbols: list[str]) -> dict[str, dict]:
    """Fetch latest trade price from Alpaca (~300 ms for 30 symbols)."""
    client = _get_alpaca_client()
    if client is None:
        return {}
    try:
        from alpaca.data.requests import StockLatestBarRequest, StockLatestTradeRequest

        # Get latest trade (real-time price) + latest bar (OHLCV)
        trade_req = StockLatestTradeRequest(symbol_or_symbols=symbols)
        bar_req = StockLatestBarRequest(symbol_or_symbols=symbols)

        trades = client.get_stock_latest_trade(trade_req)
        bars = client.get_stock_latest_bar(bar_req)

        result: dict[str, dict] = {}
        for sym in symbols:
            try:
                trade = trades.get(sym)
                bar = bars.get(sym)
                if trade is None and bar is None:
                    continue

                price = float(trade.price) if trade else (float(bar.close) if bar else 0.0)
                prev = float(bar.vwap) if bar and bar.vwap else price  # approximation
                # Use bar.open as prev-close proxy if vwap not useful
                if bar:
                    # prev close ≈ open - (close - open) reversed; use open as anchor
                    prev = float(bar.open) if bar.open else price

                high = float(bar.high) if bar else price
                low = float(bar.low) if bar else price
                volume = int(bar.volume) if bar else 0
                change = round(((price - prev) / prev * 100) if prev else 0.0, 2)

                result[sym] = {
                    "price": round(price, 2),
                    "change": change,
                    "prevClose": round(prev, 2),
                    "high": round(high, 2),
                    "low": round(low, 2),
                    "volume": volume,
                    "marketState": "REGULAR",
                }
            except Exception as e:
                logger.debug("Alpaca quote parse failed for %s: %s", sym, e)
        return result
    except Exception as exc:
        logger.warning("Alpaca batch quote failed (%s) — will fallback to yfinance", exc)
        return {}


def _fetch_batch_yfinance(symbols: list[str]) -> dict[str, dict]:
    """Fetch batch quotes using yf.download — single bulk HTTP request (~3-8s for 30 symbols)."""
    import yfinance as yf

    result: dict[str, dict] = {}
    try:
        raw = yf.download(
            symbols,
            period="2d",
            interval="1d",
            auto_adjust=True,
            progress=False,
            group_by="ticker",
            threads=False,
        )
        if raw is None or raw.empty:
            return result

        is_single = len(symbols) == 1

        for sym in symbols:
            try:
                sym_df = raw if is_single else raw[sym]
                sym_df = sym_df.dropna(how="all")
                if sym_df.empty or "Close" not in sym_df.columns:
                    continue

                price = float(sym_df["Close"].iloc[-1])
                prev = float(sym_df["Close"].iloc[-2]) if len(sym_df) >= 2 else price
                high = float(sym_df["High"].iloc[-1]) if "High" in sym_df.columns else price
                low = float(sym_df["Low"].iloc[-1]) if "Low" in sym_df.columns else price
                volume = int(sym_df["Volume"].iloc[-1]) if "Volume" in sym_df.columns else 0
                change = round(((price - prev) / prev * 100) if prev else 0.0, 2)
                result[sym] = {
                    "price": round(price, 2),
                    "change": change,
                    "prevClose": round(prev, 2),
                    "high": round(high, 2),
                    "low": round(low, 2),
                    "volume": volume,
                    "marketState": "REGULAR",
                }
            except Exception as e:
                logger.debug("yfinance quote parse failed for %s: %s", sym, e)
    except Exception as e:
        logger.warning("yfinance batch download failed: %s", e)
    return result


def _fetch_batch_sync(symbols: list[str]) -> dict[str, dict]:
    """Fetch batch quotes: Alpaca first (~300 ms), yfinance fallback (~5 s)."""
    # Try Alpaca (fast path)
    result = _fetch_batch_alpaca(symbols)
    if result:
        missing = [s for s in symbols if s not in result]
        if missing:
            # Fill gaps with yfinance for any symbols Alpaca missed
            yf_result = _fetch_batch_yfinance(missing)
            result.update(yf_result)
        return result
    # Full fallback to yfinance
    return _fetch_batch_yfinance(symbols)


@router.get("/quotes")
async def get_quotes(
    symbols: str = Query(..., description="Comma-separated ticker symbols"),
) -> JSONResponse:
    """Return real-time quotes for a batch of symbols.

    Response: {SYM: {price, change, prevClose, high, low, volume}, ...}
    Cached for 30 seconds per symbol.
    """
    raw = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    # Hard limit: max 30 symbols per request to prevent proxy timeout
    valid = [s for s in raw if _SYMBOL_RE.match(s)][:30]
    if not valid:
        return JSONResponse({})

    now = _time.monotonic()
    result: dict[str, dict] = {}
    to_fetch: list[str] = []

    for sym in valid:
        cached = _QUOTE_CACHE.get(sym)
        if cached and now - cached["_ts"] < _QUOTE_TTL:
            result[sym] = {k: v for k, v in cached.items() if k != "_ts"}
        else:
            to_fetch.append(sym)

    if to_fetch:
        loop = asyncio.get_event_loop()
        # Single batch (max 30 symbols) — fast_info avoids per-symbol HTTP calls
        try:
            fresh = await asyncio.wait_for(
                loop.run_in_executor(None, _fetch_batch_sync, to_fetch),
                timeout=15.0,
            )
            for sym, data in fresh.items():
                _QUOTE_CACHE[sym] = {**data, "_ts": now}
                result[sym] = data
        except TimeoutError:
            logger.warning("quotes: batch fetch timed out for %d symbols", len(to_fetch))

    return JSONResponse(result)


@router.get("/prices/stream/{symbol}")
async def stream_price(symbol: str, request: Request) -> StreamingResponse:
    """Stream live price updates as Server-Sent Events every 3 seconds.

    Connect via EventSource('/py-api/prices/stream/AAPL').
    Emits: {"symbol", "price", "change_pct", "ts"} every ~3s.
    Max connection duration: 10 minutes (client should reconnect).
    """
    if not _SYMBOL_RE.match(symbol):

        async def _err_gen():
            yield f"data: {json.dumps({'error': 'invalid symbol'})}\n\n"

        return StreamingResponse(_err_gen(), media_type="text/event-stream")

    async def event_generator():
        loop = asyncio.get_event_loop()
        elapsed = 0.0
        while elapsed < _MAX_DURATION:
            if await request.is_disconnected():
                logger.debug("SSE client disconnected: %s", symbol)
                break
            try:
                data = await loop.run_in_executor(None, _fetch_price_sync, symbol)
                yield f"data: {json.dumps(data)}\n\n"
            except Exception as exc:
                logger.warning("Price fetch failed for %s: %s", symbol, exc)
                yield f"data: {json.dumps({'error': str(exc)[:120]})}\n\n"
            await asyncio.sleep(_POLL_INTERVAL)
            elapsed += _POLL_INTERVAL

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
