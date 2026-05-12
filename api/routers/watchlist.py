"""Watchlist — persist scanner signals and track their live status.

Endpoints
---------
POST   /watchlist          — add one item (from a scanner result)
POST   /watchlist/bulk     — add multiple items at once
GET    /watchlist          — return all items enriched with current prices
DELETE /watchlist/{symbol} — remove one item
DELETE /watchlist/clear    — remove all items
"""

from __future__ import annotations

import json
import logging
from asyncio import get_running_loop
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["watchlist"])
logger = logging.getLogger(__name__)

_WATCHLIST_FILE = Path("data/watchlist.json")
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="watchlist")

# ─── Models ──────────────────────────────────────────────────────────────────

class WatchlistAddRequest(BaseModel):
    symbol: str = Field(..., max_length=12)
    signal: str = Field("—", max_length=10)
    entry_price: float = Field(0.0)
    stop_loss: float = Field(0.0)
    take_profit: float = Field(0.0)
    score: float = Field(0.0)
    regime: str = Field("", max_length=20)
    sentiment: str = Field("", max_length=20)
    risk_reward: float = Field(0.0)
    reason: str = Field("", max_length=1000)
    explanation: str = Field("", max_length=2000)


class WatchlistBulkRequest(BaseModel):
    items: list[WatchlistAddRequest] = Field(..., max_length=300)


# ─── Storage helpers ─────────────────────────────────────────────────────────

def _load() -> list[dict]:
    if not _WATCHLIST_FILE.exists():
        return []
    try:
        data = json.loads(_WATCHLIST_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(items: list[dict]) -> None:
    _WATCHLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    _WATCHLIST_FILE.write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _upsert(items: list[dict], entry: dict) -> list[dict]:
    """Replace existing entry for same symbol, or append."""
    symbol = entry["symbol"]
    items = [i for i in items if i.get("symbol") != symbol]
    items.append(entry)
    return items


# ─── Price fetcher ────────────────────────────────────────────────────────────

def _fetch_prices_sync(symbols: list[str]) -> dict[str, dict]:
    """Return {symbol: {price, change_pct}} for all symbols in one yfinance call."""
    if not symbols:
        return {}
    try:
        import yfinance as yf

        tickers = yf.Tickers(" ".join(symbols))
        out: dict[str, dict] = {}
        for sym in symbols:
            try:
                info = tickers.tickers[sym].fast_info
                price = float(info.last_price or 0)
                prev = float(info.previous_close or price)
                change = ((price - prev) / prev * 100) if prev else 0.0
                out[sym] = {"price": round(price, 4), "change_pct": round(change, 2)}
            except Exception:
                out[sym] = {"price": 0.0, "change_pct": 0.0}
        return out
    except Exception as exc:
        logger.warning("Price fetch failed: %s", exc)
        return {s: {"price": 0.0, "change_pct": 0.0} for s in symbols}


def _compute_status(item: dict, current_price: float) -> str:
    """Determine signal status based on current price vs stop/TP."""
    signal = item.get("signal", "—")
    stop = item.get("stop_loss", 0.0) or 0.0
    tp = item.get("take_profit", 0.0) or 0.0
    entry = item.get("entry_price", 0.0) or 0.0

    if current_price <= 0 or entry <= 0:
        return "Pending"

    is_long = signal in ("BUY", "HOLD") or signal == "—"

    if is_long:
        if stop > 0 and current_price <= stop:
            return "Stop Hit"
        if tp > 0 and current_price >= tp:
            return "TP Hit"
        if current_price > entry:
            return "On Track"
        return "Watching"
    else:  # SHORT / SELL
        if stop > 0 and current_price >= stop:
            return "Stop Hit"
        if tp > 0 and current_price <= tp:
            return "TP Hit"
        if current_price < entry:
            return "On Track"
        return "Watching"


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/watchlist", status_code=201)
def add_to_watchlist(req: WatchlistAddRequest):
    """Add or update one symbol in the watchlist."""
    entry = req.model_dump()
    entry["symbol"] = entry["symbol"].upper()
    entry["added_at"] = datetime.now(UTC).isoformat()

    items = _load()
    items = _upsert(items, entry)
    _save(items)
    logger.info("Watchlist add: %s (%s)", entry["symbol"], entry["signal"])
    return {"ok": True, "symbol": entry["symbol"], "count": len(items)}


@router.post("/watchlist/bulk", status_code=201)
def bulk_add_to_watchlist(req: WatchlistBulkRequest):
    """Add or update multiple symbols in one call."""
    items = _load()
    added = 0
    for item_req in req.items:
        entry = item_req.model_dump()
        entry["symbol"] = entry["symbol"].upper()
        entry["added_at"] = datetime.now(UTC).isoformat()
        items = _upsert(items, entry)
        added += 1
    _save(items)
    logger.info("Watchlist bulk add: %d symbols", added)
    return {"ok": True, "added": added, "count": len(items)}


@router.get("/watchlist")
async def get_watchlist():
    """Return all watchlist items enriched with live prices and status."""
    items = _load()
    if not items:
        return {"items": [], "count": 0, "refreshed_at": datetime.now(UTC).isoformat()}

    symbols = [i["symbol"] for i in items]
    loop = get_running_loop()
    prices = await loop.run_in_executor(
        _executor, lambda: _fetch_prices_sync(symbols)
    )

    enriched = []
    for item in reversed(items):  # newest first
        sym = item["symbol"]
        p = prices.get(sym, {"price": 0.0, "change_pct": 0.0})
        current_price = p["price"]
        entry_price = item.get("entry_price", 0.0) or 0.0
        pnl_pct = (
            ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0.0
        )
        enriched.append(
            {
                **item,
                "current_price": round(current_price, 4),
                "change_pct": p["change_pct"],
                "pnl_pct": round(pnl_pct, 2),
                "status": _compute_status(item, current_price),
            }
        )

    return {
        "items": enriched,
        "count": len(enriched),
        "refreshed_at": datetime.now(UTC).isoformat(),
    }


@router.delete("/watchlist/clear")
def clear_watchlist():
    """Remove all watchlist entries."""
    _save([])
    logger.info("Watchlist cleared")
    return {"ok": True, "count": 0}


@router.delete("/watchlist/{symbol}")
def remove_from_watchlist(symbol: str):
    """Remove one symbol from the watchlist."""
    symbol = symbol.upper()
    items = _load()
    before = len(items)
    items = [i for i in items if i.get("symbol") != symbol]
    if len(items) == before:
        raise HTTPException(status_code=404, detail=f"{symbol} not in watchlist")
    _save(items)
    logger.info("Watchlist remove: %s", symbol)
    return {"ok": True, "symbol": symbol, "count": len(items)}
