"""Sprint 5 (S5-5/S5-3): Closed-loop status endpoints.

Exposes:
  GET  /api/v1/loop/status         — quality gate + scheduler status
  GET  /api/v1/loop/portfolio      — paper portfolio summary + equity curve
  GET  /api/v1/loop/portfolio/open — currently open paper positions
  GET  /api/v1/loop/portfolio/closed — recent closed trades
  GET  /api/v1/loop/calibration    — fitted score→P(win) model
  POST /api/v1/loop/reconcile      — manually trigger outcome reconciliation
  POST /api/v1/loop/calibrate      — manually refit calibration
  POST /api/v1/loop/clear-degraded — clear the quality gate flag
"""

from __future__ import annotations

from datetime import UTC
from typing import Any

from fastapi import APIRouter, Depends

from api.middleware.auth import optional_auth, require_admin

router = APIRouter(prefix="/loop", tags=["closed_loop"])


@router.get("/status", dependencies=[Depends(optional_auth)])
def loop_status() -> dict[str, Any]:
    import os

    from core.quality_gate import get_status
    from core.scheduler import scheduler_status

    try:
        pwin_threshold = float(os.getenv("FINPILOT_PWIN_THRESHOLD", "0.55"))
    except ValueError:
        pwin_threshold = 0.55
    drl_gate_enabled = os.getenv("FINPILOT_DRL_GATE", "0") == "1"

    return {
        "quality_gate": get_status(),
        "scheduler": scheduler_status(),
        "decision_gate": {
            "pwin_threshold": pwin_threshold,
            "drl_gate_enabled": drl_gate_enabled,
        },
    }


@router.get("/portfolio", dependencies=[Depends(optional_auth)])
def portfolio_summary() -> dict[str, Any]:
    from core.paper_portfolio import get_equity_curve, get_summary

    return {
        "summary": get_summary(),
        "equity_curve": get_equity_curve(limit=200),
    }


@router.get("/portfolio/open", dependencies=[Depends(optional_auth)])
def portfolio_open() -> dict[str, Any]:
    from core.paper_portfolio import get_open_positions

    return {"positions": get_open_positions()}


@router.get("/portfolio/closed", dependencies=[Depends(optional_auth)])
def portfolio_closed(limit: int = 50) -> dict[str, Any]:
    from core.paper_portfolio import get_closed_history

    return {"trades": get_closed_history(limit=limit)}


@router.get("/calibration", dependencies=[Depends(optional_auth)])
def calibration_model() -> dict[str, Any]:
    from core.calibration import get_calibration_model

    model = get_calibration_model()
    return {"model": model, "fitted": model is not None}


@router.get("/calibration/stats", dependencies=[Depends(optional_auth)])
def calibration_stats() -> dict[str, Any]:
    """Return Brier, ECE, decile lift, band detail and history for the dashboard."""
    from core.calibration import get_calibration_stats

    return get_calibration_stats()


@router.post("/reconcile", dependencies=[Depends(require_admin)])
def trigger_reconcile() -> dict[str, Any]:
    from core.outcome_reconciler import reconcile_open_signals

    return reconcile_open_signals()


@router.post("/calibrate", dependencies=[Depends(require_admin)])
def trigger_calibrate() -> dict[str, Any]:
    from core.calibration import refit_with_gate

    return refit_with_gate()


@router.get("/pending", dependencies=[Depends(optional_auth)])
def list_pending_actions(include_decided: bool = False) -> dict[str, Any]:
    from core import pending_actions

    return {"actions": pending_actions.list_pending(include_decided=include_decided)}


@router.post("/approve/{pid}", dependencies=[Depends(require_admin)])
def approve_pending(pid: str) -> dict[str, Any]:
    from core import pending_actions

    try:
        return pending_actions.approve(pid, decided_by="admin")
    except KeyError as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/reject/{pid}", dependencies=[Depends(require_admin)])
def reject_pending(pid: str, reason: str = "") -> dict[str, Any]:
    from core import pending_actions

    try:
        return pending_actions.reject(pid, decided_by="admin", reason=reason)
    except KeyError as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/audit", dependencies=[Depends(optional_auth)])
def autonomy_audit(limit: int = 50) -> dict[str, Any]:
    from core import audit_log

    return {"entries": audit_log.recent(limit=limit)}


