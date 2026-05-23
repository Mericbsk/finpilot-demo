#!/usr/bin/env python3
"""Sprint 17 — Optuna HP search for ppo_range model.

Uses the same training pipeline as retrain_models.py (MarketEnv + SB3 PPO)
so optimised parameters are directly deployable.

Searches over:
  - learning_rate, gamma, gae_lambda, ent_coef
  - n_steps, batch_size, n_epochs, clip_range
  - reward weights (pnl, drawdown, inactivity_penalty, sharpe_bonus)
  - regime oversampling factor

Usage:
    python scripts/optuna_range.py                     # 40 trials
    python scripts/optuna_range.py --n-trials 80       # more budget
    python scripts/optuna_range.py --timesteps 200000  # longer per trial
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import optuna
import pandas as pd

# Ensure project root on sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from drl.callbacks import (  # noqa: E402
    CurriculumCallback,
    CurriculumConfig,
    CurriculumPhase,
    TrainingMetricsCallback,
)
from drl.config import DEFAULT_CONFIG, MarketEnvConfig, RewardWeights  # noqa: E402
from drl.data_loader import fetch_training_data, prepare_episode_data  # noqa: E402
from drl.feature_pipeline import FeaturePipeline  # noqa: E402
from drl.market_env import MarketEnv  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RANGE_SYMBOLS = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "NVDA",
    "META",
    "TSLA",
    "AMD",
    "CRM",
    "ADBE",
    "INTC",
    "QCOM",
    "SPY",
    "QQQ",
    "IWM",
]


# ---------------------------------------------------------------------------
# Data caching (fetch once, reuse across trials)
# ---------------------------------------------------------------------------

_cached_data: dict[str, pd.DataFrame | None] = {
    "train_df": None,
    "test_df": None,
    "merged": None,
}


def _get_data(symbols: list[str], period: str = "3y") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fetch and cache training data. Returns (train_df, test_df)."""
    if _cached_data["train_df"] is not None and _cached_data["test_df"] is not None:
        return _cached_data["train_df"], _cached_data["test_df"]  # type: ignore[return-value]

    logger.info("Fetching training data (one-time) ...")
    data = fetch_training_data(symbols, period=period, interval="1d")
    if not data:
        raise RuntimeError("No data fetched")

    all_dfs = []
    for sym, df in data.items():
        logger.info(f"  {sym}: {len(df)} rows")
        all_dfs.append(df)

    merged = pd.concat(all_dfs, ignore_index=True)
    n = len(merged)
    train_end = int(n * 0.8)
    train_df = merged.iloc[:train_end].copy()
    test_df = merged.iloc[train_end:].copy()

    _cached_data["train_df"] = train_df
    _cached_data["test_df"] = test_df
    _cached_data["merged"] = merged

    logger.info(f"  Merged: {n} rows (train={len(train_df)}, test={len(test_df)})")
    return train_df, test_df


def _apply_regime_weighting(
    train_df: pd.DataFrame,
    regime: str,
    oversample_factor: int,
    seed: int,
) -> pd.DataFrame:
    """Apply regime-weighted oversampling."""
    if "regime" not in train_df.columns:
        return train_df

    regime_rows = train_df[train_df["regime"] == regime]
    if len(regime_rows) < 50:
        return train_df

    non_regime = train_df[train_df["regime"] != regime]
    oversampled = pd.concat([regime_rows] * oversample_factor, ignore_index=True)
    combined = pd.concat([oversampled, non_regime], ignore_index=True)
    return combined.sample(frac=1, random_state=seed).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Objective function
# ---------------------------------------------------------------------------


