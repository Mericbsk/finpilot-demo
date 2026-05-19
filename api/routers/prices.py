"""GET /api/v1/prices/stream/{symbol} — Server-Sent Events real-time price feed.
GET /api/v1/quotes?symbols=AAPL,MSFT   — Batch real-time quote endpoint.
"""

from __future__ import annotations

import asyncio
import json
import logging
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


def _fetch_price_sync(symbol: str) -> dict:
    import yfinance as yf

    ticker = yf.Ticker(symbol)
    fi = ticker.fast_info
    try:
        info = ticker.info
        market_state = info.get("marketState", "REGULAR")
        reg_price = float(info.get("regularMarketPrice") or fi.last_price or 0)
        pre_price = float(info.get("preMarketPrice") or 0)
        post_price = float(info.get("postMarketPrice") or 0)
        if market_state == "PRE" and pre_price > 0:
            price = pre_price
        elif market_state in ("POST", "POSTPOST") and post_price > 0:
            price = post_price
        else:
            price = reg_price
    except Exception:
        price = float(fi.last_price or 0)

    prev = float(fi.previous_close or price)
    change_pct = ((price - prev) / prev * 100) if prev else 0.0
    return {
        "symbol": symbol,
        "price": round(price, 4),
        "change_pct": round(change_pct, 2),
        "ts": datetime.now(UTC).isoformat(),
    }


def _fetch_batch_sync(symbols: list[str]) -> dict[str, dict]:
    """Fetch batch quotes via yfinance.Tickers.

    Uses pre-market / after-hours price when market is not in regular session,
    so returned price always reflects the most recent tradeable value.
    """
    import yfinance as yf

    result: dict[str, dict] = {}
    try:
        tickers = yf.Tickers(" ".join(symbols))
        for sym in symbols:
            try:
                ticker = tickers.tickers[sym]
                fi = ticker.fast_info

                # fast_info.last_price == regularMarketPrice (yesterday's close
                # during pre/post market).  Use .info to get the correct current
                # session price when market is not in REGULAR state.
                try:
                    info = ticker.info
                    market_state = info.get("marketState", "REGULAR")
                    reg_price = float(info.get("regularMarketPrice") or fi.last_price or 0)
                    pre_price = float(info.get("preMarketPrice") or 0)
                    post_price = float(info.get("postMarketPrice") or 0)

                    if market_state == "PRE" and pre_price > 0:
                        price = pre_price
                    elif market_state in ("POST", "POSTPOST") and post_price > 0:
                        price = post_price
                    else:
                        price = reg_price
                except Exception:
                    price = float(fi.last_price or 0)

                prev = float(fi.previous_close or price)
                high = float(fi.day_high or 0)
                low = float(fi.day_low or 0)
                volume = int(fi.three_month_average_volume or 0)
                change = round(((price - prev) / prev * 100) if prev else 0.0, 2)
                result[sym] = {
                    "price": round(price, 2),
                    "change": change,
                    "prevClose": round(prev, 2),
                    "high": round(high, 2),
                    "low": round(low, 2),
                    "volume": volume,
                    "marketState": market_state if "market_state" in dir() else "REGULAR",
                }
            except Exception as e:
                logger.debug("Quote failed for %s: %s", sym, e)
    except Exception as e:
        logger.warning("Batch quote fetch failed: %s", e)
    return result


@router.get("/quotes")
async def get_quotes(
    symbols: str = Query(..., description="Comma-separated ticker symbols"),
) -> JSONResponse:
    """Return real-time quotes for a batch of symbols.

    Response: {SYM: {price, change, prevClose, high, low, volume}, ...}
    Cached for 30 seconds per symbol.
    """
    raw = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    valid = [s for s in raw if _SYMBOL_RE.match(s)][:200]
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
        # Fetch in batches of 50 to avoid yfinance overhead
        for i in range(0, len(to_fetch), 50):
            batch = to_fetch[i : i + 50]
            fresh = await loop.run_in_executor(None, _fetch_batch_sync, batch)
            for sym, data in fresh.items():
                _QUOTE_CACHE[sym] = {**data, "_ts": now}
                result[sym] = data

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
