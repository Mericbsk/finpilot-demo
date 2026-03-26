"""GET /api/v1/inference-cache — Serve cached DRL inference results."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(tags=["inference"])

_INFERENCE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "inference.json"


@router.get("/inference-cache")
def get_inference_cache():
    """Return the latest DRL inference results from data/inference.json."""
    if not _INFERENCE_PATH.exists():
        return {}
    with open(_INFERENCE_PATH) as f:
        return json.load(f)
