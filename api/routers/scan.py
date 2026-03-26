"""POST /api/v1/scan — Run the real technical-analysis scanner."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["scan"])


class ScanRequest(BaseModel):
    symbols: list[str] = Field(..., max_length=300)
    kelly_fraction: float = Field(0.5, ge=0.0, le=1.0)


@router.post("/scan")
def run_scan(req: ScanRequest):
    """Run the scanner's evaluate_symbols_parallel on the given symbols.

    Returns dict keyed by symbol with scanner evaluation data.
    """
    from scanner import evaluate_symbols_parallel

    results = evaluate_symbols_parallel(
        symbols=req.symbols,
        kelly_fraction=req.kelly_fraction,
    )
    # Convert list → dict keyed by symbol
    out: dict = {}
    for r in results:
        sym = r.get("symbol") or r.get("ticker")
        if sym:
            out[sym] = r
    return out
