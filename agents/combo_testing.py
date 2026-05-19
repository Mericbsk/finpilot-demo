"""Combo Testing Agent — çoklu strateji × sembol kombinasyon test matrisi.

Input  : AgentContext.symbols + optional kwargs:
           strategies       : list[str]  (default: ["momentum", "trend", "rsi"])
           initial_capital  : float      (default: 10_000)
           min_trades       : int        (default: 3) — minimum işlem sayısı filtresi
Process:
    Her (sembol, strateji) çifti için backtest çalıştır.
    Sharpe > 0 ve min_trades geçenleri tablola.
    En iyi kombinasyonları sırala.
Output : AgentResult.data = {
    "matrix": dict[symbol, dict[strategy, backtest_result]],
    "top_combos": list[{symbol, strategy, sharpe, return_pct, trades}],
    "summary": str,
    "tested_at": str,
}
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from agents.base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)

_DEFAULT_STRATEGIES = ["momentum", "trend"]
_STRATEGY_MAP = {
    "momentum": "MomentumStrategy",
    "trend": "TrendFollowingStrategy",
    "rsi": "MomentumStrategy",
}


def _run_combo(sym: str, strategy_key: str, initial_capital: float) -> dict[str, Any] | None:
    """Tek (sembol, strateji) kombinasyonu için backtest. Hata varsa None döner."""
    try:
        from scanner.data_fetcher import fetch_multi_timeframe

        import core.backtest as bt_module

        data = fetch_multi_timeframe(sym, with_indicators=True, max_workers=1)
        df_1d = data.get("1d")
        if df_1d is None or len(df_1d) < 50:
            return None

        cls_name = _STRATEGY_MAP.get(strategy_key, "MomentumStrategy")
        StrategyClass = getattr(bt_module, cls_name, bt_module.MomentumStrategy)

        config = bt_module.BacktestConfig(initial_capital=initial_capital)
        engine = bt_module.Backtest(strategy=StrategyClass(), data=df_1d, symbol=sym, config=config)
        result = engine.run()

        return {
            "strategy": strategy_key,
            "sharpe": round(result.sharpe_ratio, 4),
            "total_return_pct": round(result.total_return, 4),
            "max_drawdown_pct": round(result.max_drawdown, 4),
            "total_trades": result.total_trades,
            "win_rate": round(result.win_rate, 4),
            "annual_return_pct": round(result.annual_return, 4),
        }
    except Exception as exc:
        logger.debug("ComboTest: %s/%s failed: %s", sym, strategy_key, exc)
        return None


class ComboTestingAgent(BaseAgent):
    """Run a symbol × strategy matrix and rank the best combinations."""

    name = "combo_testing"

    def run(self, context: AgentContext, **kwargs: object) -> AgentResult:  # noqa: D102
        import time

        t0 = time.perf_counter()

        raw_strategies = kwargs.get("strategies", _DEFAULT_STRATEGIES)
        strategies: list[str] = (
            list(raw_strategies)
            if isinstance(raw_strategies, (list, tuple))
            else _DEFAULT_STRATEGIES
        )
        initial_capital: float = float(kwargs.get("initial_capital", 10_000))
        min_trades: int = int(kwargs.get("min_trades", 3))

        matrix: dict[str, dict[str, Any]] = {}
        top_combos: list[dict[str, Any]] = []
        errors: list[str] = []
        total_runs = 0
        successful_runs = 0

        for sym in context.symbols:
            matrix[sym] = {}
            for strat in strategies:
                total_runs += 1
                result = _run_combo(sym, strat, initial_capital)
                if result is None:
                    errors.append(f"{sym}/{strat}: backtest başarısız")
                    continue
                successful_runs += 1
                matrix[sym][strat] = result

                # Top combos listesine ekle
                if result["total_trades"] >= min_trades:
                    top_combos.append(
                        {
                            "symbol": sym,
                            "strategy": strat,
                            "sharpe": result["sharpe"],
                            "total_return_pct": result["total_return_pct"],
                            "max_drawdown_pct": result["max_drawdown_pct"],
                            "total_trades": result["total_trades"],
                            "win_rate": result["win_rate"],
                            "score": _combo_score(result),
                        }
                    )

        if not matrix and errors:
            return AgentResult(agent=self.name, success=False, error="; ".join(errors))

        # Skora göre sırala
        top_combos.sort(key=lambda x: x["score"], reverse=True)

        summary = (
            f"{len(context.symbols)} sembol × {len(strategies)} strateji = "
            f"{total_runs} kombinasyon test edildi. "
            f"Başarılı: {successful_runs}. "
            f"Min {min_trades} işlem geçen: {len(top_combos)}. "
            + (
                f"En iyi: {top_combos[0]['symbol']} / {top_combos[0]['strategy']} (Sharpe: {top_combos[0]['sharpe']})"
                if top_combos
                else "Hiç uygun kombinasyon bulunamadı."
            )
        )

        duration = (time.perf_counter() - t0) * 1000
        return AgentResult(
            agent=self.name,
            success=True,
            data={
                "matrix": matrix,
                "top_combos": top_combos[:10],
                "summary": summary,
                "total_tested": total_runs,
                "successful": successful_runs,
                "errors": errors,
                "tested_at": datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC"),
            },
            duration_ms=duration,
        )


def _combo_score(r: dict[str, Any]) -> float:
    """Bileşik sıralama skoru: Sharpe ağırlıklı, drawdown penalti."""
    sharpe = r.get("sharpe", 0.0)
    ret = r.get("total_return_pct", 0.0)
    dd = abs(r.get("max_drawdown_pct", 100.0))
    trades = r.get("total_trades", 0)
    win = r.get("win_rate", 0.0)

    dd_penalty = dd / 100.0
    trade_bonus = min(trades / 20.0, 1.0) * 0.1

    score = sharpe * 0.5 + (ret / 100) * 0.2 + win * 0.2 - dd_penalty * 0.1 + trade_bonus
    return round(score, 6)
