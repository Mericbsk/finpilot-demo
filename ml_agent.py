"""Command-line utilities for FinPilot's DRL agent.

The module wires together the configuration objects from :mod:`drl.config`, the
feature engineering pipeline, and the walk-forward trainer.  By default it runs
on a synthetic dataset so developers can exercise the training loop without
connecting to live data providers.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

import numpy as np
import pandas as pd

from drl.config import DEFAULT_CONFIG, MarketEnvConfig
from drl.feature_pipeline import FeatureFrame
from drl.market_env import EpisodeData
from drl.observability import PrometheusSettings, configure_prometheus
from drl.training import TrainResult, WalkForwardConfig, WalkForwardSplit, WalkForwardTrainer


@dataclass
class SyntheticParams:
    """Parameters controlling the synthetic market generator."""

    length: int = 1024
    regime_period: int = 60


# ----------------------------------------------------------------------
# Synthetic dataset helpers
# ----------------------------------------------------------------------
def _generate_synthetic_dataframe(params: SyntheticParams, config: MarketEnvConfig) -> pd.DataFrame:
    idx = pd.date_range(end=pd.Timestamp.utcnow(), periods=params.length, freq="H")
    base_trend = np.linspace(0, 10, params.length)
    noise = np.random.normal(scale=1.5, size=params.length)
    seasonal = 5.0 * np.sin(np.linspace(0, 8 * np.pi, params.length))
    close = 180 + base_trend + seasonal + noise

    volume = 1_000_000 + np.abs(np.random.normal(scale=150_000, size=params.length))
    df = pd.DataFrame({"close": close, "volume": volume}, index=idx)

    df["ema_20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema_50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ema_200"] = df["close"].ewm(span=200, adjust=False).mean()

    diff = df["close"].diff().fillna(0.0)
    gain = diff.clip(lower=0.0)
    loss = -diff.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / 14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, adjust=False).mean()
    rs = avg_gain / (avg_loss.replace(0, 1e-6))
    df["rsi"] = 100 - (100 / (1 + rs))

    ema_fast = df["close"].ewm(span=12, adjust=False).mean()
    ema_slow = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = ema_fast - ema_slow
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]

    rolling_mean = df["close"].rolling(20).mean()
    rolling_std = df["close"].rolling(20).std().fillna(1.0)
    df["bb_upper"] = rolling_mean + 2 * rolling_std
    df["bb_lower"] = rolling_mean - 2 * rolling_std
    df["atr"] = (df["close"].rolling(14).max() - df["close"].rolling(14).min()).fillna(0.5)
    df["volume_avg_20"] = df["volume"].rolling(20).mean().bfill()

    # Regime labelling (cyclical)
    regime_labels = []
    for i in range(params.length):
        cycle = (i // params.regime_period) % 3
        if cycle == 0:
            regime_labels.append("trend")
        elif cycle == 1:
            regime_labels.append("range")
        else:
            regime_labels.append("volatility")
    df["regime_label"] = regime_labels
    df["regime_trend"] = [1.0 if r == "trend" else 0.0 for r in regime_labels]
    df["regime_range"] = [1.0 if r == "range" else 0.0 for r in regime_labels]
    df["regime_volatility"] = [1.0 if r == "volatility" else 0.0 for r in regime_labels]

    # Alternative data (noise for demo)
    df["sentiment_score"] = np.random.uniform(-1, 1, size=params.length)
    df["news_sentiment"] = np.random.uniform(-1, 1, size=params.length)
    df["onchain_active_addresses"] = np.random.uniform(0, 100, size=params.length)
    df["onchain_tx_volume"] = np.random.uniform(0, 1000, size=params.length)

    df["cash_ratio"] = np.clip(np.random.uniform(0.2, 0.8, size=params.length), 0, 1)
    df["position_ratio"] = np.clip(np.random.uniform(-0.5, 0.5, size=params.length), -1, 1)
    df["open_risk"] = np.clip(np.random.uniform(0, 0.3, size=params.length), 0, 1)
    df["kelly_fraction"] = np.clip(np.random.uniform(0.1, 0.9, size=params.length), 0, 1)

    missing = [col for col in config.feature_columns if col not in df.columns]
    for col in missing:
        df[col] = 0.0

    df = df.bfill().ffill().fillna(0.0)
    return df


def _episode_from_slice(df: pd.DataFrame, config: MarketEnvConfig) -> EpisodeData:
    features = FeatureFrame(df[config.feature_columns].copy())
    prices = df["close"]
    regimes = df.get("regime_label")
    timestamps = df.index if isinstance(df.index, pd.DatetimeIndex) else None
    return EpisodeData(features=features, prices=prices, regimes=regimes, timestamps=timestamps)


# ----------------------------------------------------------------------
# Walk-forward execution
# ----------------------------------------------------------------------
def _create_splits(
    df: pd.DataFrame, config: MarketEnvConfig, n_splits: int
) -> List[WalkForwardSplit]:
    """Partition the dataframe into sequential walk-forward windows."""

    if n_splits < 1:
        raise ValueError("n_splits must be at least 1")
    window = len(df) // (n_splits + 1)
    if window < 2:
        raise ValueError("Dataset too small for requested number of splits")

    splits: List[WalkForwardSplit] = []
    for i in range(n_splits):
        start = i * window
        mid = (i + 1) * window
        end = (i + 2) * window
        train_slice = df.iloc[start:mid]
        test_slice = df.iloc[mid:end]
        if len(test_slice) < 2:
            break
        splits.append(
            WalkForwardSplit(
                train=_episode_from_slice(train_slice, config),
                test=_episode_from_slice(test_slice, config),
                label=f"split-{i:02d}",
            )
        )
    if not splits:
        raise ValueError(
            "Could not construct any walk-forward splits; adjust n_splits or dataset length"
        )
    return splits


def _print_summary(results: Iterable[TrainResult]) -> None:
    """Emit a concise metrics table to stdout."""

    print("\nWalk-forward training summary\n" + "-" * 36)
    for result in results:
        metrics = result.metrics
        print(
            f"{result.split.label}: reward={metrics.average_reward:.4f} "
            f"sharpe={metrics.sharpe_ratio:.3f} drawdown={metrics.max_drawdown:.3f} "
            f"return={metrics.total_return:.3f}"
        )
        if result.model_path:
            print(f"  model saved to: {result.model_path}")
        if result.pipeline_artifact_path:
            print(f"  pipeline artifact: {result.pipeline_artifact_path}")
    print("-" * 36)


def run_demo_training(
    *,
    env_config: MarketEnvConfig = DEFAULT_CONFIG,
    n_splits: int = 3,
    total_timesteps: int = 25_000,
    algorithm: str = "PPO",
    seed: Optional[int] = 42,
    synthetic_length: int = 1024,
    regime_period: int = 60,
    track_mlflow: bool = False,
    mlflow_experiment: str = "FinPilot-DRL",
    save_pipeline_artifacts: bool = False,
    pipeline_artifact_dir: Optional[str] = None,
    load_pipeline_artifact: Optional[str] = None,
    allow_pipeline_mismatch: bool = False,
    enable_prometheus: bool = False,
    prometheus_host: str = "0.0.0.0",
    prometheus_port: int = 9000,
) -> List[TrainResult]:
    """Execute a demo training loop on synthetic data."""

    if seed is not None:
        np.random.seed(seed)

    if enable_prometheus:
        configure_prometheus(
            PrometheusSettings(
                enabled=True,
                host=prometheus_host,
                port=prometheus_port,
            )
        )

    params = SyntheticParams(length=synthetic_length, regime_period=regime_period)
    df = _generate_synthetic_dataframe(params, env_config)
    splits = _create_splits(df, env_config, n_splits)

    trainer = WalkForwardTrainer(
        env_config,
        WalkForwardConfig(
            algorithm=algorithm,
            total_timesteps=total_timesteps,
            seed=seed,
            track_mlflow=track_mlflow,
            mlflow_experiment=mlflow_experiment,
            save_pipeline_artifacts=save_pipeline_artifacts,
            pipeline_artifact_dir=pipeline_artifact_dir,
            load_pipeline_artifact=load_pipeline_artifact,
            allow_pipeline_signature_mismatch=allow_pipeline_mismatch,
        ),
    )
    return trainer.train(splits)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Build the CLI argument parser."""

    parser = argparse.ArgumentParser(description="Run the FinPilot DRL demo trainer")
    parser.add_argument("--splits", type=int, default=3, help="Number of walk-forward windows")
    parser.add_argument("--steps", type=int, default=25_000, help="Training timesteps per split")
    parser.add_argument("--algo", choices=["PPO", "SAC"], default="PPO", help="RL algorithm")
    parser.add_argument("--length", type=int, default=1024, help="Synthetic dataset length")
    parser.add_argument(
        "--regime-period",
        type=int,
        default=60,
        dest="regime_period",
        help="Period for synthetic regime cycles",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument(
        "--mlflow",
        action="store_true",
        dest="track_mlflow",
        help="Track metrics in MLflow if available",
    )
    parser.add_argument(
        "--mlflow-experiment", default="FinPilot-DRL", help="MLflow experiment name"
    )
    parser.add_argument(
        "--save-pipeline-artifacts",
        action="store_true",
        dest="save_pipeline_artifacts",
        help="Persist fitted FeaturePipeline statistics to disk",
    )
    parser.add_argument(
        "--pipeline-artifact-dir",
        dest="pipeline_artifact_dir",
        help="Directory where pipeline artefacts will be written",
    )
    parser.add_argument(
        "--load-pipeline-artifact",
        dest="load_pipeline_artifact",
        help="Existing pipeline artefact JSON to load before training",
    )
    parser.add_argument(
        "--allow-pipeline-mismatch",
        action="store_true",
        dest="allow_pipeline_mismatch",
        help="Skip feature signature validation when loading pipeline artefacts",
    )
    parser.add_argument(
        "--prometheus",
        action="store_true",
        dest="enable_prometheus",
        help="Expose Prometheus metrics via an HTTP endpoint",
    )
    parser.add_argument(
        "--prometheus-host",
        default="0.0.0.0",
        dest="prometheus_host",
        help="Bind address for the Prometheus metrics server",
    )
    parser.add_argument(
        "--prometheus-port",
        type=int,
        default=9000,
        dest="prometheus_port",
        help="Port for the Prometheus metrics server",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entrypoint used by ``python -m ml_agent``."""

    args = parse_args(argv)
    try:
        results = run_demo_training(
            env_config=DEFAULT_CONFIG,
            n_splits=args.splits,
            total_timesteps=args.steps,
            algorithm=args.algo,
            seed=args.seed,
            synthetic_length=args.length,
            regime_period=args.regime_period,
            track_mlflow=args.track_mlflow,
            mlflow_experiment=args.mlflow_experiment,
            save_pipeline_artifacts=args.save_pipeline_artifacts,
            pipeline_artifact_dir=args.pipeline_artifact_dir,
            load_pipeline_artifact=args.load_pipeline_artifact,
            allow_pipeline_mismatch=args.allow_pipeline_mismatch,
            enable_prometheus=args.enable_prometheus,
            prometheus_host=args.prometheus_host,
            prometheus_port=args.prometheus_port,
        )
    except ImportError as exc:
        print(f"Missing optional dependency: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error during training: {exc}", file=sys.stderr)
        return 1

    _print_summary(results)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation helper
    sys.exit(main())


__all__ = ["SyntheticParams", "run_demo_training", "parse_args", "main"]
