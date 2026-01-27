"""
Portfolio Management for FinPilot.

Provides portfolio, position, and trade management functionality.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================


class TradeSide(Enum):
    """Trade side enum."""

    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order type enum."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    """Order status enum."""

    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


# ============================================================================
# DATA CLASSES
# ============================================================================


@dataclass
class Position:
    """
    Represents a portfolio position.

    Attributes:
        id: Unique position ID
        symbol: Stock symbol
        shares: Number of shares
        avg_price: Average purchase price
        opened_at: When position was opened
        updated_at: Last update time
    """

    id: str
    symbol: str
    shares: float
    avg_price: float
    opened_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def cost_basis(self) -> float:
        """Total cost basis."""
        return self.shares * self.avg_price

    def market_value(self, current_price: float) -> float:
        """Calculate current market value."""
        return self.shares * current_price

    def unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized P&L."""
        return self.market_value(current_price) - self.cost_basis

    def unrealized_pnl_pct(self, current_price: float) -> float:
        """Calculate unrealized P&L percentage."""
        if self.cost_basis == 0:
            return 0.0
        return (self.unrealized_pnl(current_price) / self.cost_basis) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "shares": self.shares,
            "avg_price": self.avg_price,
            "cost_basis": self.cost_basis,
            "opened_at": self.opened_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Position":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            symbol=data["symbol"],
            shares=data["shares"],
            avg_price=data["avg_price"],
            opened_at=(
                datetime.fromisoformat(data["opened_at"])
                if isinstance(data.get("opened_at"), str)
                else data.get("opened_at", datetime.utcnow())
            ),
            updated_at=(
                datetime.fromisoformat(data["updated_at"])
                if isinstance(data.get("updated_at"), str)
                else data.get("updated_at", datetime.utcnow())
            ),
        )


@dataclass
class Trade:
    """
    Represents a trade.

    Attributes:
        id: Unique trade ID
        portfolio_id: Portfolio this trade belongs to
        symbol: Stock symbol
        side: Buy or sell
        shares: Number of shares
        price: Execution price
        total: Total value
        commission: Trading commission
        executed_at: Execution time
        notes: Optional notes
    """

    id: str
    portfolio_id: str
    symbol: str
    side: TradeSide
    shares: float
    price: float
    total: float = 0.0
    commission: float = 0.0
    executed_at: datetime = field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

    def __post_init__(self):
        if self.total == 0:
            self.total = self.shares * self.price

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "portfolio_id": self.portfolio_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "shares": self.shares,
            "price": self.price,
            "total": self.total,
            "commission": self.commission,
            "executed_at": self.executed_at.isoformat(),
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Trade":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            portfolio_id=data["portfolio_id"],
            symbol=data["symbol"],
            side=TradeSide(data["side"]),
            shares=data["shares"],
            price=data["price"],
            total=data.get("total", 0),
            commission=data.get("commission", 0),
            executed_at=(
                datetime.fromisoformat(data["executed_at"])
                if isinstance(data.get("executed_at"), str)
                else data.get("executed_at", datetime.utcnow())
            ),
            notes=data.get("notes"),
        )


