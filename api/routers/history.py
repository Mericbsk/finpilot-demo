"""GET /api/v1/history — Signal history from the database + inference cache."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Query

from core.config import DATA_DIR, SIGNAL_ARCHIVE_DIR

router = APIRouter(tags=["history"])

_INFERENCE_PATH = DATA_DIR / "inference.json"


def _load_archive_signals(days: int) -> list[dict]:
    """Load signals from signal_archive/*.json for the last `days` days."""
    if not SIGNAL_ARCHIVE_DIR.exists():
        return []
    cutoff = datetime.now().date() - timedelta(days=days)
    items: list[dict] = []
    for f in sorted(SIGNAL_ARCHIVE_DIR.glob("*.json"), reverse=True):
        try:
            date_str = f.stem  # e.g. "2026-05-19"
            if datetime.strptime(date_str, "%Y-%m-%d").date() < cutoff:
                continue
            data = json.loads(f.read_text(encoding="utf-8"))
            if isinstance(data, list):
                items.extend(data)
        except Exception:
            pass
    return items


def _load_inference() -> dict:
    """Load inference cache JSON (fallback)."""
    if _INFERENCE_PATH.exists():
        return json.loads(_INFERENCE_PATH.read_text())
    return {}


@router.get("/history/signals")
def get_signal_history(days: int = Query(14, ge=1, le=365)):
    """Return recent signals: DB → archive files → inference cache fallback."""
    from auth.database import Database, SignalRepository

    db = Database()
    repo = SignalRepository(db)
    signals = repo.get_recent(limit=days * 20)

    if signals:
        return {"source": "database", "count": len(signals), "signals": signals}

    # Try signal_archive/*.json files
    archive = _load_archive_signals(days)
    if archive:
        return {"source": "archive", "count": len(archive), "signals": archive}

    # Fallback: return inference cache as "latest" signals
    cache = _load_inference()
    flat: list[dict] = []
    for sym, data in cache.items():
        flat.append({"symbol": sym, **data})
    return {"source": "inference_cache", "count": len(flat), "signals": flat}


@router.get("/history/stats")
def get_signal_stats():
    """Aggregate signal statistics."""
    from auth.database import Database, SignalRepository

    db = Database()
    repo = SignalRepository(db)
    return repo.get_stats()


@router.get("/history/inference")
def get_inference_cache():
    """Return the latest DRL inference results."""
    return _load_inference()


@router.get("/history/returns")
def get_signal_returns(days: int = Query(30, ge=1, le=90)):
    """For each past BUY signal, calculate T+5 and T+10 actual returns using yfinance.

    Returns per-symbol outcomes so the frontend can display win rate and P&L.
    """
    try:
        import yfinance as yf
    except ImportError:
        return {"error": "yfinance not installed", "results": []}

    from auth.database import Database, SignalRepository

    db = Database()
    repo = SignalRepository(db)
    signals = repo.get_recent(limit=days * 20)

    # Only BUY signals with a recorded price and timestamp
    buy_signals = [
        s
        for s in signals
        if str(s.get("signal", "")).upper() == "BUY" and s.get("price") and s.get("timestamp")
    ]

    if not buy_signals:
        return {"results": [], "count": 0, "source": "no_data"}

    results = []
    # Group by symbol to download price history once per symbol
    by_symbol: dict[str, list] = {}
    for s in buy_signals:
        by_symbol.setdefault(str(s["symbol"]), []).append(s)

    for symbol, sigs in by_symbol.items():
        # Determine date range needed
        oldest_ts = min(sigs, key=lambda s: s["timestamp"])["timestamp"]
        start_date = (
            datetime.fromisoformat(str(oldest_ts).replace("Z", "")) - timedelta(days=2)
        ).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        try:
            hist = yf.download(
                symbol, start=start_date, end=end_date, progress=False, auto_adjust=True
            )
            if hist.empty:
                continue
            closes = hist["Close"].squeeze()
        except Exception:
            continue

        for sig in sigs:
            entry_price = float(sig["price"])
            if entry_price <= 0:
                continue

            try:
                entry_dt = datetime.fromisoformat(str(sig["timestamp"]).replace("Z", ""))
                entry_date = entry_dt.date()
            except Exception:
                continue

            # Find the closest trading day on or after entry
            available_dates = [d.date() for d in closes.index]
            future_dates = [d for d in available_dates if d >= entry_date]
            if not future_dates:
                continue

            def get_pct(
                n_days: int,
                _future_dates: list = future_dates,
                _entry_date: object = entry_date,
                _entry_price: float = entry_price,
                _closes: object = closes,
            ) -> float | None:
                target_dates = [d for d in _future_dates if (d - _entry_date).days >= n_days]
                if not target_dates:
                    return None
                target = min(target_dates, key=lambda d: (d - _entry_date).days)
                try:
                    price_n = float(_closes[_closes.index.date == target].iloc[0])  # type: ignore[attr-defined]
                    return round((price_n - _entry_price) / _entry_price * 100, 2)
                except Exception:
                    return None

            t5 = get_pct(5)
            t10 = get_pct(10)
            t20 = get_pct(20)

            results.append(
                {
                    "symbol": symbol,
                    "signal_date": str(entry_date),
                    "entry_price": entry_price,
                    "score": sig.get("score"),
                    "t5_pct": t5,
                    "t10_pct": t10,
                    "t20_pct": t20,
                    "t5_win": t5 > 0 if t5 is not None else None,
                    "t10_win": t10 > 0 if t10 is not None else None,
                }
            )

    # Summary stats
    t5_results = [r for r in results if r["t5_pct"] is not None]
    t10_results = [r for r in results if r["t10_pct"] is not None]

    best_signal = max(t10_results, key=lambda r: r["t10_pct"]) if t10_results else None
    worst_signal = min(t10_results, key=lambda r: r["t10_pct"]) if t10_results else None

    # SPY benchmark for same period
    spy_t10_avg = None
    if t10_results:
        try:
            oldest = min(r["signal_date"] for r in t10_results)
            spy_hist = yf.download(
                "SPY",
                start=oldest,
                end=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                progress=False,
                auto_adjust=True,
            )
            if not spy_hist.empty:
                spy_closes = spy_hist["Close"].squeeze()
                spy_returns = []
                for r in t10_results:
                    ed = r["signal_date"]
                    entry_dt2 = datetime.strptime(ed, "%Y-%m-%d").date()
                    spy_dates = [d.date() for d in spy_closes.index]
                    future = [d for d in spy_dates if d >= entry_dt2]
                    target10 = [d for d in future if (d - entry_dt2).days >= 10]
                    entry_spy = [d for d in future if d >= entry_dt2]
                    if not entry_spy or not target10:
                        continue
                    s0 = float(spy_closes[spy_closes.index.date == entry_spy[0]].iloc[0])  # type: ignore[attr-defined]
                    s10 = float(
                        spy_closes[
                            spy_closes.index.date
                            == min(target10, key=lambda d: (d - entry_dt2).days)
                        ].iloc[0]
                    )  # type: ignore[attr-defined]
                    spy_returns.append((s10 - s0) / s0 * 100)
                if spy_returns:
                    spy_t10_avg = round(sum(spy_returns) / len(spy_returns), 2)
        except Exception:
            pass

    summary = {
        "t5_win_rate": round(sum(1 for r in t5_results if r["t5_win"]) / len(t5_results) * 100, 1)
        if t5_results
        else None,
        "t10_win_rate": round(
            sum(1 for r in t10_results if r["t10_win"]) / len(t10_results) * 100, 1
        )
        if t10_results
        else None,
        "t5_avg_pct": round(sum(r["t5_pct"] for r in t5_results) / len(t5_results), 2)
        if t5_results
        else None,
        "t10_avg_pct": round(sum(r["t10_pct"] for r in t10_results) / len(t10_results), 2)
        if t10_results
        else None,
        "total_signals": len(results),
        "best_signal": best_signal,
        "worst_signal": worst_signal,
        "spy_t10_avg_pct": spy_t10_avg,
    }

    return {"results": results, "count": len(results), "summary": summary, "source": "database"}


@router.get("/history/ohlcv")
def get_ohlcv(
    symbol: str = Query(..., description="Ticker symbol, e.g. AAPL"),
    period: str = Query("3mo", description="yfinance period string"),
    interval: str = Query("1d", description="yfinance interval string"),
):
    """Return OHLCV bars + EMA-20 for a single symbol.

    The time field is formatted as YYYY-MM-DD so lightweight-charts can
    parse it directly as a business-day time without a timestamp conversion.
    """
    try:
        import yfinance as yf  # noqa: PLC0415
    except ImportError:
        return {"symbol": symbol, "bars": [], "ema20": [], "error": "yfinance not installed"}

    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
    except Exception as exc:  # noqa: BLE001
        return {"symbol": symbol, "bars": [], "ema20": [], "error": str(exc)}

    if df is None or df.empty:
        return {"symbol": symbol, "bars": [], "ema20": []}

    # Flatten MultiIndex columns produced by yfinance ≥0.2 (e.g. ("Open", "AAPL") → "Open")
    if hasattr(df.columns, "levels"):
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

    bars = []
    for ts, row in df.iterrows():
        try:
            bars.append(
                {
                    "time": ts.strftime("%Y-%m-%d"),
                    "open": round(float(row["Open"]), 4),
                    "high": round(float(row["High"]), 4),
                    "low": round(float(row["Low"]), 4),
                    "close": round(float(row["Close"]), 4),
                    "volume": int(row["Volume"]),
                }
            )
        except Exception:  # noqa: BLE001
            continue

    # Compute 20-period EMA for the main chart overlay
    ema20 = []
    if len(bars) >= 2:
        k = 2 / (20 + 1)
        ema_val = bars[0]["close"]
        for bar in bars:
            ema_val = bar["close"] * k + ema_val * (1 - k)
            ema20.append({"time": bar["time"], "value": round(ema_val, 4)})

    return {"symbol": symbol, "bars": bars, "ema20": ema20}
