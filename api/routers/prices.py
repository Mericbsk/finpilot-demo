"""GET /api/v1/prices/stream/{symbol} — Server-Sent Events real-time price feed."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import UTC, datetime

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["prices"])

_SYMBOL_RE = re.compile(r"^[A-Z0-9.]{1,10}$")
_POLL_INTERVAL = 3.0
_MAX_DURATION = 600  # 10 min max per connection


def _fetch_price_sync(symbol: str) -> dict:
    import yfinance as yf

    info = yf.Ticker(symbol).fast_info
    price = float(info.last_price or 0)
    prev = float(info.previous_close or price)
    change_pct = ((price - prev) / prev * 100) if prev else 0.0
    return {
        "symbol": symbol,
        "price": round(price, 4),
        "change_pct": round(change_pct, 2),
        "ts": datetime.now(UTC).isoformat(),
    }


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
