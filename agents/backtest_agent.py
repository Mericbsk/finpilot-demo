"""Backtest Agent — runs core/backtest.py strategies on a symbol's daily data.

Input  : AgentContext.symbols + optional kwargs:
           strategy  : "momentum" | "trend" | "rsi"  (default: "momentum")
           initial_capital : float (default: 10_000)
Process: Fetch 1D OHLCV → Backtest(strategy, data) → BacktestResult.to_dict()
Output : AgentResult.data = dict[symbol, BacktestResult.to_dict()]
"""

from __future__ import annotations

import logging

from agents.base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)

_STRATEGY_MAP = {
    "momentum": "MomentumStrategy",
    "trend": "TrendFollowingStrategy",
    "rsi": "MomentumStrategy",  # alias
}


class BacktestAgent(BaseAgent):
    """Run historical backtests for each symbol using core/backtest.py."""

    name = "backtest"

    def run(self, context: AgentContext, **kwargs: object) -> AgentResult:  # noqa: D102
        import time

        t0 = time.perf_counter()

        # Check for performance feedback from previous cycle
        try:
            from agents.feedback import get_feedback

            feedback_messages = get_feedback("backtest", limit=5)
            for msg in feedback_messages:
                if msg.get("feedback_type") == "low_win_rate":
                    # Override strategy hint based on feedback recommendation
                    if "strategy" not in kwargs:
                        kwargs = dict(kwargs)
                        kwargs["strategy"] = msg["data"].get("recommendation_strategy", "trend")
                        logger.info(
                            "Backtest: applying feedback strategy override → %s (win_rate was %.1f%%)",
                            kwargs["strategy"],
                            msg["data"].get("win_rate", 0),
                        )
                    break
        except Exception:
            pass  # feedback is best-effort

        strategy_key: str = str(kwargs.get("strategy", "momentum"))
        initial_capital: float = float(kwargs.get("initial_capital", 10_000))

        try:
            from scanner.data_fetcher import fetch_multi_timeframe

            import core.backtest as bt_module
        except ImportError as exc:
            return AgentResult(agent=self.name, success=False, error=f"Import error: {exc}")

        strategy_cls_name = _STRATEGY_MAP.get(strategy_key, "MomentumStrategy")
        StrategyClass = getattr(bt_module, strategy_cls_name, bt_module.MomentumStrategy)

        results: dict = {}
        errors: list[str] = []

        for sym in context.symbols:
            try:
                data = fetch_multi_timeframe(sym, with_indicators=True, max_workers=2)
                df_1d = data.get("1d")
                if df_1d is None or len(df_1d) < 50:
                    errors.append(
                        f"{sym}: insufficient daily data ({len(df_1d) if df_1d is not None else 0} bars)"
                    )
                    continue

                strategy = StrategyClass()
                config = bt_module.BacktestConfig(initial_capital=initial_capital)
                engine = bt_module.Backtest(
                    strategy=strategy,
                    data=df_1d,
                    symbol=sym,
                    config=config,
                )
                result = engine.run()
                results[sym] = result.to_dict()
                logger.info(
                    "BacktestAgent: %s → return=%.1f%% sharpe=%.2f trades=%d",
                    sym,
                    result.total_return,
                    result.sharpe_ratio,
                    result.total_trades,
                )
            except Exception as exc:
                logger.warning("BacktestAgent: %s failed: %s", sym, exc)
                errors.append(f"{sym}: {exc}")

        duration = (time.perf_counter() - t0) * 1000
        if not results and errors:
            return AgentResult(
                agent=self.name,
                success=False,
                error="; ".join(errors),
                duration_ms=duration,
            )

        return AgentResult(
            agent=self.name,
            success=True,
            data=results,
            duration_ms=duration,
        )
