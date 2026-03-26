#!/usr/bin/env python3
"""Sprint 18 — DRL Agent Retraining Script

Trains 3 regime-specific agents (trend/range/volatile) with:
  - Symbol-agnostic features (relative ratios — works across ALL symbols)
  - Simplified 3-term reward (PnL + DD + Cost)
  - HMM-based regime detection
  - Observation stacking (n_stack=4) OR RecurrentPPO (LSTM)
  - Multi-symbol curriculum (progressive symbol introduction)
  - Learnable ensemble weights (auto-saved after training)
  - 3M timesteps per agent (vs 500K before)
  - Pipeline artifact saved alongside model

Usage:
    python scripts/train_sprint18.py                        # PPO + stacking (14 core)
    python scripts/train_sprint18.py --algorithm RPPO       # RecurrentPPO (LSTM)
    python scripts/train_sprint18.py --curriculum           # Multi-symbol curriculum
    python scripts/train_sprint18.py --agent trend          # Train one
    python scripts/train_sprint18.py --timesteps 500000     # Quick test
    python scripts/train_sprint18.py --symbol-set broad     # 50 diverse symbols
    python scripts/train_sprint18.py --symbol-set full      # All 1542 FinPilot symbols
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("train_sprint18")


def parse_args():
    parser = argparse.ArgumentParser(description="Sprint 18/19 DRL Training")
    parser.add_argument(
        "--agent",
        default="all",
        help=(
            "Which agent(s) to train. Options: "
            "trend, range, volatile, momentum, meanrev, breakout, "
            "scalper, swing, conservative, aggressive, "
            "all (regime only), all-specialists (all 10), "
            "or comma-separated list e.g. 'trend,momentum,conservative'"
        ),
    )
    parser.add_argument(
        "--timesteps",
        type=int,
        default=3_000_000,
        help="Total training timesteps per agent (default: 3M)",
    )
    parser.add_argument(
        "--n-stack",
        type=int,
        default=4,
        help="Observation stacking depth (default: 4)",
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=None,
        help="Training symbols (default: 14 standard symbols)",
    )
    parser.add_argument(
        "--period",
        default="2y",
        help="Data period (default: 2y)",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=3e-4,
        help="Learning rate (default: 3e-4)",
    )
    parser.add_argument(
        "--gamma",
        type=float,
        default=0.99,
        help="Discount factor (default: 0.99)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed",
    )
    parser.add_argument(
        "--algorithm",
        choices=["PPO", "RPPO", "RecurrentPPO", "SAC"],
        default="PPO",
        help="Algorithm: PPO (MLP+stacking), RPPO/RecurrentPPO (LSTM), or SAC (off-policy)",
    )
    parser.add_argument(
        "--curriculum",
        action="store_true",
        default=False,
        help="Enable multi-symbol curriculum (progressive symbol introduction)",
    )
    parser.add_argument(
        "--symbol-set",
        choices=["core", "broad", "full"],
        default="core",
        help="Symbol universe: core (14), broad (50 diverse), full (all FinPilot presets)",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Sprint 18 Phase 4.2: Symbol universe definitions
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

_BROAD_SYMBOLS = _CORE_SYMBOLS + [
    # US large cap (diversified sectors)
    "JPM",
    "V",
    "UNH",
    "JNJ",
    "PG",
    "XOM",
    "HD",
    "BAC",
    "PFE",
    "KO",
    # International / regional
    "TSM",
    "BABA",
    "NVO",
    "SAP",
    "ASML",
    # Commodities & energy
    "XLE",
    "GLD",
    "SLV",
    "USO",
    # Bonds & defensive
    "TLT",
    "VNQ",
    "XLU",
    # Small cap / high vol
    "ARKK",
    "PLTR",
    "SOFI",
    "COIN",
    "RIOT",
    # Sector ETFs
    "XLK",
    "XLF",
    "XLV",
    "XBI",
    "SMH",
    # Crypto proxy
    "BTC-USD",
    "ETH-USD",
]


def _get_full_symbols() -> list[str]:
    """Load all symbols from FinPilot stock presets."""
    try:
        from views.components.stock_presets import STOCK_PRESETS, StockPreset

        all_syms: set[str] = set()
        for preset in STOCK_PRESETS:
            if isinstance(preset, StockPreset):
                all_syms.update(preset.symbols)
            elif isinstance(preset, dict):
                all_syms.update(preset.get("symbols", []))
        return sorted(all_syms)
    except ImportError:
        logger.warning("stock_presets not importable — falling back to broad symbols")
        return _BROAD_SYMBOLS


def get_symbol_set(name: str, explicit_symbols: list[str] | None = None) -> list[str]:
    """Return the appropriate symbol list for the requested set."""
    if explicit_symbols:
        return explicit_symbols
    if name == "core":
        return _CORE_SYMBOLS
    elif name == "broad":
        return _BROAD_SYMBOLS
    elif name == "full":
        return _get_full_symbols()
    return _CORE_SYMBOLS


def load_training_data(symbols: list[str], period: str) -> dict[str, pd.DataFrame]:
    """Fetch multi-symbol data with HMM regime labels."""
    from drl.data_loader import fetch_training_data

    logger.info("Fetching data for %d symbols (period=%s)...", len(symbols), period)
    data = fetch_training_data(symbols, period=period, interval="1d")
    logger.info("Loaded %d/%d symbols successfully", len(data), len(symbols))
    return data


def filter_by_regime(
    data: dict[str, pd.DataFrame], target_regime: str, min_pct: float = 0.15
) -> pd.DataFrame:
    """Concatenate multi-symbol data, weighted toward target regime.

    Unlike previous training (single symbol), we merge all symbols but
    oversample windows where the target regime is dominant.
    Each symbol's prices are normalized to 1.0 to prevent cross-symbol
    price jumps in the concatenated series.
    """
    from drl.specialists import _normalize_prices

    frames = []
    for symbol, df in data.items():
        df_copy = _normalize_prices(df)
        df_copy["_symbol"] = symbol
        frames.append(df_copy)

    merged = pd.concat(frames, ignore_index=False)

    # Count regime distribution
    regime_col = f"regime_{target_regime}"
    if regime_col in merged.columns:
        target_pct = merged[regime_col].mean()
        logger.info(
            "Regime '%s' represents %.1f%% of data (%d rows)",
            target_regime,
            target_pct * 100,
            len(merged),
        )
    else:
        logger.warning("Regime column %s not found, using all data", regime_col)

    merged.drop(columns=["_symbol"], inplace=True, errors="ignore")
    return merged


def create_episode(df: pd.DataFrame):
    """Create EpisodeData from DataFrame."""
    from drl.config import DEFAULT_CONFIG
    from drl.data_loader import _add_placeholder_features, prepare_episode_data

    df = _add_placeholder_features(df)
    # Ensure all columns
    for col in DEFAULT_CONFIG.feature_columns:
        if col not in df.columns:
            df[col] = 0.0
    return prepare_episode_data(df)


def train_single_agent(
    agent_tag: str,
    data: dict[str, pd.DataFrame],
    timesteps: int,
    n_stack: int,
    lr: float,
    seed: int,
    algorithm: str = "PPO",
    use_curriculum: bool = False,
    gamma: float = 0.99,
) -> dict:
    """Train one specialist agent and save it.

    Sprint 19: uses AgentSpecialty for per-agent reward profiles, data filtering,
    and environment overrides.  Falls back to default config for legacy tags.
    """
    from drl.config import DEFAULT_CONFIG
    from drl.data_loader import create_train_test_split
    from drl.feature_pipeline import FeaturePipeline
    from drl.market_env import MarketEnv
    from drl.model_registry import get_registry
    from drl.persistence import build_artifact, save_artifact
    from stable_baselines3.common.vec_env import DummyVecEnv, VecFrameStack

    # Sprint 19: load specialist config if available
    specialty = None
    try:
        from drl.specialists import filter_multi_symbol, get_specialist

        specialty = get_specialist(agent_tag)
        logger.info(
            "Using specialist profile: %s (%s / %s)",
            specialty.name,
            specialty.domain.value,
            specialty.tag.value,
        )
    except (ImportError, KeyError, ValueError):
        logger.info("No specialist profile for '%s', using defaults", agent_tag)

    # Algorithm selection (specialist may prefer a specific algorithm)
    effective_algo = algorithm
    if specialty and algorithm == "PPO" and specialty.preferred_algorithm != "PPO":
        effective_algo = specialty.preferred_algorithm
        logger.info("Specialist prefers %s → overriding algorithm", effective_algo)

    is_recurrent = effective_algo.upper() in ("RPPO", "RECURRENTPPO")
    is_sac = effective_algo.upper() == "SAC"

    if is_recurrent:
        from sb3_contrib import RecurrentPPO

        algo_cls = RecurrentPPO
        policy_name = "MlpLstmPolicy"
        algo_label = "RecurrentPPO"
    elif is_sac:
        from stable_baselines3 import SAC

        algo_cls = SAC
        policy_name = "MlpPolicy"
        algo_label = "SAC"
    else:
        from stable_baselines3 import PPO

        algo_cls = PPO
        policy_name = "MlpPolicy"
        algo_label = "PPO"

    model_name = f"{'rppo' if is_recurrent else 'ppo'}_{agent_tag}"
    effective_n_stack = specialty.n_stack if specialty else n_stack

    logger.info("=" * 60)
    logger.info(
        "TRAINING: %s | algo=%s | timesteps=%d | n_stack=%d | lr=%s",
        model_name,
        algo_label,
        timesteps,
        effective_n_stack,
        lr,
    )
    if specialty:
        logger.info(
            "  Domain: %s | Reward: pnl=%.1f dd=%.2f cost=%.2f",
            specialty.domain.value,
            specialty.reward.pnl,
            specialty.reward.drawdown,
            specialty.reward.cost,
        )
    logger.info("=" * 60)

    # 1. Prepare data — specialist data filter or legacy regime filter
    if specialty:
        merged = filter_multi_symbol(data, specialty.data_filter)
        logger.info("Specialist data filter: %d rows retained", len(merged))
    else:
        merged = filter_by_regime(data, agent_tag)

    if len(merged) < 100:
        logger.error("Not enough data for %s training (%d rows)", agent_tag, len(merged))
        return {"agent": agent_tag, "status": "failed", "error": "insufficient data"}

    train_df, test_df, _ = create_train_test_split(merged, train_ratio=0.8)
    logger.info("Train: %d rows | Test: %d rows", len(train_df), len(test_df))

    # 2. Create episodes with specialist config
    config = specialty.build_config() if specialty else DEFAULT_CONFIG
    train_episode = create_episode(train_df)
    test_episode = create_episode(test_df)

    # 3. Fit pipeline on training data
    pipeline = FeaturePipeline(config)
    pipeline.fit(train_episode.features)

    # 4. Create env with observation stacking (disabled for LSTM)
    def make_env():
        return MarketEnv(train_episode, pipeline, config)

    vec_env = DummyVecEnv([make_env])
    if effective_n_stack > 1 and not is_recurrent:
        vec_env = VecFrameStack(vec_env, n_stack=effective_n_stack)
        logger.info(
            "Obs stacking: %d → %d features",
            len(config.feature_columns),
            len(config.feature_columns) * effective_n_stack,
        )
    elif is_recurrent:
        logger.info("LSTM policy: temporal memory handled internally (no frame stacking)")

    # 4b. Multi-symbol curriculum callbacks
    callbacks = []
    if use_curriculum:
        from drl.callbacks import (
            CurriculumCallback,
            CurriculumConfig,
            MultiSymbolCallback,
            MultiSymbolCurriculumConfig,
        )

        # Build per-symbol episodes for rotation
        symbol_episodes = {}
        for symbol, sym_df in data.items():
            try:
                ep = create_episode(sym_df)
                symbol_episodes[symbol] = ep
            except Exception as e:
                logger.warning("Skipping %s for curriculum: %s", symbol, e)

        # Difficulty curriculum (costs + position limits)
        diff_cfg = CurriculumConfig(total_timesteps=timesteps)
        callbacks.append(CurriculumCallback(diff_cfg, smooth=True, verbose=1))

        # Symbol diversity curriculum
        sym_cfg = MultiSymbolCurriculumConfig(total_timesteps=timesteps)
        callbacks.append(
            MultiSymbolCallback(
                config=sym_cfg,
                episodes=symbol_episodes,
                pipeline=pipeline,
                env_config=config,
                verbose=1,
            )
        )
        logger.info(
            "Curriculum: %d symbol episodes | 3-phase difficulty | symbol rotation",
            len(symbol_episodes),
        )

    # 5. Build model
    t0 = time.time()
    if is_sac:
        # SAC: off-policy — different hyper-parameter set
        model = algo_cls(
            policy_name,
            vec_env,
            learning_rate=lr,
            buffer_size=100_000,
            batch_size=256,
            gamma=gamma,
            tau=0.005,
            ent_coef="auto",
            verbose=0,
            seed=seed,
        )
    else:
        # Sprint 24: wider network for complex reward signals
        policy_kwargs = {"net_arch": {"pi": [128, 128], "vf": [128, 128]}}
        model = algo_cls(
            policy_name,
            vec_env,
            learning_rate=lr,
            n_steps=2048,
            batch_size=256,
            n_epochs=10,
            gamma=gamma,
            gae_lambda=0.95,
            ent_coef=0.005,
            vf_coef=0.5,
            max_grad_norm=0.5,
            verbose=0,
            seed=seed,
            policy_kwargs=policy_kwargs,
        )

    logger.info("Training started... (%s)", algo_label)
    model.learn(total_timesteps=timesteps, callback=callbacks or None, progress_bar=True)
    train_time = time.time() - t0
    logger.info("Training completed in %.1fs", train_time)

    # 6. Evaluate on test data
    # NOTE: We use raw MarketEnv (not DummyVecEnv) for evaluation because
    # DummyVecEnv auto-resets on episode end, which clears the env's history.
    # For models trained with VecFrameStack, we manually stack observations.
    logger.info("Evaluating on test set...")

    eval_env = MarketEnv(test_episode, pipeline, config)
    obs, info = eval_env.reset()

    # Manual observation stacking for VecFrameStack-trained models
    use_stacking = effective_n_stack > 1 and not is_recurrent
    if use_stacking:
        obs_stack = np.zeros((effective_n_stack, len(obs)), dtype=np.float32)
        obs_stack[-1] = obs

    done = False
    lstm_states = None
    episode_starts = np.array([True])

    while not done:
        if use_stacking:
            stacked_obs = obs_stack.flatten()[np.newaxis, :]  # (1, n_stack*n_features)
        else:
            stacked_obs = obs[np.newaxis, :]  # (1, n_features)

        if is_recurrent:
            action, lstm_states = model.predict(
                stacked_obs, state=lstm_states, episode_start=episode_starts, deterministic=True
            )
            episode_starts = np.array([False])
        else:
            action, _ = model.predict(stacked_obs, deterministic=True)

        raw_action = action[0]  # unwrap from batch dim
        obs, reward, terminated, truncated, info = eval_env.step(raw_action)
        done = terminated or truncated

        if use_stacking:
            obs_stack = np.roll(obs_stack, -1, axis=0)
            obs_stack[-1] = obs

    # History is preserved because we used raw env (no auto-reset)
    history = eval_env.get_history()
    metrics = _compute_metrics(history)
    metrics["train_time_s"] = round(train_time, 1)
    logger.info(
        "Results: sharpe=%.4f | return=%.4f | max_dd=%.4f | trades=%d",
        metrics["sharpe_ratio"],
        metrics["total_return"],
        metrics["max_drawdown"],
        metrics.get("n_trades", 0),
    )

    # 7. Save model
    registry = get_registry()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_id = f"{model_name}_{timestamp}"
    model_dir = Path("models") / model_id
    model_dir.mkdir(parents=True, exist_ok=True)

    model_path = model_dir / "model"
    model.save(str(model_path))

    # Save pipeline artifact
    artifact = build_artifact(pipeline)
    save_artifact(artifact, model_dir / "pipeline.json")

    # Register in registry
    from drl.model_registry import ModelMetadata

    # Sprint 19: specialist metadata
    specialist_info = {}
    if specialty:
        specialist_info = {
            "domain": specialty.domain.value,
            "reward_pnl": specialty.reward.pnl,
            "reward_dd": specialty.reward.drawdown,
            "reward_cost": specialty.reward.cost,
            "data_filter": str(specialty.data_filter),
        }

    registry._registry[model_id] = ModelMetadata(
        model_id=model_id,
        name=model_name,
        algorithm=algo_label,
        version=f"v_sprint19_{timestamp}",
        created_at=datetime.now().isoformat(),
        total_timesteps=timesteps,
        training_symbols=list(data.keys()),
        metrics=metrics,
        hyperparameters={
            "lr": lr,
            "n_stack": effective_n_stack if not is_recurrent else 1,
            "n_steps": 2048,
            "batch_size": 256,
            "ent_coef": 0.005,
            "reward": "specialist" if specialty else "simplified_3term",
            "regime_detection": "hmm",
            "policy": policy_name,
            "curriculum": use_curriculum,
            **specialist_info,
        },
        feature_columns=list(config.feature_columns),
        model_path=str(model_path),
        pipeline_path=str(model_dir / "pipeline.json"),
        is_active=False,
        tags=[
            agent_tag,
            "sprint19",
            "specialist" if specialty else "regime_specific",
            "hmm",
            "lstm" if is_recurrent else "stacked",
            *(["curriculum"] if use_curriculum else []),
            *([specialty.domain.value] if specialty else []),
        ],
        notes=(
            f"Sprint 19 Specialist: {specialty.name if specialty else agent_tag} | "
            f"{algo_label} + "
            f"{'LSTM memory' if is_recurrent else f'obs stacking (n={effective_n_stack})'}"
            f"{' + multi-symbol curriculum' if use_curriculum else ''}"
        ),
    )
    registry._save_registry()

    logger.info("✅ Saved: %s → %s", model_id, model_dir)

    return {
        "agent": agent_tag,
        "model_id": model_id,
        "status": "success",
        "metrics": metrics,
        "train_time_s": train_time,
    }


def _compute_metrics(history: list[dict]) -> dict:
    """Extract metrics from episode history."""
    if not history:
        return {"sharpe_ratio": 0, "total_return": 0, "max_drawdown": 0, "avg_reward": 0}

    pnl = np.array([float(h.get("pnl", 0)) for h in history])
    rewards = np.array([float(h.get("reward", 0)) for h in history])
    equity = np.array([float(h.get("equity", 1)) for h in history])
    positions = np.array([float(h.get("position", 0)) for h in history])

    pnl_std = float(np.std(pnl)) or 1e-8
    sharpe = float(np.mean(pnl) / pnl_std)
    max_eq = np.maximum.accumulate(equity)
    max_dd = float(np.max((max_eq - equity) / max_eq)) if len(equity) > 0 else 0
    total_return = float(equity[-1] - equity[0]) if len(equity) > 1 else 0

    n_trades = sum(
        1 for i in range(1, len(positions)) if abs(positions[i] - positions[i - 1]) > 0.02
    )
    active_pct = round(100 * np.mean(np.abs(positions) > 0.05), 1)
    action_values = {round(p, 1) for p in positions}

    return {
        "sharpe_ratio": round(sharpe, 4),
        "total_return": round(total_return, 4),
        "max_drawdown": round(max_dd, 4),
        "avg_reward": round(float(np.mean(rewards)), 6),
        "n_trades": n_trades,
        "active_pct": active_pct,
        "action_diversity": round(len(action_values) / max(len(positions), 1), 2),
    }


def main():
    args = parse_args()

    # Symbol universe selection (Phase 4.2)
    symbols = get_symbol_set(args.symbol_set, args.symbols)

    # Sprint 19: resolve agent selection
    from drl.specialists import list_all_tags

    all_specialist_tags = list_all_tags()

    if args.agent == "all":
        agents = ["trend", "range", "volatile"]  # legacy regime set
    elif args.agent == "all-specialists":
        agents = all_specialist_tags  # all 10 specialists
    elif "," in args.agent:
        agents = [a.strip() for a in args.agent.split(",")]
    else:
        agents = [args.agent]

    print("=" * 60)
    print("🚀 SPRINT 19 — MULTI-SPECIALIST DRL TRAINING")
    print("=" * 60)
    print(f"  Agents:     {', '.join(agents)} ({len(agents)} total)")
    print(f"  Algorithm:  {args.algorithm} (may be overridden per specialist)")
    print(f"  Timesteps:  {args.timesteps:,}")
    print(
        f"  Obs Stack:  {args.n_stack}{' (disabled for LSTM)' if args.algorithm != 'PPO' else ''}"
    )
    print(f"  Curriculum: {'ON' if args.curriculum else 'OFF'}")
    print(f"  Symbol Set: {args.symbol_set} ({len(symbols)} symbols)")
    print(f"  Period:     {args.period}")
    print(f"  LR:         {args.lr}")
    print("  Features:   symbol-agnostic (relative ratios)")
    print(f"  Available:  {', '.join(all_specialist_tags)}")
    print("=" * 60)

    # Load data once (shared across all agents)
    data = load_training_data(symbols, args.period)
    if not data:
        logger.error("No data loaded. Exiting.")
        sys.exit(1)

    # Train agents
    agents = ["trend", "range", "volatile"] if args.agent == "all" else agents
    results = []

    for agent_tag in agents:
        result = train_single_agent(
            agent_tag=agent_tag,
            data=data,
            timesteps=args.timesteps,
            n_stack=args.n_stack,
            lr=args.lr,
            seed=args.seed,
            algorithm=args.algorithm,
            use_curriculum=args.curriculum,
            gamma=args.gamma,
        )
        results.append(result)
        print()

    # Summary
    print("\n" + "=" * 60)
    print("📊 TRAINING SUMMARY")
    print("=" * 60)
    for r in results:
        status = "✅" if r["status"] == "success" else "❌"
        m = r.get("metrics", {})
        print(
            f"  {status} {r['agent']:10s} | "
            f"Sharpe: {m.get('sharpe_ratio', 0):+.4f} | "
            f"Return: {m.get('total_return', 0):+.4f} | "
            f"DD: {m.get('max_drawdown', 0):.4f} | "
            f"Trades: {m.get('n_trades', 0)}"
        )
    print("=" * 60)

    # Save summary
    summary_path = Path("logs") / f"train_sprint18_{datetime.now():%Y%m%d_%H%M%S}.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n📄 Detay: {summary_path}")


if __name__ == "__main__":
    main()
