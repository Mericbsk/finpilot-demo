#!/usr/bin/env python3
"""Sprint 20 — Optuna HP Tuning for Trio Ensemble (momentum / swing / conservative)

Agent-specific search spaces with Walk-Forward evaluation.
Each trial trains a short run and evaluates on held-out data.
Best params are then used for full 3M retraining.

SPEED-OPTIMISED:
  - NO VecFrameStack during tuning (22-dim obs vs 88-dim) — params transfer
  - Focused search space (~8 params vs 15)
  - Default 50K timesteps, tuneable via CLI
  - Fixed hyper-params that are less impactful (clip, vf_coef, max_grad_norm, gae)

Usage:
    python scripts/optuna_trio.py --agent momentum --n-trials 30
    python scripts/optuna_trio.py --agent swing --n-trials 25
    python scripts/optuna_trio.py --agent conservative --n-trials 30
    python scripts/optuna_trio.py --agent all --n-trials 25      # tune all 3
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import numpy as np
import optuna
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from drl.config import (
    MarketEnvConfig,
    RewardWeights,
)
from drl.data_loader import create_train_test_split
from drl.feature_pipeline import FeaturePipeline
from drl.market_env import EpisodeData, MarketEnv
from drl.specialists import (
    filter_multi_symbol,
    get_specialist,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    force=True,
    stream=sys.stdout,
)
logger = logging.getLogger("optuna_trio")

# Suppress noisy loggers during optimization
for _name in ["hmmlearn", "drl.data_loader", "urllib3", "yfinance"]:
    logging.getLogger(_name).setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# Symbol sets — 14 core symbols for fast tuning
# ---------------------------------------------------------------------------

_CORE_SYMBOLS = [
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
    "SPY",
    "QQQ",
    "IWM",
]

_TUNING_SYMBOLS = _CORE_SYMBOLS


# ---------------------------------------------------------------------------
# Data cache (load once, reuse across all trials)
# ---------------------------------------------------------------------------

_data_cache: dict[str, pd.DataFrame] | None = None


def _load_data(symbols: list[str], period: str = "2y") -> dict[str, pd.DataFrame]:
    global _data_cache
    if _data_cache is not None:
        return _data_cache

    from scripts.train_sprint18 import load_training_data

    _data_cache = load_training_data(symbols, period)
    logger.info("Data cached: %d symbols", len(_data_cache))
    return _data_cache


def create_episode(df: pd.DataFrame) -> EpisodeData:
    """Create an EpisodeData from a DataFrame."""
    from scripts.train_sprint18 import create_episode as _ce

    return _ce(df)


# ---------------------------------------------------------------------------
# Agent-specific search spaces (focused — ~8 dimensions)
# ---------------------------------------------------------------------------


@dataclass
class SearchSpace:
    """Focused hyperparameter search ranges for a specific agent."""

    agent_tag: str

    # Core PPO params (searched)
    lr_range: tuple[float, float] = (1e-5, 5e-4)
    gamma_range: tuple[float, float] = (0.97, 0.999)
    n_epochs_range: tuple[int, int] = (3, 8)
    batch_choices: list[int] = field(default_factory=lambda: [128, 256])

    # Fixed PPO params (not searched — sensible defaults)
    n_steps: int = 1024
    gae_lambda: float = 0.95
    ent_coef: float = 0.01
    clip_range: float = 0.2
    vf_coef: float = 0.5
    max_grad_norm: float = 0.5

    # Reward params (searched)
    pnl_range: tuple[float, float] = (5.0, 20.0)
    dd_range: tuple[float, float] = (0.1, 1.0)
    cost_range: tuple[float, float] = (0.03, 0.2)
    sharpe_bonus_range: tuple[float, float] = (0.0, 0.4)


# Focused search spaces per agent
SEARCH_SPACES = {
    "momentum": SearchSpace(
        agent_tag="momentum",
        lr_range=(1e-5, 5e-4),
        gamma_range=(0.97, 0.999),
        n_epochs_range=(3, 5),
        batch_choices=[256, 512],
        n_steps=1024,
        gae_lambda=0.95,
        ent_coef=0.01,
        clip_range=0.2,
        # Momentum: big PnL, moderate DD
        pnl_range=(8.0, 22.0),
        dd_range=(0.15, 0.55),
        cost_range=(0.03, 0.12),
        sharpe_bonus_range=(0.0, 0.2),
    ),
    "swing": SearchSpace(
        agent_tag="swing",
        lr_range=(1e-5, 3e-4),
        gamma_range=(0.98, 0.9999),
        n_epochs_range=(3, 5),
        batch_choices=[128, 256],
        n_steps=1024,
        gae_lambda=0.95,
        ent_coef=0.005,
        clip_range=0.2,
        # Swing: balanced
        pnl_range=(8.0, 18.0),
        dd_range=(0.15, 0.50),
        cost_range=(0.02, 0.08),
        sharpe_bonus_range=(0.05, 0.30),
    ),
    "conservative": SearchSpace(
        agent_tag="conservative",
        lr_range=(5e-5, 5e-4),
        gamma_range=(0.99, 0.9999),
        n_epochs_range=(3, 5),
        batch_choices=[256, 512],
        n_steps=1024,
        gae_lambda=0.95,
        ent_coef=0.02,
        clip_range=0.25,
        # Conservative: heavy DD penalty, Sharpe focus
        pnl_range=(4.0, 14.0),
        dd_range=(0.4, 1.2),
        cost_range=(0.05, 0.20),
        sharpe_bonus_range=(0.10, 0.60),
    ),
}


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


def _compute_metrics(history: list[dict]) -> dict:
    """Extract metrics from episode history."""
    if not history:
        return {
            "sharpe_ratio": 0,
            "total_return": 0,
            "max_drawdown": 0,
            "n_trades": 0,
            "active_pct": 0,
        }

    pnl = np.array([float(h.get("pnl", 0)) for h in history])
    equity = np.array([float(h.get("equity", 1)) for h in history])
    positions = np.array([float(h.get("position", 0)) for h in history])

    pnl_std = float(np.std(pnl)) or 1e-8
    sharpe = float(np.mean(pnl) / pnl_std)
    max_eq = np.maximum.accumulate(equity)
    max_dd = float(np.max((max_eq - equity) / np.where(max_eq > 0, max_eq, 1.0)))
    total_return = float(equity[-1] - equity[0]) if len(equity) > 1 else 0

    n_trades = sum(
        1 for i in range(1, len(positions)) if abs(positions[i] - positions[i - 1]) > 0.02
    )
    active_pct = float(np.mean(np.abs(positions) > 0.05)) * 100

    return {
        "sharpe_ratio": round(sharpe, 4),
        "total_return": round(total_return, 4),
        "max_drawdown": round(max_dd, 4),
        "n_trades": n_trades,
        "active_pct": round(active_pct, 1),
    }


# ---------------------------------------------------------------------------
# Objective function
# ---------------------------------------------------------------------------


def create_objective(
    agent_tag: str,
    space: SearchSpace,
    symbols: list[str],
    timesteps_per_trial: int,
    period: str,
    force_ppo: bool = False,
):
    """Create the Optuna objective closure for a specific agent.

    SPEED NOTES:
    - NO VecFrameStack — uses raw 22-dim obs for fast training.
      HP params (lr, gamma, batch, reward weights) transfer to stacked training.
    - Eval uses raw obs too (no obs stacking) for consistency.
    - force_ppo=True uses PPO even for RPPO agents (reward weights transfer).
    """

    specialty = get_specialist(agent_tag)
    is_recurrent = not force_ppo and specialty.preferred_algorithm.upper() in (
        "RPPO",
        "RECURRENTPPO",
    )

    # Pre-filter and cache data splits
    data = _load_data(symbols, period)
    merged = filter_multi_symbol(data, specialty.data_filter)
    train_df, test_df, _ = create_train_test_split(merged, train_ratio=0.8)

    logger.info(
        "%s data: train=%d test=%d rows",
        agent_tag,
        len(train_df),
        len(test_df),
    )

    # Pre-build episodes (reused across trials)
    train_episode = create_episode(train_df)
    test_episode = create_episode(test_df)

    def objective(trial: optuna.Trial) -> float:
        # === Core PPO hyperparameters (searched) ===
        lr = trial.suggest_float("lr", space.lr_range[0], space.lr_range[1], log=True)
        gamma = trial.suggest_float("gamma", space.gamma_range[0], space.gamma_range[1])
        n_epochs = trial.suggest_int("n_epochs", space.n_epochs_range[0], space.n_epochs_range[1])
        batch_size = trial.suggest_categorical("batch_size", space.batch_choices)

        # === Reward weights (searched) ===
        pnl_w = trial.suggest_float("pnl_weight", space.pnl_range[0], space.pnl_range[1])
        dd_w = trial.suggest_float("dd_weight", space.dd_range[0], space.dd_range[1])
        cost_w = trial.suggest_float("cost_weight", space.cost_range[0], space.cost_range[1])
        sharpe_b = trial.suggest_float(
            "sharpe_bonus", space.sharpe_bonus_range[0], space.sharpe_bonus_range[1]
        )

        # Fixed params (not searched)
        n_steps = space.n_steps
        gae_lambda = space.gae_lambda
        ent_coef = space.ent_coef
        clip_range_val = space.clip_range
        vf_coef = space.vf_coef
        max_grad_norm = space.max_grad_norm

        if batch_size > n_steps:
            batch_size = n_steps

        # === Build config with trial reward weights ===
        reward = RewardWeights(
            pnl=pnl_w,
            drawdown=dd_w,
            cost=cost_w,
            sharpe_bonus=sharpe_b,
            turnover_penalty=specialty.reward.turnover_penalty,
            leverage=specialty.reward.leverage,
        )

        config = specialty.build_config()
        config = MarketEnvConfig(
            feature_specs=config.feature_specs,
            reward=reward,
            transaction_costs=config.transaction_costs,
            pilotshield=config.pilotshield,
            schema_version=config.schema_version,
            target_dtype=config.target_dtype,
        )

        # === Create env (NO VecFrameStack for speed) ===
        pipeline = FeaturePipeline(config)
        pipeline.fit(train_episode.features)

        from stable_baselines3.common.vec_env import DummyVecEnv

        def make_env():
            return MarketEnv(train_episode, pipeline, config)

        vec_env = DummyVecEnv([make_env])

        # === Build model ===
        t0 = time.time()
        try:
            if is_recurrent:
                from sb3_contrib import RecurrentPPO

                model = RecurrentPPO(
                    "MlpLstmPolicy",
                    vec_env,
                    learning_rate=lr,
                    n_steps=n_steps,
                    batch_size=batch_size,
                    n_epochs=n_epochs,
                    gamma=gamma,
                    gae_lambda=gae_lambda,
                    ent_coef=ent_coef,
                    vf_coef=vf_coef,
                    max_grad_norm=max_grad_norm,
                    clip_range=clip_range_val,
                    verbose=0,
                    seed=42,
                )
            else:
                from stable_baselines3 import PPO

                model = PPO(
                    "MlpPolicy",
                    vec_env,
                    learning_rate=lr,
                    n_steps=n_steps,
                    batch_size=batch_size,
                    n_epochs=n_epochs,
                    gamma=gamma,
                    gae_lambda=gae_lambda,
                    ent_coef=ent_coef,
                    vf_coef=vf_coef,
                    max_grad_norm=max_grad_norm,
                    clip_range=clip_range_val,
                    verbose=0,
                    seed=42,
                )

            model.learn(total_timesteps=timesteps_per_trial)
        except Exception as e:
            logger.warning("Trial %d train failed: %s", trial.number, e)
            vec_env.close()
            return float("-inf")

        train_time = time.time() - t0
        vec_env.close()

        # === Evaluate on test set (raw obs, no stacking) ===
        eval_env = MarketEnv(test_episode, pipeline, config)
        result = eval_env.reset()
        obs = result[0] if isinstance(result, tuple) else result

        done = False
        lstm_states = None
        episode_starts = np.array([True])

        while not done:
            obs_input = obs[np.newaxis, :]
            if is_recurrent:
                action, lstm_states = model.predict(
                    obs_input,
                    state=lstm_states,
                    episode_start=episode_starts,
                    deterministic=True,
                )
                episode_starts = np.array([False])
            else:
                action, _ = model.predict(obs_input, deterministic=True)

            result = eval_env.step(action[0])
            if len(result) == 5:
                obs, reward, terminated, truncated, info = result
                done = terminated or truncated
            else:
                obs, reward, done, info = result

        history = eval_env.get_history()
        if not history:
            return float("-inf")

        metrics = _compute_metrics(history)

        # === Composite objective ===
        sharpe = metrics["sharpe_ratio"]
        dd = metrics["max_drawdown"]
        active = metrics["active_pct"] / 100.0

        activity_bonus = 0.05 * min(active, 1.0)

        # Agent-specific DD penalty thresholds
        if agent_tag == "conservative":
            dd_threshold, dd_penalty_mult = 0.15, 1.0
        elif agent_tag == "swing":
            dd_threshold, dd_penalty_mult = 0.30, 0.5
        else:  # momentum
            dd_threshold, dd_penalty_mult = 0.35, 0.3

        dd_penalty = -dd_penalty_mult * max(dd - dd_threshold, 0)
        ret_bonus = 0.02 * max(metrics["total_return"], 0)

        objective_value = sharpe + activity_bonus + dd_penalty + ret_bonus

        # Store metrics in trial
        trial.set_user_attr("sharpe", metrics["sharpe_ratio"])
        trial.set_user_attr("return", metrics["total_return"])
        trial.set_user_attr("max_dd", metrics["max_drawdown"])
        trial.set_user_attr("trades", metrics["n_trades"])
        trial.set_user_attr("active_pct", metrics["active_pct"])
        trial.set_user_attr("train_time", round(train_time, 1))

        msg = (
            f"Trial {trial.number:3d}: obj={objective_value:.4f} "
            f"sharpe={metrics['sharpe_ratio']:.4f} ret={metrics['total_return']:.4f} "
            f"dd={metrics['max_drawdown']:.4f} trades={metrics['n_trades']} "
            f"active={metrics['active_pct']:.0f}% [{train_time:.0f}s]"
        )
        print(msg, flush=True)

        return objective_value

    return objective


# ---------------------------------------------------------------------------
# Tuning orchestrator
# ---------------------------------------------------------------------------


def tune_agent(
    agent_tag: str,
    n_trials: int,
    timesteps: int,
    symbols: list[str],
    period: str,
    timeout: int | None = None,
    force_ppo: bool = False,
) -> dict:
    """Run Optuna optimization for one agent. Returns best params."""

    space = SEARCH_SPACES[agent_tag]
    specialty = get_specialist(agent_tag)
    algo_label = (
        "PPO (proxy)"
        if force_ppo and specialty.preferred_algorithm.upper() in ("RPPO", "RECURRENTPPO")
        else specialty.preferred_algorithm
    )

    print(f"\n{'=' * 70}", flush=True)
    print(f"  OPTUNA HP SEARCH — {agent_tag} ({specialty.name})", flush=True)
    print(f"{'=' * 70}", flush=True)
    print(f"  Trials     : {n_trials}", flush=True)
    print(f"  Steps/trial: {timesteps:,}", flush=True)
    print(f"  Symbols    : {len(symbols)}", flush=True)
    print(f"  Algorithm  : {algo_label}", flush=True)
    print("  Obs dim    : 22 (no VecFrameStack for speed)", flush=True)
    print("  Search dims: 8 (lr,gamma,epochs,batch + 4 reward)", flush=True)
    print(f"{'=' * 70}\n", flush=True)

    # Pre-load data
    _load_data(symbols, period)

    study = optuna.create_study(
        study_name=f"finpilot-{agent_tag}-hpo",
        direction="maximize",
        sampler=optuna.samplers.TPESampler(
            seed=42,
            n_startup_trials=min(10, n_trials // 3),
        ),
        pruner=optuna.pruners.NopPruner(),
    )

    objective = create_objective(
        agent_tag=agent_tag,
        space=space,
        symbols=symbols,
        timesteps_per_trial=timesteps,
        period=period,
        force_ppo=force_ppo,
    )

    study.optimize(
        objective,
        n_trials=n_trials,
        timeout=timeout,
        show_progress_bar=False,
    )

    # === Results ===
    completed = [t for t in study.trials if t.value is not None and t.value > float("-inf")]
    if not completed:
        print(f"\n  WARNING: No valid trials for {agent_tag}!", flush=True)
        return {"agent": agent_tag, "best_params": {}, "best_value": 0, "best_attrs": {}}

    best = study.best_trial
    print(f"\n{'=' * 70}", flush=True)
    print(f"  {agent_tag.upper()} OPTIMIZATION COMPLETE", flush=True)
    print(f"{'=' * 70}", flush=True)
    print(f"  Valid trials: {len(completed)}/{len(study.trials)}", flush=True)
    print(f"  Best trial  : #{best.number}", flush=True)
    print(f"  Objective   : {best.value:.4f}", flush=True)
    print(f"  Sharpe      : {best.user_attrs.get('sharpe', '?')}", flush=True)
    print(f"  Return      : {best.user_attrs.get('return', '?')}", flush=True)
    print(f"  Max DD      : {best.user_attrs.get('max_dd', '?')}", flush=True)
    print(f"  Trades      : {best.user_attrs.get('trades', '?')}", flush=True)
    print(f"  Active%     : {best.user_attrs.get('active_pct', '?')}", flush=True)
    print(f"  Train time  : {best.user_attrs.get('train_time', '?')}s", flush=True)
    print("\n  BEST PARAMETERS:", flush=True)
    for k, v in sorted(best.params.items()):
        if isinstance(v, float):
            print(f"    {k:25s}: {v:.6f}", flush=True)
        else:
            print(f"    {k:25s}: {v}", flush=True)
    # Also print the FIXED params for reference
    print("\n  FIXED PARAMS (not tuned):", flush=True)
    print(f"    {'n_steps':25s}: {space.n_steps}", flush=True)
    print(f"    {'gae_lambda':25s}: {space.gae_lambda}", flush=True)
    print(f"    {'ent_coef':25s}: {space.ent_coef}", flush=True)
    print(f"    {'clip_range':25s}: {space.clip_range}", flush=True)
    print(f"    {'vf_coef':25s}: {space.vf_coef}", flush=True)
    print(f"    {'max_grad_norm':25s}: {space.max_grad_norm}", flush=True)
    print(f"{'=' * 70}", flush=True)

    # Top 5
    print("\n  TOP 5 TRIALS:", flush=True)
    print(
        f"  {'#':>4s} {'Obj':>8s} {'Sharpe':>8s} {'Return':>8s} {'DD':>8s} {'Trades':>7s} {'Time':>6s}",
        flush=True,
    )
    sorted_trials = sorted(completed, key=lambda t: t.value, reverse=True)
    for t in sorted_trials[:5]:
        print(
            f"  {t.number:4d} {t.value:8.4f} "
            f"{t.user_attrs.get('sharpe', 0):8.4f} "
            f"{t.user_attrs.get('return', 0):8.4f} "
            f"{t.user_attrs.get('max_dd', 0):8.4f} "
            f"{t.user_attrs.get('trades', 0):7d} "
            f"{t.user_attrs.get('train_time', 0):5.0f}s",
            flush=True,
        )

    # Save results
    results_path = ROOT / "data" / f"optuna_{agent_tag}_results.json"
    results = {
        "agent": agent_tag,
        "timestamp": datetime.now().isoformat(),
        "n_trials": n_trials,
        "timesteps_per_trial": timesteps,
        "symbols": symbols,
        "best_trial": best.number,
        "best_value": round(best.value, 4),
        "best_params": best.params,
        "fixed_params": {
            "n_steps": space.n_steps,
            "gae_lambda": space.gae_lambda,
            "ent_coef": space.ent_coef,
            "clip_range": space.clip_range,
            "vf_coef": space.vf_coef,
            "max_grad_norm": space.max_grad_norm,
        },
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
    print(f"\n  Results saved: {results_path}", flush=True)

    return {
        "agent": agent_tag,
        "best_params": best.params,
        "best_value": best.value,
        "best_attrs": best.user_attrs,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Optuna HP tuning for trio ensemble")
    parser.add_argument(
        "--agent",
        default="all",
        choices=["momentum", "swing", "conservative", "all"],
        help="Which agent to tune (default: all)",
    )
    parser.add_argument("--n-trials", type=int, default=30, help="Trials per agent (default: 30)")
    parser.add_argument(
        "--timesteps",
        type=int,
        default=50_000,
        help="Training steps per trial (default: 50K — fast search)",
    )
    parser.add_argument("--period", default="2y", help="Data period")
    parser.add_argument("--timeout", type=int, default=None, help="Timeout in seconds per agent")
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=None,
        help="Override symbol list (default: 14 core symbols)",
    )
    parser.add_argument(
        "--force-ppo",
        action="store_true",
        help="Use PPO even for RPPO agents (faster tuning, reward weights transfer)",
    )
    args = parser.parse_args()

    symbols = args.symbols or _TUNING_SYMBOLS
    agents = ["momentum", "swing", "conservative"] if args.agent == "all" else [args.agent]

    total_start = time.time()
    all_results = {}
    for agent in agents:
        result = tune_agent(
            agent_tag=agent,
            n_trials=args.n_trials,
            timesteps=args.timesteps,
            symbols=symbols,
            period=args.period,
            timeout=args.timeout,
            force_ppo=args.force_ppo,
        )
        all_results[agent] = result

    # Summary
    total_time = time.time() - total_start
    if len(all_results) > 1:
        print(f"\n{'=' * 70}", flush=True)
        print("  TRIO OPTIMIZATION SUMMARY", flush=True)
        print(f"{'=' * 70}", flush=True)
        for agent, res in all_results.items():
            attrs = res.get("best_attrs", {})
            print(
                f"  {agent:15s}: obj={res.get('best_value', 0):.4f} "
                f"sharpe={attrs.get('sharpe', '?')} "
                f"ret={attrs.get('return', '?')} "
                f"dd={attrs.get('max_dd', '?')}",
                flush=True,
            )
        print(f"\n  Total time: {total_time / 60:.1f} min", flush=True)
        print(f"{'=' * 70}", flush=True)

        combined_path = ROOT / "data" / "optuna_trio_results.json"
        with open(combined_path, "w") as f:
            json.dump(
                {
                    a: {
                        "best_params": r["best_params"],
                        "best_value": r["best_value"],
                        "best_attrs": r["best_attrs"],
                    }
                    for a, r in all_results.items()
                },
                f,
                indent=2,
                default=str,
            )
        print(f"\n  Combined results: {combined_path}", flush=True)
    else:
        print(f"\n  Total time: {total_time / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
