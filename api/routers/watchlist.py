"""Watchlist — persist scanner signals and track their live status.

Endpoints
---------
POST   /watchlist                 — add one item (from a scanner result)
POST   /watchlist/bulk            — add multiple items at once
GET    /watchlist                 — return all items enriched with current prices
GET    /watchlist/today           — return only today's signals
GET    /watchlist/dates           — return dates that have archived signals + counts
GET    /watchlist/history         — return archived signals for a specific date
GET    /watchlist/performance     — signal performance report (TP/Stop hit rate)
PATCH  /watchlist/{id}/status     — update lifecycle status manually
PATCH  /watchlist/{id}/note       — update notes and tags
POST   /watchlist/archive         — snapshot today's signals to archive (idempotent)
DELETE /watchlist/{symbol}        — remove one item
DELETE /watchlist/clear           — remove all items
"""

from __future__ import annotations

import json
import logging
import uuid
from asyncio import get_running_loop
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(tags=["watchlist"])
logger = logging.getLogger(__name__)

_WATCHLIST_FILE = Path("data/watchlist.json")
_ARCHIVE_DIR = Path("data/signal_archive")
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="watchlist")

# ─── Price cache (TTL = 60 s) ─────────────────────────────────────────────────
_price_cache: dict[str, dict] = {}  # symbol → {price, change_pct}
_price_cache_ts: float = 0.0  # unix timestamp of last full fetch

_PRICE_CACHE_TTL = 60.0  # seconds

# Lifecycle states
LIFECYCLE_STATES = {
    "new",
    "watching",
    "active",
    "resolved_win",
    "resolved_loss",
    "expired",
    "cancelled",
}

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
    source_model: str = Field("scanner_v2", max_length=50)
    notes: str = Field("", max_length=2000)
    tags: list[str] = Field(default_factory=list)


class WatchlistBulkRequest(BaseModel):
    items: list[WatchlistAddRequest] = Field(..., max_length=300)


class LifecycleUpdateRequest(BaseModel):
    status_lifecycle: str = Field(..., max_length=20)


class NoteUpdateRequest(BaseModel):
    notes: str = Field("", max_length=2000)
    tags: list[str] = Field(default_factory=list)


# ─── Storage helpers ─────────────────────────────────────────────────────────


def _migrate_item(item: dict) -> dict:
    """Ensure all new fields are present on items that predate the schema update."""
    if "id" not in item or not item["id"]:
        item["id"] = f"sig_{uuid.uuid4().hex[:12]}"
    if "signal_date" not in item:
        added_raw = item.get("added_at", "")
        item["signal_date"] = (
            added_raw[:10] if added_raw else datetime.now(UTC).strftime("%Y-%m-%d")
        )
    if "status_lifecycle" not in item:
        item["status_lifecycle"] = "watching"
    if "notes" not in item:
        item["notes"] = ""
    if "tags" not in item:
        item["tags"] = []
    if "source_model" not in item:
        item["source_model"] = "scanner_v2"
    return item


