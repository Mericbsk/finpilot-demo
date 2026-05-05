"""GET /api/v1/models — List all DRL models from registry."""

from __future__ import annotations

import dataclasses

from drl.model_registry import ModelRegistry
from fastapi import APIRouter, Depends, HTTPException

from api.middleware.auth import require_admin

router = APIRouter(tags=["models"])

_registry = ModelRegistry()


@router.get("/models")
def list_models(algorithm: str | None = None, tags: str | None = None):
    """Return all models from registry.json.

    Optional filters: ?algorithm=PPO  or  ?tags=trend,momentum
    """
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    models = _registry.list_models(algorithm=algorithm, tags=tag_list)
    return [dataclasses.asdict(m) for m in models]


@router.get("/models/{model_id}")
def get_model(model_id: str):
    """Return single model metadata."""
    meta = _registry.get_metadata(model_id)
    return dataclasses.asdict(meta)


@router.post("/models/{model_id}/activate", dependencies=[Depends(require_admin)])
def activate_model(model_id: str):
    """Set a model as the active version for its name group."""
    try:
        _registry.set_active(model_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    meta = _registry.get_metadata(model_id)
    return {"ok": True, "model_id": model_id, "name": meta.name}


@router.post("/models/activate-best", dependencies=[Depends(require_admin)])
def activate_best_models():
    """For each unique model name, activate the model with the highest Sharpe ratio.

    Returns a summary of which model was activated per name group.
    """
    all_models = _registry.list_models()
    # Group by name
    groups: dict[str, list] = {}
    for m in all_models:
        groups.setdefault(m.name, []).append(m)

    activated = []
    for name, candidates in groups.items():
        # Pick best by sharpe_ratio; fallback to total_return
        with_sharpe = [m for m in candidates if m.metrics.get("sharpe_ratio") is not None]
        if with_sharpe:
            best = max(with_sharpe, key=lambda m: m.metrics["sharpe_ratio"])
        else:
            best = max(candidates, key=lambda m: m.metrics.get("total_return", 0))
        _registry.set_active(best.model_id)
        activated.append(
            {
                "name": name,
                "model_id": best.model_id,
                "sharpe": best.metrics.get("sharpe_ratio"),
                "total_return": best.metrics.get("total_return"),
            }
        )

    return {"activated": activated, "count": len(activated)}
