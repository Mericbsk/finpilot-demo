# -*- coding: utf-8 -*-
"""
FinPilot Backtesting Engine
===========================

Historical strategy backtesting with:
- Multi-strategy support
- Performance metrics (Sharpe, Drawdown, Win Rate)
- Trade logging and analysis
- Position sizing with Kelly criterion
- Slippage and commission modeling

Usage:
    from core.backtest import Backtest, Strategy, BacktestResult

    class MyStrategy(Strategy):
        def generate_signals(self, data):
            ...

    bt = Backtest(strategy=MyStrategy(), data=df)
    result = bt.run()
    print(result.summary())
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ============================================
# 📊 Core Types
# ============================================


class TradeDirection(str, Enum):
    """Trade direction enum."""

    LONG = "long"
    SHORT = "short"


class TradeStatus(str, Enum):
    """Trade status enum."""

    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


@dataclass
class Trade:
    """Single trade record."""

    id: str
    symbol: str
    direction: TradeDirection
    entry_date: datetime
    entry_price: float
    shares: float
    exit_date: Optional[datetime] = None
    exit_price: Optional[float] = None
    status: TradeStatus = TradeStatus.OPEN
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    commission: float = 0.0
    slippage: float = 0.0
    tags: List[str] = field(default_factory=list)

    @property
    def pnl(self) -> float:
        """Calculate profit/loss."""
        if self.exit_price is None:
            return 0.0

        if self.direction == TradeDirection.LONG:
            gross = (self.exit_price - self.entry_price) * self.shares
        else:
            gross = (self.entry_price - self.exit_price) * self.shares

        return gross - self.commission - self.slippage

    @property
    def pnl_percent(self) -> float:
        """Calculate percentage P&L."""
        cost = self.entry_price * self.shares
        if cost == 0:
            return 0.0
        return (self.pnl / cost) * 100

    @property
    def holding_days(self) -> int:
        """Calculate holding period in days."""
        if self.exit_date is None:
            return 0
        return (self.exit_date - self.entry_date).days

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "direction": self.direction.value,
            "entry_date": self.entry_date.isoformat(),
            "entry_price": self.entry_price,
            "shares": self.shares,
            "exit_date": self.exit_date.isoformat() if self.exit_date else None,
            "exit_price": self.exit_price,
            "status": self.status.value,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "pnl": self.pnl,
            "pnl_percent": self.pnl_percent,
            "holding_days": self.holding_days,
            "tags": self.tags,
        }


@dataclass
class Signal:
    """Trading signal."""

    date: datetime
    symbol: str
    direction: TradeDirection
    strength: float  # 0-1
    price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================
# 📈 Strategy Base Class
# ============================================


class Strategy(ABC):
    """
    Abstract base class for trading strategies.

    Subclass and implement generate_signals() to create custom strategies.
    """

    name: str = "BaseStrategy"
    description: str = "Base strategy class"

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        self.params = params or {}

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame, symbol: str) -> List[Signal]:
        """
        Generate trading signals from data.

        Args:
            data: OHLCV DataFrame with indicators
            symbol: Symbol being analyzed

        Returns:
            List of Signal objects
        """
        pass

    def on_trade_open(self, trade: Trade) -> None:
        """Called when a trade is opened."""
        pass

    def on_trade_close(self, trade: Trade) -> None:
        """Called when a trade is closed."""
        pass


# ============================================
# 📊 Built-in Strategies
# ============================================


class MomentumStrategy(Strategy):
    """
    Momentum-based strategy using RSI and moving averages.
    """

    name = "Momentum"
    description = "RSI + EMA crossover momentum strategy"

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        defaults = {
            "rsi_period": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "ema_fast": 12,
            "ema_slow": 26,
            "min_strength": 0.6,
        }
        super().__init__({**defaults, **(params or {})})

    def generate_signals(self, data: pd.DataFrame, symbol: str) -> List[Signal]:
        signals = []

        if len(data) < 50:
            return signals

        # Calculate indicators if not present
        df = data.copy()
        if "rsi" not in df.columns:
            df["rsi"] = self._calculate_rsi(df["Close"], self.params["rsi_period"])
        if "ema_fast" not in df.columns:
            df["ema_fast"] = df["Close"].ewm(span=self.params["ema_fast"]).mean()
        if "ema_slow" not in df.columns:
            df["ema_slow"] = df["Close"].ewm(span=self.params["ema_slow"]).mean()

        for i in range(1, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i - 1]
            date = df.index[i] if isinstance(df.index[i], datetime) else datetime.now()

            # Buy signal: RSI oversold + EMA crossover
            if (
                prev["rsi"] < self.params["rsi_oversold"]
                and row["rsi"] > self.params["rsi_oversold"]
                and row["ema_fast"] > row["ema_slow"]
            ):

                strength = min(1.0, (self.params["rsi_oversold"] - prev["rsi"]) / 20 + 0.5)
                if strength >= self.params["min_strength"]:
                    signals.append(
                        Signal(
                            date=date,
                            symbol=symbol,
                            direction=TradeDirection.LONG,
                            strength=strength,
                            price=row["Close"],
                            stop_loss=row["Close"] * 0.95,
                            take_profit=row["Close"] * 1.10,
                        )
                    )

            # Sell signal: RSI overbought + EMA crossover
            elif (
                prev["rsi"] > self.params["rsi_overbought"]
                and row["rsi"] < self.params["rsi_overbought"]
                and row["ema_fast"] < row["ema_slow"]
            ):

                strength = min(1.0, (prev["rsi"] - self.params["rsi_overbought"]) / 20 + 0.5)
                if strength >= self.params["min_strength"]:
                    signals.append(
                        Signal(
                            date=date,
                            symbol=symbol,
                            direction=TradeDirection.SHORT,
                            strength=strength,
                            price=row["Close"],
                        )
                    )

        return signals

    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))


class TrendFollowingStrategy(Strategy):
    """
    Trend following strategy using Bollinger Bands and MACD.
    """

    name = "TrendFollowing"
    description = "Bollinger Bands + MACD trend strategy"

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        defaults = {
            "bb_period": 20,
            "bb_std": 2.0,
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
        }
        super().__init__({**defaults, **(params or {})})

    def generate_signals(self, data: pd.DataFrame, symbol: str) -> List[Signal]:
        signals = []

        if len(data) < 50:
            return signals

        df = data.copy()

        # Bollinger Bands
        df["bb_mid"] = df["Close"].rolling(self.params["bb_period"]).mean()
        df["bb_std"] = df["Close"].rolling(self.params["bb_period"]).std()
        df["bb_upper"] = df["bb_mid"] + self.params["bb_std"] * df["bb_std"]
        df["bb_lower"] = df["bb_mid"] - self.params["bb_std"] * df["bb_std"]

        # MACD
        ema_fast = df["Close"].ewm(span=self.params["macd_fast"]).mean()
        ema_slow = df["Close"].ewm(span=self.params["macd_slow"]).mean()
        df["macd"] = ema_fast - ema_slow
        df["macd_signal"] = df["macd"].ewm(span=self.params["macd_signal"]).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        for i in range(1, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i - 1]
            date = df.index[i] if isinstance(df.index[i], datetime) else datetime.now()

            # Buy: Price touches lower band + MACD crossover
            if row["Close"] <= row["bb_lower"] and prev["macd_hist"] < 0 and row["macd_hist"] > 0:

                signals.append(
                    Signal(
                        date=date,
                        symbol=symbol,
                        direction=TradeDirection.LONG,
                        strength=0.7,
                        price=row["Close"],
                        stop_loss=row["bb_lower"] * 0.98,
                        take_profit=row["bb_mid"],
                    )
                )

            # Sell: Price touches upper band + MACD crossover down
            elif row["Close"] >= row["bb_upper"] and prev["macd_hist"] > 0 and row["macd_hist"] < 0:

                signals.append(
                    Signal(
                        date=date,
                        symbol=symbol,
                        direction=TradeDirection.SHORT,
                        strength=0.7,
                        price=row["Close"],
                    )
                )

        return signals


# ============================================
# 🏦 Portfolio & Position Management
# ============================================


@dataclass
class Portfolio:
    """Portfolio state during backtest."""

    initial_capital: float
    cash: float = 0.0
    equity: float = 0.0
    positions: Dict[str, float] = field(default_factory=dict)  # symbol -> shares
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[Tuple[datetime, float]] = field(default_factory=list)

    def __post_init__(self):
        self.cash = self.initial_capital
        self.equity = self.initial_capital

    @property
    def total_value(self) -> float:
        """Total portfolio value (cash + positions)."""
        return self.cash + self.equity

    @property
    def open_positions(self) -> Dict[str, float]:
        """Currently open positions."""
        return {k: v for k, v in self.positions.items() if v != 0}

    @property
    def closed_trades(self) -> List[Trade]:
        """All closed trades."""
        return [t for t in self.trades if t.status == TradeStatus.CLOSED]


# ============================================
# 📊 Backtest Result & Metrics
# ============================================


@dataclass
class BacktestResult:
    """Backtest execution result with performance metrics."""

    strategy_name: str
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    trades: List[Trade]
    equity_curve: pd.DataFrame

    # Calculated metrics
    total_return: float = 0.0
    annual_return: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_trade_pnl: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0

    def __post_init__(self):
        self._calculate_metrics()

    def _calculate_metrics(self) -> None:
        """Calculate all performance metrics."""
        closed = [t for t in self.trades if t.status == TradeStatus.CLOSED]

        self.total_trades = len(closed)
        if self.total_trades == 0:
            return

        # P&L metrics
        pnls = [t.pnl for t in closed]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]

        self.winning_trades = len(wins)
        self.losing_trades = len(losses)
        self.win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0

        self.avg_trade_pnl = np.mean(pnls) if pnls else 0
        self.avg_win = np.mean(wins) if wins else 0
        self.avg_loss = np.mean(losses) if losses else 0

        # Profit factor
        gross_profit = sum(wins) if wins else 0
        gross_loss = abs(sum(losses)) if losses else 1
        self.profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        # Returns
        self.total_return = (self.final_capital - self.initial_capital) / self.initial_capital * 100

        # Annual return
        days = (self.end_date - self.start_date).days
        if days > 0:
            self.annual_return = ((1 + self.total_return / 100) ** (365 / days) - 1) * 100

        # Drawdown
        if not self.equity_curve.empty:
            equity = self.equity_curve["equity"]
            peak = equity.expanding().max()
            drawdown = (equity - peak) / peak * 100
            self.max_drawdown = abs(drawdown.min())

            # Drawdown duration
            in_drawdown = drawdown < 0
            if in_drawdown.any():
                dd_groups = (~in_drawdown).cumsum()[in_drawdown]
                if len(dd_groups) > 0:
                    self.max_drawdown_duration = dd_groups.value_counts().max()

        # Sharpe ratio (assuming risk-free rate = 0)
        if not self.equity_curve.empty:
            returns = self.equity_curve["equity"].pct_change().dropna()
            if len(returns) > 1 and returns.std() > 0:
                self.sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std()

                # Sortino (downside deviation)
                downside = returns[returns < 0]
                if len(downside) > 0 and downside.std() > 0:
                    self.sortino_ratio = np.sqrt(252) * returns.mean() / downside.std()

    def summary(self) -> str:
        """Generate summary report."""
        return f"""