def _load() -> list[dict]:
    if not _WATCHLIST_FILE.exists():
        return []
    try:
        data = json.loads(_WATCHLIST_FILE.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else []
        return [_migrate_item(i) for i in items]
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


def _auto_lifecycle(item: dict, current_price: float) -> str:
    """Compute lifecycle status from price data; respects manual overrides."""
    current = item.get("status_lifecycle", "new")
    # Don't override terminal states that the user explicitly set
    if current in {"cancelled", "resolved_win", "resolved_loss", "expired"}:
        return current

    tp = item.get("take_profit", 0.0) or 0.0
    sl = item.get("stop_loss", 0.0) or 0.0
    signal = item.get("signal", "BUY")
    is_long = signal in ("BUY", "HOLD", "—")
    added_raw = item.get("added_at", "")

    # Check expiry (21 calendar days)
    if added_raw:
        try:
            added_dt = datetime.fromisoformat(added_raw)
            if (datetime.now(UTC) - added_dt).days >= 21:
                return "expired"
        except Exception:
            pass

    if current_price > 0:
        if is_long:
            if tp > 0 and current_price >= tp:
                return "resolved_win"
            if sl > 0 and current_price <= sl:
                return "resolved_loss"
        else:
            if tp > 0 and current_price <= tp:
                return "resolved_win"
            if sl > 0 and current_price >= sl:
                return "resolved_loss"

    # Promote new → watching after 24 hours
    if current == "new" and added_raw:
        try:
            added_dt = datetime.fromisoformat(added_raw)
            if (datetime.now(UTC) - added_dt).total_seconds() >= 86400:
                return "watching"
        except Exception:
            pass

    return current


def _load_archive(date_str: str) -> list[dict]:
    """Load signals for a specific date from archive."""
    path = _ARCHIVE_DIR / f"{date_str}.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_archive(date_str: str, items: list[dict]) -> None:
    """Write a daily snapshot to archive (idempotent — overwrites)."""
    _ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    path = _ARCHIVE_DIR / f"{date_str}.json"
    try:
        path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.warning("Archive write failed for %s: %s", date_str, exc)


# ─── Price fetcher ────────────────────────────────────────────────────────────


def _fetch_prices_sync(symbols: list[str]) -> dict[str, dict]:
    """Return {symbol: {price, change_pct}} for all symbols via yfinance download.

    Results are cached for _PRICE_CACHE_TTL seconds to avoid re-fetching on
    every hot-reload or repeated request.
    """
    import time

    global _price_cache, _price_cache_ts  # noqa: PLW0603

    if not symbols:
        return {}

    # Return cached prices if still fresh
    now = time.monotonic()
    missing = [s for s in symbols if s not in _price_cache]
    if not missing and (now - _price_cache_ts) < _PRICE_CACHE_TTL:
        return {s: _price_cache[s] for s in symbols}

    # Which symbols to actually fetch (stale or new)
    to_fetch = symbols if (now - _price_cache_ts) >= _PRICE_CACHE_TTL else missing
    if not to_fetch:
        return {s: _price_cache.get(s, {"price": 0.0, "change_pct": 0.0}) for s in symbols}

    fallback_fetch = {s: {"price": 0.0, "change_pct": 0.0} for s in to_fetch}
    try:
        import yfinance as yf

        df = yf.download(
            to_fetch,
            period="2d",
            interval="1d",
            auto_adjust=True,
            progress=False,
            timeout=15,
        )
        if df.empty:
            _price_cache.update(fallback_fetch)
        else:
            # Multi-ticker: columns are MultiIndex (field, symbol); single-ticker: flat
            if isinstance(df.columns, type(df.columns)) and hasattr(df.columns, "levels"):
                close = df.get("Close", df)
                for sym in to_fetch:
                    try:
                        series = close[sym].dropna()
                        if len(series) < 1:
                            _price_cache[sym] = {"price": 0.0, "change_pct": 0.0}
                            continue
                        price = float(series.iloc[-1])
                        prev = float(series.iloc[-2]) if len(series) >= 2 else price
                        change = ((price - prev) / prev * 100) if prev else 0.0
                        _price_cache[sym] = {
                            "price": round(price, 4),
                            "change_pct": round(change, 2),
                        }
                    except Exception:
                        _price_cache[sym] = {"price": 0.0, "change_pct": 0.0}
            else:
                # Single ticker
                sym = to_fetch[0]
                try:
                    series = df["Close"].dropna()
                    price = float(series.iloc[-1])
                    prev = float(series.iloc[-2]) if len(series) >= 2 else price
                    change = ((price - prev) / prev * 100) if prev else 0.0
                    _price_cache[sym] = {"price": round(price, 4), "change_pct": round(change, 2)}
                except Exception:
                    _price_cache[sym] = {"price": 0.0, "change_pct": 0.0}
            # Fill any still-missing
            for s in to_fetch:
                if s not in _price_cache:
                    _price_cache[s] = {"price": 0.0, "change_pct": 0.0}
        _price_cache_ts = now
    except Exception as exc:
        logger.warning("Price fetch failed: %s", exc)
        _price_cache.update(fallback_fetch)

    return {s: _price_cache.get(s, {"price": 0.0, "change_pct": 0.0}) for s in symbols}


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
    entry["id"] = f"sig_{uuid.uuid4().hex[:12]}"
    entry["signal_date"] = datetime.now(UTC).strftime("%Y-%m-%d")
    entry["status_lifecycle"] = "new"

    items = _load()
    items = _upsert(items, entry)
    _save(items)
    logger.info("Watchlist add: %s (%s)", entry["symbol"], entry["signal"])
    return {"ok": True, "symbol": entry["symbol"], "id": entry["id"], "count": len(items)}


@router.post("/watchlist/bulk", status_code=201)
def bulk_add_to_watchlist(req: WatchlistBulkRequest):
    """Add or update multiple symbols in one call."""
    items = _load()
    added = 0
    now = datetime.now(UTC)
    for item_req in req.items:
        entry = item_req.model_dump()
        entry["symbol"] = entry["symbol"].upper()
        entry["added_at"] = now.isoformat()
        entry["id"] = f"sig_{uuid.uuid4().hex[:12]}"
        entry["signal_date"] = now.strftime("%Y-%m-%d")
        entry["status_lifecycle"] = "new"
        items = _upsert(items, entry)
        added += 1
    _save(items)
    logger.info("Watchlist bulk add: %d symbols", added)
    return {"ok": True, "added": added, "count": len(items)}


@router.get("/watchlist")
async def get_watchlist():
    """Return all watchlist items enriched with live prices, status, and lifecycle."""
    items = _load()
    if not items:
        return {"items": [], "count": 0, "refreshed_at": datetime.now(UTC).isoformat()}

    symbols = [i["symbol"] for i in items]
    loop = get_running_loop()
    prices = await loop.run_in_executor(_executor, lambda: _fetch_prices_sync(symbols))

    enriched = []
    changed = False
    for item in reversed(items):  # newest first
        sym = item["symbol"]
        p = prices.get(sym, {"price": 0.0, "change_pct": 0.0})
        current_price = p["price"]
        entry_price = item.get("entry_price", 0.0) or 0.0
        pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0.0

        new_lifecycle = _auto_lifecycle(item, current_price)
        if new_lifecycle != item.get("status_lifecycle"):
            item["status_lifecycle"] = new_lifecycle
            changed = True

        enriched.append(
            {
                **item,
                "current_price": round(current_price, 4),
                "change_pct": p["change_pct"],
                "pnl_pct": round(pnl_pct, 2),
                "status": _compute_status(item, current_price),
            }
        )

    # Persist any auto-lifecycle changes
    if changed:
        # rebuild items list preserving original order with updated lifecycle
        updated_map = {e["id"]: e for e in enriched}
        updated_items = [
            {
                k: v
                for k, v in updated_map.get(i["id"], i).items()
                if k not in ("current_price", "change_pct", "pnl_pct", "status")
            }
            if i["id"] in updated_map
            else i
            for i in reversed(items)  # restore original order
        ]
        _save(list(reversed(updated_items)))

    return {
        "items": enriched,
        "count": len(enriched),
        "refreshed_at": datetime.now(UTC).isoformat(),
    }


@router.get("/watchlist/today")
async def get_today_signals():
    """Return only signals added today (UTC date)."""
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    items = _load()
    today_items = [i for i in items if i.get("signal_date", "") == today]

    if not today_items:
        return {
            "items": [],
            "count": 0,
            "date": today,
            "refreshed_at": datetime.now(UTC).isoformat(),
        }

    symbols = [i["symbol"] for i in today_items]
    loop = get_running_loop()
    prices = await loop.run_in_executor(_executor, lambda: _fetch_prices_sync(symbols))

    enriched = []
    for item in reversed(today_items):
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
        "date": today,
        "refreshed_at": datetime.now(UTC).isoformat(),
    }


