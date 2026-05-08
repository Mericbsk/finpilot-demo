"""POST /api/v1/scan — Run the real technical-analysis scanner."""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(tags=["scan"])
logger = logging.getLogger(__name__)

_SHORTLIST_DIR = Path("data/shortlists")
_STALE_DAYS = 7  # warn if newest shortlist is older than this
_SCAN_TIMEOUT_SECONDS = 300  # 5 minutes max per scan request

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="scan")


class ScanRequest(BaseModel):
    symbols: list[str] = Field(..., max_length=300)
    kelly_fraction: float = Field(0.5, ge=0.0, le=1.0)


@router.post("/scan")
async def run_scan(req: ScanRequest):
    """Run the scanner's evaluate_symbols_parallel on the given symbols.

    Runs in a thread pool with a 5-minute timeout to prevent hanging.
    Returns dict keyed by symbol with scanner evaluation data.
    Also persists results to data/shortlists/ for legacy compatibility.
    """
    try:
        from scanner import evaluate_symbols_parallel
    except ImportError as exc:
        logger.error("Scanner module unavailable: %s", exc)
        raise HTTPException(status_code=503, detail="Scanner module is not available.") from exc

    loop = asyncio.get_running_loop()

    try:
        results = await asyncio.wait_for(
            loop.run_in_executor(
                _executor,
                lambda: evaluate_symbols_parallel(
                    symbols=req.symbols,
                    kelly_fraction=req.kelly_fraction,
                ),
            ),
            timeout=_SCAN_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        logger.error(
            "Scan timed out after %ds for %d symbols", _SCAN_TIMEOUT_SECONDS, len(req.symbols)
        )
        raise HTTPException(
            status_code=504, detail=f"Scan timed out after {_SCAN_TIMEOUT_SECONDS}s"
        ) from None
    except Exception as exc:
        logger.exception("Scan failed for %d symbols: %s", len(req.symbols), exc)
        raise HTTPException(
            status_code=500, detail=f"Scan error: {type(exc).__name__}: {exc}"
        ) from exc

    # Convert list → dict keyed by symbol
    out: dict = {}
    for r in results:
        sym = r.get("symbol") or r.get("ticker")
        if sym:
            out[sym] = r

    # Persist shortlist CSV so legacy Streamlit panels stay current
    if out:
        try:
            _SHORTLIST_DIR.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M")
            csv_path = _SHORTLIST_DIR / f"shortlist_{ts}.csv"
            pd.DataFrame(list(out.values())).to_csv(csv_path, index=False)
            logger.info("Shortlist saved: %s (%d symbols)", csv_path, len(out))
        except Exception as exc:
            logger.warning("Could not save shortlist CSV: %s", exc)

    return out


@router.get("/scan/shortlist/status")
def shortlist_status():
    """Return age of the newest shortlist CSV and a staleness warning if > 7 days."""
    _SHORTLIST_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(_SHORTLIST_DIR.glob("shortlist_*.csv"))
    if not files:
        return {
            "newest_file": None,
            "age_days": None,
            "stale": True,
            "warning": "No shortlist files found.",
        }

    newest = files[-1]
    mtime = datetime.fromtimestamp(newest.stat().st_mtime, tz=UTC)
    age_days = (datetime.now(tz=UTC) - mtime).days
    stale = age_days > _STALE_DAYS
    return {
        "newest_file": newest.name,
        "age_days": age_days,
        "stale": stale,
        "warning": f"Shortlist is {age_days} days old — run a scan to refresh." if stale else None,
    }


@router.get("/chart/{symbol}")
async def get_chart(
    symbol: str,
    interval: str = Query("1d", pattern="^(15m|1h|4h|1d)$"),
    days: int = Query(90, ge=7, le=400),
):
    """Return OHLCV candles + SMA-50 for a symbol, formatted for TradingView LW Charts."""
    try:
        from scanner.data_fetcher import fetch_with_indicators
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="Scanner module unavailable") from exc

    loop = asyncio.get_running_loop()
    try:
        df = await asyncio.wait_for(
            loop.run_in_executor(
                _executor, lambda: fetch_with_indicators(symbol.upper(), interval, days)
            ),
            timeout=30,
        )
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Chart data fetch timed out") from None
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chart fetch error: {exc}") from exc

    if df is None or df.empty:
        raise HTTPException(status_code=404, detail=f"No data for {symbol}")

    df = df.reset_index()
    time_col = next(
        (c for c in df.columns if str(c).lower() in ("date", "datetime", "index")), df.columns[0]
    )

    candles = []
    for _, row in df.iterrows():
        t = row[time_col]
        ts = int(pd.Timestamp(t).timestamp()) if not isinstance(t, (int, float)) else int(t)
        candles.append(
            {
                "time": ts,
                "open": round(float(row.get("Open", row.get("open", 0))), 4),
                "high": round(float(row.get("High", row.get("high", 0))), 4),
                "low": round(float(row.get("Low", row.get("low", 0))), 4),
                "close": round(float(row.get("Close", row.get("close", 0))), 4),
                "volume": int(row.get("Volume", row.get("volume", 0)) or 0),
            }
        )

    sma50_col = next(
        (c for c in df.columns if str(c).lower() in ("sma50", "sma_50", "sma 50")), None
    )
    sma50 = []
    if sma50_col:
        for _, row in df.iterrows():
            v = row[sma50_col]
            if pd.notna(v):
                t = row[time_col]
                ts = int(pd.Timestamp(t).timestamp()) if not isinstance(t, (int, float)) else int(t)
                sma50.append({"time": ts, "value": round(float(v), 4)})

    return {"symbol": symbol.upper(), "interval": interval, "candles": candles, "sma50": sma50}
