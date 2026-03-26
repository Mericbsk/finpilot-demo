"""POST /api/v1/backtest — Run a strategy backtest via the core engine."""

from __future__ import annotations

from enum import StrEnum

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["backtest"])


class StrategyName(StrEnum):
    MOMENTUM = "Momentum"
    MEAN_REVERSION = "MeanReversion"
    TREND_FOLLOWING = "TrendFollowing"


class BacktestRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10)
    strategy: StrategyName = StrategyName.MOMENTUM
    period: str = Field("1y", pattern=r"^(3mo|6mo|1y|2y|5y)$")
    initial_capital: float = Field(10_000, ge=100, le=10_000_000)
    position_size_pct: float = Field(25, ge=1, le=100)
    stop_loss_pct: float = Field(5, ge=0.5, le=50)
    take_profit_pct: float = Field(15, ge=1, le=100)


@router.post("/backtest")
def run_backtest(req: BacktestRequest):
    """Run a real backtest using core.backtest engine + Yahoo Finance data."""
    import pandas as pd
    from scanner import fetch

    from core.backtest import (
        Backtest,
        BacktestConfig,
        MomentumStrategy,
        TrendFollowingStrategy,
    )

    # Fetch historical data
    df: pd.DataFrame = fetch(req.symbol, period=req.period, interval="1d")
    if df is None or df.empty or len(df) < 30:
        return {"error": f"Insufficient data for {req.symbol}", "symbol": req.symbol}

    # Select strategy
    strategy_map = {
        StrategyName.MOMENTUM: MomentumStrategy,
        StrategyName.MEAN_REVERSION: TrendFollowingStrategy,  # closest match
        StrategyName.TREND_FOLLOWING: TrendFollowingStrategy,
    }
    strategy_cls = strategy_map.get(req.strategy, MomentumStrategy)
    strategy = strategy_cls()

    config = BacktestConfig(
        initial_capital=req.initial_capital,
        max_position_size=req.position_size_pct / 100,
    )

    bt = Backtest(strategy=strategy, data=df, symbol=req.symbol, config=config)
    result = bt.run()

    # Build equity curve list for frontend charting
    equity_list: list[float] = []
    if not result.equity_curve.empty and "equity" in result.equity_curve.columns:
        equity_list = result.equity_curve["equity"].tolist()
    elif result.trades:
        # fallback: build simple equity from trades
        eq = req.initial_capital
        for t in result.trades:
            eq += t.pnl
            equity_list.append(round(eq, 2))
    if not equity_list:
        equity_list = [req.initial_capital, result.final_capital]

    # Monthly returns (approximate from equity)
    monthly: list[dict] = []
    if not result.equity_curve.empty and "equity" in result.equity_curve.columns:
        ec = result.equity_curve.copy()
        ec.index = pd.to_datetime(ec.index, errors="coerce")
        monthly_eq = ec["equity"].resample("ME").last().dropna()
        if len(monthly_eq) > 1:
            rets = monthly_eq.pct_change().dropna() * 100
            for dt, val in rets.items():
                monthly.append({"month": dt.strftime("%b"), "return": round(val, 1)})

    return {
        "symbol": req.symbol,
        "strategy": req.strategy,
        "period": req.period,
        "initial_capital": req.initial_capital,
        "final_capital": round(result.final_capital, 2),
        "total_return": round(result.total_return, 2),
        "sharpe_ratio": round(result.sharpe_ratio, 2),
        "sortino_ratio": round(result.sortino_ratio, 2),
        "max_drawdown": round(result.max_drawdown, 2),
        "win_rate": round(result.win_rate * 100, 1),
        "profit_factor": round(result.profit_factor, 2),
        "total_trades": result.total_trades,
        "winning_trades": result.winning_trades,
        "losing_trades": result.losing_trades,
        "avg_win": round(result.avg_win, 2),
        "avg_loss": round(result.avg_loss, 2),
        "equity": equity_list,
        "monthly": monthly,
    }
