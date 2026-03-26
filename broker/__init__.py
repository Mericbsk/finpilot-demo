"""
Alpaca Paper Trading Broker — Sprint 21.

Provides a clean interface for placing and managing orders on Alpaca's
paper trading environment.  Integrates with BuySignalRepository and
AlpacaOrderRepository for full audit trail.

Environment variables required:
    ALPACA_API_KEY      — Alpaca paper trading API key
    ALPACA_SECRET_KEY   — Alpaca paper trading secret key

Usage:
    from broker.alpaca_broker import AlpacaBroker

    broker = AlpacaBroker()
    order = broker.place_buy_order("AAPL", qty=5, limit_price=195.50)
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Alpaca SDK imports (graceful fallback)
# ---------------------------------------------------------------------------
try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.enums import OrderClass, OrderSide, OrderType, TimeInForce  # noqa: F401
    from alpaca.trading.requests import (
        LimitOrderRequest,
        MarketOrderRequest,
        StopLossRequest,
        TakeProfitRequest,
    )

    ALPACA_SDK_AVAILABLE = True
except ImportError:
    ALPACA_SDK_AVAILABLE = False
    logger.warning("alpaca-py not installed — broker disabled")

# ---------------------------------------------------------------------------
# DB imports
# ---------------------------------------------------------------------------
try:
    from auth.database import (
        AlpacaOrderRepository,
        BuySignalRepository,
        get_database,
    )

    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False


# ===========================================================================
# AlpacaBroker
# ===========================================================================


class AlpacaBroker:
    """Paper trading broker backed by the Alpaca API."""

    # Alpaca paper trading base URL
    PAPER_BASE_URL = "https://paper-api.alpaca.markets"

    def __init__(
        self,
        api_key: str | None = None,
        secret_key: str | None = None,
    ):
        self.api_key = api_key or self._resolve_key("ALPACA_API_KEY")
        self.secret_key = secret_key or self._resolve_key("ALPACA_SECRET_KEY")
        self._client: TradingClient | None = None

        # Repositories (lazy)
        self._order_repo: AlpacaOrderRepository | None = None
        self._signal_repo: BuySignalRepository | None = None

    @staticmethod
    def _resolve_key(name: str) -> str:
        """Resolve key from env → streamlit secrets."""
        val = os.environ.get(name, "")
        if val:
            return val
        try:
            import streamlit as st

            return st.secrets.get(name, "")
        except Exception:
            return ""

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_available(self) -> bool:
        return ALPACA_SDK_AVAILABLE and bool(self.api_key) and bool(self.secret_key)

    @property
    def client(self) -> TradingClient:
        if self._client is None:
            if not ALPACA_SDK_AVAILABLE:
                raise RuntimeError("alpaca-py is not installed")
            self._client = TradingClient(
                api_key=self.api_key,
                secret_key=self.secret_key,
                paper=True,
            )
        return self._client

    @property
    def order_repo(self) -> AlpacaOrderRepository | None:
        if self._order_repo is None and DB_AVAILABLE:
            self._order_repo = AlpacaOrderRepository(get_database())
        return self._order_repo

    @property
    def signal_repo(self) -> BuySignalRepository | None:
        if self._signal_repo is None and DB_AVAILABLE:
            self._signal_repo = BuySignalRepository(get_database())
        return self._signal_repo

    # ------------------------------------------------------------------
    # Account
    # ------------------------------------------------------------------

    def get_account(self) -> dict[str, Any]:
        """Return paper trading account info."""
        acct = self.client.get_account()
        return {
            "id": str(acct.id),
            "cash": float(acct.cash),
            "portfolio_value": float(acct.portfolio_value),
            "buying_power": float(acct.buying_power),
            "equity": float(acct.equity),
            "currency": acct.currency,
            "status": str(acct.status),
        }

    def get_positions(self) -> list[dict[str, Any]]:
        """Return all open positions."""
        positions = self.client.get_all_positions()
        return [
            {
                "symbol": p.symbol,
                "qty": float(p.qty),
                "avg_entry_price": float(p.avg_entry_price),
                "current_price": float(p.current_price),
                "market_value": float(p.market_value),
                "unrealized_pl": float(p.unrealized_pl),
                "unrealized_plpc": float(p.unrealized_plpc),
            }
            for p in positions
        ]

    # ------------------------------------------------------------------
    # Order placement
    # ------------------------------------------------------------------

    def place_buy_order(
        self,
        symbol: str,
        qty: int | float = 1,
        limit_price: float | None = None,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        buy_signal_id: int | None = None,
        time_in_force: str = "day",
    ) -> dict[str, Any]:
        """
        Place a BUY order on Alpaca paper trading.

        Args:
            symbol: Ticker (e.g. "AAPL")
            qty: Number of shares
            limit_price: If set, places a limit order; otherwise market order
            stop_loss: Stop-loss price (creates bracket via separate stop order)
            take_profit: Take-profit price (informational, logged)
            buy_signal_id: Link back to buy_signals table
            time_in_force: "day" or "gtc"

        Returns:
            Dict with order details.
        """
        tif = TimeInForce.DAY if time_in_force == "day" else TimeInForce.GTC

        # Use bracket order (OTO) when stop_loss or take_profit is provided
        use_bracket = bool(stop_loss or take_profit)

        order_kwargs = {
            "symbol": symbol,
            "qty": float(qty),
            "side": OrderSide.BUY,
            "time_in_force": tif,
        }

        if use_bracket:
            order_kwargs["order_class"] = OrderClass.BRACKET
            if stop_loss:
                order_kwargs["stop_loss"] = StopLossRequest(stop_price=round(stop_loss, 2))
            if take_profit:
                order_kwargs["take_profit"] = TakeProfitRequest(limit_price=round(take_profit, 2))

        if limit_price:
            order_kwargs["type"] = OrderType.LIMIT
            order_kwargs["limit_price"] = round(limit_price, 2)
            req = LimitOrderRequest(**order_kwargs)
        else:
            order_kwargs["type"] = OrderType.MARKET
            req = MarketOrderRequest(**order_kwargs)

        bracket_label = " (bracket)" if use_bracket else ""
        logger.info(
            f"Placing BUY order: {symbol} x{qty} @ {limit_price or 'MARKET'}{bracket_label}"
        )
        order = self.client.submit_order(req)
        result = self._order_to_dict(order)

        # Persist to DB
        if self.order_repo:
            self.order_repo.save(
                {
                    "order_id": result["order_id"],
                    "buy_signal_id": buy_signal_id,
                    "symbol": symbol,
                    "side": "buy",
                    "qty": float(qty),
                    "order_type": f"{'limit' if limit_price else 'market'}{'_bracket' if use_bracket else ''}",
                    "limit_price": limit_price,
                    "stop_price": stop_loss,
                    "time_in_force": time_in_force,
                    "status": result["status"],
                    "submitted_at": result["submitted_at"],
                    "raw_response": json.dumps(result, default=str),
                }
            )

        # Link to buy signal
        if buy_signal_id and self.signal_repo:
            self.signal_repo.link_alpaca_order(buy_signal_id, result["order_id"])

        logger.info(f"Order placed: {result['order_id']} — {symbol} — {result['status']}")
        return result

    def _place_stop_loss(
        self,
        symbol: str,
        qty: int | float,
        stop_price: float,
        tif: TimeInForce,
        buy_signal_id: int | None,
    ) -> dict[str, Any]:
        """Place a sell stop order to protect a position."""
        from alpaca.trading.requests import StopOrderRequest

        req = StopOrderRequest(
            symbol=symbol,
            qty=float(qty),
            side=OrderSide.SELL,
            type=OrderType.STOP,
            time_in_force=TimeInForce.GTC,  # Stop-losses should be GTC
            stop_price=round(stop_price, 2),
        )
        order = self.client.submit_order(req)
        result = self._order_to_dict(order)

        if self.order_repo:
            self.order_repo.save(
                {
                    "order_id": result["order_id"],
                    "buy_signal_id": buy_signal_id,
                    "symbol": symbol,
                    "side": "sell",
                    "qty": float(qty),
                    "order_type": "stop",
                    "stop_price": stop_price,
                    "time_in_force": "gtc",
                    "status": result["status"],
                    "submitted_at": result["submitted_at"],
                    "raw_response": json.dumps(result, default=str),
                }
            )

        logger.info(f"Stop-loss placed: {symbol} @ ${stop_price}")
        return result

    # ------------------------------------------------------------------
    # Order management
    # ------------------------------------------------------------------

    def get_orders(self, status: str = "open") -> list[dict[str, Any]]:
        """Get orders by status (open, closed, all)."""
        from alpaca.trading.requests import GetOrdersRequest

        req = GetOrdersRequest(status=status)
        orders = self.client.get_orders(req)
        return [self._order_to_dict(o) for o in orders]

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order."""
        try:
            self.client.cancel_order_by_id(order_id)
            if self.order_repo:
                self.order_repo.update_status(order_id, "canceled")
            return True
        except Exception as e:
            logger.error(f"Cancel failed for {order_id}: {e}")
            return False

    def cancel_all_orders(self) -> int:
        """Cancel all open orders."""
        statuses = self.client.cancel_orders()
        return len(statuses) if statuses else 0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _order_to_dict(order: Any) -> dict[str, Any]:
        return {
            "order_id": str(order.id),
            "symbol": order.symbol,
            "side": str(order.side),
            "qty": float(order.qty) if order.qty else 0,
            "filled_qty": float(order.filled_qty) if order.filled_qty else 0,
            "type": str(order.type),
            "limit_price": float(order.limit_price) if order.limit_price else None,
            "stop_price": float(order.stop_price) if order.stop_price else None,
            "status": str(order.status),
            "submitted_at": str(order.submitted_at) if order.submitted_at else None,
            "filled_at": str(order.filled_at) if order.filled_at else None,
            "filled_avg_price": float(order.filled_avg_price) if order.filled_avg_price else None,
        }

    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        risk_per_trade: float = 0.02,
        max_position_pct: float = 0.10,
    ) -> int:
        """
        Calculate shares to buy based on risk management.

        Args:
            entry_price: Buy price
            stop_loss: Stop-loss price
            risk_per_trade: Max fraction of portfolio to risk (default 2%)
            max_position_pct: Max fraction of portfolio for one position (default 10%)

        Returns:
            Number of shares (integer).
        """
        try:
            acct = self.get_account()
            portfolio_value = acct["portfolio_value"]
        except Exception:
            portfolio_value = 100_000  # fallback

        risk_amount = portfolio_value * risk_per_trade
        price_risk = abs(entry_price - stop_loss)

        if price_risk <= 0:
            price_risk = entry_price * 0.02  # fallback: 2% of price

        shares_by_risk = int(risk_amount / price_risk)
        max_shares = int((portfolio_value * max_position_pct) / entry_price)

        return max(1, min(shares_by_risk, max_shares))
