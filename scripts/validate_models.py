#!/usr/bin/env python3
"""Walk-forward validation & overfitting test for all registered DRL models.

Sprint 13 — Critical items #3 & #4.

For each model in the registry this script:
  1. Fetches historical daily data for training symbols via yfinance.
  2. Wraps the model in a signal generator (action > 0.3 → BUY, < −0.3 → SELL).
  3. Runs anchored walk-forward analysis (5 folds).
  4. Flags overfitting (train Sharpe > 2× test Sharpe).
  5. Writes back per-model metrics to models/registry.json.
  6. Prints a summary report.

Usage:
    python scripts/validate_models.py                   # all registered models
    python scripts/validate_models.py --model v5        # single version
    python scripts/validate_models.py --symbol AAPL     # specific symbol
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from drl.backtest_engine import (  # noqa: E402
    BacktestConfig,
    WalkForwardOptimizer,
    WalkForwardResult,
)
from drl.config import DEFAULT_CONFIG  # noqa: E402
from drl.data_loader import fetch_training_data  # noqa: E402
from drl.model_registry import ModelMetadata, get_registry  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
VALIDATION_SYMBOLS = ["AAPL", "NVDA", "TSLA"]  # fast; skip crypto for yf daily
WF_SPLITS = 5
BACKTEST_CFG = BacktestConfig(
    initial_capital=10_000,
    position_size_pct=0.10,
    commission_pct=0.001,
    slippage_pct=0.0005,
    stop_loss_pct=0.05,
    take_profit_pct=0.15,
    n_splits=WF_SPLITS,
)
ACTION_THRESHOLD = 0.3


# ---------------------------------------------------------------------------
# Signal generator factory
# ---------------------------------------------------------------------------


def make_signal_generator(
    model: Any,
    feature_cols: list[str],
    threshold: float = ACTION_THRESHOLD,
):
    """Return a callable(df) → pd.Series of {1, 0, −1} signals."""

    def _generate(df: pd.DataFrame) -> pd.Series:
        # Build observation matrix — fill missing cols with 0
        obs_df = pd.DataFrame(0.0, index=df.index, columns=feature_cols)
        for col in feature_cols:
            if col in df.columns:
                obs_df[col] = df[col].values
        obs = obs_df.values.astype(np.float32)
        obs = np.nan_to_num(obs, nan=0.0, posinf=0.0, neginf=0.0)

        actions = np.empty(len(obs))
        for i, row in enumerate(obs):
            act, _ = model.predict(row, deterministic=True)
            actions[i] = float(act[0]) if hasattr(act, "__len__") else float(act)

        signals = np.where(actions > threshold, 1, np.where(actions < -threshold, -1, 0))
        return pd.Series(signals, index=df.index)

    return _generate


# ---------------------------------------------------------------------------
# Core validation
# ---------------------------------------------------------------------------


def validate_model(
    model_id: str,
    metadata: ModelMetadata,
    data: dict[str, pd.DataFrame],
    config: BacktestConfig,
) -> dict[str, Any]:
    """Run walk-forward validation on a single model. Returns metrics dict."""
    from stable_baselines3 import PPO

    model_path = metadata.model_path
    logger.info("  Loading %s …", model_path)
    model = PPO.load(model_path)

    feature_cols = metadata.feature_columns or DEFAULT_CONFIG.feature_columns
    sig_gen = make_signal_generator(model, feature_cols)

    all_wf_results: list[WalkForwardResult] = []
    symbol_metrics: dict[str, dict] = {}

    for symbol, df in data.items():
        if df.empty or len(df) < 100:
            logger.warning("  %s: not enough data (%d rows), skip", symbol, len(df))
            continue

        logger.info("  %s: %d rows → walk-forward (%d folds) …", symbol, len(df), WF_SPLITS)

        wfo = WalkForwardOptimizer(config)
        results = wfo.run_anchored(df, sig_gen, price_col="close")
        all_wf_results.extend(results)

        summary = wfo.summary()
        symbol_metrics[symbol] = summary
        logger.info(
            "    Sharpe train=%.3f  test=%.3f  degradation=%.1f%%  overfit_folds=%d/%d",
            summary.get("avg_train_sharpe", 0),
            summary.get("avg_test_sharpe", 0),
            summary.get("sharpe_degradation", 0) * 100,
            summary.get("overfit_folds", 0),
            summary.get("n_folds", 0),
        )

    if not all_wf_results:
        return {"error": "no walk-forward results"}

    # Aggregate across symbols
    train_sharpes = [r.train_metrics.sharpe_ratio for r in all_wf_results]
    test_sharpes = [r.test_metrics.sharpe_ratio for r in all_wf_results]
    test_returns = [r.test_metrics.total_return for r in all_wf_results]
    test_drawdowns = [r.test_metrics.max_drawdown for r in all_wf_results]
    overfit_count = sum(1 for r in all_wf_results if r.is_overfit)

    avg_train_sharpe = float(np.mean(train_sharpes))
    avg_test_sharpe = float(np.mean(test_sharpes))
    sharpe_degradation = (1 - avg_test_sharpe / avg_train_sharpe) if avg_train_sharpe > 0 else 0.0
    is_robust = overfit_count < len(all_wf_results) * 0.3

    metrics = {
        "sharpe_ratio": round(avg_test_sharpe, 4),
        "sharpe_train": round(avg_train_sharpe, 4),
        "sharpe_degradation": round(sharpe_degradation, 4),
        "total_return": round(float(np.mean(test_returns)), 4),
        "max_drawdown": round(float(np.mean(test_drawdowns)), 4),
        "win_rate": round(float(np.mean([r.test_metrics.win_rate for r in all_wf_results])), 4),
        "profit_factor": round(
            float(np.mean([r.test_metrics.profit_factor for r in all_wf_results])), 4
        ),
        "overfit_folds": overfit_count,
        "total_folds": len(all_wf_results),
        "is_robust": is_robust,
        "validation_symbols": list(data.keys()),
    }

    return metrics


# ---------------------------------------------------------------------------
# Overfitting report
# ---------------------------------------------------------------------------


def overfitting_report(registry_data: dict[str, dict]) -> str:
    """Generate a multi-model overfitting comparison report."""
    lines = [
        "",
        "═" * 80,
        "  OVERFITTING REPORT",
        "═" * 80,
        f"  {'Model ID':<45s} {'Train':>8s} {'Test':>8s} {'Degrad':>8s} {'Status':>10s}",
        "─" * 80,
    ]

    for model_id, meta in sorted(registry_data.items(), key=lambda kv: kv[1].get("version", "")):
        m = meta.get("metrics", {})
        if not m or "sharpe_train" not in m:
            lines.append(f"  {model_id:<45s}  {'—':>8s} {'—':>8s} {'—':>8s} {'SKIPPED':>10s}")
            continue

        train_s = m["sharpe_train"]
        test_s = m["sharpe_ratio"]
        degrad = m["sharpe_degradation"]
        robust = m.get("is_robust", False)
        status = "✓ ROBUST" if robust else "✗ OVERFIT"

        lines.append(
            f"  {model_id:<45s}  {train_s:>8.3f} {test_s:>8.3f} {degrad:>7.1%} {status:>10s}"
        )

    lines.append("═" * 80)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Walk-forward model validation")
    parser.add_argument("--model", type=str, help="Filter by version (e.g. v5)")
    parser.add_argument("--symbol", type=str, help="Single symbol override")
    parser.add_argument("--period", type=str, default="2y", help="yfinance period")
    args = parser.parse_args()

    logger.info("═" * 60)
    logger.info("Walk-Forward Validation + Overfitting Test — Sprint 13")
    logger.info("═" * 60)

    # 1. Load registry
    registry = get_registry("models/")
    all_models = registry.list_models(algorithm="PPO")
    if not all_models:
        logger.error("No models found in registry!")
        sys.exit(1)

    if args.model:
        all_models = [m for m in all_models if m.version == args.model]
        if not all_models:
            logger.error("No model with version %s", args.model)
            sys.exit(1)

    logger.info("Models to validate: %d", len(all_models))

    # 2. Fetch data (once for all models)
    symbols = [args.symbol] if args.symbol else VALIDATION_SYMBOLS
    logger.info("Fetching data for %s (period=%s) …", symbols, args.period)
    data = fetch_training_data(symbols, period=args.period, interval="1d")

    if not data:
        logger.error("Could not fetch any market data!")
        sys.exit(1)

    logger.info("Data loaded: %s", {s: len(df) for s, df in data.items()})

    # 3. Validate each model
    for meta in all_models:
        logger.info("")
        logger.info("─" * 60)
        logger.info("Model: %s (%s)", meta.model_id, meta.version)
        logger.info("─" * 60)

        try:
            metrics = validate_model(meta.model_id, meta, data, BACKTEST_CFG)
        except Exception as exc:
            logger.error("  FAILED: %s", exc)
            continue

        if "error" in metrics:
            logger.warning("  %s", metrics["error"])
            continue

        # Update registry
        meta.metrics = metrics
        registry._save_registry()
        logger.info("  → Metrics saved to registry")

    # 4. Overfitting report
    registry_path = Path("models/registry.json")
    with open(registry_path) as f:
        reg_data = json.load(f)
    report = overfitting_report(reg_data)
    logger.info(report)

    # 5. Save report
    report_path = ROOT / "reports" / "wf_validation_report.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        f.write(report)
    logger.info("Report saved to %s", report_path)

    logger.info("")
    logger.info("═" * 60)
    logger.info("✓  Validation complete")
    logger.info("═" * 60)


if __name__ == "__main__":
    main()
