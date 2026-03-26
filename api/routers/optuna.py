"""GET /api/v1/optuna/results — Serve real Optuna hyperparameter search results."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["optuna"])

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

_OPTUNA_FILES = {
    "conservative": _DATA_DIR / "optuna_conservative_results.json",
    "momentum": _DATA_DIR / "optuna_momentum_results.json",
    "range": _DATA_DIR / "optuna_range_results.json",
    "swing": _DATA_DIR / "optuna_swing_results.json",
}


@router.get("/optuna/agents")
def list_optuna_agents():
    """Return available agents that have Optuna results."""
    return [k for k, v in _OPTUNA_FILES.items() if v.exists()]


@router.get("/optuna/results")
def get_optuna_results(agent: str = "conservative"):
    """Return Optuna trial results for a specific agent.

    Query: ?agent=conservative|momentum|range|swing
    """
    path = _OPTUNA_FILES.get(agent)
    if not path or not path.exists():
        raise HTTPException(404, f"No Optuna results for agent '{agent}'")
    with open(path) as f:
        return json.load(f)
