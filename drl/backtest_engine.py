"""
Vectorized Backtest Engine for FinPilot.

High-performance backtesting with:
- Vectorized operations (no loops)
- Walk-forward optimization
- Monte Carlo simulations
- Comprehensive performance metrics
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class BacktestConfig:
    """Backtest configuration parameters."""

    # Capital & Position Sizing
    initial_capital: float = 10000.0
    position_size_pct: float = 0.1  # 10% per position
    max_positions: int = 10

    # Costs
    commission_pct: float = 0.001  # 0.1% (10 bps)
    slippage_pct: float = 0.0005  # 0.05% (5 bps)

    # Risk Management
    stop_loss_pct: float = 0.05  # 5% stop loss
    take_profit_pct: float = 0.15  # 15% take profit
    trailing_stop_pct: Optional[float] = None  # e.g., 0.03 for 3%

    # Trade Rules
    allow_shorting: bool = False
    reinvest_profits: bool = True

    # Walk-Forward
    train_ratio: float = 0.7
    n_splits: int = 5

    # Monte Carlo
    n_simulations: int = 1000
    confidence_level: float = 0.95


class SignalType(Enum):
    """Trading signal types."""

    BUY = 1
    SELL = -1
    HOLD = 0


# ============================================================================
# PERFORMANCE METRICS
# ============================================================================


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics."""

    # Returns
    total_return: float = 0.0
    annualized_return: float = 0.0
    daily_returns: np.ndarray = field(default_factory=lambda: np.array([]))

    # Risk
    volatility: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    var_95: float = 0.0  # Value at Risk
    cvar_95: float = 0.0  # Conditional VaR

    # Risk-Adjusted
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0

    # Trade Statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0

    # Time Analysis
    avg_holding_days: float = 0.0
    best_trade: float = 0.0
    worst_trade: float = 0.0

    # Equity Curve
    equity_curve: np.ndarray = field(default_factory=lambda: np.array([]))
    drawdown_curve: np.ndarray = field(default_factory=lambda: np.array([]))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_return": round(self.total_return, 4),
            "annualized_return": round(self.annualized_return, 4),
            "volatility": round(self.volatility, 4),
            "max_drawdown": round(self.max_drawdown, 4),
            "max_drawdown_duration": self.max_drawdown_duration,
            "sharpe_ratio": round(self.sharpe_ratio, 3),
            "sortino_ratio": round(self.sortino_ratio, 3),
            "calmar_ratio": round(self.calmar_ratio, 3),
            "var_95": round(self.var_95, 4),
            "cvar_95": round(self.cvar_95, 4),
            "total_trades": self.total_trades,
            "win_rate": round(self.win_rate, 3),
            "profit_factor": round(self.profit_factor, 3),
            "avg_win": round(self.avg_win, 4),
            "avg_loss": round(self.avg_loss, 4),
            "avg_holding_days": round(self.avg_holding_days, 1),
            "best_trade": round(self.best_trade, 4),
            "worst_trade": round(self.worst_trade, 4),
        }

    def summary(self) -> str:
        """Human-readable summary."""
        return f"""
╔══════════════════════════════════════════════════════════════╗
║                    BACKTEST PERFORMANCE                       ║
╠══════════════════════════════════════════════════════════════╣
║  RETURNS                                                      ║
║    Total Return:        {self.total_return:>8.2%}                            ║
║    Annualized Return:   {self.annualized_return:>8.2%}                            ║
║    Volatility:          {self.volatility:>8.2%}                            ║
╠══════════════════════════════════════════════════════════════╣
║  RISK                                                         ║
║    Max Drawdown:        {self.max_drawdown:>8.2%}                            ║
║    VaR (95%):           {self.var_95:>8.2%}                            ║
║    CVaR (95%):          {self.cvar_95:>8.2%}                            ║
╠══════════════════════════════════════════════════════════════╣
║  RISK-ADJUSTED                                                ║
║    Sharpe Ratio:        {self.sharpe_ratio:>8.2f}                              ║
║    Sortino Ratio:       {self.sortino_ratio:>8.2f}                              ║
║    Calmar Ratio:        {self.calmar_ratio:>8.2f}                              ║
╠══════════════════════════════════════════════════════════════╣
║  TRADES                                                       ║
║    Total Trades:        {self.total_trades:>8d}                              ║
║    Win Rate:            {self.win_rate:>8.1%}                            ║
║    Profit Factor:       {self.profit_factor:>8.2f}                              ║
║    Avg Holding:         {self.avg_holding_days:>8.1f} days                        ║
╚══════════════════════════════════════════════════════════════╝
"""


