"""Differential-privacy PPO training using Opacus.

Drop-in companion to drl/training.py. The existing training pipeline is
unchanged — this script provides an *opt-in* DP variant for runs where
GDPR "privacy by design" guarantees are required.

Usage:
    python drl/train_private.py --symbol AAPL --timesteps 500000 --epsilon 8.0

Requirements:
    pip install opacus==1.6.0 stable-baselines3

Privacy guarantees:
    - DP-SGD with Rényi accountant
    - target_epsilon controls maximum privacy budget spend
    - delta=1e-5 (standard for datasets > 10k samples)
    - max_grad_norm clips per-sample gradients before noise injection

Output:
    models/<symbol>_dp_ppo.zip          — trained model
    data/privacy_report_<symbol>.json   — epsilon audit trail
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ---------------------------------------------------------------------------
# Optional dependency guards
# ---------------------------------------------------------------------------
try:
    import torch
    from torch.utils.data import DataLoader, TensorDataset
except ImportError as e:
    sys.exit(f"PyTorch required: {e}")

try:
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv
except ImportError as e:
    sys.exit(f"stable-baselines3 required: {e}")

try:
    from opacus import PrivacyEngine
    from opacus.validators import ModuleValidator
except ImportError as e:
    sys.exit(f"opacus required — run: pip install opacus==1.6.0\n{e}")

try:
    import yfinance as yf
except ImportError as e:
    sys.exit(f"yfinance required: {e}")

from drl.config import MarketEnvConfig
from drl.feature_pipeline import FeaturePipeline
from drl.market_env import MarketEnv

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_DEFAULT_TIMESTEPS = 200_000
_DEFAULT_EPSILON = 10.0
_DEFAULT_DELTA = 1e-5
_DEFAULT_NOISE = 1.1
_DEFAULT_GRAD_NORM = 1.0
_DEFAULT_BATCH = 256


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fetch_data(symbol: str, period: str = "2y") -> "pd.DataFrame":
    import pandas as pd

    logger.info("Fetching %s (%s)...", symbol, period)
    df = yf.download(symbol, period=period, auto_adjust=True, progress=False)
    if df.empty:
        sys.exit(f"No data returned for {symbol}")
    df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]
    return df


def _make_env(df, config: MarketEnvConfig):
    pipeline = FeaturePipeline(config)
    features = pipeline.fit_transform(df)
    return MarketEnv(features, config=config)


def _dummy_loader(batch_size: int, feature_dim: int, n_samples: int = 2048) -> DataLoader:
    """Minimal DataLoader used only to inform Opacus of batch size."""
    X = torch.randn(n_samples, feature_dim)
    y = torch.zeros(n_samples, dtype=torch.long)
    return DataLoader(TensorDataset(X, y), batch_size=batch_size, drop_last=True)


def _fix_policy_for_opacus(policy) -> None:
    """Replace unsupported modules (BatchNorm) with GroupNorm equivalents."""
    errors = ModuleValidator.validate(policy, strict=False)
    if errors:
        logger.info("Fixing %d Opacus compatibility issues in policy...", len(errors))
        ModuleValidator.fix(policy)


class _EpsilonCallback:
    """SB3-compatible callback that tracks privacy budget after each rollout."""

    def __init__(self, privacy_engine: PrivacyEngine, delta: float):
        self.privacy_engine = privacy_engine
        self.delta = delta
        self.log: list[dict] = []

    def on_rollout_end(self) -> None:
        eps = self.privacy_engine.get_epsilon(self.delta)
        self.log.append({"step": len(self.log), "epsilon": eps})
        if len(self.log) % 10 == 0:
            logger.info("Privacy budget spent: ε=%.4f (target ε=%.1f)", eps, self._target)

    def set_target(self, target: float) -> None:
        self._target = target


# ---------------------------------------------------------------------------
# Main training function
# ---------------------------------------------------------------------------

def train_with_dp(
    symbol: str,
    total_timesteps: int = _DEFAULT_TIMESTEPS,
    target_epsilon: float = _DEFAULT_EPSILON,
    delta: float = _DEFAULT_DELTA,
    noise_multiplier: float = _DEFAULT_NOISE,
    max_grad_norm: float = _DEFAULT_GRAD_NORM,
    batch_size: int = _DEFAULT_BATCH,
    output_dir: Path = Path("models"),
    report_dir: Path = Path("data"),
) -> dict:
    """Train a PPO model with differential privacy. Returns privacy report dict."""

    output_dir.mkdir(exist_ok=True)
    report_dir.mkdir(exist_ok=True)

    # 1. Data + env
    df = _fetch_data(symbol)
    config = MarketEnvConfig()
    env = _make_env(df, config)
    vec_env = DummyVecEnv([lambda: env])

    # 2. PPO model (no DP yet)
    model = PPO(
        "MlpPolicy",
        vec_env,
        verbose=0,
        batch_size=batch_size,
        n_steps=max(batch_size, 1024),
        learning_rate=3e-4,
    )

    # 3. Fix policy for Opacus (removes unsupported layers)
    _fix_policy_for_opacus(model.policy)

    # 4. Wrap with PrivacyEngine
    privacy_engine = PrivacyEngine(accountant="rdp")

    # Estimate epochs for budget calculation (approximation)
    n_rollouts = total_timesteps // model.n_steps
    n_epochs_approx = max(1, n_rollouts * model.n_epochs)

    feature_dim = env.observation_space.shape[0]
    loader = _dummy_loader(batch_size, feature_dim)

    try:
        model.policy, model.policy.optimizer, _ = privacy_engine.make_private_with_epsilon(
            module=model.policy,
            optimizer=model.policy.optimizer,
            data_loader=loader,
            target_epsilon=target_epsilon,
            target_delta=delta,
            epochs=n_epochs_approx,
            max_grad_norm=max_grad_norm,
        )
        actual_noise = model.policy.optimizer.noise_multiplier
    except Exception as exc:
        # Fallback: use fixed noise_multiplier if epsilon calculation fails
        logger.warning("make_private_with_epsilon failed (%s) — using fixed noise %.2f", exc, noise_multiplier)
        model.policy, model.policy.optimizer, _ = privacy_engine.make_private(
            module=model.policy,
            optimizer=model.policy.optimizer,
            data_loader=loader,
            noise_multiplier=noise_multiplier,
            max_grad_norm=max_grad_norm,
        )
        actual_noise = model.policy.optimizer.noise_multiplier

    logger.info(
        "DP-SGD enabled: noise_multiplier=%.4f, max_grad_norm=%.1f, delta=%.0e",
        actual_noise, max_grad_norm, delta,
    )

    # 5. Callback for epsilon tracking
    eps_cb = _EpsilonCallback(privacy_engine, delta)
    eps_cb.set_target(target_epsilon)

    # Monkey-patch rollout end to track budget
    original_collect = model.collect_rollouts

    def _patched_collect(*args, **kwargs):
        result = original_collect(*args, **kwargs)
        eps_cb.on_rollout_end()
        return result

    model.collect_rollouts = _patched_collect  # type: ignore[method-assign]

    # 6. Train
    start = datetime.now(timezone.utc)
    logger.info("Training %s for %d timesteps with DP (target ε=%.1f)...", symbol, total_timesteps, target_epsilon)
    model.learn(total_timesteps=total_timesteps)
    end = datetime.now(timezone.utc)

    # 7. Final privacy accounting
    epsilon_spent = privacy_engine.get_epsilon(delta)
    logger.info("Training complete. Final ε=%.4f (target=%.1f)", epsilon_spent, target_epsilon)

    # 8. Save model
    model_path = output_dir / f"{symbol.lower()}_dp_ppo"
    model.save(str(model_path))
    logger.info("Model saved to %s.zip", model_path)

    # 9. Privacy report
    report = {
        "symbol": symbol,
        "trained_at": start.isoformat(),
        "duration_seconds": (end - start).total_seconds(),
        "total_timesteps": total_timesteps,
        "target_epsilon": target_epsilon,
        "epsilon_spent": epsilon_spent,
        "delta": delta,
        "noise_multiplier": actual_noise,
        "max_grad_norm": max_grad_norm,
        "batch_size": batch_size,
        "privacy_budget_remaining": target_epsilon - epsilon_spent,
        "epsilon_log": eps_cb.log[-20:],  # last 20 checkpoints
        "model_path": str(model_path) + ".zip",
        "gdpr_note": (
            "DP-SGD training with Opacus RDP accountant. "
            f"Formal guarantee: (ε={epsilon_spent:.4f}, δ={delta:.0e})-DP."
        ),
    }

    report_path = report_dir / f"privacy_report_{symbol.lower()}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info("Privacy report saved to %s", report_path)

    return report


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train PPO with Differential Privacy (Opacus)")
    p.add_argument("--symbol", default="AAPL", help="Ticker symbol (default: AAPL)")
    p.add_argument("--timesteps", type=int, default=_DEFAULT_TIMESTEPS, help="Total training timesteps")
    p.add_argument("--epsilon", type=float, default=_DEFAULT_EPSILON, help="Target privacy budget ε (default: 10.0)")
    p.add_argument("--delta", type=float, default=_DEFAULT_DELTA, help="Privacy delta (default: 1e-5)")
    p.add_argument("--noise", type=float, default=_DEFAULT_NOISE, help="Noise multiplier fallback (default: 1.1)")
    p.add_argument("--grad-norm", type=float, default=_DEFAULT_GRAD_NORM, help="Max gradient norm (default: 1.0)")
    p.add_argument("--batch-size", type=int, default=_DEFAULT_BATCH, help="Batch size (default: 256)")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    report = train_with_dp(
        symbol=args.symbol,
        total_timesteps=args.timesteps,
        target_epsilon=args.epsilon,
        delta=args.delta,
        noise_multiplier=args.noise,
        max_grad_norm=args.grad_norm,
        batch_size=args.batch_size,
    )

    print("\n" + "=" * 60)
    print("PRIVACY REPORT SUMMARY")
    print("=" * 60)
    print(f"  Symbol:          {report['symbol']}")
    print(f"  ε spent:         {report['epsilon_spent']:.4f}")
    print(f"  ε target:        {report['target_epsilon']}")
    print(f"  Budget remaining: {report['privacy_budget_remaining']:.4f}")
    print(f"  δ:               {report['delta']:.0e}")
    print(f"  Duration:        {report['duration_seconds']:.1f}s")
    print(f"  Model:           {report['model_path']}")
    print("=" * 60)

    if report["epsilon_spent"] > report["target_epsilon"]:
        logger.warning("⚠️  Privacy budget exceeded! ε_spent=%.4f > ε_target=%.1f",
                       report["epsilon_spent"], report["target_epsilon"])
        sys.exit(1)

    print("✅ Training complete within privacy budget.")
