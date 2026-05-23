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
_CACHE_MAX_AGE_HOURS = 24

# Memory cache: (data, status, mtime_ns). Invalidated when file mtime changes.
_mem_cache: tuple[dict, dict[str, Any], int] | None = None


def _load_cached_inference() -> tuple[dict, dict[str, Any]]:
    """Load inference.json with mtime-based memory cache.

    Returns:
        (data, status) — data is symbol-keyed dict; status from _check_drl_cache.
        Both are empty/invalid when file missing or unreadable.
    """
    global _mem_cache
    if not _INFERENCE_PATH.exists():
        return {}, _check_drl_cache({})
    try:
        mtime = _INFERENCE_PATH.stat().st_mtime_ns
    except OSError:
        return {}, _check_drl_cache({})

    if _mem_cache is not None and _mem_cache[2] == mtime:
        return _mem_cache[0], _mem_cache[1]

    try:
        data = json.loads(_INFERENCE_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("inference.json read failed: %s", exc)
        return {}, _check_drl_cache({})

    status = _check_drl_cache(data)
    _mem_cache = (data, status, mtime)
    return data, status


def _check_drl_cache(cached: dict) -> dict[str, Any]:
    """Validate DRL cache quality. Returns a metadata dict consumed by callers.

    Checks performed:
    - ``fresh``: cache timestamp is within _CACHE_MAX_AGE_HOURS
    - ``real``: confidence values are not all identical (default/fallback guard)
    - ``valid``: both conditions met — safe to use in scoring

    Returns dict with keys: valid, fresh, real, age_hours, symbol_count, warning.
    """
    if not cached:
        return {
            "valid": False,
            "fresh": False,
            "real": False,
            "age_hours": None,
            "symbol_count": 0,
            "warning": "Cache is empty",
        }

    # Age check — use first entry's timestamp
    age_hours: float | None = None
    fresh = False
    try:
        ts_str = next(iter(cached.values()), {}).get("timestamp", "")
        if ts_str:
            ts = datetime.fromisoformat(ts_str)
            age_hours = (datetime.now(UTC) - ts).total_seconds() / 3600
            fresh = age_hours < _CACHE_MAX_AGE_HOURS
    except Exception:
        fresh = False

    # Identity check — if all confidences are the same value it's a fallback/default
    confidences = [float(v.get("confidence", 0)) for v in cached.values() if v]
    real = not (len(confidences) > 1 and len(set(confidences)) == 1)

    valid = fresh and real
    warning: str | None = None
    if not fresh:
        age_str = f"{age_hours:.1f}h" if age_hours is not None else "unknown"
        warning = f"DRL cache is stale ({age_str} old). Re-run inference to update."
    elif not real:
        warning = (
            "DRL cache contains uniform confidence values — model may not be loaded correctly."
        )

    return {
        "valid": valid,
        "fresh": fresh,
        "real": real,
        "age_hours": round(age_hours, 1) if age_hours is not None else None,
        "symbol_count": len(cached),
        "warning": warning,
    }


@router.get("/inference-cache")
def get_inference_cache():
    """Return the latest DRL inference results plus cache validity metadata."""
    data, status = _load_cached_inference()
    return {"results": data, "cache_status": status}


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
