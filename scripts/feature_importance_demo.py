"""CLI helper to compute feature importance using SHAP.

Usage examples
--------------
Run a lightweight synthetic training loop and display the top features:

    python -m scripts.feature_importance_demo --sample-size 512 --timesteps 10000

Persist CSV reports for global and regime-specific importances:

    python -m scripts.feature_importance_demo --output-dir reports/
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from drl.analysis import (
    RegimeStats,
    build_narrative_payload,
    collect_policy_dataset,
    compute_shap_summary,
    estimate_regime_success,
    fit_surrogate_policy,
    summarize_alternative_signals,
)
from drl.config import DEFAULT_CONFIG
from ml_agent import run_demo_training


def _run_demo_training(args: argparse.Namespace):
    try:
        return run_demo_training(
            env_config=DEFAULT_CONFIG,
            n_splits=args.splits,
            total_timesteps=args.timesteps,
            algorithm=args.algorithm,
            seed=args.seed,
            synthetic_length=args.synthetic_length,
            regime_period=args.regime_period,
            track_mlflow=False,
        )
    except ImportError as exc:
        raise SystemExit(
            "Demo training requires stable-baselines3. Install it via "
            "'pip install stable-baselines3'."
        ) from exc


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute SHAP-based feature importance.")
    parser.add_argument("--output-dir", type=Path, help="Directory to write CSV summaries to.")
    parser.add_argument(
        "--sample-size", type=int, default=1024, help="Sample size for SHAP computation."
    )
    parser.add_argument(
        "--splits", type=int, default=2, help="Walk-forward splits when running demo training."
    )
    parser.add_argument(
        "--timesteps",
        type=int,
        default=20_000,
        help="Training timesteps per split for the demo run.",
    )
    parser.add_argument("--algorithm", choices=["PPO", "SAC"], default="PPO")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--synthetic-length", type=int, default=768)
    parser.add_argument("--regime-period", type=int, default=60)
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    results = _run_demo_training(args)

    dataset = collect_policy_dataset(results, DEFAULT_CONFIG)
    surrogate = fit_surrogate_policy(dataset)
    summary = compute_shap_summary(surrogate, dataset, sample_size=args.sample_size)

    print("\nTop features (global):")
    print(summary.global_importance.head(10).to_string(index=False))

    for regime, df in summary.regime_importance.items():
        print(f"\nTop features for regime={regime}:")
        print(df.head(10).to_string(index=False))

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        summary.global_importance.to_csv(args.output_dir / "global_importance.csv", index=False)
        for regime, df in summary.regime_importance.items():
            safe_name = regime.lower().replace(" ", "_")
            df.to_csv(args.output_dir / f"importance_{safe_name}.csv", index=False)
        np.save(args.output_dir / "shap_values.npy", summary.shap_values)
        np.save(args.output_dir / "base_values.npy", summary.base_values)
        print(f"\nReports written to {args.output_dir}")

    _emit_explainability_demo(dataset, results)

    return 0


def _emit_explainability_demo(dataset, results) -> None:
    if not dataset.feature_names:
        return

    frame = pd.DataFrame(dataset.features, columns=dataset.feature_names)
    if dataset.timestamps and any(ts is not None for ts in dataset.timestamps):
        frame = frame.copy()
        frame["timestamp"] = pd.to_datetime(dataset.timestamps, errors="coerce")
        frame = frame.sort_values("timestamp", na_position="last").reset_index(drop=True)

    sentiment_signal, whale_signal = summarize_alternative_signals(frame)

    print("\nAlternatif veri özeti:")
    for signal in (sentiment_signal, whale_signal):
        print(f"- {signal.name}: {signal.description} [{signal.strength}]")

    current_regime = dataset.regimes[-1] if dataset.regimes else None
    regime_snapshot = estimate_regime_success(dataset.regimes, dataset.rewards, current_regime)

    drawdowns = [abs(getattr(result.metrics, "max_drawdown", 0.0)) for result in results]
    regime_stats = RegimeStats(
        name=regime_snapshot.name,
        success_rate=regime_snapshot.success_rate,
        average_reward=regime_snapshot.average_reward,
        max_drawdown=float(np.mean(drawdowns)) if drawdowns else None,
    )

    current_price = None
    if "close" in frame.columns and not frame["close"].empty:
        current_price = float(frame["close"].iloc[-1])

    payload = build_narrative_payload(
        regime_stats,
        sentiment_signal,
        whale_signal,
        current_price=current_price,
        max_allowed_drawdown=0.05,
    )

    print("\nNarratif özet:")
    print(f"{payload.title_1}: {payload.text_1}")
    print(f"{payload.title_2}: {payload.text_2}")
    if payload.exit_price is not None:
        print(f"Önerilen çıkış fiyatı: {payload.exit_price:,.2f}")


if __name__ == "__main__":
    raise SystemExit(main())
