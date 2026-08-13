"""POST /api/v1/scan — Run the real technical-analysis scanner."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import math
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import pandas as pd
from auth.tokens import TokenPayload
from distribution.scan_contract import full_scan_problems
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from api.middleware.auth import require_auth

router = APIRouter(tags=["scan"])
logger = logging.getLogger(__name__)

_SHORTLIST_DIR = Path("data/shortlists")
_FEEDBACK_DIR = Path("data/feedback")
_REPORTS_DIR = Path("data/daily_reports")
_SHADOW_DIR = Path("data/shadow")
_STALE_DAYS = 7
# Timeout per scan call.  200-symbol batches with Alpaca bulk prefetch + 32-worker
# evaluation typically complete in 30-60s, but slow markets or yfinance fallback
# can push this to ~5 min.  600s gives comfortable headroom.
_SCAN_TIMEOUT_SECONDS = 600

# 16 workers allows up to 16 concurrent scan requests without queuing.
# Each request only occupies a thread during the evaluate phase (Alpaca
# I/O runs in its own async loop) so 16 is well within container limits.
_executor = ThreadPoolExecutor(max_workers=16, thread_name_prefix="scan")


def _clean_value(v: object) -> object:
    """Replace NaN/Inf with None so JSON serialisation never fails."""
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


class ScanRequest(BaseModel):
    symbols: list[str] = Field(..., max_length=500)
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


def _persist_shadow_ledger(out: dict, universe: int) -> None:
    """Append every evaluated row, including rejected rows, to the shadow ledger."""
    if not out:
        return
    try:
        _SHADOW_DIR.mkdir(parents=True, exist_ok=True)
        path = _SHADOW_DIR / "scan_shadow.jsonl"
        scan_id = datetime.now(tz=UTC).isoformat()
        with path.open("a", encoding="utf-8") as handle:
            for symbol, row in out.items():
                record = {
                    "scan_id": scan_id,
                    "universe": universe,
                    "symbol": symbol,
                    "timestamp": row.get("timestamp"),
                    "selection_eligible": bool(
                        row.get("selection_eligible", row.get("entry_ok", False))
                    ),
                    "entry_ok": bool(row.get("entry_ok", False)),
                    "reject_reason": list(row.get("reject_reason", [])),
                    "data_quality_tier": row.get("data_quality_tier"),
                    "data_quality_status": row.get("data_quality_status"),
                    "execution_confidence": row.get("execution_confidence"),
                    "execution_feasible": row.get("execution_feasible"),
                    "strategy_scores": row.get("strategy_scores", {}),
                    "ranking_method": row.get("ranking_method"),
                    "selected_by_legacy_quality": row.get("selected_by_legacy_quality", False),
                    "selected_by_v2": row.get("selected_by_v2", False),
                    "selected_by_both": row.get("selected_by_both", False),
                    "legacy_only": row.get("legacy_only", False),
                    "v2_only": row.get("v2_only", False),
                    "dollar_adv": row.get("dollar_adv"),
                    "position_cap_notional": row.get("position_cap_notional"),
                    "position_cap_applied": row.get("position_cap_applied", False),
                    "position_cap_reject_reason": row.get("position_cap_reject_reason"),
                    "exit_profiles": row.get("exit_profiles", {}),
                }
                handle.write(json.dumps(record, ensure_ascii=True, default=str) + "\n")
    except Exception as exc:
        logger.warning("Could not persist shadow ledger: %s", exc)


def _trigger_distribution_draft(universe: int) -> None:
    """Best-effort: after a manual/ad-hoc scan, queue today's distribution
    draft in the background if it hasn't been queued yet for today (see
    distribution.jobs.maybe_trigger_draft_after_scan for guards — trading day,
    minimum universe size, not-already-drafted). Runs in a daemon thread so a
    slow Telegram call never delays the scan HTTP response.
    """
    try:
        import threading

        from distribution.jobs import maybe_trigger_draft_after_scan

        threading.Thread(
            target=maybe_trigger_draft_after_scan,
            args=(universe,),
            daemon=True,
            name="dist-draft-trigger",
        ).start()

        # Gölge skor kartını da arka planda güncelle (env-gated, best-effort).
        # Ayrı süreçte fire-and-forget; scan yanıtını bloklamaz.
        from distribution.jobs import maybe_run_shadow_scorecard_after_scan

        threading.Thread(
            target=maybe_run_shadow_scorecard_after_scan,
            args=(universe,),
            daemon=True,
            name="shadow-scorecard-trigger",
        ).start()
    except Exception as exc:
        logger.debug("Distribution draft trigger skipped: %s", exc)


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
            if not r.get("selection_eligible", r.get("entry_ok", False)):
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

            _now = datetime.now(tz=UTC)
            entry: dict = {
                "symbol": sym,
                "signal": scanner_signal,
                "entry_price": float(r.get("price") or 0),
                "stop_loss": float(r.get("stop_loss") or 0),
                "take_profit": float(r.get("take_profit") or 0),
                "score": float(r.get("filter_score") or r.get("score") or 0),
                "finpilot_score": int(r.get("finpilot_score") or 0),
                "composite_score": int(r.get("composite_score") or 0),
                "signal_date": _now.strftime("%Y-%m-%d"),
                "regime": "Bull" if r.get("regime") else "Bear",
                "sentiment": "Bullish" if direction else "Bearish",
                "risk_reward": float(r.get("risk_reward") or 0),
                "reason": r.get("reason") or "",
                "explanation": r.get("explanation") or "",
                "added_at": _now.isoformat(),
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
        from scanner.data_fetcher import reset_yf_fetch_count

        reset_yf_fetch_count()  # P1: measure yfinance fallback usage for THIS scan
    except Exception:  # noqa: BLE001
        pass
    _t_start = time.perf_counter()

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

    _t_eval_done = time.perf_counter()

    drl_cache, drl_valid = _load_drl_cache()
    out = _enrich_results(results, drl_cache, drl_valid)
    _t_scoring_done = time.perf_counter()
    try:
        from scanner.data_fetcher import yf_fetch_count

        _yf_fb = yf_fetch_count()  # P1: symbols that hit the slow yfinance fallback
    except Exception:  # noqa: BLE001
        _yf_fb = -1
    # P0.1: per-timeframe Alpaca(IEX) miss counts — which timeframe drove fallback.
    try:
        from scanner.data_fetcher import alpaca_miss_by_tf

        _alpaca_miss = alpaca_miss_by_tf()
    except Exception:  # noqa: BLE001
        _alpaca_miss = {}
    try:
        from scanner.performance import snapshot as stage_timing

        _stage_timing = stage_timing()
    except Exception:  # noqa: BLE001
        _stage_timing = []
    logger.info(
        "scan timing: symbols=%d yf_fallback=%d alpaca_miss=%s eval=%.2fs enrich=%.2fs total=%.2fs",
        len(req.symbols),
        _yf_fb,
        _alpaca_miss,
        _t_eval_done - _t_start,
        _t_scoring_done - _t_eval_done,
        _t_scoring_done - _t_start,
    )
    _timing = {
        "eval_s": round(_t_eval_done - _t_start, 2),
        "enrich_s": round(_t_scoring_done - _t_eval_done, 2),
        "total_s": round(_t_scoring_done - _t_start, 2),
        "symbols": len(req.symbols),
        "yf_fallback": _yf_fb,
        "alpaca_miss": _alpaca_miss,
        "stage_timing": _stage_timing,
    }
    _append_scan_timing_log(_timing, universe=len(req.symbols))
    _persist_shortlist(out)
    _persist_shadow_ledger(out, universe=len(req.symbols))
    _auto_add_watchlist(out, drl_cache, drl_valid)
    _persist_distribution_export(
        out,
        universe=len(req.symbols),
        timing=_timing,
    )
    try:
        from core.analytics import increment_event

        increment_event("scan_run")
    except Exception:
        pass
    return out


class ScanSummarizeRequest(BaseModel):
    results: dict[str, dict] = Field(
        ...,
        description="Aggregated /scan sonuclari — TUM batch'lerin birlesimi (symbol -> result dict)",
    )
    universe: int | None = Field(None, ge=1)
    scan_complete: bool | None = None
    scan_id: str | None = Field(None, max_length=100)


@router.post("/scan/summarize")
async def summarize_scan(
    req: ScanSummarizeRequest,
    _auth: Annotated[TokenPayload, Depends(require_auth)],
):
    """Tum batch'ler bittikten sonra frontend'in TEK kez cagirdigi ozet endpoint'i.

    Kural-tabanli aday havuzundan (entry_ok VEYA conviction_tier A/B/C) LLM ile
    basari olasiligi en yuksek <=10 taneyi secer/daraltir + tek seferlik Telegram
    bildirimi gonderir. LLM kullanilamazsa kural-tabanli siralamaya duser.
    """
    from scanner.scan_summary import summarize_full_scan

    problems = full_scan_problems(req.results, req.universe, req.scan_complete)
    if problems:
        raise HTTPException(
            status_code=422,
            detail=("Aggregate scan incomplete: " + "; ".join(problems)),
        )

    # The browser scans the universe in 200-symbol batches and only has the
    # complete result set at this boundary. Persist that aggregate so the
    # distribution layer never publishes the last batch as today's scan.
    if req.scan_complete is not False:
        _persist_distribution_export(
            req.results,
            universe=req.universe or len(req.results),
            scan_id=req.scan_id,
            scan_complete=True,
        )
        _trigger_distribution_draft(universe=req.universe or len(req.results))

    loop = asyncio.get_running_loop()
    try:
        summary = await asyncio.wait_for(
            loop.run_in_executor(_executor, lambda: summarize_full_scan(req.results)),
            timeout=180,
        )
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Summarize timed out after 180s") from None
    except Exception as exc:
        logger.exception("scan/summarize failed")
        raise HTTPException(
            status_code=500, detail=f"Summarize error: {type(exc).__name__}: {exc}"
        ) from exc
    return {
        **summary,
        "distribution": {
            "persisted": True,
            "universe": req.universe or len(req.results),
            "result_count": len(req.results),
        },
    }


class AnalyzeRequest(BaseModel):
    symbols: list[str] = Field(..., max_length=200)
    kelly_fraction: float = Field(0.5, ge=0.0, le=1.0)


@router.post("/scan/analyze")
async def run_analyze(
    req: AnalyzeRequest,
    _auth: Annotated[TokenPayload, Depends(require_auth)],
):
    """Birleşik shortlist analizi: scan → social → enrich → bull/bear.

    Per-sembol birleşik görünüm döndürür (scan + social + bull + bear + enrichment).
    LLM zenginleştirmesi FINPILOT_LLM_BACKEND=ollama iken yerel modelle yapılır;
    backend kapalıysa enrichment alanları boş/temiz döner (akış bozulmaz).
    """
    try:
        from core.pipeline import analyze_shortlist
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="Pipeline module unavailable.") from exc

    loop = asyncio.get_running_loop()
    try:
        view = await asyncio.wait_for(
            loop.run_in_executor(
                _executor,
                lambda: analyze_shortlist(symbols=req.symbols, kelly_fraction=req.kelly_fraction),
            ),
            timeout=_SCAN_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        raise HTTPException(
            status_code=504, detail=f"Analyze timed out after {_SCAN_TIMEOUT_SECONDS}s"
        ) from None
    except Exception as exc:
        logger.exception("Analyze failed for %d symbols: %s", len(req.symbols), exc)
        raise HTTPException(
            status_code=500, detail=f"Analyze error: {type(exc).__name__}: {exc}"
        ) from exc
    return view


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
        ts = int(pd.Timestamp(t).timestamp()) if not isinstance(t, int | float) else int(t)
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
                ts = int(pd.Timestamp(t).timestamp()) if not isinstance(t, int | float) else int(t)
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


def _append_scan_timing_log(timing: dict, universe: int) -> None:
    """Append one line per /scan call to a persistent timing history (JSONL).

    P0.1 (2026-07-31 scanner audit): per-batch timing was only kept in the latest
    scan_export (overwritten each batch), so full-universe wall-clock and fallback
    history were unqueryable. This append-only log closes that blind spot without
    touching scan output. Best-effort — must never break the scan.
    """
    try:
        export_dir = Path(os.getenv("FINPILOT_DIST_DIR", "data/distribution"))
        export_dir.mkdir(parents=True, exist_ok=True)
        rec = {
            "ts": datetime.now(tz=UTC).isoformat(),
            "date": datetime.now(tz=UTC).strftime("%Y-%m-%d"),
            "universe": universe,
            "symbols": timing.get("symbols"),
            "eval_s": timing.get("eval_s"),
            "enrich_s": timing.get("enrich_s"),
            "total_s": timing.get("total_s"),
            "yf_fallback": timing.get("yf_fallback"),
            "alpaca_miss": timing.get("alpaca_miss", {}),
            "stage_timing": timing.get("stage_timing", []),
        }
        with (export_dir / "scan_timing.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    except Exception as exc:  # pragma: no cover - observation must never break scan
        logger.debug("scan timing log skipped: %s", exc)


def _persist_distribution_export(
    results: dict,
    universe: int,
    scan_id: str | None = None,
    scan_complete: bool | None = None,
    timing: dict | None = None,
) -> None:
    """Write full enriched scan results for the distribution layer.

    The daily brief / web demo snapshot is built from THIS export (it carries
    tier/conviction fields) — never from legacy daily_reports. Atomic writes
    (tmp+replace) so a concurrent reader can never see a half-written file.
    Best-effort: failure must never break the scan.
    """
    try:
        import os as _os

        export_dir = Path(_os.getenv("FINPILOT_DIST_DIR", "data/distribution"))
        export_dir.mkdir(parents=True, exist_ok=True)
        rows = list(results.values()) if isinstance(results, dict) else list(results or [])
        for row in rows:
            if not isinstance(row, dict) or row.get("scan_status") != "unavailable":
                continue
            reason = str((row.get("reject_reason") or ["unavailable"])[0])
            row.setdefault("data_quality", {"available": {}, "missing_fields": [reason]})
            row.setdefault("execution_reject_reason", [reason])
            row.setdefault("execution_confidence", "Tier 0")
            row.setdefault("legacy_quality_score", 0.0)
            row.setdefault("ranking_score", 0.0)
            row.setdefault("v2_score", 0.0)
            row.setdefault("strategy_scores", {"legacy_quality": 0.0, "v2": 0.0})
            row.setdefault("conviction_tier", "")
            row.setdefault("conviction_prob", 0.0)
            row.setdefault("position_cap_notional", None)
            row.setdefault("position_cap_applied", False)
            row.setdefault("position_cap_reject_reason", None)
        payload = {
            "date": datetime.now(tz=UTC).strftime("%Y-%m-%d"),
            "generated_at": datetime.now(tz=UTC).isoformat(),
            # scan_id identifies the SYMBOL SET (identical across same-universe
            # runs); run_id identifies THIS run — never confuse the two.
            "run_id": datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%S"),
            "universe": universe,
            "scan_id": scan_id
            or hashlib.sha256(
                "|".join(
                    sorted(
                        str(row.get("symbol") or row.get("ticker") or "").upper()
                        for row in (
                            list(results.values()) if isinstance(results, dict) else results
                        )
                        if isinstance(row, dict) and (row.get("symbol") or row.get("ticker"))
                    )
                ).encode()
            ).hexdigest()[:24],
            "scan_complete": scan_complete is not False,
            # Per-run performance (P0 instrumentation): eval/enrich/total seconds
            # so scan duration is queryable history, not a file-mtime guess.
            "timing": timing or {},
            "result_count": len(rows),
            "results": rows,
        }
        current_results = payload["results"]
        problems = full_scan_problems(current_results, universe, scan_complete)
        current_symbols = {
            str(row.get("symbol") or row.get("ticker") or "").upper()
            for row in current_results
            if isinstance(row, dict) and (row.get("symbol") or row.get("ticker"))
        }
        if problems:
            partial_path = export_dir / (
                f"scan_export_{payload['date']}_partial_{len(current_symbols)}.json"
            )
            partial_path.write_text(
                json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8"
            )
            logger.info(
                "distribution partial export saved without replacing latest: universe=%d/%d",
                universe,
                int(os.getenv("FINPILOT_FULL_UNIVERSE_SIZE", "1812")),
            )
            return
        dated_path = export_dir / f"scan_export_{payload['date']}.json"
        if dated_path.exists():
            try:
                existing = json.loads(dated_path.read_text(encoding="utf-8"))
                existing_universe = int(existing.get("universe") or 0)
                existing_results = existing.get("results") or []
                existing_symbols = {
                    str(row.get("symbol") or row.get("ticker") or "").upper()
                    for row in existing_results
                    if isinstance(row, dict) and (row.get("symbol") or row.get("ticker"))
                }
                existing_is_larger = (
                    existing_universe > universe
                    or len(existing_results) > len(current_results)
                    or len(existing_symbols) > len(current_symbols)
                )
                if existing_is_larger:
                    logger.warning(
                        "distribution export skipped: new scan is smaller than existing "
                        "export for %s (universe=%d/%d, results=%d/%d, symbols=%d/%d)",
                        payload["date"],
                        universe,
                        existing_universe,
                        len(current_results),
                        len(existing_results),
                        len(current_symbols),
                        len(existing_symbols),
                    )
                    return
                # Degraded-run guard (2026-07-24): an equal-size run whose
                # enrichment produced ZERO graded/eligible rows must not
                # overwrite an existing enriched export — last-writer-wins
                # destroyed the published evidence once already.
                from distribution.prepublish_gate import _grade_like

                def _enriched_count(rows: list) -> int:
                    return sum(
                        1
                        for row in rows
                        if isinstance(row, dict)
                        and (_grade_like(row) or row.get("selection_eligible") is True)
                    )

                if _enriched_count(current_results) == 0 and _enriched_count(existing_results) > 0:
                    degraded_path = export_dir / (
                        f"scan_export_{payload['date']}_degraded_"
                        f"{datetime.now(tz=UTC).strftime('%H%M%S')}.json"
                    )
                    degraded_path.write_text(
                        json.dumps(payload, ensure_ascii=False, default=str),
                        encoding="utf-8",
                    )
                    logger.warning(
                        "distribution export DIVERTED to %s: new run has 0 enriched "
                        "rows while existing export for %s has %d — latest kept intact",
                        degraded_path.name,
                        payload["date"],
                        _enriched_count(existing_results),
                    )
                    return
            except (OSError, TypeError, ValueError, json.JSONDecodeError):
                pass
        text = json.dumps(payload, ensure_ascii=False, default=str)
        for name in ("scan_export_latest.json", dated_path.name):
            tmp = export_dir / (name + ".tmp")
            tmp.write_text(text, encoding="utf-8")
            tmp.replace(export_dir / name)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("distribution export failed (non-fatal): %s", exc)
