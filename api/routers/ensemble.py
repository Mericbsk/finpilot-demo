"""POST /api/v1/ensemble — Run ensemble router predictions."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.middleware.auth import require_auth

router = APIRouter(tags=["ensemble"])


class EnsembleRequest(BaseModel):
    symbols: list[str] = Field(..., max_length=50)
    max_symbols: int = Field(20, ge=1, le=50)


@router.post("/ensemble", dependencies=[Depends(require_auth)])
def ensemble_predict(req: EnsembleRequest):
    """Run multi-agent ensemble predictions.

    Uses get_ensemble_predictions() which internally loads agents,
    detects regimes, and runs voting.
    """
    from drl.ensemble_router import get_ensemble_predictions

    results = get_ensemble_predictions(
        symbols=req.symbols[: req.max_symbols],
        max_symbols=req.max_symbols,
    )
    return results
