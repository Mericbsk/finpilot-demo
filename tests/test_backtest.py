# -*- coding: utf-8 -*-
"""
Tests for Backtesting Engine
"""
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from core.backtest import (
    Backtest,
    BacktestConfig,
    BacktestResult,
    MomentumStrategy,
    Portfolio,
    Signal,
    Strategy,
    Trade,
    TradeDirection,
    TradeStatus,
    TrendFollowingStrategy,
    compare_strategies,
)

# ============================================
# Fixtures
# ============================================


@pytest.fixture
def sample_ohlcv_data():
    """Generate sample OHLCV data."""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=100, freq="D")

    price = []
    base = 100
    for i in range(100):
        if i % 20 < 10:
            base += 0.5
        else:
            base -= 0.5
        price.append(base + np.random.randn() * 0.5)

    return pd.DataFrame(
        {
            "Open": [p * 0.99 for p in price],
            "High": [p * 1.02 for p in price],
            "Low": [p * 0.98 for p in price],
            "Close": price,
            "Volume": np.random.randint(1000000, 5000000, 100),
        },
        index=dates,
    )


@pytest.fixture
def simple_strategy():
    """Simple strategy for testing."""

    class SimpleStrategy(Strategy):
        name = "SimpleTest"
        description = "Simple test strategy"

        def generate_signals(self, data, symbol):
            signals = []
            for i, (date, row) in enumerate(data.iterrows()):
                if i % 20 == 5:
                    signals.append(
                        Signal(
                            date=date if isinstance(date, datetime) else datetime.now(),
                            symbol=symbol,
                            direction=TradeDirection.LONG,
                            strength=0.8,
                            price=row["Close"],
                            stop_loss=row["Close"] * 0.95,
                            take_profit=row["Close"] * 1.05,
                        )
                    )
                elif i % 20 == 15:
                    signals.append(
                        Signal(
                            date=date if isinstance(date, datetime) else datetime.now(),
                            symbol=symbol,
                            direction=TradeDirection.SHORT,
                            strength=0.7,
                            price=row["Close"],
                        )
                    )
            return signals

    return SimpleStrategy()


# ============================================
# Trade Tests
# ============================================


class TestTrade:
    """Tests for Trade dataclass."""

    def test_trade_creation(self):
        """Test basic trade creation."""
        trade = Trade(
            id="T0001",
            symbol="AAPL",
            direction=TradeDirection.LONG,
            entry_date=datetime(2023, 1, 1),
            entry_price=100.0,
            shares=10.0,
        )

        assert trade.id == "T0001"
        assert trade.symbol == "AAPL"
        assert trade.direction == TradeDirection.LONG
        assert trade.shares == 10.0
        assert trade.status == TradeStatus.OPEN

    def test_trade_pnl_calculation(self):
        """Test P&L calculation for closed trade."""
        trade = Trade(
            id="T0001",
            symbol="AAPL",
            direction=TradeDirection.LONG,
            entry_date=datetime(2023, 1, 1),
            entry_price=100.0,
            shares=10.0,
            exit_date=datetime(2023, 1, 10),
            exit_price=110.0,
            status=TradeStatus.CLOSED,
            commission=2.0,
        )

        # (110 - 100) * 10 - 2 = 98
        assert trade.pnl == 98.0

    def test_trade_pnl_percent(self):
        """Test percentage P&L calculation."""
        trade = Trade(
            id="T0001",
            symbol="AAPL",
            direction=TradeDirection.LONG,
            entry_date=datetime(2023, 1, 1),
            entry_price=100.0,
            shares=10.0,
            exit_date=datetime(2023, 1, 10),
            exit_price=110.0,
            status=TradeStatus.CLOSED,
        )

        # 100 / 1000 * 100 = 10%
        assert trade.pnl_percent == 10.0

    def test_trade_holding_days(self):
        """Test holding period calculation."""
        trade = Trade(
            id="T0001",
            symbol="AAPL",
            direction=TradeDirection.LONG,
            entry_date=datetime(2023, 1, 1),
            entry_price=100.0,
            shares=10.0,
            exit_date=datetime(2023, 1, 11),
            exit_price=110.0,
            status=TradeStatus.CLOSED,
        )

        assert trade.holding_days == 10

    def test_trade_to_dict(self):
        """Test trade serialization."""
        trade = Trade(
            id="T0001",
            symbol="AAPL",
            direction=TradeDirection.LONG,
            entry_date=datetime(2023, 1, 1),
            entry_price=100.0,
            shares=10.0,
        )

        data = trade.to_dict()
        assert data["id"] == "T0001"
        assert data["symbol"] == "AAPL"
        assert data["direction"] == "long"


# ============================================
# Signal Tests
# ============================================


class TestSignal:
    """Tests for Signal dataclass."""

    def test_signal_creation(self):
        """Test signal creation."""
        signal = Signal(
            date=datetime(2023, 1, 1),
            symbol="AAPL",
            direction=TradeDirection.LONG,
            strength=0.8,
            price=100.0,
            stop_loss=95.0,
            take_profit=110.0,
        )

        assert signal.symbol == "AAPL"
        assert signal.direction == TradeDirection.LONG
        assert signal.strength == 0.8
        assert signal.stop_loss == 95.0
        assert signal.take_profit == 110.0


# ============================================
# Strategy Tests
# ============================================


