"""Trade router — Alpaca paper trading from the frontend."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["trade"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class OrderRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10)
    qty: float = Field(0, ge=0, description="Shares to buy. 0 = auto-calculate from risk.")
    limit_price: float | None = Field(None, ge=0)
    stop_loss: float | None = Field(None, ge=0)
    take_profit: float | None = Field(None, ge=0)
    time_in_force: str = Field("day", pattern=r"^(day|gtc)$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_broker():
    """Lazy-import broker so module loads even without alpaca-py."""
    from broker import AlpacaBroker

    b = AlpacaBroker()
    if not b.is_available:
        raise HTTPException(
            status_code=503,
            detail="Alpaca not configured. Set ALPACA_API_KEY and ALPACA_SECRET_KEY.",
        )
    return b


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/trade/account")
def get_account():
    """Return Alpaca paper trading account info."""
    broker = _get_broker()
    try:
        return broker.get_account()
    except Exception as e:
        logger.error(f"Account fetch failed: {e}")
        raise HTTPException(status_code=502, detail=str(e)) from e


@router.get("/trade/positions")
def get_positions():
    """Return all open Alpaca positions."""
    broker = _get_broker()
    try:
        return broker.get_positions()
    except Exception as e:
        logger.error(f"Positions fetch failed: {e}")
        raise HTTPException(status_code=502, detail=str(e)) from e


@router.get("/trade/orders")
def get_orders(status: str = "open"):
    """Return orders (open / closed / all)."""
    broker = _get_broker()
    try:
        return broker.get_orders(status=status)
    except Exception as e:
        logger.error(f"Orders fetch failed: {e}")
        raise HTTPException(status_code=502, detail=str(e)) from e


@router.post("/trade/buy")
def place_buy(req: OrderRequest):
    """Place a BUY order on Alpaca paper trading.

    If qty=0, auto-calculates position size via 2% risk rule.
    If stop_loss + take_profit are provided, creates a bracket order.
    """
    broker = _get_broker()

    qty = req.qty
    entry = req.limit_price or 0

    # Auto-calculate position size from risk management
    if qty == 0 and req.stop_loss and entry > 0:
        qty = broker.calculate_position_size(entry, req.stop_loss)
    elif qty == 0 and entry > 0:
        # Fallback: buy ~$500 worth
        qty = max(1, int(500 / entry))
    elif qty == 0:
        qty = 1

    try:
        result = broker.place_buy_order(
            symbol=req.symbol.upper(),
            qty=qty,
            limit_price=req.limit_price,
            stop_loss=req.stop_loss,
            take_profit=req.take_profit,
            time_in_force=req.time_in_force,
        )
        return result
    except Exception as e:
        logger.error(f"Order failed for {req.symbol}: {e}")
        raise HTTPException(status_code=502, detail=str(e)) from e


@router.delete("/trade/orders/{order_id}")
def cancel_order(order_id: str):
    """Cancel a specific order."""
    broker = _get_broker()
    ok = broker.cancel_order(order_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Cancel failed")
    return {"status": "canceled", "order_id": order_id}