@router.get("/champion/edge", dependencies=[Depends(optional_auth)])
def champion_edge() -> dict[str, Any]:
    """Sprint 16 (S16-04): Live champion edge visibility.

    Returns the current champion model metadata + the last 30 days rolling
    Brier score and paper portfolio PnL — the single most important
    "is the self-improving loop actually improving?" signal.
    """
    import time
    from datetime import datetime, timedelta

    from core.kpi_tracker import _load_all_signals, get_kpis

    champion: dict[str, Any] | None = None
    try:
        from research.registry import get_champion as _get_champ

        champion = _get_champ()
    except Exception:
        champion = None

    # 30d rolling Brier from resolved signals.
    cutoff_ts = (datetime.utcnow() - timedelta(days=30)).timestamp()
    signals = _load_all_signals()
    recent_resolved: list[dict] = []
    for s in signals:
        try:
            ts_raw = s.get("timestamp") or s.get("ts")
            if isinstance(ts_raw, str):
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00")).timestamp()
            elif isinstance(ts_raw, (int, float)):
                ts = float(ts_raw)
            else:
                continue
            if ts < cutoff_ts:
                continue
            if s.get("outcome") in ("win", "loss"):
                recent_resolved.append(s)
        except Exception:
            continue

    brier_30d: float | None = None
    if recent_resolved:
        # Score is on 0–100; calibrated probability is on 0–1.
        # Prefer p_win_calib if present; else normalize score/100.
        sq_err = []
        for s in recent_resolved:
            p = s.get("p_win_calib")
            if p is None:
                raw = s.get("score", 0) or 0
                p = max(0.0, min(1.0, float(raw) / 100.0))
            else:
                p = float(p)
            y = 1.0 if s["outcome"] == "win" else 0.0
            sq_err.append((p - y) ** 2)
        if sq_err:
            brier_30d = round(sum(sq_err) / len(sq_err), 4)

    # Paper portfolio PnL (uses entire history; safe degradation).
    paper_pnl_total: float | None = None
    paper_pnl_30d: float | None = None
    try:
        from core.paper_portfolio import get_closed_history, get_summary

        summary = get_summary()
        paper_pnl_total = float(summary.get("total_pnl_pct", 0.0))
        history = get_closed_history(limit=500)
        recent_pnls = []
        for h in history:
            try:
                ts_raw = h.get("closed_at") or h.get("exit_time") or h.get("ts")
                if isinstance(ts_raw, str):
                    ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00")).timestamp()
                else:
                    ts = float(ts_raw or 0)
                if ts >= cutoff_ts:
                    recent_pnls.append(float(h.get("pnl_pct", 0.0)))
            except Exception:
                continue
        if recent_pnls:
            paper_pnl_30d = round(sum(recent_pnls), 2)
    except Exception:
        pass

    kpis = get_kpis()

    return {
        "champion": champion,
        "edge": {
            "brier_30d": brier_30d,
            "resolved_signals_30d": len(recent_resolved),
            "paper_pnl_30d_pct": paper_pnl_30d,
            "paper_pnl_total_pct": paper_pnl_total,
        },
        "lifetime_kpis": {
            "win_rate": kpis.get("win_rate"),
            "profit_factor": kpis.get("profit_factor"),
            "total_signals": kpis.get("total_signals"),
            "resolved_signals": kpis.get("resolved_signals"),
        },
        "checked_at": time.time(),
    }


@router.post("/clear-degraded", dependencies=[Depends(require_admin)])
def clear_degraded() -> dict[str, Any]:
    from core.quality_gate import clear_degraded as _clear

    return {"cleared": _clear()}


@router.get("/uptime", dependencies=[Depends(optional_auth)])
def loop_uptime() -> dict[str, Any]:
    """Sprint 6 (s6-uptime-monitor): scheduler liveness probe.

    Returns wall-clock seconds since the last completed scheduler tick. Used by
    the autonomy uptime panel and Prometheus alerting.
    """
    import time

    from core.scheduler import scheduler_status

    status = scheduler_status()
    last_run = status.get("last_run")
    seconds_since_tick: float | None = None
    if last_run:
        try:
            from datetime import datetime

            ts = (
                datetime.fromisoformat(last_run.replace("Z", "+00:00"))
                if isinstance(last_run, str)
                else last_run
            )
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=UTC)
            seconds_since_tick = max(0.0, (datetime.now(UTC) - ts).total_seconds())
        except Exception:
            seconds_since_tick = None

    healthy = seconds_since_tick is not None and seconds_since_tick < 900  # 15 min
    return {
        "running": status.get("running", False),
        "last_run": last_run,
        "cycle_count": status.get("cycle_count", 0),
        "seconds_since_last_tick": seconds_since_tick,
        "healthy": healthy,
        "checked_at": time.time(),
    }
