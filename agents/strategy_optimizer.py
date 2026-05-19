"""Strategy Optimizer Agent — parametre optimizasyonu (Optuna veya grid search).

Input  : AgentContext.symbols + optional kwargs:
           strategy     : "momentum" | "trend" | "rsi"  (default: "momentum")
           method       : "optuna" | "grid"  (default: "grid" — optuna opsiyonel)
           n_trials     : int (default: 30) — Optuna trial sayısı
           initial_capital : float (default: 10_000)
Process:
    Her sembol için parametre kombinasyonlarını dene,
    Sharpe oranını maksimize eden parametreleri bul.
Output : AgentResult.data = dict[symbol, {
    "best_params": dict,
    "best_sharpe": float,
    "best_return_pct": float,
    "best_trades": int,
    "all_results": list[dict],  — top 5
    "method": str,
}]
"""

from __future__ import annotations

import itertools
import logging
from typing import Any

from agents.base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)

# Grid search param space — keys must match Strategy.params dict keys
_PARAM_GRID = {
    "momentum": {
        "ema_fast": [5, 10, 15, 20],
        "ema_slow": [26, 40, 60],
        "rsi_oversold": [25, 30, 35],
    },
    "trend": {
        "bb_period": [15, 20, 25],
        "macd_fast": [8, 12, 16],
        "macd_slow": [20, 26, 30],
    },
}

# Optuna param space — (low, high, is_int)
_OPTUNA_SPACE = {
    "momentum": {
        "ema_fast": (5, 25, True),
        "ema_slow": (20, 70, True),
        "rsi_oversold": (20, 40, True),
    },
    "trend": {
        "bb_period": (10, 30, True),
        "macd_fast": (6, 16, True),
        "macd_slow": (18, 35, True),
    },
}


def _run_single_backtest(
    sym: str, strategy_key: str, params: dict, initial_capital: float
) -> dict[str, Any] | None:
    """Tek parametre seti için backtest çalıştır, sonuç dict döndür."""
    try:
        from scanner.data_fetcher import fetch_multi_timeframe

        import core.backtest as bt_module

        data = fetch_multi_timeframe(sym, with_indicators=True, max_workers=1)
        df_1d = data.get("1d")
        if df_1d is None or len(df_1d) < 60:
            return None

        strategy_cls_name = (
            "MomentumStrategy" if strategy_key != "trend" else "TrendFollowingStrategy"
        )
        StrategyClass = getattr(bt_module, strategy_cls_name, bt_module.MomentumStrategy)

        # Pass params through constructor (Strategy stores them in self.params dict)
        strategy = StrategyClass(params=params)

        config = bt_module.BacktestConfig(initial_capital=initial_capital)
        engine = bt_module.Backtest(
            strategy=strategy,
            data=df_1d,
            symbol=sym,
            config=config,
        )
        result = engine.run()

        return {
            "params": params,
            "sharpe": round(result.sharpe_ratio, 4),
            "total_return_pct": round(result.total_return, 4),
            "max_drawdown_pct": round(result.max_drawdown, 4),
            "total_trades": result.total_trades,
            "win_rate": round(result.win_rate, 4),
        }
    except Exception as exc:
        logger.debug("Optimizer single run failed: %s", exc)
        return None


class StrategyOptimizerAgent(BaseAgent):
    """Find optimal strategy parameters using grid search or Optuna."""

    name = "strategy_optimizer"

    def run(self, context: AgentContext, **kwargs: object) -> AgentResult:  # noqa: D102
        import time

        t0 = time.perf_counter()

        strategy_key: str = str(kwargs.get("strategy", "momentum"))
        method: str = str(kwargs.get("method", "grid"))
        n_trials: int = int(kwargs.get("n_trials", 30))
        initial_capital: float = float(kwargs.get("initial_capital", 10_000))

        results: dict[str, Any] = {}
        errors: list[str] = []

        for sym in context.symbols:
            try:
                sym_result = self._optimize_symbol(
                    sym, strategy_key, method, n_trials, initial_capital
                )
                if sym_result:
                    results[sym] = sym_result
                else:
                    errors.append(f"{sym}: optimizasyon sonuç üretemedi")
            except Exception as exc:
                logger.warning("Optimizer: %s failed: %s", sym, exc)
                errors.append(f"{sym}: {exc}")

        duration = (time.perf_counter() - t0) * 1000

        if not results and errors:
            return AgentResult(agent=self.name, success=False, error="; ".join(errors))

        return AgentResult(
            agent=self.name,
            success=True,
            data=results,
            duration_ms=duration,
        )

    def _optimize_symbol(
        self, sym: str, strategy_key: str, method: str, n_trials: int, initial_capital: float
    ) -> dict[str, Any] | None:
        if method == "optuna":
            return self._optuna_optimize(sym, strategy_key, n_trials, initial_capital)
        return self._grid_optimize(sym, strategy_key, initial_capital)

    def _grid_optimize(
        self, sym: str, strategy_key: str, initial_capital: float
    ) -> dict[str, Any] | None:
        """Grid search — tüm parametre kombinasyonlarını dener."""
        param_space = _PARAM_GRID.get(strategy_key, _PARAM_GRID["momentum"])
        keys = list(param_space.keys())
        values = list(param_space.values())
        combos = list(itertools.product(*values))

        all_results: list[dict] = []
        for combo in combos:
            params = dict(zip(keys, combo, strict=False))
            r = _run_single_backtest(sym, strategy_key, params, initial_capital)
            if r:
                all_results.append(r)

        if not all_results:
            return None

        # Sharpe, sonra return, sonra trades sırasıyla sırala
        all_results.sort(
            key=lambda x: (x["sharpe"], x["total_return_pct"], x["total_trades"]), reverse=True
        )
        best = all_results[0]

        return {
            "best_params": best["params"],
            "best_sharpe": best["sharpe"],
            "best_return_pct": best["total_return_pct"],
            "best_trades": best["total_trades"],
            "best_win_rate": best["win_rate"],
            "all_results": all_results[:5],
            "method": "grid",
            "combos_tested": len(all_results),
        }

    def _optuna_optimize(
        self, sym: str, strategy_key: str, n_trials: int, initial_capital: float
    ) -> dict[str, Any] | None:
        """Optuna ile Bayesian optimizasyon."""
        try:
            import optuna

            optuna.logging.set_verbosity(optuna.logging.WARNING)
        except ImportError:
            logger.info("Optuna bulunamadı, grid search'e geçiliyor.")
            return self._grid_optimize(sym, strategy_key, initial_capital)

        space = _OPTUNA_SPACE.get(strategy_key, _OPTUNA_SPACE["momentum"])
        trial_results: list[dict] = []

        def objective(trial: optuna.Trial) -> float:
            params: dict[str, Any] = {}
            for name, (low, high, is_int) in space.items():
                if is_int:
                    params[name] = trial.suggest_int(name, low, high)
                else:
                    params[name] = trial.suggest_float(name, low, high)
            r = _run_single_backtest(sym, strategy_key, params, initial_capital)
            if r is None:
                return -999.0
            trial_results.append(r)
            return r["sharpe"]

        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

        if not trial_results:
            return None

        trial_results.sort(key=lambda x: x["sharpe"], reverse=True)
        best = trial_results[0]

        return {
            "best_params": study.best_params,
            "best_sharpe": round(study.best_value, 4),
            "best_return_pct": best["total_return_pct"],
            "best_trades": best["total_trades"],
            "best_win_rate": best["win_rate"],
            "all_results": trial_results[:5],
            "method": "optuna",
            "combos_tested": len(trial_results),
        }
