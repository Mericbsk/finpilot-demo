"""
Portfolio Optimiser — Riskfolio-Lib wrapper.

Supports HRP (Hierarchical Risk Parity) and MV (Mean-Variance) methods.
Falls back gracefully if Riskfolio-Lib is not installed.

Usage:
    from drl.portfolio_optimizer import optimize

    result = optimize(["AAPL", "NVDA", "MSFT", "TSLA"], method="HRP")
    # result.weights → {"AAPL": 0.32, "NVDA": 0.28, ...}
    # result.metrics → {"sharpe": 1.4, "volatility": 0.18, ...}
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Literal

logger = logging.getLogger(__name__)

OptimMethod = Literal["HRP", "MV", "CVaR"]


@dataclass
class OptimResult:
    """Result from a portfolio optimisation run."""

    weights: dict[str, float]
    method: str
    metrics: dict[str, float] = field(default_factory=dict)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and bool(self.weights)


def optimize(
    symbols: list[str],
    method: OptimMethod = "HRP",
    period: str = "1y",
    interval: str = "1d",
) -> OptimResult:
    """Optimise portfolio weights for the given symbols.

    Args:
        symbols:  List of ticker symbols (≥2 required).
        method:   'HRP' | 'MV' | 'CVaR'
        period:   yfinance period string for historical data.
        interval: yfinance interval string.

    Returns:
        OptimResult with weights and risk metrics.
    """
    if len(symbols) < 2:  # noqa: PLR2004
        return OptimResult(
            weights={s: 1.0 / len(symbols) for s in symbols},
            method=method,
            error="Need at least 2 symbols to optimise.",
        )

    # -- fetch price history --------------------------------------------------
    try:
        import yfinance as yf  # noqa: PLC0415
    except ImportError:
        return OptimResult(weights={}, method=method, error="yfinance not installed.")

    try:
        raw = yf.download(
            symbols,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=True,
            group_by="ticker",
        )
    except Exception as exc:  # noqa: BLE001
        return OptimResult(weights={}, method=method, error=f"Data fetch failed: {exc}")

    # Build a clean returns DataFrame ----------------------------------------
    try:
        import pandas as pd  # noqa: PLC0415

        # yfinance ≥0.2 with multi-ticker returns MultiIndex: (field, ticker)
        if isinstance(raw.columns, pd.MultiIndex):
            close = (
                raw["Close"]
                if "Close" in raw.columns.get_level_values(0)
                else raw.xs("Close", axis=1, level=0)
            )
        else:
            close = raw[["Close"]] if "Close" in raw.columns else raw

        close = close.dropna(how="all").ffill()
        # Drop symbols with too little data
        close = close.loc[:, close.notna().sum() > 20]  # noqa: PLR2004
        if close.shape[1] < 2:  # noqa: PLR2004
            return OptimResult(weights={}, method=method, error="Insufficient price history.")
        returns = close.pct_change().dropna()
    except Exception as exc:  # noqa: BLE001
        return OptimResult(weights={}, method=method, error=f"Data processing failed: {exc}")

    # -- optimise -------------------------------------------------------------
    try:
        import riskfolio as rp  # noqa: PLC0415

        port = rp.Portfolio(returns=returns)
        port.assets_stats(method_mu="hist", method_cov="hist")

        if method == "HRP":
            w_df = port.optimization(
                model="HRP",
                codependence="pearson",
                rm="MV",
                rf=0,
                linkage="ward",
                max_k=10,
                leaf_order=True,
            )
        elif method == "CVaR":
            port.alpha = 0.05
            w_df = port.optimization(model="Classic", rm="CVaR", obj="Sharpe", rf=0, l=0)
        else:  # MV — Mean-Variance max Sharpe
            w_df = port.optimization(model="Classic", rm="MV", obj="Sharpe", rf=0, l=0)

        weights_raw: dict[str, float] = w_df["weights"].to_dict()
        # Normalise (should already sum to 1.0, but guard for rounding)
        total = sum(weights_raw.values()) or 1.0
        weights = {k: round(v / total, 6) for k, v in weights_raw.items() if v > 1e-6}

        # Risk metrics
        metrics: dict[str, float] = {}
        try:
            perf = rp.RiskFunctions.RiskMeasure(
                returns.values,
                w_df.values,
                cov=returns.cov().values,
            )
            metrics["volatility"] = round(float(perf), 4)
        except Exception:  # noqa: BLE001
            pass
        try:
            ann_ret = float((returns.mean() @ w_df["weights"]) * 252)
            ann_vol = float((returns.std() @ w_df["weights"].abs()) * (252**0.5))
            metrics["annual_return"] = round(ann_ret, 4)
            metrics["annual_volatility"] = round(ann_vol, 4)
            if ann_vol > 0:
                metrics["sharpe"] = round(ann_ret / ann_vol, 4)
        except Exception:  # noqa: BLE001
            pass

        logger.info(
            "Portfolio optimised via %s: %d assets, sharpe=%.2f",
            method,
            len(weights),
            metrics.get("sharpe", float("nan")),
        )
        return OptimResult(weights=weights, method=method, metrics=metrics)

    except ImportError:
        pass  # fall through to equal-weight fallback

    except Exception as exc:  # noqa: BLE001
        logger.warning("Riskfolio optimisation failed: %s", exc)
        return OptimResult(weights={}, method=method, error=str(exc))

    # -- equal-weight fallback (Riskfolio not installed) ---------------------
    syms = list(returns.columns)
    eq = round(1.0 / len(syms), 6)
    return OptimResult(
        weights={s: eq for s in syms},
        method=f"{method}_fallback_equal",
        metrics={},
        error="Riskfolio-Lib not installed — returning equal weights.",
    )
