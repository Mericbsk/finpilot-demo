"""POST /api/v1/scan — Run the real technical-analysis scanner."""

from __future__ import annotations

import asyncio
import json
import logging
import math
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import pandas as pd
from auth.tokens import TokenPayload
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from api.middleware.auth import require_auth

router = APIRouter(tags=["scan"])
logger = logging.getLogger(__name__)

_SHORTLIST_DIR = Path("data/shortlists")
_FEEDBACK_DIR = Path("data/feedback")
_REPORTS_DIR = Path("data/daily_reports")
_STALE_DAYS = 7
_SCAN_TIMEOUT_SECONDS = 300

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="scan")


def _clean_value(v: object) -> object:
    """Replace NaN/Inf with None so JSON serialisation never fails."""
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


class ScanRequest(BaseModel):
    symbols: list[str] = Field(..., max_length=300)
    kelly_fraction: float = Field(0.5, ge=0.0, le=1.0)


class FeedbackRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field("", max_length=500)
    page: str = Field("demo", max_length=50)
    ticker: str | None = Field(None, max_length=10)


# ---------------------------------------------------------------------------
# SRP helpers (Sprint 5 T5)
# ---------------------------------------------------------------------------


def _load_drl_cache() -> tuple[dict, bool]:
    """Load DRL inference cache from disk (memory-cached via mtime).

    Returns:
        (cache_dict, is_valid) — cache_dict is empty dict when unavailable.
    """
    try:
        from routers.inference import _load_cached_inference

        cache, status = _load_cached_inference()
        return cache, bool(status.get("valid", False))
    except Exception as exc:
        logger.debug("DRL cache load skipped: %s", exc)
    return {}, False


def _enrich_results(
    results: list[dict],
    drl_cache: dict,
    drl_valid: bool,
) -> dict:
    """Convert raw scanner list to symbol-keyed dict; add explanation, reason,
    and unified FinPilot Score to each entry.

    Args:
        results:   Raw list from evaluate_symbols_parallel
        drl_cache: Loaded DRL cache dict
        drl_valid: Whether the DRL cache passed freshness checks

    Returns:
        Dict keyed by symbol with enriched scan entries.
    """
    try:
        from scanner.signals import build_explanation, build_reason

        _explain_ok = True
    except ImportError:
        _explain_ok = False

    try:
        from scanner.finpilot_score import compute_finpilot_score

        _fps_ok = True
    except ImportError:
        _fps_ok = False

    out: dict = {}
    for r in results:
        sym = r.get("symbol") or r.get("ticker")
        if not sym:
            continue

        r["explanation"] = build_explanation(r) if _explain_ok else ""
        r["reason"] = build_reason(r) if _explain_ok else ""

        if _fps_ok:
            scanner_signal = "BUY" if r.get("direction") else "SELL"
            drl_entry = drl_cache.get(sym, {}) if drl_valid else {}
            r["finpilot_score"] = compute_finpilot_score(
                scanner_composite=int(r.get("composite_score") or 0),
                scanner_signal=scanner_signal,
                drl_signal=drl_entry.get("signal"),
                drl_confidence=drl_entry.get("confidence"),
            )

        out[sym] = r
    return out


def _persist_shortlist(out: dict) -> None:
    """Save scan results to a timestamped CSV for legacy Streamlit compatibility."""
    if not out:
        return
    try:
        _SHORTLIST_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        csv_path = _SHORTLIST_DIR / f"shortlist_{ts}.csv"
        pd.DataFrame(list(out.values())).to_csv(csv_path, index=False)
        logger.info("Shortlist saved: %s (%d symbols)", csv_path, len(out))
    except Exception as exc:
        logger.warning("Could not save shortlist CSV: %s", exc)


