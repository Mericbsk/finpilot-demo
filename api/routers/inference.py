"""Inference endpoints — serve cached results and run live DRL inference."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.middleware.auth import require_auth

logger = logging.getLogger(__name__)

router = APIRouter(tags=["inference"])

_INFERENCE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "inference.json"


@router.get("/inference-cache")
def get_inference_cache():
    """Return the latest DRL inference results from data/inference.json."""
    if not _INFERENCE_PATH.exists():
        return {}
    with open(_INFERENCE_PATH) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# POST /inference/run — Live DRL inference
# ---------------------------------------------------------------------------


class InferenceRunRequest(BaseModel):
    symbols: list[str] = Field(default_factory=list, max_length=20)
    model_version: str = Field(default="active")


class InferenceRunResponse(BaseModel):
    results: dict[str, Any]
    model_id: str | None
    count: int
    timestamp: str


@router.post(
    "/inference/run", response_model=InferenceRunResponse, dependencies=[Depends(require_auth)]
)
def run_inference(req: InferenceRunRequest):
    """Run live DRL inference on given symbols and update the cache.

    If symbols list is empty, re-runs on the symbols already in the cache.
    Max 20 symbols per request.
    """
    # Lazy import — SB3 is heavy
    try:
        from drl.inference import DRLInference
    except ImportError as err:
        raise HTTPException(
            status_code=503,
            detail="DRL inference module not available. Install stable-baselines3.",
        ) from err

    # Determine symbols
    symbols = [s.strip().upper() for s in req.symbols if s.strip()]
    if not symbols:
        # Fall back to symbols already in cache
        if _INFERENCE_PATH.exists():
            with open(_INFERENCE_PATH) as f:
                cached = json.load(f)
            symbols = list(cached.keys())
        if not symbols:
            raise HTTPException(
                status_code=400,
                detail="No symbols provided and inference cache is empty.",
            )

    symbols = symbols[:20]  # Hard cap

    # Load model
    engine = DRLInference()
    loaded = engine.load_model(version=req.model_version)
    if not loaded:
        raise HTTPException(
            status_code=503,
            detail=f"Could not load DRL model (version={req.model_version}).",
        )

    # Run batch prediction
    predictions = engine.batch_predict(symbols)
    now = datetime.now(UTC).isoformat()

    # Build results dict
    results: dict[str, Any] = {}
    for pred in predictions:
        results[pred.symbol] = {
            "ai_score": round(pred.confidence * 100, 2),
            "signal": pred.action.name,
            "confidence": round(pred.confidence, 4),
            "regime": pred.regime or "unknown",
            "price": 0,  # price is in features, not exposed by PredictionResult
            "timestamp": now,
            "raw_action": pred.raw_action
            if isinstance(pred.raw_action, (int, float))
            else float(pred.raw_action),
            "suggested_position": pred.suggested_position,
            "kelly_fraction": pred.kelly_fraction,
            "model_id": pred.model_id,
        }

    # Merge with existing cache (update, don't replace)
    existing: dict[str, Any] = {}
    if _INFERENCE_PATH.exists():
        try:
            with open(_INFERENCE_PATH) as f:
                existing = json.load(f)
        except Exception:
            pass

    existing.update(results)

    # Write updated cache
    _INFERENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_INFERENCE_PATH, "w") as f:
        json.dump(existing, f, indent=2, default=str)

    logger.info("Inference run complete: %d symbols, model=%s", len(results), engine.model_id)

    return InferenceRunResponse(
        results=results,
        model_id=engine.model_id,
        count=len(results),
        timestamp=now,
    )