╔══════════════════════════════════════════════════════════════╗
║                 BACKTEST RESULTS: {self.strategy_name:20} ║
╠══════════════════════════════════════════════════════════════╣
║ Symbol: {self.symbol:15} Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}
╠══════════════════════════════════════════════════════════════╣
║ RETURNS                                                       ║
║   Initial Capital:    ${self.initial_capital:>12,.2f}                    ║
║   Final Capital:      ${self.final_capital:>12,.2f}                    ║
║   Total Return:       {self.total_return:>12.2f}%                       ║
║   Annual Return:      {self.annual_return:>12.2f}%                       ║
╠══════════════════════════════════════════════════════════════╣
║ RISK METRICS                                                  ║
║   Sharpe Ratio:       {self.sharpe_ratio:>12.2f}                        ║
║   Sortino Ratio:      {self.sortino_ratio:>12.2f}                        ║
║   Max Drawdown:       {self.max_drawdown:>12.2f}%                       ║
╠══════════════════════════════════════════════════════════════╣
║ TRADE STATISTICS                                              ║
║   Total Trades:       {self.total_trades:>12}                           ║
║   Win Rate:           {self.win_rate * 100:>12.1f}%                       ║
║   Profit Factor:      {self.profit_factor:>12.2f}                        ║
║   Avg Trade P&L:      ${self.avg_trade_pnl:>12,.2f}                    ║
║   Avg Win:            ${self.avg_win:>12,.2f}                    ║
║   Avg Loss:           ${self.avg_loss:>12,.2f}                    ║
╚══════════════════════════════════════════════════════════════╝
"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "strategy_name": self.strategy_name,
            "symbol": self.symbol,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "initial_capital": self.initial_capital,
            "final_capital": self.final_capital,
            "total_return": self.total_return,
            "annual_return": self.annual_return,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "max_drawdown": self.max_drawdown,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "trades": [t.to_dict() for t in self.trades],
        }


