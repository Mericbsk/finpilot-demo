"""FinPilot Research API — walk-forward, sweep, champion/challenger registry."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException

router = APIRouter(prefix="/research", tags=["research"])
logger = logging.getLogger(__name__)

_pipeline_running = False


@router.get("/status")
def research_status() -> dict[str, Any]:
    """Return latest walk-forward summary + current champion."""
    out: dict[str, Any] = {"pipeline_running": _pipeline_running}

    try:
        from research.walkforward import load_last_results

        out["walkforward"] = load_last_results() or {"status": "not_run"}
    except Exception as exc:
        out["walkforward"] = {"status": "error", "error": str(exc)}

    try:
        from research.registry import ModelRegistry

        reg = ModelRegistry()
        out["champion"] = reg.get_champion()
        out["challengers"] = reg.get_challengers(limit=5)
    except Exception as exc:
        out["champion"] = None
        out["challengers"] = []
        logger.warning("research_status: registry error: %s", exc)

    try:
        from research.sweep import load_last_weights

        out["best_weights"] = load_last_weights()
    except Exception as exc:
        out["best_weights"] = None

    return out


@router.post("/run")
def trigger_pipeline(background_tasks: BackgroundTasks) -> dict[str, str]:
    """Trigger the research pipeline (WF + sweep + registry) in the background."""
    global _pipeline_running
    if _pipeline_running:
        raise HTTPException(status_code=409, detail="Pipeline already running")
    _pipeline_running = True
    background_tasks.add_task(_run_pipeline_task)
    return {"status": "started"}


def _run_pipeline_task() -> None:
    global _pipeline_running
    try:
        from research.pipeline import run_research_pipeline

        result = run_research_pipeline()
        logger.info("research pipeline completed: %s", result.get("registry", {}).get("status"))
    except Exception as exc:
        logger.error("research pipeline error: %s", exc)
    finally:
        _pipeline_running = False


@router.get("/registry")
def list_registry(limit: int = 20) -> dict[str, Any]:
    """List champion and recent challengers from the model registry."""
    try:
        from research.registry import ModelRegistry

        reg = ModelRegistry()
        return {
            "champion": reg.get_champion(),
            "challengers": reg.get_challengers(limit=limit),
        }
    except Exception as exc:
        logger.warning("list_registry error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/registry/promote-best")
def promote_best(min_improvement: float = 0.01) -> dict[str, Any]:
    """Manually trigger auto-promote: promote best challenger if it beats champion."""
    try:
        from research.registry import ModelRegistry

        reg = ModelRegistry()
        promoted = reg.auto_promote_best(min_brier_improvement=min_improvement)
        champion = reg.get_champion()
        return {"promoted": promoted, "champion": champion}
    except Exception as exc:
        logger.warning("promote_best error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