def _auto_add_watchlist(out: dict, drl_cache: dict, drl_valid: bool) -> None:
    """Auto-add BUY signals (entry_ok=True) to the watchlist.

    Alpha Tracker tarafından hesaplanan ``score_floor`` varsa, composite_score
    bu eşiğin altındaki sinyaller watchlist'e yine eklenir — ancak
    ``score_warning=True`` flag'i ile işaretlenir. Hard block yok.
    """
    if not out:
        return
    try:
        from routers.watchlist import _load, _save, _upsert

        # Alpha Tracker'dan gelen dinamik score floor (sadece flag için)
        score_floor: int | None = None
        try:
            from agents.alpha_tracker import get_score_floor

            score_floor = get_score_floor()
        except Exception:
            pass

        wl = _load()
        added = 0
        flagged_low_score = 0
        for sym, r in out.items():
            if not r.get("entry_ok"):
                continue

            # Score floor kontrolü — atlamıyoruz, sadece flag ekliyoruz
            score_warning = False
            if score_floor is not None:
                composite = float(r.get("composite_score") or 0)
                if composite < score_floor:
                    score_warning = True
                    flagged_low_score += 1
                    logger.debug(
                        "Score uyarısı: %s composite_score=%.1f < floor=%d",
                        sym,
                        composite,
                        score_floor,
                    )

            direction = r.get("direction", False)
            scanner_signal = "BUY" if direction else "SELL"

            drl_conflict = False
            if drl_valid and sym in drl_cache:
                drl_sig = drl_cache[sym].get("signal", "")
                if drl_sig and drl_sig != scanner_signal and drl_sig != "HOLD":
                    drl_conflict = True
                    logger.info(
                        "DRL conflict for %s: scanner=%s drl=%s", sym, scanner_signal, drl_sig
                    )

            entry: dict = {
                "symbol": sym,
                "signal": scanner_signal,
                "entry_price": float(r.get("price") or 0),
                "stop_loss": float(r.get("stop_loss") or 0),
                "take_profit": float(r.get("take_profit") or 0),
                "score": float(r.get("filter_score") or r.get("score") or 0),
                "regime": "Bull" if r.get("regime") else "Bear",
                "sentiment": "Bullish" if direction else "Bearish",
                "risk_reward": float(r.get("risk_reward") or 0),
                "reason": r.get("reason") or "",
                "explanation": r.get("explanation") or "",
                "added_at": datetime.now(tz=UTC).isoformat(),
                "current_price": 0.0,
                "change_pct": 0.0,
                "pnl_pct": 0.0,
                "status": "Pending",
                "drl_conflict": drl_conflict,
                "drl_signal": drl_cache.get(sym, {}).get("signal") if drl_valid else None,
                "drl_confidence": drl_cache.get(sym, {}).get("confidence") if drl_valid else None,
                "score_warning": score_warning,
                "score_floor": score_floor,
            }
            wl = _upsert(wl, entry)
            added += 1
        if added:
            _save(wl)
            logger.info(
                "Auto-watchlist: %d BUY signals saved (%d low-score flagged)",
                added,
                flagged_low_score,
            )
    except Exception as exc:
        logger.warning("Auto-watchlist failed: %s", exc)


@router.post("/scan")
async def run_scan(
    req: ScanRequest,
    _auth: Annotated[TokenPayload, Depends(require_auth)],
):
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

    drl_cache, drl_valid = _load_drl_cache()
    out = _enrich_results(results, drl_cache, drl_valid)
    _persist_shortlist(out)
    _auto_add_watchlist(out, drl_cache, drl_valid)
    try:
        from core.analytics import increment_event

        increment_event("scan_run")
    except Exception:
        pass
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
    days: int = Query(90, ge=1, le=400),
):
    """Return OHLCV candles + SMA-50 for a symbol, formatted for TradingView LW Charts."""
    try:
        from scanner.data_fetcher import fetch_with_indicators
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="Scanner module unavailable") from exc

    # yfinance per-interval history limits — caller may request days=90 for all
    # intervals; cap it here so 15m/1h don't 404.
    _INTERVAL_MAX_DAYS = {"15m": 59, "1h": 729, "4h": 729, "1d": 400}
    days = min(days, _INTERVAL_MAX_DAYS.get(interval, 400))

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