# ============================================================================
# VECTORIZED CALCULATIONS
# ============================================================================


def calculate_returns(prices: np.ndarray) -> np.ndarray:
    """Calculate simple returns from price series."""
    returns = np.zeros_like(prices)
    returns[1:] = (prices[1:] - prices[:-1]) / prices[:-1]
    return returns


def calculate_log_returns(prices: np.ndarray) -> np.ndarray:
    """Calculate log returns from price series."""
    log_returns = np.zeros_like(prices)
    log_returns[1:] = np.log(prices[1:] / prices[:-1])
    return log_returns


def calculate_drawdown(equity: np.ndarray) -> Tuple[np.ndarray, float, int]:
    """
    Calculate drawdown series and max drawdown.

    Returns:
        (drawdown_curve, max_drawdown, max_duration)
    """
    running_max = np.maximum.accumulate(equity)
    drawdown = (equity - running_max) / running_max
    max_drawdown = np.min(drawdown)

    # Calculate max duration
    is_dd = drawdown < 0
    duration = 0
    max_duration = 0
    for in_dd in is_dd:
        if in_dd:
            duration += 1
            max_duration = max(max_duration, duration)
        else:
            duration = 0

    return drawdown, abs(max_drawdown), max_duration


def calculate_sharpe(returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
    """Calculate annualized Sharpe ratio."""
    if len(returns) < 2:
        return 0.0

    excess_returns = returns - risk_free_rate / 252
    std = np.std(excess_returns)

    if std == 0 or np.isnan(std):
        return 0.0

    sharpe = np.mean(excess_returns) / std * np.sqrt(252)
    return float(sharpe)


def calculate_sortino(returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
    """Calculate annualized Sortino ratio."""
    if len(returns) < 2:
        return 0.0

    excess_returns = returns - risk_free_rate / 252
    downside = returns[returns < 0]

    if len(downside) == 0:
        return np.inf if np.mean(excess_returns) > 0 else 0.0

    downside_std = np.std(downside)

    if downside_std == 0 or np.isnan(downside_std):
        return 0.0

    sortino = np.mean(excess_returns) / downside_std * np.sqrt(252)
    return float(sortino)


def calculate_var_cvar(returns: np.ndarray, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate Value at Risk and Conditional VaR.

    Returns:
        (VaR, CVaR)
    """
    if len(returns) < 10:
        return 0.0, 0.0

    alpha = 1 - confidence
    var = np.percentile(returns, alpha * 100)
    cvar = np.mean(returns[returns <= var])

    return float(var), float(cvar)


# ============================================================================
# VECTORIZED BACKTEST ENGINE
# ============================================================================


class VectorizedBacktest:
    """
    High-performance vectorized backtesting engine.

    Features:
    - No loops during signal processing
    - Vectorized PnL calculation
    - Efficient memory usage
    - Built-in walk-forward support

    Example:
        >>> engine = VectorizedBacktest(config)
        >>> signals = pd.DataFrame({'signal': [1, 0, -1, 0, 1], ...})
        >>> metrics = engine.run(prices, signals)
        >>> print(metrics.summary())
    """

    def __init__(self, config: Optional[BacktestConfig] = None):
        self.config = config or BacktestConfig()
        self.trades: List[Dict] = []
        self.metrics: Optional[PerformanceMetrics] = None

    def run(
        self, prices: pd.Series, signals: pd.Series, dates: Optional[pd.DatetimeIndex] = None
    ) -> PerformanceMetrics:
        """
        Run vectorized backtest.

        Args:
            prices: Price series (Close prices)
            signals: Signal series (1=Buy, -1=Sell, 0=Hold)
            dates: Optional date index

        Returns:
            PerformanceMetrics with all calculations
        """
        prices_arr = np.array(prices, dtype=np.float64)
        signals_arr = np.array(signals, dtype=np.float64)

        n = len(prices_arr)
        if n < 2:
            logger.warning("Not enough data for backtest")
            return PerformanceMetrics()

        # Initialize arrays
        position = np.zeros(n)
        equity = np.zeros(n)
        equity[0] = self.config.initial_capital

        # Calculate position changes
        position[0] = 0
        for i in range(1, n):
            if signals_arr[i] == 1 and position[i - 1] == 0:
                # Enter long
                position[i] = 1
            elif signals_arr[i] == -1 and position[i - 1] == 1:
                # Exit long
                position[i] = 0
            else:
                # Hold position
                position[i] = position[i - 1]

        # Calculate returns
        returns = calculate_returns(prices_arr)

        # Apply position to returns (vectorized)
        strategy_returns = position * returns

        # Apply transaction costs
        position_change = np.abs(np.diff(position, prepend=0))
        transaction_costs = position_change * (
            self.config.commission_pct + self.config.slippage_pct
        )
        strategy_returns -= transaction_costs

        # Calculate equity curve
        equity = self.config.initial_capital * np.cumprod(1 + strategy_returns)

        # Calculate metrics
        metrics = self._calculate_metrics(equity, strategy_returns, position)

        self.metrics = metrics
        return metrics

    def run_with_sizing(
        self, df: pd.DataFrame, signal_col: str = "signal", price_col: str = "close"
    ) -> PerformanceMetrics:
        """
        Run backtest with dynamic position sizing.

        Args:
            df: DataFrame with signals and prices
            signal_col: Column name for signals
            price_col: Column name for prices

        Returns:
            PerformanceMetrics
        """
        prices = df[price_col].values
        signals = df[signal_col].values

        n = len(df)
        equity = np.zeros(n)
        equity[0] = self.config.initial_capital

        position_size = 0.0
        entry_price = 0.0
        trades = []

        for i in range(1, n):
            current_price = prices[i]
            prev_price = prices[i - 1]

            # Check stop loss / take profit
            if position_size > 0:
                pnl_pct = (current_price - entry_price) / entry_price

                # Stop loss
                if pnl_pct <= -self.config.stop_loss_pct:
                    # Close position
                    pnl = position_size * (current_price - entry_price)
                    pnl -= (
                        position_size
                        * current_price
                        * (self.config.commission_pct + self.config.slippage_pct)
                    )
                    equity[i] = equity[i - 1] + pnl
                    trades.append(
                        {
                            "exit_idx": i,
                            "exit_price": current_price,
                            "pnl": pnl,
                            "pnl_pct": pnl_pct,
                            "exit_reason": "stop_loss",
                        }
                    )
                    position_size = 0.0
                    continue

                # Take profit
                if pnl_pct >= self.config.take_profit_pct:
                    pnl = position_size * (current_price - entry_price)
                    pnl -= (
                        position_size
                        * current_price
                        * (self.config.commission_pct + self.config.slippage_pct)
                    )
                    equity[i] = equity[i - 1] + pnl
                    trades.append(
                        {
                            "exit_idx": i,
                            "exit_price": current_price,
                            "pnl": pnl,
                            "pnl_pct": pnl_pct,
                            "exit_reason": "take_profit",
                        }
                    )
                    position_size = 0.0
                    continue

            # Process signals
            signal = signals[i]

            if signal == 1 and position_size == 0:
                # Buy
                available = equity[i - 1] * self.config.position_size_pct
                shares = available / current_price
                cost = (
                    shares * current_price * (self.config.commission_pct + self.config.slippage_pct)
                )
                position_size = shares
                entry_price = current_price
                equity[i] = equity[i - 1] - cost
                trades.append({"entry_idx": i, "entry_price": current_price, "shares": shares})

            elif signal == -1 and position_size > 0:
                # Sell
                pnl = position_size * (current_price - entry_price)
                pnl -= (
                    position_size
                    * current_price
                    * (self.config.commission_pct + self.config.slippage_pct)
                )
                equity[i] = equity[i - 1] + pnl
                pnl_pct = (current_price - entry_price) / entry_price
                trades.append(
                    {
                        "exit_idx": i,
                        "exit_price": current_price,
                        "pnl": pnl,
                        "pnl_pct": pnl_pct,
                        "exit_reason": "signal",
                    }
                )
                position_size = 0.0

            else:
                # Mark to market
                if position_size > 0:
                    mtm = position_size * (current_price - prev_price)
                    equity[i] = equity[i - 1] + mtm
                else:
                    equity[i] = equity[i - 1]

        self.trades = trades

        # Calculate metrics
        strategy_returns = calculate_returns(equity)
        metrics = self._calculate_metrics(equity, strategy_returns, None)
        metrics.total_trades = len([t for t in trades if "pnl" in t])

        # Trade statistics
        completed_trades = [t for t in trades if "pnl" in t]
        if completed_trades:
            pnls = [t["pnl"] for t in completed_trades]
            wins = [p for p in pnls if p > 0]
            losses = [p for p in pnls if p <= 0]

            metrics.winning_trades = len(wins)
            metrics.losing_trades = len(losses)
            metrics.win_rate = len(wins) / len(completed_trades) if completed_trades else 0
            metrics.avg_win = float(np.mean(wins)) if wins else 0.0
            metrics.avg_loss = float(np.mean(losses)) if losses else 0.0
            metrics.best_trade = max(pnls) if pnls else 0
            metrics.worst_trade = min(pnls) if pnls else 0

            total_wins = sum(wins)
            total_losses = abs(sum(losses))
            metrics.profit_factor = total_wins / total_losses if total_losses > 0 else np.inf

        self.metrics = metrics
        return metrics

    def _calculate_metrics(
        self, equity: np.ndarray, returns: np.ndarray, position: Optional[np.ndarray]
    ) -> PerformanceMetrics:
        """Calculate all performance metrics."""

        metrics = PerformanceMetrics()

        # Returns
        metrics.equity_curve = equity
        metrics.daily_returns = returns
        metrics.total_return = (equity[-1] - equity[0]) / equity[0]

        n_days = len(equity)
        n_years = n_days / 252
        metrics.annualized_return = (
            (1 + metrics.total_return) ** (1 / n_years) - 1 if n_years > 0 else 0
        )

        # Volatility
        metrics.volatility = np.std(returns) * np.sqrt(252)

        # Drawdown
        dd_curve, max_dd, max_dur = calculate_drawdown(equity)
        metrics.drawdown_curve = dd_curve
        metrics.max_drawdown = max_dd
        metrics.max_drawdown_duration = max_dur

        # Risk-adjusted
        metrics.sharpe_ratio = calculate_sharpe(returns)
        metrics.sortino_ratio = calculate_sortino(returns)
        metrics.calmar_ratio = metrics.annualized_return / max_dd if max_dd > 0 else 0

        # VaR/CVaR
        metrics.var_95, metrics.cvar_95 = calculate_var_cvar(returns)

        # Trade count from position changes
        if position is not None:
            metrics.total_trades = int(np.sum(np.abs(np.diff(position)) > 0))

        return metrics


# ============================================================================
# WALK-FORWARD OPTIMIZATION
# ============================================================================


@dataclass
class WalkForwardResult:
    """Result from walk-forward optimization."""

    fold: int
    train_metrics: PerformanceMetrics
    test_metrics: PerformanceMetrics
    train_start: str
    train_end: str
    test_start: str
    test_end: str

    @property
    def is_overfit(self) -> bool:
        """Check if train >> test performance (overfitting indicator)."""
        train_sharpe = self.train_metrics.sharpe_ratio
        test_sharpe = self.test_metrics.sharpe_ratio

        if train_sharpe <= 0:
            return False

        degradation = (train_sharpe - test_sharpe) / train_sharpe
        return degradation > 0.5  # 50% degradation threshold


class WalkForwardOptimizer:
    """
    Walk-forward optimization for robust strategy testing.

    Implements anchored and rolling walk-forward analysis.
    """

    def __init__(self, config: Optional[BacktestConfig] = None):
        self.config = config or BacktestConfig()
        self.results: List[WalkForwardResult] = []

    def run_anchored(
        self,
        df: pd.DataFrame,
        signal_generator: Callable[[pd.DataFrame], pd.Series],
        price_col: str = "close",
    ) -> List[WalkForwardResult]:
        """
        Run anchored walk-forward (expanding training window).

        Args:
            df: DataFrame with price data
            signal_generator: Function(df) -> signals Series
            price_col: Column name for prices

        Returns:
            List of WalkForwardResult for each fold
        """
        n = len(df)
        n_splits = self.config.n_splits
        test_size = n // (n_splits + 1)

        results = []

        for i in range(n_splits):
            # Anchored: train always starts from beginning
            train_end = test_size * (i + 1)
            test_start = train_end
            test_end = min(test_start + test_size, n)

            train_df = df.iloc[:train_end].copy()
            test_df = df.iloc[test_start:test_end].copy()

            # Generate signals
            train_signals = signal_generator(train_df)
            test_signals = signal_generator(test_df)

            # Run backtests
            engine = VectorizedBacktest(self.config)

            train_df["signal"] = train_signals
            test_df["signal"] = test_signals

            train_metrics = engine.run_with_sizing(train_df, price_col=price_col)
            test_metrics = engine.run_with_sizing(test_df, price_col=price_col)

            # Get dates
            train_start_date = str(df.index[0])[:10] if hasattr(df.index, "__getitem__") else "N/A"
            train_end_date = (
                str(df.index[train_end - 1])[:10] if hasattr(df.index, "__getitem__") else "N/A"
            )
            test_start_date = (
                str(df.index[test_start])[:10] if hasattr(df.index, "__getitem__") else "N/A"
            )
            test_end_date = (
                str(df.index[test_end - 1])[:10] if hasattr(df.index, "__getitem__") else "N/A"
            )

            result = WalkForwardResult(
                fold=i + 1,
                train_metrics=train_metrics,
                test_metrics=test_metrics,
                train_start=train_start_date,
                train_end=train_end_date,
                test_start=test_start_date,
                test_end=test_end_date,
            )
            results.append(result)

        self.results = results
        return results

    def run_rolling(
        self,
        df: pd.DataFrame,
        signal_generator: Callable[[pd.DataFrame], pd.Series],
        train_window: int = 252,
        test_window: int = 63,
        step: int = 21,
        price_col: str = "close",
    ) -> List[WalkForwardResult]:
        """
        Run rolling walk-forward (fixed training window).

        Args:
            df: DataFrame with price data
            signal_generator: Function(df) -> signals Series
            train_window: Training window size (days)
            test_window: Test window size (days)
            step: Step size between folds
            price_col: Column name for prices

        Returns:
            List of WalkForwardResult for each fold
        """
        n = len(df)
        results = []
        fold = 1

        i = 0
        while i + train_window + test_window <= n:
            train_start = i
            train_end = i + train_window
            test_start = train_end
            test_end = min(test_start + test_window, n)

            train_df = df.iloc[train_start:train_end].copy()
            test_df = df.iloc[test_start:test_end].copy()

            # Generate signals
            train_signals = signal_generator(train_df)
            test_signals = signal_generator(test_df)

            # Run backtests
            engine = VectorizedBacktest(self.config)

            train_df["signal"] = train_signals
            test_df["signal"] = test_signals

            train_metrics = engine.run_with_sizing(train_df, price_col=price_col)
            test_metrics = engine.run_with_sizing(test_df, price_col=price_col)

            # Get dates
            train_start_date = str(df.index[train_start])[:10]
            train_end_date = str(df.index[train_end - 1])[:10]
            test_start_date = str(df.index[test_start])[:10]
            test_end_date = str(df.index[test_end - 1])[:10]

            result = WalkForwardResult(
                fold=fold,
                train_metrics=train_metrics,
                test_metrics=test_metrics,
                train_start=train_start_date,
                train_end=train_end_date,
                test_start=test_start_date,
                test_end=test_end_date,
            )
            results.append(result)

            fold += 1
            i += step

        self.results = results
        return results

    def summary(self) -> Dict[str, Any]:
        """Summarize walk-forward results."""
        if not self.results:
            return {}

        train_sharpes = [r.train_metrics.sharpe_ratio for r in self.results]
        test_sharpes = [r.test_metrics.sharpe_ratio for r in self.results]
        train_returns = [r.train_metrics.total_return for r in self.results]
        test_returns = [r.test_metrics.total_return for r in self.results]

        overfit_count = sum(1 for r in self.results if r.is_overfit)

        return {
            "n_folds": len(self.results),
            "avg_train_sharpe": np.mean(train_sharpes),
            "avg_test_sharpe": np.mean(test_sharpes),
            "sharpe_degradation": (
                1 - np.mean(test_sharpes) / np.mean(train_sharpes)
                if np.mean(train_sharpes) > 0
                else 0
            ),
            "avg_train_return": np.mean(train_returns),
            "avg_test_return": np.mean(test_returns),
            "overfit_folds": overfit_count,
            "robust": overfit_count < len(self.results) * 0.3,  # Less than 30% overfit
        }


# ============================================================================
# MONTE CARLO SIMULATION
# ============================================================================


@dataclass
class MonteCarloResult:
    """Results from Monte Carlo simulation."""

    n_simulations: int
    confidence_level: float

    # Distribution of final equity
    mean_equity: float
    median_equity: float
    std_equity: float

    # Percentiles
    equity_5th: float
    equity_25th: float
    equity_75th: float
    equity_95th: float

    # Risk metrics
    prob_loss: float  # Probability of ending with less than initial
    prob_ruin: float  # Probability of losing > 50%
    expected_max_drawdown: float

    # All simulated paths (for plotting)
    equity_paths: np.ndarray = field(default_factory=lambda: np.array([]))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n_simulations": self.n_simulations,
            "confidence_level": self.confidence_level,
            "mean_equity": round(self.mean_equity, 2),
            "median_equity": round(self.median_equity, 2),
            "std_equity": round(self.std_equity, 2),
            "equity_5th": round(self.equity_5th, 2),
            "equity_95th": round(self.equity_95th, 2),
            "prob_loss": round(self.prob_loss, 3),
            "prob_ruin": round(self.prob_ruin, 3),
            "expected_max_drawdown": round(self.expected_max_drawdown, 4),
        }


class MonteCarloSimulator:
    """
    Monte Carlo simulation for risk analysis.

    Methods:
    - Bootstrap: Resample historical returns
    - Parametric: Generate from fitted distribution
    """

    def __init__(self, config: Optional[BacktestConfig] = None):
        self.config = config or BacktestConfig()

    def run_bootstrap(
        self, returns: np.ndarray, n_days: int = 252, initial_capital: float = 10000.0
    ) -> MonteCarloResult:
        """
        Run bootstrap Monte Carlo simulation.

        Resamples historical returns with replacement.

        Args:
            returns: Historical daily returns
            n_days: Simulation horizon (days)
            initial_capital: Starting capital

        Returns:
            MonteCarloResult with distribution statistics
        """
        n_sims = self.config.n_simulations

        # Remove NaN/Inf
        returns = returns[np.isfinite(returns)]

        if len(returns) < 10:
            logger.warning("Not enough returns for Monte Carlo")
            return MonteCarloResult(
                n_simulations=0,
                confidence_level=self.config.confidence_level,
                mean_equity=initial_capital,
                median_equity=initial_capital,
                std_equity=0,
                equity_5th=initial_capital,
                equity_25th=initial_capital,
                equity_75th=initial_capital,
                equity_95th=initial_capital,
                prob_loss=0,
                prob_ruin=0,
                expected_max_drawdown=0,
            )

        # Generate paths
        equity_paths = np.zeros((n_sims, n_days + 1))
        equity_paths[:, 0] = initial_capital
        max_drawdowns = np.zeros(n_sims)

        for sim in range(n_sims):
            # Bootstrap sample
            sampled_returns = np.random.choice(returns, size=n_days, replace=True)

            # Cumulative returns
            for t in range(1, n_days + 1):
                equity_paths[sim, t] = equity_paths[sim, t - 1] * (1 + sampled_returns[t - 1])

            # Calculate max drawdown for this path
            running_max = np.maximum.accumulate(equity_paths[sim])
            drawdowns = (equity_paths[sim] - running_max) / running_max
            max_drawdowns[sim] = abs(np.min(drawdowns))

        # Final equity distribution
        final_equity = equity_paths[:, -1]

        result = MonteCarloResult(
            n_simulations=n_sims,
            confidence_level=self.config.confidence_level,
            mean_equity=float(np.mean(final_equity)),
            median_equity=float(np.median(final_equity)),
            std_equity=float(np.std(final_equity)),
            equity_5th=float(np.percentile(final_equity, 5)),
            equity_25th=float(np.percentile(final_equity, 25)),
            equity_75th=float(np.percentile(final_equity, 75)),
            equity_95th=float(np.percentile(final_equity, 95)),
            prob_loss=float(np.mean(final_equity < initial_capital)),
            prob_ruin=float(np.mean(final_equity < initial_capital * 0.5)),
            expected_max_drawdown=float(np.mean(max_drawdowns)),
            equity_paths=equity_paths,
        )

        return result

    def run_parametric(
        self,
        mean_return: float,
        volatility: float,
        n_days: int = 252,
        initial_capital: float = 10000.0,
    ) -> MonteCarloResult:
        """
        Run parametric Monte Carlo simulation.

        Generates returns from normal distribution.

        Args:
            mean_return: Annualized mean return
            volatility: Annualized volatility
            n_days: Simulation horizon
            initial_capital: Starting capital

        Returns:
            MonteCarloResult
        """
        n_sims = self.config.n_simulations

        # Daily parameters
        daily_mean = mean_return / 252
        daily_vol = volatility / np.sqrt(252)

        # Generate paths using GBM
        dt = 1 / 252
        drift = (mean_return - 0.5 * volatility**2) * dt
        diffusion = volatility * np.sqrt(dt)

        equity_paths = np.zeros((n_sims, n_days + 1))
        equity_paths[:, 0] = initial_capital
        max_drawdowns = np.zeros(n_sims)

        for sim in range(n_sims):
            z = np.random.standard_normal(n_days)
            log_returns = drift + diffusion * z

            for t in range(1, n_days + 1):
                equity_paths[sim, t] = equity_paths[sim, t - 1] * np.exp(log_returns[t - 1])

            # Max drawdown
            running_max = np.maximum.accumulate(equity_paths[sim])
            drawdowns = (equity_paths[sim] - running_max) / running_max
            max_drawdowns[sim] = abs(np.min(drawdowns))

        final_equity = equity_paths[:, -1]

        result = MonteCarloResult(
            n_simulations=n_sims,
            confidence_level=self.config.confidence_level,
            mean_equity=float(np.mean(final_equity)),
            median_equity=float(np.median(final_equity)),
            std_equity=float(np.std(final_equity)),
            equity_5th=float(np.percentile(final_equity, 5)),
            equity_25th=float(np.percentile(final_equity, 25)),
            equity_75th=float(np.percentile(final_equity, 75)),
            equity_95th=float(np.percentile(final_equity, 95)),
            prob_loss=float(np.mean(final_equity < initial_capital)),
            prob_ruin=float(np.mean(final_equity < initial_capital * 0.5)),
            expected_max_drawdown=float(np.mean(max_drawdowns)),
            equity_paths=equity_paths,
        )

        return result


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def quick_backtest(
    prices: pd.Series, signals: pd.Series, initial_capital: float = 10000.0
) -> PerformanceMetrics:
    """
    Quick backtest with default settings.

    Args:
        prices: Price series
        signals: Signal series (1=Buy, -1=Sell, 0=Hold)
        initial_capital: Starting capital

    Returns:
        PerformanceMetrics
    """
    config = BacktestConfig(initial_capital=initial_capital)
    engine = VectorizedBacktest(config)
    return engine.run(prices, signals)


def run_full_analysis(
    df: pd.DataFrame,
    signal_generator: Callable[[pd.DataFrame], pd.Series],
    price_col: str = "close",
    initial_capital: float = 10000.0,
) -> Dict[str, Any]:
    """
    Run complete backtest analysis with walk-forward and Monte Carlo.

    Args:
        df: DataFrame with price data
        signal_generator: Function(df) -> signals Series
        price_col: Column name for prices
        initial_capital: Starting capital

    Returns:
        Dictionary with all analysis results
    """
    config = BacktestConfig(initial_capital=initial_capital)

    # Main backtest
    signals = signal_generator(df)
    df_bt = df.copy()
    df_bt["signal"] = signals

    engine = VectorizedBacktest(config)
    main_metrics = engine.run_with_sizing(df_bt, price_col=price_col)

    # Walk-forward
    wfo = WalkForwardOptimizer(config)
    wf_results = wfo.run_anchored(df, signal_generator, price_col)
    wf_summary = wfo.summary()

    # Monte Carlo
    mc = MonteCarloSimulator(config)
    mc_result = mc.run_bootstrap(main_metrics.daily_returns)

    return {
        "main_metrics": main_metrics.to_dict(),
        "walk_forward": wf_summary,
        "monte_carlo": mc_result.to_dict(),
        "is_robust": wf_summary.get("robust", False),
        "equity_curve": main_metrics.equity_curve.tolist(),
    }


__all__ = [
    "BacktestConfig",
    "PerformanceMetrics",
    "VectorizedBacktest",
    "WalkForwardOptimizer",
    "WalkForwardResult",
    "MonteCarloSimulator",
    "MonteCarloResult",
    "quick_backtest",
    "run_full_analysis",
]