# ============================================
# 🔧 Backtest Engine
# ============================================


@dataclass
class BacktestConfig:
    """Backtest configuration."""

    initial_capital: float = 10000.0
    commission_rate: float = 0.001  # 0.1%
    slippage_rate: float = 0.0005  # 0.05%
    max_position_size: float = 0.25  # 25% of portfolio
    use_kelly: bool = False
    kelly_fraction: float = 0.25
    risk_per_trade: float = 0.02  # 2%


class Backtest:
    """
    Main backtesting engine.

    Usage:
        bt = Backtest(
            strategy=MomentumStrategy(),
            data=df,
            symbol="AAPL",
            config=BacktestConfig(initial_capital=10000)
        )
        result = bt.run()
    """

    def __init__(
        self,
        strategy: Strategy,
        data: pd.DataFrame,
        symbol: str = "UNKNOWN",
        config: Optional[BacktestConfig] = None,
    ):
        self.strategy = strategy
        self.data = data
        self.symbol = symbol
        self.config = config or BacktestConfig()

        self.portfolio = Portfolio(initial_capital=self.config.initial_capital)
        self.trade_counter = 0

    def run(self) -> BacktestResult:
        """Execute backtest."""
        logger.info(f"Starting backtest: {self.strategy.name} on {self.symbol}")

        # Generate signals
        signals = self.strategy.generate_signals(self.data, self.symbol)
        logger.info(f"Generated {len(signals)} signals")

        # Process signals chronologically
        for signal in sorted(signals, key=lambda s: s.date):
            self._process_signal(signal)

        # Close any remaining positions at last price
        self._close_all_positions(self.data.iloc[-1])

        # Build equity curve
        equity_curve = self._build_equity_curve()

        # Get dates
        start_date = (
            self.data.index[0] if isinstance(self.data.index[0], datetime) else datetime.now()
        )
        end_date = (
            self.data.index[-1] if isinstance(self.data.index[-1], datetime) else datetime.now()
        )

        return BacktestResult(
            strategy_name=self.strategy.name,
            symbol=self.symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.config.initial_capital,
            final_capital=self.portfolio.cash,
            trades=self.portfolio.trades,
            equity_curve=equity_curve,
        )

    def _process_signal(self, signal: Signal) -> None:
        """Process a trading signal."""
        if signal.direction == TradeDirection.LONG:
            self._open_long(signal)
        else:
            self._close_long(signal)

    def _open_long(self, signal: Signal) -> None:
        """Open a long position."""
        # Check if already in position
        if self.symbol in self.portfolio.open_positions:
            return

        # Calculate position size
        position_value = self.portfolio.cash * self.config.max_position_size
        if self.config.use_kelly and signal.stop_loss:
            kelly_size = self._calculate_kelly_size(signal)
            position_value = min(position_value, kelly_size)

        shares = position_value / signal.price
        commission = position_value * self.config.commission_rate
        slippage = position_value * self.config.slippage_rate

        # Check if enough cash
        total_cost = position_value + commission + slippage
        if total_cost > self.portfolio.cash:
            return

        # Open trade
        self.trade_counter += 1
        trade = Trade(
            id=f"T{self.trade_counter:04d}",
            symbol=self.symbol,
            direction=TradeDirection.LONG,
            entry_date=signal.date,
            entry_price=signal.price * (1 + self.config.slippage_rate),
            shares=shares,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            commission=commission,
            slippage=slippage,
        )

        self.portfolio.trades.append(trade)
        self.portfolio.positions[self.symbol] = shares
        self.portfolio.cash -= total_cost

        self.strategy.on_trade_open(trade)
        logger.debug(f"Opened: {trade.id} @ ${trade.entry_price:.2f}")

    def _close_long(self, signal: Signal) -> None:
        """Close a long position."""
        if self.symbol not in self.portfolio.open_positions:
            return

        # Find open trade
        open_trade = None
        for trade in self.portfolio.trades:
            if trade.symbol == self.symbol and trade.status == TradeStatus.OPEN:
                open_trade = trade
                break

        if open_trade is None:
            return

        # Close trade
        exit_price = signal.price * (1 - self.config.slippage_rate)
        position_value = open_trade.shares * exit_price
        commission = position_value * self.config.commission_rate

        open_trade.exit_date = signal.date
        open_trade.exit_price = exit_price
        open_trade.status = TradeStatus.CLOSED
        open_trade.commission += commission

        self.portfolio.cash += position_value - commission
        del self.portfolio.positions[self.symbol]

        self.strategy.on_trade_close(open_trade)
        logger.debug(f"Closed: {open_trade.id} @ ${exit_price:.2f}, P&L: ${open_trade.pnl:.2f}")

    def _close_all_positions(self, row: pd.Series) -> None:
        """Close all remaining positions at market."""
        for symbol in list(self.portfolio.open_positions.keys()):
            for trade in self.portfolio.trades:
                if trade.symbol == symbol and trade.status == TradeStatus.OPEN:
                    exit_price = row["Close"]
                    position_value = trade.shares * exit_price

                    trade.exit_date = row.name if isinstance(row.name, datetime) else datetime.now()
                    trade.exit_price = exit_price
                    trade.status = TradeStatus.CLOSED

                    self.portfolio.cash += position_value
                    del self.portfolio.positions[symbol]

    def _calculate_kelly_size(self, signal: Signal) -> float:
        """Calculate position size using Kelly criterion."""
        if not signal.stop_loss:
            return self.portfolio.cash * self.config.max_position_size

        # Estimate win probability from signal strength
        win_prob = 0.5 + (signal.strength - 0.5) * 0.3  # Map 0-1 to 0.35-0.65

        # Calculate risk/reward
        risk = abs(signal.price - signal.stop_loss) / signal.price
        reward = (
            abs(signal.take_profit - signal.price) / signal.price
            if signal.take_profit
            else risk * 2
        )

        # Kelly formula: f* = (bp - q) / b where b = reward/risk
        b = reward / risk if risk > 0 else 1
        kelly = (b * win_prob - (1 - win_prob)) / b

        # Apply Kelly fraction
        kelly = max(0, min(kelly * self.config.kelly_fraction, self.config.max_position_size))

        return self.portfolio.cash * kelly

    def _build_equity_curve(self) -> pd.DataFrame:
        """Build equity curve DataFrame."""
        curve_data = []

        for date, row in self.data.iterrows():
            equity = self.portfolio.cash
            for symbol, shares in self.portfolio.positions.items():
                equity += shares * row["Close"]

            curve_data.append(
                {
                    "date": date,
                    "equity": equity,
                    "cash": self.portfolio.cash,
                }
            )

        return pd.DataFrame(curve_data).set_index("date")


