"""Watchlist — persist scanner signals and track their live status.

Endpoints
---------
POST   /watchlist                — add one item (from a scanner result)
POST   /watchlist/bulk           — add multiple items at once
GET    /watchlist                — return all items enriched with current prices
GET    /watchlist/performance    — signal performance report (TP/Stop hit rate)
DELETE /watchlist/{symbol}       — remove one item
DELETE /watchlist/clear          — remove all items
"""

from __future__ import annotations

import json
import logging
from asyncio import get_running_loop
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
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
    content = json.dumps(items, ensure_ascii=False, indent=2)
    try:
        _WATCHLIST_FILE.write_text(content, encoding="utf-8")
    except PermissionError:
        # Fallback for Docker/WSL volume mounts where file may be read-only
        import os

        os.chmod(_WATCHLIST_FILE, 0o644)  # nosec B103
        _WATCHLIST_FILE.write_text(content, encoding="utf-8")


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
    prices = await loop.run_in_executor(_executor, lambda: _fetch_prices_sync(symbols))

    enriched = []
    for item in reversed(items):  # newest first
        sym = item["symbol"]
        p = prices.get(sym, {"price": 0.0, "change_pct": 0.0})
        current_price = p["price"]
        entry_price = item.get("entry_price", 0.0) or 0.0
        pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0.0
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


# ─── Performance Report ───────────────────────────────────────────────────────


def _evaluate_signal_sync(item: dict, days: int) -> dict:
    """
    Fetch OHLCV history from added_at to added_at+days and determine outcome:
    - TP_HIT   : high crossed take_profit (BUY) or low crossed take_profit (SELL)
    - STOP_HIT : low crossed stop_loss (BUY) or high crossed stop_loss (SELL)
    - OPEN     : neither happened yet
    Returns enriched dict with outcome, pnl_pct, duration_bars.
    """
    try:
        import yfinance as yf

        added_raw = item.get("added_at", "")
        if not added_raw:
            return {
                **item,
                "outcome": "NO_DATE",
                "pnl_pct": 0.0,
                "exit_price": 0.0,
                "exit_at": None,
            }

        added_dt = datetime.fromisoformat(added_raw)
        start = added_dt.date()
        end = (added_dt + timedelta(days=days + 3)).date()  # +3 for weekends/holidays

        ticker = yf.Ticker(item["symbol"])
        hist = ticker.history(start=str(start), end=str(end), interval="1d")

        if hist.empty:
            return {
                **item,
                "outcome": "NO_DATA",
                "pnl_pct": 0.0,
                "exit_price": 0.0,
                "exit_at": None,
            }

        entry = item.get("entry_price", 0.0) or 0.0
        tp = item.get("take_profit", 0.0) or 0.0
        sl = item.get("stop_loss", 0.0) or 0.0
        signal = item.get("signal", "BUY")
        is_long = signal in ("BUY", "HOLD", "—")

        # Walk candles in order — first breach wins
        candles = list(hist.itertuples())[:days]  # limit to requested days
        for candle in candles:
            high = float(candle.High)
            low = float(candle.Low)
            date_str = str(candle.Index.date())

            if is_long:
                # Long: TP = price goes UP to take_profit, Stop = price falls to stop_loss
                if tp > 0 and high >= tp:
                    pnl = ((tp - entry) / entry * 100) if entry > 0 else 0.0
                    return {
                        **item,
                        "outcome": "TP_HIT",
                        "pnl_pct": round(pnl, 2),
                        "exit_price": tp,
                        "exit_at": date_str,
                    }
                if sl > 0 and low <= sl:
                    pnl = ((sl - entry) / entry * 100) if entry > 0 else 0.0
                    return {
                        **item,
                        "outcome": "STOP_HIT",
                        "pnl_pct": round(pnl, 2),
                        "exit_price": sl,
                        "exit_at": date_str,
                    }
            else:
                # Short: TP = price falls to take_profit, Stop = price rises to stop_loss
                if tp > 0 and low <= tp:
                    pnl = ((entry - tp) / entry * 100) if entry > 0 else 0.0
                    return {
                        **item,
                        "outcome": "TP_HIT",
                        "pnl_pct": round(pnl, 2),
                        "exit_price": tp,
                        "exit_at": date_str,
                    }
                if sl > 0 and high >= sl:
                    pnl = ((entry - sl) / entry * 100) if entry > 0 else 0.0
                    return {
                        **item,
                        "outcome": "STOP_HIT",
                        "pnl_pct": round(pnl, 2),
                        "exit_price": sl,
                        "exit_at": date_str,
                    }

        # Still open — use last close for unrealised PnL
        last_close = float(candles[-1].Close) if candles else entry
        if is_long:
            pnl = ((last_close - entry) / entry * 100) if entry > 0 else 0.0
        else:
            pnl = ((entry - last_close) / entry * 100) if entry > 0 else 0.0
        return {
            **item,
            "outcome": "OPEN",
            "pnl_pct": round(pnl, 2),
            "exit_price": round(last_close, 4),
            "exit_at": None,
        }

    except Exception as exc:
        logger.warning("Performance eval failed for %s: %s", item.get("symbol"), exc)
        return {**item, "outcome": "ERROR", "pnl_pct": 0.0, "exit_price": 0.0, "exit_at": None}