def create_objective(
    symbols: list[str],
    timesteps_per_trial: int,
    period: str,
):
    """Create the Optuna objective closure."""

    def objective(trial: optuna.Trial) -> float:
        # --- Hyperparameters to search ---
        lr = trial.suggest_float("learning_rate", 5e-5, 5e-4, log=True)
        gamma = trial.suggest_float("gamma", 0.98, 0.999)
        gae_lambda = trial.suggest_float("gae_lambda", 0.90, 0.99)
        ent_coef = trial.suggest_float("ent_coef", 0.005, 0.08, log=True)
        vf_coef = trial.suggest_float("vf_coef", 0.3, 0.7)
        n_steps = trial.suggest_categorical("n_steps", [1024, 2048, 4096])
        batch_size = trial.suggest_categorical("batch_size", [64, 128, 256])
        n_epochs = trial.suggest_int("n_epochs", 3, 10)
        clip_range = trial.suggest_float("clip_range", 0.1, 0.3)
        max_grad_norm = trial.suggest_float("max_grad_norm", 0.3, 1.0)

        # --- Reward weights ---
        pnl_weight = trial.suggest_float("pnl_weight", 5.0, 20.0)
        dd_weight = trial.suggest_float("dd_weight", 0.2, 1.0)
        inactivity_penalty = trial.suggest_float("inactivity_penalty", 0.005, 0.03)
        sharpe_bonus = trial.suggest_float("sharpe_bonus", 0.05, 0.30)
        position_bonus = trial.suggest_float("position_bonus", 0.002, 0.01)

        # --- Regime oversampling ---
        oversample_factor = trial.suggest_int("oversample_factor", 2, 5)

        # --- Get cached data ---
        train_df, test_df = _get_data(symbols, period)

        # --- Apply regime weighting ---
        weighted_train = _apply_regime_weighting(
            train_df, regime="range", oversample_factor=oversample_factor, seed=42
        )

        # --- Build config with trial reward weights ---
        config = MarketEnvConfig(
            feature_specs=DEFAULT_CONFIG.feature_specs,
            reward=RewardWeights(
                pnl=pnl_weight,
                drawdown=dd_weight,
                cost=DEFAULT_CONFIG.reward.cost,
                turnover_penalty=DEFAULT_CONFIG.reward.turnover_penalty,
                leverage=DEFAULT_CONFIG.reward.leverage,
                regime_bonus=DEFAULT_CONFIG.reward.regime_bonus,
                inactivity_penalty=inactivity_penalty,
                position_bonus=position_bonus,
                sharpe_bonus=sharpe_bonus,
            ),
            transaction_costs=DEFAULT_CONFIG.transaction_costs,
            pilotshield=DEFAULT_CONFIG.pilotshield,
            schema_version=DEFAULT_CONFIG.schema_version,
            target_dtype=DEFAULT_CONFIG.target_dtype,
        )

        # --- Prepare episode data ---
        train_episode = prepare_episode_data(weighted_train, config)
        test_episode = prepare_episode_data(test_df, config)

        pipeline = FeaturePipeline(config)
        pipeline.fit(train_episode.features)

        # --- 3-phase curriculum (simplified for speed) ---
        curriculum_phases = [
            CurriculumPhase(
                name="easy",
                start_pct=0.0,
                end_pct=0.30,
                cost_multiplier=0.2,
                position_limit_multiplier=0.5,
                pnl_weight_multiplier=1.5,
                drawdown_weight_multiplier=0.2,
                exploration_bonus=0.05,
            ),
            CurriculumPhase(
                name="medium",
                start_pct=0.30,
                end_pct=0.70,
                cost_multiplier=0.6,
                position_limit_multiplier=0.8,
                pnl_weight_multiplier=1.2,
                drawdown_weight_multiplier=0.5,
                exploration_bonus=0.02,
            ),
            CurriculumPhase(
                name="hard",
                start_pct=0.70,
                end_pct=1.0,
                cost_multiplier=1.0,
                position_limit_multiplier=1.0,
                pnl_weight_multiplier=1.0,
                drawdown_weight_multiplier=1.0,
                exploration_bonus=0.0,
            ),
        ]

        curriculum_cfg = CurriculumConfig(
            total_timesteps=timesteps_per_trial,
            phases=curriculum_phases,
            log_interval=max(5000, timesteps_per_trial // 10),
            verbose=False,
        )

        callbacks = [
            CurriculumCallback(config=curriculum_cfg, smooth=True, verbose=0),
            TrainingMetricsCallback(log_interval=max(5000, timesteps_per_trial // 10), verbose=0),
        ]

        # --- Create env + model ---
        from stable_baselines3 import PPO
        from stable_baselines3.common.vec_env import DummyVecEnv

        def _make_env():
            return MarketEnv(train_episode, pipeline, config)

        vec_env = DummyVecEnv([_make_env])

        model = PPO(
            "MlpPolicy",
            vec_env,
            learning_rate=lr,
            gamma=gamma,
            gae_lambda=gae_lambda,
            ent_coef=ent_coef,
            vf_coef=vf_coef,
            n_steps=n_steps,
            batch_size=batch_size,
            n_epochs=n_epochs,
            clip_range=clip_range,
            max_grad_norm=max_grad_norm,
            verbose=0,
            seed=42,
        )

        # --- Train ---
        t0 = time.time()
        try:
            model.learn(total_timesteps=timesteps_per_trial, callback=callbacks)
        except Exception as e:
            logger.warning(f"Trial {trial.number} train failed: {e}")
            return float("-inf")
        train_time = time.time() - t0

        # --- Evaluate on test set ---
        eval_env = MarketEnv(test_episode, pipeline, config)
        obs, _info = eval_env.reset()
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            step_result = eval_env.step(action)
            if len(step_result) == 5:
                obs, _reward, terminated, truncated, _info = step_result
                done = bool(terminated or truncated)
            else:
                obs, _reward, done, _info = step_result
                done = bool(done)

        history = eval_env.get_history()
        if not history:
            return float("-inf")

        # --- Compute metrics ---
        pnl = np.array([float(h.get("pnl", 0.0)) for h in history])
        equity = np.array([float(h.get("equity", 1.0)) for h in history])
        rewards = np.array([float(h.get("reward", 0.0)) for h in history])

        total_return = float(equity[-1] - equity[0]) if len(equity) > 1 else 0.0
        pnl_std = float(np.std(pnl)) or 1e-6
        sharpe = float(np.mean(pnl) / pnl_std)
        max_eq = np.maximum.accumulate(equity)
        drawdowns = (max_eq - equity) / np.where(max_eq > 0, max_eq, 1.0)
        max_dd = float(np.max(drawdowns))

        # Trade activity
        positions = [float(h.get("position", 0)) for h in history]
        trades = sum(
            1 for i in range(1, len(positions)) if abs(positions[i] - positions[i - 1]) > 0.02
        )
        active_pct = sum(1 for p in positions if abs(p) > 0.05) / max(len(positions), 1)

        # --- Composite objective ---
        # Primary: Sharpe ratio
        # Penalty: high drawdown, inactivity
        activity_bonus = 0.1 * min(active_pct, 1.0)
        dd_penalty = -0.5 * max(max_dd - 0.3, 0)  # penalty if DD > 30%
        objective_value = sharpe + activity_bonus + dd_penalty

        # Store all metrics for analysis
        trial.set_user_attr("sharpe", round(sharpe, 4))
        trial.set_user_attr("total_return", round(total_return, 4))
        trial.set_user_attr("max_drawdown", round(max_dd, 4))
        trial.set_user_attr("trades", trades)
        trial.set_user_attr("active_pct", round(active_pct * 100, 1))
        trial.set_user_attr("train_time", round(train_time, 1))
        trial.set_user_attr("avg_reward", round(float(np.mean(rewards)), 4))

        logger.info(
            f"Trial {trial.number:3d}: obj={objective_value:.4f} "
            f"sharpe={sharpe:.4f} ret={total_return:.4f} dd={max_dd:.4f} "
            f"trades={trades} active={active_pct:.0%} [{train_time:.0f}s]"
        )

        return objective_value

    return objective


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Optuna HP search for ppo_range")
    parser.add_argument("--n-trials", type=int, default=40, help="Number of Optuna trials")
    parser.add_argument(
        "--timesteps", type=int, default=150_000, help="Timesteps per trial (lower = faster search)"
    )
    parser.add_argument("--timeout", type=int, default=None, help="Timeout in seconds")
    parser.add_argument("--period", default="3y", help="Data period")
    parser.add_argument("--symbols", nargs="+", default=RANGE_SYMBOLS, help="Training symbols")
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("  OPTUNA HP SEARCH — ppo_range (mean-reversion)")
    print("=" * 70)
    print(f"  Trials     : {args.n_trials}")
    print(f"  Steps/trial: {args.timesteps}")
    print(f"  Symbols    : {len(args.symbols)}")
    print(f"  Timeout    : {args.timeout or 'None'}")
    print("=" * 70 + "\n")

    # Pre-fetch data
    _get_data(args.symbols, args.period)

    # Create study
    study = optuna.create_study(
        study_name="finpilot-range-hpo",
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=42, n_startup_trials=10),
        pruner=optuna.pruners.NopPruner(),  # no pruning — each trial is short
    )

    objective = create_objective(
        symbols=args.symbols,
        timesteps_per_trial=args.timesteps,
        period=args.period,
    )

    # Run search
    study.optimize(
        objective,
        n_trials=args.n_trials,
        timeout=args.timeout,
        show_progress_bar=True,
    )

    # Results
    best = study.best_trial
    print("\n" + "=" * 70)
    print("  OPTUNA SEARCH COMPLETE")
    print("=" * 70)
    print(f"  Best trial : #{best.number}")
    print(f"  Objective  : {best.value:.4f}")
    print(f"  Sharpe     : {best.user_attrs.get('sharpe', '?')}")
    print(f"  Return     : {best.user_attrs.get('total_return', '?')}")
    print(f"  MaxDD      : {best.user_attrs.get('max_drawdown', '?')}")
    print(f"  Trades     : {best.user_attrs.get('trades', '?')}")
    print(f"  Active%    : {best.user_attrs.get('active_pct', '?')}")
    print("-" * 70)
    print("  BEST PARAMETERS:")
    for k, v in sorted(best.params.items()):
        if isinstance(v, float):
            print(f"    {k:25s}: {v:.6f}")
        else:
            print(f"    {k:25s}: {v}")
    print("=" * 70)

    # Save results
    results_path = ROOT / "data" / "optuna_range_results.json"
    results = {
        "best_trial": best.number,
        "best_value": round(best.value, 4),
        "best_params": best.params,
        "best_attrs": best.user_attrs,
        "all_trials": [
            {
                "number": t.number,
                "value": round(t.value, 4) if t.value is not None else None,
                "params": t.params,
                "attrs": t.user_attrs,
                "state": str(t.state),
            }
            for t in study.trials
        ],
    }
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Results saved to {results_path}")

    # Print top-5 trials
    print("\n  TOP 5 TRIALS:")
    print(f"  {'#':>4s} {'Objective':>10s} {'Sharpe':>8s} {'Return':>8s} {'DD':>8s} {'Trades':>8s}")
    print("  " + "-" * 50)
    sorted_trials = sorted(
        [t for t in study.trials if t.value is not None],
        key=lambda t: t.value,  # type: ignore[arg-type,return-value]
        reverse=True,
    )
    for t in sorted_trials[:5]:
        print(
            f"  {t.number:4d} {t.value:10.4f} "  # type: ignore[arg-type]
            f"{t.user_attrs.get('sharpe', 0):8.4f} "
            f"{t.user_attrs.get('total_return', 0):8.4f} "
            f"{t.user_attrs.get('max_drawdown', 0):8.4f} "
            f"{t.user_attrs.get('trades', 0):8d}"
        )
    print()

    return study


if __name__ == "__main__":
    main()