@dataclass
class Portfolio:
    """
    Represents a user's portfolio.

    Attributes:
        id: Unique portfolio ID
        user_id: Owner user ID
        cash: Available cash
        positions: List of positions
        created_at: Creation time
        updated_at: Last update time
    """

    id: str
    user_id: str
    cash: float = 0.0
    positions: List[Position] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def position_count(self) -> int:
        """Number of positions."""
        return len(self.positions)

    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position by symbol."""
        for pos in self.positions:
            if pos.symbol == symbol:
                return pos
        return None

    def total_cost_basis(self) -> float:
        """Total cost basis of all positions."""
        return sum(pos.cost_basis for pos in self.positions)

    def total_market_value(self, prices: Dict[str, float]) -> float:
        """Calculate total market value given current prices."""
        total = self.cash
        for pos in self.positions:
            if pos.symbol in prices:
                total += pos.market_value(prices[pos.symbol])
        return total

    def total_unrealized_pnl(self, prices: Dict[str, float]) -> float:
        """Calculate total unrealized P&L."""
        return sum(
            pos.unrealized_pnl(prices.get(pos.symbol, pos.avg_price)) for pos in self.positions
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "cash": self.cash,
            "positions": [pos.to_dict() for pos in self.positions],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Portfolio":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            user_id=data["user_id"],
            cash=data.get("cash", 0),
            positions=[Position.from_dict(p) for p in data.get("positions", [])],
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if isinstance(data.get("created_at"), str)
                else data.get("created_at", datetime.utcnow())
            ),
            updated_at=(
                datetime.fromisoformat(data["updated_at"])
                if isinstance(data.get("updated_at"), str)
                else data.get("updated_at", datetime.utcnow())
            ),
        )


@dataclass
class Watchlist:
    """
    Represents a user's watchlist.

    Attributes:
        id: Unique watchlist ID
        user_id: Owner user ID
        name: Watchlist name
        symbols: List of symbols
        created_at: Creation time
        updated_at: Last update time
    """

    id: str
    user_id: str
    name: str
    symbols: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_symbol(self, symbol: str) -> bool:
        """Add symbol to watchlist."""
        if symbol not in self.symbols:
            self.symbols.append(symbol)
            self.updated_at = datetime.utcnow()
            return True
        return False

    def remove_symbol(self, symbol: str) -> bool:
        """Remove symbol from watchlist."""
        if symbol in self.symbols:
            self.symbols.remove(symbol)
            self.updated_at = datetime.utcnow()
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "symbols": self.symbols,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# ============================================================================
# PORTFOLIO MANAGER
# ============================================================================


class PortfolioManager:
    """
    Manages portfolio operations.

    Example:
        >>> from auth.database import Database, PortfolioRepository
        >>> db = Database()
        >>> repo = PortfolioRepository(db)
        >>> manager = PortfolioManager(repo)
        >>>
        >>> portfolio = manager.create_portfolio("user_123", initial_cash=10000)
        >>> manager.execute_trade(portfolio.id, "AAPL", TradeSide.BUY, 10, 150.0)
    """

    def __init__(self, repository=None):
        """
        Initialize portfolio manager.

        Args:
            repository: PortfolioRepository instance (optional)
        """
        self.repository = repository
        self._portfolios: Dict[str, Portfolio] = {}  # In-memory cache

    def create_portfolio(self, user_id: str, initial_cash: float = 0.0) -> Portfolio:
        """
        Create a new portfolio.

        Args:
            user_id: Owner user ID
            initial_cash: Initial cash balance

        Returns:
            New Portfolio instance
        """
        portfolio = Portfolio(id=str(uuid.uuid4()), user_id=user_id, cash=initial_cash)

        if self.repository:
            self.repository.save(portfolio.to_dict())

        self._portfolios[portfolio.id] = portfolio
        logger.info(f"Created portfolio {portfolio.id} for user {user_id}")

        return portfolio

    def get_portfolio(self, portfolio_id: str) -> Optional[Portfolio]:
        """Get portfolio by ID."""
        if portfolio_id in self._portfolios:
            return self._portfolios[portfolio_id]

        if self.repository:
            data = self.repository.get_by_id(portfolio_id)
            if data:
                portfolio = Portfolio.from_dict(data)
                self._portfolios[portfolio_id] = portfolio
                return portfolio

        return None

    def get_user_portfolio(self, user_id: str) -> Optional[Portfolio]:
        """Get portfolio for a user."""
        # Check cache
        for portfolio in self._portfolios.values():
            if portfolio.user_id == user_id:
                return portfolio

        # Check database
        if self.repository:
            data = self.repository.get_by_user(user_id)
            if data:
                portfolio = Portfolio.from_dict(data)
                self._portfolios[portfolio.id] = portfolio
                return portfolio

        return None

    def execute_trade(
        self,
        portfolio_id: str,
        symbol: str,
        side: TradeSide,
        shares: float,
        price: float,
        commission: float = 0.0,
        notes: Optional[str] = None,
    ) -> Trade:
        """
        Execute a trade.

        Args:
            portfolio_id: Portfolio ID
            symbol: Stock symbol
            side: Buy or sell
            shares: Number of shares
            price: Execution price
            commission: Trading commission
            notes: Optional notes

        Returns:
            Trade instance

        Raises:
            ValueError: If insufficient cash or shares
        """
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio not found: {portfolio_id}")

        total = shares * price

        if side == TradeSide.BUY:
            total_cost = total + commission
            if portfolio.cash < total_cost:
                raise ValueError(f"Insufficient cash: {portfolio.cash} < {total_cost}")

            portfolio.cash -= total_cost

            # Update or create position
            position = portfolio.get_position(symbol)
            if position:
                # Average up/down
                new_shares = position.shares + shares
                new_avg = ((position.shares * position.avg_price) + total) / new_shares
                position.shares = new_shares
                position.avg_price = new_avg
                position.updated_at = datetime.utcnow()
            else:
                position = Position(
                    id=str(uuid.uuid4()), symbol=symbol, shares=shares, avg_price=price
                )
                portfolio.positions.append(position)

        elif side == TradeSide.SELL:
            position = portfolio.get_position(symbol)
            if not position:
                raise ValueError(f"No position for {symbol}")

            if position.shares < shares:
                raise ValueError(f"Insufficient shares: {position.shares} < {shares}")

            position.shares -= shares
            position.updated_at = datetime.utcnow()

            if position.shares == 0:
                portfolio.positions.remove(position)

            portfolio.cash += total - commission

        portfolio.updated_at = datetime.utcnow()

        # Create trade record
        trade = Trade(
            id=str(uuid.uuid4()),
            portfolio_id=portfolio_id,
            symbol=symbol,
            side=side,
            shares=shares,
            price=price,
            total=total,
            commission=commission,
            notes=notes,
        )

        # Persist
        if self.repository:
            self.repository.save(portfolio.to_dict())
            self.repository.add_trade(trade.to_dict())

        logger.info(f"Trade executed: {side.value} {shares} {symbol} @ {price}")

        return trade

    def deposit(self, portfolio_id: str, amount: float) -> float:
        """Deposit cash to portfolio."""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio not found: {portfolio_id}")

        portfolio.cash += amount
        portfolio.updated_at = datetime.utcnow()

        if self.repository:
            self.repository.save(portfolio.to_dict())

        logger.info(f"Deposited {amount} to portfolio {portfolio_id}")
        return portfolio.cash

    def withdraw(self, portfolio_id: str, amount: float) -> float:
        """Withdraw cash from portfolio."""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio not found: {portfolio_id}")

        if portfolio.cash < amount:
            raise ValueError(f"Insufficient cash: {portfolio.cash} < {amount}")

        portfolio.cash -= amount
        portfolio.updated_at = datetime.utcnow()

        if self.repository:
            self.repository.save(portfolio.to_dict())

        logger.info(f"Withdrew {amount} from portfolio {portfolio_id}")
        return portfolio.cash

    def get_trades(
        self, portfolio_id: str, symbol: Optional[str] = None, limit: int = 100
    ) -> List[Trade]:
        """Get trade history."""
        if self.repository:
            trades_data = self.repository.get_trades(portfolio_id, symbol, limit)
            return [Trade.from_dict(t) for t in trades_data]
        return []


__all__ = [
    "TradeSide",
    "OrderType",
    "OrderStatus",
    "Position",
    "Trade",
    "Portfolio",
    "Watchlist",
    "PortfolioManager",
]