@router.get("/watchlist/performance")
async def get_watchlist_performance(days: int = Query(default=1, ge=1, le=30)):
    """
    Signal performance report.
    For each watchlist item checks if TP or Stop was hit within `days` trading days
    of the signal being added.
    Returns per-signal outcomes + aggregate stats (hit rate, avg PnL, etc.).
    """
    items = _load()
    if not items:
        return {
            "days": days,
            "total": 0,
            "tp_hit": 0,
            "stop_hit": 0,
            "open": 0,
            "tp_rate": 0.0,
            "stop_rate": 0.0,
            "avg_pnl": 0.0,
            "avg_pnl_tp": 0.0,
            "avg_pnl_stop": 0.0,
            "signals": [],
            "evaluated_at": datetime.now(UTC).isoformat(),
        }

    loop = get_running_loop()
    results = await loop.run_in_executor(
        _executor,
        lambda: [_evaluate_signal_sync(item, days) for item in items],
    )

    tp_items = [r for r in results if r["outcome"] == "TP_HIT"]
    stop_items = [r for r in results if r["outcome"] == "STOP_HIT"]
    open_items = [r for r in results if r["outcome"] == "OPEN"]
    closed = len(tp_items) + len(stop_items)

    avg_pnl = round(sum(r["pnl_pct"] for r in results) / len(results), 2) if results else 0.0
    avg_pnl_tp = round(sum(r["pnl_pct"] for r in tp_items) / len(tp_items), 2) if tp_items else 0.0
    avg_pnl_stop = (
        round(sum(r["pnl_pct"] for r in stop_items) / len(stop_items), 2) if stop_items else 0.0
    )

    return {
        "days": days,
        "total": len(results),
        "tp_hit": len(tp_items),
        "stop_hit": len(stop_items),
        "open": len(open_items),
        "other": len(results) - len(tp_items) - len(stop_items) - len(open_items),
        "tp_rate": round(len(tp_items) / len(results) * 100, 1) if results else 0.0,
        "stop_rate": round(len(stop_items) / len(results) * 100, 1) if results else 0.0,
        "closed_rate": round(closed / len(results) * 100, 1) if results else 0.0,
        "avg_pnl": avg_pnl,
        "avg_pnl_tp": avg_pnl_tp,
        "avg_pnl_stop": avg_pnl_stop,
        "signals": sorted(results, key=lambda r: r.get("added_at", ""), reverse=True),
        "evaluated_at": datetime.now(UTC).isoformat(),
    }
