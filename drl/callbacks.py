"""Curriculum learning callbacks for FinPilot DRL training.

Implements progressive difficulty scaling during training.  The agent starts
with relaxed conditions (low costs, narrow position limits) and is gradually
exposed to realistic market frictions as training progresses.  This avoids
early-stage policy collapse where random exploration is heavily penalised by
transaction costs.

Usage::

    from drl.callbacks import CurriculumCallback, CurriculumConfig

    curriculum = CurriculumCallback(CurriculumConfig(total_timesteps=100_000))
    trainer = WalkForwardTrainer(env_config, algo_config)
    # The trainer passes callbacks to model.learn()
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np

try:
    from stable_baselines3.common.callbacks import BaseCallback  # type: ignore

    HAS_SB3_CALLBACKS = True
except Exception:
    HAS_SB3_CALLBACKS = False

    class BaseCallback:  # type: ignore[no-redef]
        """Stub for when SB3 is not installed."""

        def __init__(self, verbose: int = 0) -> None:
            self.verbose = verbose
            self.num_timesteps = 0
            self.n_calls = 0
            self.model = None
            self.training_env = None
            self.logger = None  # type: ignore
            self.locals: dict[str, Any] = {}
            self.globals: dict[str, Any] = {}

        def _on_step(self) -> bool:
            return True

        def _on_training_start(self) -> None:
            pass

        def _on_training_end(self) -> None:
            pass


logger = logging.getLogger(__name__)


# ============================================================================
# CURRICULUM CONFIG
# ============================================================================


@dataclass
class CurriculumPhase:
    """A single phase in the curriculum schedule."""

    name: str
    start_pct: float  # fraction of training when this phase starts (0.0-1.0)
    end_pct: float  # fraction when it ends

    # Transaction cost multiplier (1.0 = normal, 0.0 = free)
    cost_multiplier: float = 1.0

    # Position limit multiplier (1.0 = config default)
    position_limit_multiplier: float = 1.0

    # Reward weight overrides (multipliers applied to base weights)
    pnl_weight_multiplier: float = 1.0
    drawdown_weight_multiplier: float = 1.0
    exploration_bonus: float = 0.0  # extra entropy-like exploration reward


@dataclass
class CurriculumConfig:
    """Configuration for curriculum learning."""

    total_timesteps: int = 50_000
    phases: list[CurriculumPhase] | None = None
    log_interval: int = 5_000
    verbose: bool = True

    def __post_init__(self) -> None:
        if self.phases is None:
            self.phases = self._default_phases()

    @staticmethod
    def _default_phases() -> list[CurriculumPhase]:
        """Three-phase default curriculum.

        Phase A (0-30%): Easy — low costs, narrow positions, exploration bonus
        Phase B (30-70%): Medium — normal costs, expanding positions
        Phase C (70-100%): Hard — full costs, full positions, drawdown emphasis
        """
        return [
            CurriculumPhase(
                name="easy",
                start_pct=0.0,
                end_pct=0.3,
                cost_multiplier=0.2,
                position_limit_multiplier=0.5,
                pnl_weight_multiplier=1.5,
                drawdown_weight_multiplier=0.3,
                exploration_bonus=0.05,
            ),
            CurriculumPhase(
                name="medium",
                start_pct=0.3,
                end_pct=0.7,
                cost_multiplier=0.6,
                position_limit_multiplier=0.8,
                pnl_weight_multiplier=1.2,
                drawdown_weight_multiplier=0.7,
                exploration_bonus=0.02,
            ),
            CurriculumPhase(
                name="hard",
                start_pct=0.7,
                end_pct=1.0,
                cost_multiplier=1.0,
                position_limit_multiplier=1.0,
                pnl_weight_multiplier=1.0,
                drawdown_weight_multiplier=1.2,
                exploration_bonus=0.0,
            ),
        ]

    def get_phase(self, progress: float) -> CurriculumPhase:
        """Get the active phase for the given training progress (0.0-1.0)."""
        progress = max(0.0, min(1.0, progress))
        if self.phases is None:
            self.phases = self._default_phases()
        for phase in self.phases:
            if phase.start_pct <= progress < phase.end_pct:
                return phase
        return self.phases[-1]

    def interpolate(self, progress: float) -> dict[str, float]:
        """Smoothly interpolate curriculum parameters at given progress.

        Returns a dictionary with interpolated multipliers, avoiding abrupt
        transitions between phases.
        """
        progress = max(0.0, min(1.0, progress))
        if self.phases is None:
            self.phases = self._default_phases()

        phase = self.get_phase(progress)
        phase_progress = 0.0
        if (phase.end_pct - phase.start_pct) > 0:
            phase_progress = (progress - phase.start_pct) / (phase.end_pct - phase.start_pct)

        # Find the next phase for interpolation
        next_phase = phase
        for p in self.phases:
            if p.start_pct > phase.start_pct:
                next_phase = p
                break

        # Smooth interpolation within phase (ease toward next phase)
        alpha = phase_progress
        return {
            "cost_multiplier": phase.cost_multiplier
            + alpha * (next_phase.cost_multiplier - phase.cost_multiplier),
            "position_limit_multiplier": phase.position_limit_multiplier
            + alpha * (next_phase.position_limit_multiplier - phase.position_limit_multiplier),
            "pnl_weight_multiplier": phase.pnl_weight_multiplier
            + alpha * (next_phase.pnl_weight_multiplier - phase.pnl_weight_multiplier),
            "drawdown_weight_multiplier": phase.drawdown_weight_multiplier
            + alpha * (next_phase.drawdown_weight_multiplier - phase.drawdown_weight_multiplier),
            "exploration_bonus": phase.exploration_bonus
            + alpha * (next_phase.exploration_bonus - phase.exploration_bonus),
        }


# ============================================================================
# CURRICULUM CALLBACK
# ============================================================================


class CurriculumCallback(BaseCallback):
    """SB3 callback that adjusts environment parameters during training.

    Modifies the underlying :class:`~drl.market_env.MarketEnv` parameters
    through the vectorised environment wrapper at each phase transition.

    Parameters
    ----------
    config:
        Curriculum schedule configuration.
    smooth:
        When True, interpolate between phases instead of discrete jumps.
    """

    def __init__(
        self,
        config: CurriculumConfig | None = None,
        smooth: bool = True,
        verbose: int = 0,
    ) -> None:
        super().__init__(verbose=verbose)
        self.config = config or CurriculumConfig()
        self.smooth = smooth
        self._current_phase_name: str = ""
        self._phase_history: list[dict[str, Any]] = []
        self._last_log_step: int = 0

    def _on_training_start(self) -> None:
        """Apply initial (easy) phase settings."""
        self._apply_curriculum(0.0)
        if self.verbose:
            logger.info("🎓 Curriculum learning başlatıldı")

    def _on_step(self) -> bool:
        """Check if phase transition should occur."""
        progress = self.num_timesteps / max(self.config.total_timesteps, 1)
        self._apply_curriculum(progress)

        # Periodic logging
        if (self.num_timesteps - self._last_log_step) >= self.config.log_interval:
            self._last_log_step = self.num_timesteps
            phase = self.config.get_phase(progress)
            if self.config.verbose:
                logger.info(
                    f"  📊 Curriculum [{phase.name}] "
                    f"step={self.num_timesteps} "
                    f"progress={progress:.1%} "
                    f"cost_mult={self._get_current_params().get('cost_multiplier', 1.0):.2f}"
                )
        return True

    def _on_training_end(self) -> None:
        """Log curriculum completion."""
        if self.verbose:
            logger.info(f"🎓 Curriculum tamamlandı — {len(self._phase_history)} faz geçişi yapıldı")

    def _apply_curriculum(self, progress: float) -> None:
        """Apply curriculum parameters to the training environment."""
        phase = self.config.get_phase(progress)

        if self.smooth:
            params = self.config.interpolate(progress)
        else:
            params = {
                "cost_multiplier": phase.cost_multiplier,
                "position_limit_multiplier": phase.position_limit_multiplier,
                "pnl_weight_multiplier": phase.pnl_weight_multiplier,
                "drawdown_weight_multiplier": phase.drawdown_weight_multiplier,
                "exploration_bonus": phase.exploration_bonus,
            }

        # Detect phase transitions
        if phase.name != self._current_phase_name:
            if self._current_phase_name:
                self._phase_history.append(
                    {
                        "from_phase": self._current_phase_name,
                        "to_phase": phase.name,
                        "timestep": self.num_timesteps,
                        "progress": progress,
                    }
                )
                if self.config.verbose:
                    logger.info(
                        f"  🔄 Faz geçişi: {self._current_phase_name} → {phase.name} "
                        f"(step {self.num_timesteps})"
                    )
            self._current_phase_name = phase.name

        # Apply to environments
        self._update_envs(params)

    def _update_envs(self, params: dict[str, float]) -> None:
        """Push curriculum parameters into the vectorised environments."""
        if self.training_env is None:
            return

        try:
            for env_idx in range(self.training_env.num_envs):
                env = self.training_env.envs[env_idx]  # type: ignore[attr-defined]
                if not hasattr(env, "_cost_model") or not hasattr(env, "config"):
                    continue

                # Scale transaction costs
                base_commission = env.config.transaction_costs.commission_bps
                base_slippage = env.config.transaction_costs.slippage_bps
                cost_mult = params["cost_multiplier"]
                env._cost_model = type(env._cost_model)(
                    commission_bps=base_commission * cost_mult,
                    slippage_bps=base_slippage * cost_mult,
                    holding_penalty_bps=env.config.transaction_costs.holding_penalty_bps,
                )

                # Scale position limits
                pos_mult = params["position_limit_multiplier"]
                base_max_pos = env.config.pilotshield.max_absolute_position
                env._limits = type(env._limits)(
                    max_absolute_position=base_max_pos * pos_mult,
                    max_leverage=env.config.pilotshield.max_leverage,
                    risk_appetite=env.config.pilotshield.risk_appetite,
                    confidence_threshold=env.config.pilotshield.confidence_threshold,
                    allow_shorting=env.config.pilotshield.allow_shorting,
                )

                # Scale reward weights
                base_rw = env.config.reward
                env._reward_weights = type(env._reward_weights)(
                    pnl=base_rw.pnl * params["pnl_weight_multiplier"],
                    drawdown=base_rw.drawdown * params["drawdown_weight_multiplier"],
                    cost=base_rw.cost,
                    leverage=base_rw.leverage,
                    regime_bonus=base_rw.regime_bonus + params["exploration_bonus"],
                    turnover_penalty=base_rw.turnover_penalty,
                    sharpe_bonus=base_rw.sharpe_bonus,
                    inactivity_penalty=base_rw.inactivity_penalty,
                    position_bonus=base_rw.position_bonus,
                )

        except Exception as e:
            logger.debug(f"Curriculum env update skipped: {e}")

    def _get_current_params(self) -> dict[str, float]:
        """Return current curriculum parameters."""
        progress = self.num_timesteps / max(self.config.total_timesteps, 1)
        if self.smooth:
            return self.config.interpolate(progress)
        phase = self.config.get_phase(progress)
        return {
            "cost_multiplier": phase.cost_multiplier,
            "position_limit_multiplier": phase.position_limit_multiplier,
        }

    def get_phase_history(self) -> list[dict[str, Any]]:
        """Return a list of all phase transition events."""
        return list(self._phase_history)


# ============================================================================
# METRICS TRACKING CALLBACK
# ============================================================================


class TrainingMetricsCallback(BaseCallback):
    """Tracks and logs training metrics periodically.

    Records episode rewards, equity, drawdown and position statistics
    during training for later analysis.
    """

    def __init__(
        self,
        log_interval: int = 1_000,
        verbose: int = 0,
    ) -> None:
        super().__init__(verbose=verbose)
        self.log_interval = log_interval
        self._episode_rewards: list[float] = []
        self._episode_lengths: list[int] = []
        self._current_episode_reward: float = 0.0
        self._current_episode_length: int = 0
        self._metrics_log: list[dict[str, float]] = []

    def _on_step(self) -> bool:
        # Accumulate rewards
        if "rewards" in self.locals:
            rewards = self.locals["rewards"]
            if rewards is not None:
                self._current_episode_reward += float(np.mean(rewards))
                self._current_episode_length += 1

        # Check for episode end
        if "dones" in self.locals:
            dones = self.locals["dones"]
            if dones is not None and any(dones):
                self._episode_rewards.append(self._current_episode_reward)
                self._episode_lengths.append(self._current_episode_length)
                self._current_episode_reward = 0.0
                self._current_episode_length = 0

        # Periodic logging
        if self.num_timesteps % self.log_interval == 0 and self._episode_rewards:
            recent = self._episode_rewards[-10:]
            metrics = {
                "timestep": float(self.num_timesteps),
                "avg_episode_reward": float(np.mean(recent)),
                "std_episode_reward": float(np.std(recent)),
                "n_episodes": float(len(self._episode_rewards)),
                "avg_episode_length": float(np.mean(self._episode_lengths[-10:])),
            }
            self._metrics_log.append(metrics)

            if self.verbose:
                logger.info(
                    f"  📈 Step {self.num_timesteps}: "
                    f"avg_reward={metrics['avg_episode_reward']:.4f} "
                    f"episodes={int(metrics['n_episodes'])}"
                )

        return True

    def get_metrics_log(self) -> list[dict[str, float]]:
        """Return all recorded metrics."""
        return list(self._metrics_log)


# ============================================================================
# MULTI-SYMBOL CURRICULUM
# ============================================================================


@dataclass
class SymbolTier:
    """A group of symbols introduced at a specific training progress point."""

    name: str
    symbols: list[str]
    start_pct: float  # training progress when this tier activates (0.0-1.0)


@dataclass
class MultiSymbolCurriculumConfig:
    """Configuration for progressive multi-symbol introduction.

    Training starts with a few stable, high-liquidity symbols and gradually
    adds more volatile / less-liquid ones as the agent matures.

    The default 3-tier schedule:
      - Tier 1 (0-30%):  mega-cap liquid (SPY, QQQ, AAPL, MSFT)
      - Tier 2 (30-60%): large-cap tech (GOOGL, AMZN, NVDA, META)
      - Tier 3 (60-100%): mid-cap + volatile (AMD, CRM, ADBE, INTC, TSLA, IWM)
    """

    tiers: list[SymbolTier] | None = None
    rotation_interval: int = 2048  # switch symbol every N steps
    total_timesteps: int = 3_000_000

    def __post_init__(self) -> None:
        if self.tiers is None:
            self.tiers = self._default_tiers()

    @staticmethod
    def _default_tiers() -> list[SymbolTier]:
        return [
            SymbolTier(
                name="mega_cap",
                symbols=["SPY", "QQQ", "AAPL", "MSFT"],
                start_pct=0.0,
            ),
            SymbolTier(
                name="large_cap",
                symbols=["GOOGL", "AMZN", "NVDA", "META"],
                start_pct=0.30,
            ),
            SymbolTier(
                name="mid_volatile",
                symbols=["AMD", "CRM", "ADBE", "INTC", "TSLA", "IWM"],
                start_pct=0.60,
            ),
        ]

    def get_active_symbols(self, progress: float) -> list[str]:
        """Return all symbols available at the given training progress."""
        if self.tiers is None:
            self.tiers = self._default_tiers()
        active: list[str] = []
        for tier in self.tiers:
            if progress >= tier.start_pct:
                active.extend(tier.symbols)
        return active


class MultiSymbolCallback(BaseCallback):
    """SB3 callback that rotates training episodes across symbols.

    Works with :class:`SymbolRotatingEnv` to progressively introduce new
    symbols as training progresses, implementing a diversity curriculum.

    Parameters
    ----------
    config:
        Multi-symbol curriculum configuration.
    episodes:
        Dict mapping symbol → EpisodeData (pre-computed).
    pipeline:
        Fitted FeaturePipeline instance.
    env_config:
        Market environment configuration.
    """

    def __init__(
        self,
        config: MultiSymbolCurriculumConfig,
        episodes: dict,  # symbol → EpisodeData
        pipeline: "FeaturePipeline",
        env_config: "MarketEnvConfig",
        verbose: int = 0,
    ) -> None:
        super().__init__(verbose=verbose)
        self.config = config
        self.episodes = episodes
        self.pipeline = pipeline
        self.env_config = env_config
        self._active_symbols: list[str] = []
        self._current_symbol: str = ""
        self._last_rotation_step: int = 0
        self._rng = np.random.default_rng(42)

    def _on_training_start(self) -> None:
        self._apply_symbol_update(0.0)
        if self.verbose:
            logger.info("🌍 Multi-symbol curriculum: %d total symbols across %d tiers",
                        sum(len(t.symbols) for t in (self.config.tiers or [])),
                        len(self.config.tiers or []))

    def _on_step(self) -> bool:
        progress = self.num_timesteps / max(self.config.total_timesteps, 1)
        self._apply_symbol_update(progress)

        # Periodic symbol rotation
        if (self.num_timesteps - self._last_rotation_step) >= self.config.rotation_interval:
            self._rotate_symbol()
            self._last_rotation_step = self.num_timesteps

        return True

    def _apply_symbol_update(self, progress: float) -> None:
        """Update the set of active symbols based on progress."""
        new_active = self.config.get_active_symbols(progress)
        # Filter to symbols we actually have episodes for
        new_active = [s for s in new_active if s in self.episodes]

        if set(new_active) != set(self._active_symbols):
            added = set(new_active) - set(self._active_symbols)
            self._active_symbols = new_active
            if added and self.verbose:
                logger.info("  🌍 Symbols expanded: +%s → %d total",
                            ", ".join(sorted(added)), len(self._active_symbols))

    def _rotate_symbol(self) -> None:
        """Swap the underlying environment's episode to a random active symbol."""
        if not self._active_symbols or self.training_env is None:
            return

        next_symbol = self._rng.choice(self._active_symbols)
        if next_symbol not in self.episodes:
            return

        try:
            from .market_env import MarketEnv
            episode = self.episodes[next_symbol]

            for env_idx in range(self.training_env.num_envs):
                env = self.training_env.envs[env_idx]  # type: ignore[attr-defined]
                if isinstance(env, MarketEnv):
                    # Re-initialize env with new episode data
                    env.__init__(episode, self.pipeline, self.env_config)  # type: ignore[misc]
                    env.reset()
                    self._current_symbol = next_symbol

        except Exception as e:
            logger.debug("Symbol rotation failed: %s", e)

    def get_active_symbols(self) -> list[str]:
        """Return currently active symbols."""
        return list(self._active_symbols)


__all__ = [
    "CurriculumCallback",
    "CurriculumConfig",
    "CurriculumPhase",
    "MultiSymbolCallback",
    "MultiSymbolCurriculumConfig",
    "SymbolTier",
    "TrainingMetricsCallback",
]
