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


@router.post("/reconcile", dependencies=[Depends(require_admin)])
def trigger_reconcile() -> dict[str, Any]:
    from core.outcome_reconciler import reconcile_open_signals

    return reconcile_open_signals()


@router.post("/calibrate", dependencies=[Depends(require_admin)])
def trigger_calibrate() -> dict[str, Any]:
    from core.calibration import refit_calibration

    return refit_calibration()


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
            from datetime import datetime, timezone

            ts = (
                datetime.fromisoformat(last_run.replace("Z", "+00:00"))
                if isinstance(last_run, str)
                else last_run
            )
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            seconds_since_tick = max(
                0.0, (datetime.now(timezone.utc) - ts).total_seconds()
            )
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