class TestMomentumStrategy:
    """Tests for MomentumStrategy."""

    def test_strategy_creation(self):
        """Test strategy instantiation."""
        strategy = MomentumStrategy()

        assert strategy.name == "Momentum"
        assert "rsi_period" in strategy.params
        assert strategy.params["rsi_period"] == 14

    def test_strategy_custom_params(self):
        """Test strategy with custom parameters."""
        strategy = MomentumStrategy(params={"rsi_period": 21})

        assert strategy.params["rsi_period"] == 21

    def test_generate_signals_returns_list(self, sample_ohlcv_data):
        """Test signal generation returns list."""
        strategy = MomentumStrategy()
        signals = strategy.generate_signals(sample_ohlcv_data, "TEST")

        assert isinstance(signals, list)


class TestTrendFollowingStrategy:
    """Tests for TrendFollowingStrategy."""

    def test_strategy_creation(self):
        """Test strategy instantiation."""
        strategy = TrendFollowingStrategy()

        assert strategy.name == "TrendFollowing"
        assert "bb_period" in strategy.params


# ============================================
# Portfolio Tests
# ============================================


class TestPortfolio:
    """Tests for Portfolio dataclass."""

    def test_portfolio_creation(self):
        """Test portfolio initialization."""
        portfolio = Portfolio(initial_capital=10000.0)

        assert portfolio.initial_capital == 10000.0
        assert portfolio.cash == 10000.0
        assert portfolio.equity == 10000.0
        assert len(portfolio.positions) == 0

    def test_portfolio_open_positions(self):
        """Test open positions property."""
        portfolio = Portfolio(initial_capital=10000.0)
        portfolio.positions = {"AAPL": 10.0, "GOOGL": 0.0}

        assert portfolio.open_positions == {"AAPL": 10.0}


# ============================================
# Backtest Tests
# ============================================


class TestBacktestConfig:
    """Tests for BacktestConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = BacktestConfig()

        assert config.initial_capital == 10000.0
        assert config.commission_rate == 0.001
        assert config.max_position_size == 0.25

    def test_custom_config(self):
        """Test custom configuration."""
        config = BacktestConfig(
            initial_capital=50000.0,
            commission_rate=0.002,
        )

        assert config.initial_capital == 50000.0
        assert config.commission_rate == 0.002


class TestBacktest:
    """Tests for Backtest engine."""

    def test_backtest_creation(self, sample_ohlcv_data, simple_strategy):
        """Test backtest instantiation."""
        bt = Backtest(strategy=simple_strategy, data=sample_ohlcv_data, symbol="TEST")

        assert bt.strategy.name == "SimpleTest"
        assert bt.symbol == "TEST"

    def test_backtest_run(self, sample_ohlcv_data, simple_strategy):
        """Test backtest execution."""
        bt = Backtest(
            strategy=simple_strategy,
            data=sample_ohlcv_data,
            symbol="TEST",
            config=BacktestConfig(initial_capital=10000.0),
        )

        result = bt.run()

        assert isinstance(result, BacktestResult)
        assert result.strategy_name == "SimpleTest"
        assert result.initial_capital == 10000.0

    def test_backtest_generates_trades(self, sample_ohlcv_data, simple_strategy):
        """Test that backtest generates trades."""
        bt = Backtest(strategy=simple_strategy, data=sample_ohlcv_data, symbol="TEST")

        result = bt.run()

        # SimpleStrategy generates signals at days 5, 15, 25, 35, etc.
        assert result.total_trades > 0

    def test_backtest_with_custom_config(self, sample_ohlcv_data, simple_strategy):
        """Test backtest with custom configuration."""
        config = BacktestConfig(
            initial_capital=50000.0, commission_rate=0.002, max_position_size=0.5
        )

        bt = Backtest(
            strategy=simple_strategy, data=sample_ohlcv_data, symbol="TEST", config=config
        )

        result = bt.run()

        assert result.initial_capital == 50000.0


# ============================================
# BacktestResult Tests
# ============================================


class TestBacktestResult:
    """Tests for BacktestResult."""

    def test_result_metrics(self, sample_ohlcv_data, simple_strategy):
        """Test that result calculates metrics."""
        bt = Backtest(strategy=simple_strategy, data=sample_ohlcv_data, symbol="TEST")

        result = bt.run()

        # Check metrics are calculated
        assert hasattr(result, "total_return")
        assert hasattr(result, "sharpe_ratio")
        assert hasattr(result, "max_drawdown")
        assert hasattr(result, "win_rate")

    def test_result_summary(self, sample_ohlcv_data, simple_strategy):
        """Test summary generation."""
        bt = Backtest(strategy=simple_strategy, data=sample_ohlcv_data, symbol="TEST")

        result = bt.run()
        summary = result.summary()

        assert "BACKTEST RESULTS" in summary
        assert "SimpleTest" in summary

    def test_result_to_dict(self, sample_ohlcv_data, simple_strategy):
        """Test result serialization."""
        bt = Backtest(strategy=simple_strategy, data=sample_ohlcv_data, symbol="TEST")

        result = bt.run()
        data = result.to_dict()

        assert data["strategy_name"] == "SimpleTest"
        assert "total_return" in data
        assert "trades" in data


# ============================================
# Compare Strategies Tests
# ============================================


class TestCompareStrategies:
    """Tests for strategy comparison."""

    def test_compare_strategies(self, sample_ohlcv_data):
        """Test comparing multiple strategies."""
        strategies = [
            MomentumStrategy(),
            TrendFollowingStrategy(),
        ]

        comparison = compare_strategies(
            strategies=strategies, data=sample_ohlcv_data, symbol="TEST"
        )

        assert isinstance(comparison, pd.DataFrame)
        assert len(comparison) == 2
        assert "strategy" in comparison.columns
        assert "total_return" in comparison.columns