@router.get("/watchlist/dates")
def get_signal_dates():
    """Return list of dates that have archived signals, with counts."""
    _ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    dates = []
    for path in sorted(_ARCHIVE_DIR.glob("*.json"), reverse=True):
        date_str = path.stem
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            count = len(data) if isinstance(data, list) else 0
            dates.append({"date": date_str, "count": count})
        except Exception:
            dates.append({"date": date_str, "count": 0})
    # Also include today from live watchlist if not archived yet
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    today_in_archive = any(d["date"] == today for d in dates)
    if not today_in_archive:
        items = _load()
        today_count = sum(1 for i in items if i.get("signal_date", "") == today)
        if today_count > 0:
            dates.insert(0, {"date": today, "count": today_count, "live": True})
    return {"dates": dates, "total_days": len(dates)}


@router.get("/watchlist/history")
async def get_signal_history(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Return archived signals for a specific date."""
    today = datetime.now(UTC).strftime("%Y-%m-%d")

    if date == today:
        # Serve from live watchlist for today
        items = _load()
        day_items = [i for i in items if i.get("signal_date", "") == today]
    else:
        day_items = _load_archive(date)

    total = len(day_items)
    start = (page - 1) * limit
    page_items = day_items[start : start + limit]

    return {
        "date": date,
        "items": page_items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if total else 0,
    }


@router.post("/watchlist/archive", status_code=200)
def archive_today():
    """Snapshot today's signals to archive file (idempotent)."""
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    items = _load()
    today_items = [i for i in items if i.get("signal_date", "") == today]
    _save_archive(today, today_items)
    logger.info("Archived %d signals for %s", len(today_items), today)
    return {"ok": True, "date": today, "archived": len(today_items)}


@router.patch("/watchlist/{item_id}/status")
def update_lifecycle_status(item_id: str, req: LifecycleUpdateRequest):
    """Manually update lifecycle status for a signal by ID."""
    if req.status_lifecycle not in LIFECYCLE_STATES:
        raise HTTPException(
            status_code=422, detail=f"Invalid status. Must be one of: {sorted(LIFECYCLE_STATES)}"
        )
    items = _load()
    for item in items:
        if item.get("id") == item_id:
            item["status_lifecycle"] = req.status_lifecycle
            _save(items)
            return {"ok": True, "id": item_id, "status_lifecycle": req.status_lifecycle}
    raise HTTPException(status_code=404, detail=f"Signal {item_id} not found")


@router.patch("/watchlist/{item_id}/note")
def update_note(item_id: str, req: NoteUpdateRequest):
    """Update notes and tags for a signal by ID."""
    items = _load()
    for item in items:
        if item.get("id") == item_id:
            item["notes"] = req.notes
            item["tags"] = req.tags
            _save(items)
            return {"ok": True, "id": item_id}
    raise HTTPException(status_code=404, detail=f"Signal {item_id} not found")


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

    # Signal type breakdown
    signal_types: dict[str, dict] = {}
    for r in results:
        sig = r.get("signal", "—")
        if sig not in signal_types:
            signal_types[sig] = {
                "signal": sig,
                "count": 0,
                "tp": 0,
                "stop": 0,
                "open": 0,
                "pnl_sum": 0.0,
            }
        signal_types[sig]["count"] += 1
        if r["outcome"] == "TP_HIT":
            signal_types[sig]["tp"] += 1
        elif r["outcome"] == "STOP_HIT":
            signal_types[sig]["stop"] += 1
        else:
            signal_types[sig]["open"] += 1
        signal_types[sig]["pnl_sum"] += r["pnl_pct"]

    by_type = []
    for sig_data in signal_types.values():
        n = sig_data["count"]
        by_type.append(
            {
                "signal": sig_data["signal"],
                "count": n,
                "tp_count": sig_data["tp"],
                "stop_count": sig_data["stop"],
                "open_count": sig_data["open"],
                "tp_rate": round(sig_data["tp"] / n * 100, 1) if n else 0.0,
                "avg_pnl": round(sig_data["pnl_sum"] / n, 2) if n else 0.0,
            }
        )
    by_type.sort(key=lambda x: x["tp_rate"], reverse=True)

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
        "by_type": by_type,
        "signals": sorted(results, key=lambda r: r.get("added_at", ""), reverse=True),
        "evaluated_at": datetime.now(UTC).isoformat(),
    }