@router.get("/scan/shortlist/latest")
def get_shortlist_latest(limit: int = Query(30, ge=1, le=100)):
    """Return the latest shortlist CSV as JSON, sorted by score desc.

    Used by the public demo page to display real scan results without
    requiring a full re-scan.
    """
    _SHORTLIST_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(_SHORTLIST_DIR.glob("shortlist_*.csv"))
    if not files:
        return {"stocks": [], "source": None, "timestamp": None, "count": 0}

    newest = files[-1]
    try:
        df = pd.read_csv(newest)

        # Coerce boolean string columns
        for col in (
            "regime",
            "direction",
            "entry_ok",
            "high_quality_signal",
            "trend_strength",
            "volume_spike",
            "price_momentum",
            "liquidity_ok",
            "timeframe_aligned",
            "momentum_confluence",
        ):
            if col in df.columns:
                df[col] = df[col].map(lambda x: str(x).lower() in ("true", "1"))

        # Sort by best available score column
        for score_col in ("composite_score", "filter_score", "score"):
            if score_col in df.columns:
                df = df.sort_values(score_col, ascending=False)
                break

        df = df.head(limit)
        stocks = [
            {k: _clean_value(v) for k, v in row.items()} for row in df.to_dict(orient="records")
        ]
        mtime = datetime.fromtimestamp(newest.stat().st_mtime, tz=UTC)
        return {
            "stocks": stocks,
            "source": newest.name,
            "timestamp": mtime.isoformat(),
            "count": len(stocks),
        }
    except Exception as exc:
        logger.error("Failed to read shortlist: %s", exc)
        raise HTTPException(status_code=500, detail=f"Shortlist read error: {exc}") from exc


@router.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    """Append a demo feedback entry to data/feedback/feedback.jsonl."""
    _FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "rating": req.rating,
        "comment": req.comment,
        "page": req.page,
        "ticker": req.ticker,
        "timestamp": datetime.now(tz=UTC).isoformat(),
    }
    feedback_path = _FEEDBACK_DIR / "feedback.jsonl"
    with open(feedback_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    logger.info("Feedback saved: rating=%d page=%s", req.rating, req.page)
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Daily Report Endpoints
# ---------------------------------------------------------------------------


class DailyReportRequest(BaseModel):
    date: str = Field(..., description="YYYY-MM-DD")
    universe_size: int = Field(0, ge=0)
    scanned: int = Field(0, ge=0)
    buy_signals: int = Field(0, ge=0)
    top_signals: list[dict] = Field(default_factory=list)
    paper_trades: list[dict] = Field(default_factory=list)
    notes: str = Field("", max_length=2000)


@router.post("/scan/daily-report")
def save_daily_report(req: DailyReportRequest):
    """Persist a daily scan report to data/daily_reports/YYYY-MM-DD.json."""
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = _REPORTS_DIR / f"{req.date}.json"
    payload = req.model_dump()
    payload["saved_at"] = datetime.now(tz=UTC).isoformat()
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str)
    logger.info("Daily report saved: %s (%d signals)", req.date, req.buy_signals)
    return {"status": "ok", "path": str(report_path)}


@router.get("/scan/daily-reports")
def list_daily_reports(limit: int = Query(30, ge=1, le=90)):
    """Return metadata list of saved daily reports, newest first."""
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(_REPORTS_DIR.glob("*.json"), reverse=True)[:limit]
    out = []
    for f in files:
        try:
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
            out.append(
                {
                    "date": data.get("date", f.stem),
                    "scanned": data.get("scanned", 0),
                    "buy_signals": data.get("buy_signals", 0),
                    "paper_trades": len(data.get("paper_trades", [])),
                    "saved_at": data.get("saved_at"),
                }
            )
        except Exception as exc:
            logger.warning("Could not read report %s: %s", f.name, exc)
    return {"reports": out, "count": len(out)}


@router.get("/scan/daily-report/{date}")
def get_daily_report(date: str):
    """Return full daily report for a given YYYY-MM-DD date."""
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = _REPORTS_DIR / f"{date}.json"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail=f"No report for {date}")
    try:
        with open(report_path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
