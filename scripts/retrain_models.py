#!/usr/bin/env python3
"""Sprint 14 — Retrain all DRL models with improved reward function.

Trains 5 PPO variants using the Sprint 13 reward improvements:
  - Turnover penalty (0.05)
  - Rolling Sharpe bonus (0.10)
  - Stochastic volume-dependent slippage
  - Holding penalty (1 bps)
  - Curriculum learning (3-phase)

Each variant has distinct hyperparameters to cover different trading styles:
  1. conservative  — low LR, high gamma, more timesteps
  2. balanced      — default params, curriculum learning
  3. aggressive    — higher LR, lower gamma, high entropy
  4. explorer      — very high ent_coef for maximum exploration
  5. long_horizon  — extended training (100k steps), deep curriculum

Usage:
    python scripts/retrain_models.py                  # all 5 variants
    python scripts/retrain_models.py --only balanced  # single variant
    python scripts/retrain_models.py --symbols AAPL MSFT
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

# Ensure project root on sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from drl.callbacks import (  # noqa: E402
    CurriculumCallback,
    CurriculumConfig,
    TrainingMetricsCallback,
)
from drl.config import DEFAULT_CONFIG, MarketEnvConfig  # noqa: E402
from drl.data_loader import (  # noqa: E402
    fetch_training_data,
    prepare_episode_data,
)
from drl.feature_pipeline import FeaturePipeline  # noqa: E402
from drl.market_env import MarketEnv  # noqa: E402
from drl.model_registry import ModelRegistry  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Model variant definitions
# ---------------------------------------------------------------------------

@dataclass
class ModelVariant:
    name: str
    tag: str
    total_timesteps: int
    learning_rate: float
    gamma: float
    gae_lambda: float
    ent_coef: float
    vf_coef: float
    seed: int
    use_curriculum: bool
    notes: str


VARIANTS: list[ModelVariant] = [
    ModelVariant(
        name="ppo_conservative",
        tag="conservative",
        total_timesteps=80_000,
        learning_rate=1e-4,
        gamma=0.995,
        gae_lambda=0.98,
        ent_coef=0.005,
        vf_coef=0.5,
        seed=42,
        use_curriculum=True,
        notes="Low LR, high gamma — favours patient, risk-averse strategies",
    ),
    ModelVariant(
        name="ppo_balanced",
        tag="balanced",
        total_timesteps=60_000,
        learning_rate=3e-4,
        gamma=0.99,
        gae_lambda=0.95,
        ent_coef=0.01,
        vf_coef=0.5,
        seed=123,
        use_curriculum=True,
        notes="Default params with curriculum learning — general-purpose",
    ),
    ModelVariant(
        name="ppo_aggressive",
        tag="aggressive",
        total_timesteps=60_000,
        learning_rate=5e-4,
        gamma=0.97,
        gae_lambda=0.90,
        ent_coef=0.02,
        vf_coef=0.5,
        seed=456,
        use_curriculum=True,
        notes="Higher LR, lower gamma — faster adaptation, momentum trading",
    ),
    ModelVariant(
        name="ppo_explorer",
        tag="explorer",
        total_timesteps=60_000,
        learning_rate=3e-4,
        gamma=0.99,
        gae_lambda=0.95,
        ent_coef=0.05,
        vf_coef=0.5,
        seed=789,
        use_curriculum=False,
        notes="Very high entropy — maximum exploration to avoid constant-HOLD",
    ),
    ModelVariant(
        name="ppo_longhorizon",
        tag="longhorizon",
        total_timesteps=100_000,
        learning_rate=2e-4,
        gamma=0.995,
        gae_lambda=0.97,
        ent_coef=0.01,
        vf_coef=0.5,
        seed=2024,
        use_curriculum=True,
        notes="Extended training (100k steps) — deep curriculum for robust policy",
    ),
]


# ---------------------------------------------------------------------------
# Training helpers
# ---------------------------------------------------------------------------

def train_single_variant(
    variant: ModelVariant,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    config: MarketEnvConfig,
) -> dict:
    """Train one model variant and return metrics + model object."""
    logger.info("=" * 60)
    logger.info(f"Training: {variant.name} ({variant.tag})")
    logger.info(f"  timesteps={variant.total_timesteps}  lr={variant.learning_rate}")
    logger.info(f"  gamma={variant.gamma}  ent_coef={variant.ent_coef}")
    logger.info(f"  curriculum={variant.use_curriculum}  seed={variant.seed}")
    logger.info("=" * 60)

    # Prepare episode data
    train_episode = prepare_episode_data(train_df, config)
    test_episode = prepare_episode_data(test_df, config)

    # Fit feature pipeline on training data
    pipeline = FeaturePipeline(config)
    pipeline.fit(train_episode.features)

    # Build callbacks
    callbacks = []
    if variant.use_curriculum:
        curriculum_cfg = CurriculumConfig(
            total_timesteps=variant.total_timesteps,
            log_interval=max(5000, variant.total_timesteps // 10),
            verbose=True,
        )
        callbacks.append(CurriculumCallback(config=curriculum_cfg, smooth=True, verbose=1))

    metrics_cb = TrainingMetricsCallback(
        log_interval=max(2000, variant.total_timesteps // 20),
        verbose=1,
    )
    callbacks.append(metrics_cb)

    # Create environment + model
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv

    def _make_train_env():
        return MarketEnv(train_episode, pipeline, config)

    vec_env = DummyVecEnv([_make_train_env])

    model = PPO(
        "MlpPolicy",
        vec_env,
        learning_rate=variant.learning_rate,
        gamma=variant.gamma,
        gae_lambda=variant.gae_lambda,
        ent_coef=variant.ent_coef,
        vf_coef=variant.vf_coef,
        verbose=0,
        seed=variant.seed,
    )

    # Train
    t0 = time.time()
    model.learn(
        total_timesteps=variant.total_timesteps,
        callback=callbacks,
    )
    train_time = time.time() - t0
    logger.info(f"  Training completed in {train_time:.1f}s")

    # Evaluate on test set
    eval_env = MarketEnv(test_episode, pipeline, config)
    obs, _info = eval_env.reset()
    done = False
    while not done:
        action, _state = model.predict(obs, deterministic=True)
        step_result = eval_env.step(action)
        if len(step_result) == 5:
            obs, _reward, terminated, truncated, _info = step_result
            done = bool(terminated or truncated)
        else:
            obs, _reward, done, _info = step_result
            done = bool(done)

    history = eval_env.get_history()

    # Compute metrics
    metrics = _compute_eval_metrics(history)
    logger.info(f"  Eval: sharpe={metrics['sharpe_ratio']:.4f}  "
                f"return={metrics['total_return']:.4f}  "
                f"max_dd={metrics['max_drawdown']:.4f}  "
                f"avg_reward={metrics['avg_reward']:.4f}")

    # Check action diversity (not constant HOLD)
    positions = [float(h.get("position", 0)) for h in history]
    if positions:
        nonzero = sum(1 for p in positions if abs(p) > 0.05)
        nonzero_pct = nonzero / len(positions)
        trades = sum(1 for i in range(1, len(positions))
                     if abs(positions[i] - positions[i - 1]) > 0.02)
        metrics["action_diversity"] = round(nonzero_pct, 2)
        metrics["n_trades"] = trades
        metrics["active_pct"] = round(nonzero_pct * 100, 1)
        logger.info(f"  Trades={trades}  active={nonzero_pct:.0%} of steps")
    else:
        metrics["action_diversity"] = 0.0
        metrics["n_trades"] = 0
        metrics["active_pct"] = 0.0

    metrics["train_time_s"] = round(train_time, 1)

    return {
        "model": model,
        "pipeline": pipeline,
        "metrics": metrics,
        "history": history,
        "variant": variant,
    }


def _compute_eval_metrics(history: list[dict]) -> dict[str, float]:
    """Extract evaluation metrics from history."""
    if not history:
        return {"avg_reward": 0.0, "sharpe_ratio": 0.0, "max_drawdown": 0.0, "total_return": 0.0}

    pnl = np.array([float(h.get("pnl", 0.0)) for h in history])
    rewards = np.array([float(h.get("reward", 0.0)) for h in history])
    equity = np.array([float(h.get("equity", 1.0)) for h in history])

    total_return = float(equity[-1] - equity[0]) if len(equity) > 1 else float(np.sum(pnl))
    pnl_std = float(np.std(pnl)) or 1e-6
    sharpe = float(np.mean(pnl) / pnl_std)
    max_eq = np.maximum.accumulate(equity)
    drawdowns = (max_eq - equity) / np.where(max_eq > 0, max_eq, 1.0)
    max_dd = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0
    avg_reward = float(np.mean(rewards))

    return {
        "avg_reward": round(avg_reward, 6),
        "sharpe_ratio": round(sharpe, 4),
        "max_drawdown": round(max_dd, 4),
        "total_return": round(total_return, 4),
    }


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Retrain all DRL models (Sprint 14)")
    parser.add_argument("--symbols", nargs="+", default=["AAPL", "NVDA", "TSLA"],
                        help="Symbols to train on")
    parser.add_argument("--period", default="2y", help="Data period for yfinance")
    parser.add_argument("--only", default=None, help="Train only this variant tag")
    parser.add_argument("--skip-registry-clean", action="store_true",
                        help="Don't clear old models from registry")
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("  SPRINT 14 — FULL MODEL RETRAINING")
    print("=" * 70)
    print(f"  Symbols: {args.symbols}")
    print(f"  Period : {args.period}")
    print(f"  Variants: {len(VARIANTS)}")
    print("=" * 70 + "\n")

    # Step 1: Fetch training data
    logger.info("Step 1/5: Fetching training data …")
    data = fetch_training_data(args.symbols, period=args.period, interval="1d")
    if not data:
        logger.error("No data fetched — aborting")
        sys.exit(1)

    # Merge all symbols for multi-asset training
    all_dfs = []
    for sym, df in data.items():
        logger.info(f"  {sym}: {len(df)} rows")
        all_dfs.append(df)

    merged = pd.concat(all_dfs, ignore_index=True)
    logger.info(f"  Merged: {len(merged)} total rows")

    # Step 2: Create train/test split (80/20 chronological)
    logger.info("Step 2/5: Creating train/test split …")
    n = len(merged)
    train_end = int(n * 0.8)
    train_df = merged.iloc[:train_end].copy()
    test_df = merged.iloc[train_end:].copy()
    logger.info(f"  Train: {len(train_df)} rows  |  Test: {len(test_df)} rows")

    config = DEFAULT_CONFIG

    # Step 3: Train all variants
    logger.info("Step 3/5: Training models …")
    variants_to_train = VARIANTS
    if args.only:
        variants_to_train = [v for v in VARIANTS if v.tag == args.only]
        if not variants_to_train:
            logger.error(f"Unknown variant tag: {args.only}")
            sys.exit(1)

    results = []
    for variant in variants_to_train:
        try:
            result = train_single_variant(variant, train_df, test_df, config)
            results.append(result)
        except Exception as e:
            logger.error(f"  FAILED: {variant.name} — {e}")
            import traceback
            traceback.print_exc()

    if not results:
        logger.error("All training runs failed — aborting")
        sys.exit(1)

    # Step 4: Register models
    logger.info("\nStep 4/5: Registering models …")
    registry = ModelRegistry("models/")

    # Optionally clean old entries
    if not args.skip_registry_clean:
        old_ids = list(registry._registry.keys())
        for old_id in old_ids:
            try:
                registry.delete_model(old_id, force=True)
                logger.info(f"  Removed old model: {old_id}")
            except Exception as exc:
                logger.debug("Could not delete %s: %s", old_id, exc)

    best_sharpe = -np.inf
    best_model_id = None

    for res in results:
        variant = res["variant"]
        metrics = res["metrics"]
        model = res["model"]
        pipeline = res["pipeline"]

        model_id = registry.save_model(
            model=model,
            name=variant.name,
            algorithm="PPO",
            metrics=metrics,
            hyperparameters={
                "total_timesteps": variant.total_timesteps,
                "learning_rate": variant.learning_rate,
                "gamma": variant.gamma,
                "gae_lambda": variant.gae_lambda,
                "ent_coef": variant.ent_coef,
                "vf_coef": variant.vf_coef,
                "seed": variant.seed,
                "use_curriculum": variant.use_curriculum,
            },
            training_symbols=args.symbols,
            total_timesteps=variant.total_timesteps,
            feature_columns=list(config.feature_columns),
            pipeline=pipeline,
            tags=[variant.tag, "sprint14", "retrained"],
            notes=variant.notes,
        )

        logger.info(f"  Registered: {model_id}")
        logger.info(f"    sharpe={metrics['sharpe_ratio']:.4f}  "
                     f"return={metrics['total_return']:.4f}  "
                     f"trades={metrics.get('n_trades', 0)}")

        if metrics["sharpe_ratio"] > best_sharpe:
            best_sharpe = metrics["sharpe_ratio"]
            best_model_id = model_id

    # Step 5: Set best model as active & save best copy
    if best_model_id:
        registry.set_active(best_model_id)
        logger.info(f"\n  ★ Active model: {best_model_id} (sharpe={best_sharpe:.4f})")

        # Copy best model to models/best/
        best_dir = Path("models/best")
        best_dir.mkdir(parents=True, exist_ok=True)
        best_result = next(r for r in results
                          if registry._registry[best_model_id].name == r["variant"].name)
        best_result["model"].save(str(best_dir / "best_model"))
        logger.info(f"  Best model copied to {best_dir / 'best_model.zip'}")

    # Summary report
    print("\n" + "=" * 70)
    print("  TRAINING SUMMARY — Sprint 14")
    print("=" * 70)
    print(f"  {'Variant':<20s} {'Sharpe':>8s} {'Return':>8s} {'MaxDD':>8s} {'Trades':>8s} {'Time':>8s}")
    print("  " + "─" * 60)
    for res in results:
        v = res["variant"]
        m = res["metrics"]
        active = " ★" if registry._registry.get(
            next((mid for mid, meta in registry._registry.items()
                  if meta.name == v.name), ""), None
        ) and registry._registry.get(
            next((mid for mid, meta in registry._registry.items()
                  if meta.name == v.name), ""), None
        ) is not None and registry._registry[
            next((mid for mid, meta in registry._registry.items()
                  if meta.name == v.name), "")
        ].is_active else ""
        print(f"  {v.tag:<20s} {m['sharpe_ratio']:>8.4f} {m['total_return']:>8.4f} "
              f"{m['max_drawdown']:>8.4f} {m.get('n_trades', 0):>8d} "
              f"{m.get('train_time_s', 0):>7.1f}s{active}")
    print("=" * 70)
    print(f"  Best: {best_model_id} (sharpe={best_sharpe:.4f})")
    print(f"  Registry: {len(registry._registry)} models")
    print("=" * 70 + "\n")

    return results


if __name__ == "__main__":
    main()
