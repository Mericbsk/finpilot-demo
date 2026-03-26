"""GET /api/v1/models — List all DRL models from registry."""

from __future__ import annotations

import dataclasses

from drl.model_registry import ModelRegistry
from fastapi import APIRouter

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