# ============================================
# 📊 Comparison & Optimization
# ============================================


def compare_strategies(
    strategies: List[Strategy],
    data: pd.DataFrame,
    symbol: str,
    config: Optional[BacktestConfig] = None,
) -> pd.DataFrame:
    """
    Compare multiple strategies on the same data.

    Returns DataFrame with comparison metrics.
    """
    results = []

    for strategy in strategies:
        bt = Backtest(strategy=strategy, data=data, symbol=symbol, config=config)
        result = bt.run()
        results.append(
            {
                "strategy": strategy.name,
                "total_return": result.total_return,
                "annual_return": result.annual_return,
                "sharpe_ratio": result.sharpe_ratio,
                "max_drawdown": result.max_drawdown,
                "win_rate": result.win_rate * 100,
                "profit_factor": result.profit_factor,
                "total_trades": result.total_trades,
            }
        )

    return pd.DataFrame(results)


__all__ = [
    # Types
    "TradeDirection",
    "TradeStatus",
    "Trade",
    "Signal",
    # Strategy
    "Strategy",
    "MomentumStrategy",
    "TrendFollowingStrategy",
    # Portfolio
    "Portfolio",
    # Backtest
    "BacktestConfig",
    "Backtest",
    "BacktestResult",
    # Utilities
    "compare_strategies",
]
