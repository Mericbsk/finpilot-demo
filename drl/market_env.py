"""OpenAI Gym compatible environment for FinPilot reinforcement learning.

The environment consumes feature tensors produced by :mod:`drl.feature_pipeline`
and applies reward shaping based on the configuration objects in
:mod:`drl.config`.  It is intentionally lightweight so that the same
implementation can be reused in offline training, paper trading, and real-time
monitoring agents.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from .config import MarketEnvConfig, PilotShieldLimits, RewardWeights, TransactionCostModel
from .feature_pipeline import FeatureFrame, FeaturePipeline

USE_GYMNASIUM = False
if TYPE_CHECKING:  # pragma: no cover - hints only
    import gymnasium as gym
    from gymnasium import spaces  # type: ignore
else:  # pragma: no cover - optional runtime dependency
    try:
        import gymnasium as gym  # type: ignore
        from gymnasium import spaces  # type: ignore

        USE_GYMNASIUM = True
    except Exception:  # pragma: no cover - gymnasium missing at runtime
        try:
            import gym  # type: ignore
            from gym import spaces  # type: ignore
        except Exception:  # pragma: no cover - gym missing at runtime
            gym = None  # type: ignore
            spaces = None  # type: ignore


BaseEnvType = object if TYPE_CHECKING else object
if gym is not None:  # pragma: no cover - when gym available
    BaseEnvType = gym.Env  # type: ignore


class BaseEnv(BaseEnvType):  # type: ignore[misc]
    """Duck-typed base class compatible with Gym/Gymnasium APIs."""

    observation_space: object | None = None
    action_space: object | None = None

    def reset(self, *, seed: int | None = None, options: dict | None = None):  # type: ignore[override]
        raise NotImplementedError

    def step(self, action):  # type: ignore[override]
        raise NotImplementedError


@dataclass
class EpisodeData:
    """Container passed to :class:`MarketEnv` during initialisation."""

    features: FeatureFrame
    prices: pd.Series
    regimes: pd.Series | None = None
    timestamps: pd.Index | None = None

    def __post_init__(self) -> None:
        if self.timestamps is None and isinstance(self.prices.index, pd.DatetimeIndex):
            object.__setattr__(self, "timestamps", self.prices.index)


@dataclass
class PortfolioSnapshot:
    cash: float
    equity: float
    position: float
    drawdown: float


class MarketEnv(BaseEnv):
    """Trading environment with reward shaping and PilotShield guardrails."""

    metadata = {"render.modes": []}

    def __init__(
        self,
        episode: EpisodeData,
        pipeline: FeaturePipeline,
        config: MarketEnvConfig,
    ) -> None:
        if pipeline is None:
            raise ValueError("FeaturePipeline instance is required")
        if not pipeline._stats:  # type: ignore[attr-defined]
            pipeline.fit(episode.features)

        self.config = config
        self.pipeline = pipeline
        self._raw_features = episode.features
        self._feature_tensor = pipeline.transform(episode.features)
        # Safety: ensure no NaN/Inf leaks into observations
        self._feature_tensor = np.nan_to_num(self._feature_tensor, nan=0.0, posinf=5.0, neginf=-5.0)
        self._prices = episode.prices.astype(float).to_numpy()
        self._regimes = episode.regimes.tolist() if episode.regimes is not None else None
        self._timestamps = episode.timestamps.tolist() if episode.timestamps is not None else None
        self._episode_len = len(self._prices)
        if self._episode_len != len(self._feature_tensor):
            raise ValueError("Features and prices must align in length")
        if self._episode_len < 2:
            raise ValueError("Episode must contain at least two timesteps")

        # PilotShield limits & cost models
        self._limits: PilotShieldLimits = config.pilotshield
        self._reward_weights: RewardWeights = config.reward
        self._cost_model: TransactionCostModel = config.transaction_costs

        # Internal state
        self._t = 0
        self._position = 0.0
        self._equity = 1.0
        self._cash = 1.0
        self._max_equity = 1.0
        self._history: list[dict[str, float | str]] = []
        self._returns_buffer: list[float] = []  # Sprint 13: rolling Sharpe
        self._trade_count: int = 0  # Sprint 16: track trade count for terminal reward

        # Spaces (if gym available)
        feature_dim = self._feature_tensor.shape[1]
        max_abs_pos = float(self._limits.max_absolute_position)

        # Sprint 13: precompute volume column index for stochastic slippage
        self._volume_col_idx: int | None = None
        feature_cols = config.feature_columns
        if "volume" in feature_cols:
            self._volume_col_idx = feature_cols.index("volume")

        if spaces is not None:
            self.observation_space = spaces.Box(
                low=-np.inf,
                high=np.inf,
                shape=(feature_dim,),
                dtype=np.float32,
            )
            self.action_space = spaces.Box(
                low=-max_abs_pos,
                high=max_abs_pos,
                shape=(1,),
                dtype=np.float32,
            )
        else:  # pragma: no cover - for non-gym deployments
            self.observation_space = None
            self.action_space = None

    # ------------------------------------------------------------------
    # Environment API
    # ------------------------------------------------------------------
    def reset(self, *, seed: int | None = None, options: dict | None = None):  # type: ignore[override]
        self._t = 0
        self._position = 0.0
        self._equity = 1.0
        self._cash = 1.0
        self._max_equity = 1.0
        self._history.clear()
        self._returns_buffer.clear()
        self._trade_count = 0
        observation = self._feature_tensor[self._t].copy()
        # Sprint 16: inject dynamic portfolio state into observation
        self._inject_portfolio_state(observation)
        info = self._build_info(0.0, 0.0, 0.0)
        return observation, info

    def step(self, action):  # type: ignore[override]
        target_position = self._clamp_action(action)
        prev_price = self._prices[self._t]
        next_index = self._t + 1
        next_price = self._prices[next_index]

        price_return = (next_price - prev_price) / prev_price
        portfolio_return = target_position * price_return

        # Trading costs based on position change
        position_change = target_position - self._position
        commission_rate = self._cost_model.commission_bps / 10000.0

        # Sprint 13: stochastic volume-dependent slippage
        base_slippage = self._cost_model.slippage_bps / 10000.0
        if self._cost_model.stochastic_slippage:
            # Volume-proxy: use feature tensor's volume column if present
            vol_ratio = 1.0
            volume_col_idx = self._volume_col_idx
            if volume_col_idx is not None:
                vol_val = float(self._feature_tensor[self._t, volume_col_idx])
                # Negative z-score → low volume → higher slippage
                vol_ratio = max(0.5, 1.0 - self._cost_model.slippage_vol_scale * min(vol_val, 0.0))
            noise = float(np.random.uniform(0.8, 1.2))
            slippage_rate = base_slippage * vol_ratio * noise
        else:
            slippage_rate = base_slippage

        transaction_cost = abs(position_change) * (commission_rate + slippage_rate)
        holding_cost = abs(target_position) * (self._cost_model.holding_penalty_bps / 10000.0)

        pnl = portfolio_return - transaction_cost - holding_cost

        # Update portfolio equity and drawdown
        self._position = target_position
        # Sprint 17: clamp pnl to avoid equity overflow → NaN
        pnl = float(np.clip(pnl, -0.5, 0.5))
        self._equity *= 1.0 + pnl
        self._equity = float(np.clip(self._equity, 1e-6, 1e12))
        self._max_equity = max(self._max_equity, self._equity)
        drawdown = 1.0 - (self._equity / self._max_equity)

        # Reward shaping
        reward = self._reward_weights.pnl * pnl
        reward -= self._reward_weights.cost * transaction_cost
        reward -= self._reward_weights.drawdown * drawdown
        leverage_penalty = max(0.0, abs(target_position) - self._limits.max_leverage)
        reward -= self._reward_weights.leverage * leverage_penalty
        reward += self._reward_weights.regime_bonus * self._regime_alignment(target_position)

        # Sprint 13: turnover penalty — penalise excessive position changes
        turnover = abs(position_change)
        reward -= self._reward_weights.turnover_penalty * turnover

        # Sprint 14: inactivity penalty — discourage constant-HOLD behaviour
        if abs(target_position) < 0.05:
            reward -= self._reward_weights.inactivity_penalty

        # Sprint 14: position bonus — reward conviction (non-zero positions)
        reward += self._reward_weights.position_bonus * abs(target_position)

        # Sprint 13: rolling Sharpe bonus — reward risk-adjusted returns
        self._returns_buffer.append(pnl)
        if len(self._returns_buffer) >= 20:
            _ret = np.array(self._returns_buffer[-60:])  # last 60 steps
            _std = float(np.std(_ret))
            if _std > 1e-8:
                rolling_sharpe = float(np.mean(_ret)) / _std
                reward += self._reward_weights.sharpe_bonus * np.clip(rolling_sharpe, -2.0, 2.0)

        # Sprint 16: track trade count
        if abs(position_change) > 0.02:
            self._trade_count += 1

        self._t = next_index
        terminated = next_index >= (self._episode_len - 1)
        truncated = False

        # Sprint 16: terminal reward — episode-end Sharpe bonus/penalty
        if terminated and len(self._returns_buffer) > 10:
            terminal_ret = np.array(self._returns_buffer)
            terminal_std = float(np.std(terminal_ret)) or 1e-8
            terminal_sharpe = float(np.mean(terminal_ret)) / terminal_std
            reward += 5.0 * np.clip(terminal_sharpe, -2.0, 2.0)
            # Bonus for active trading (penalise if fewer than ~5% of steps had trades)
            trade_ratio = self._trade_count / max(len(self._returns_buffer), 1)
            if trade_ratio < 0.05:
                reward -= 2.0  # severe penalty for near-zero activity
            elif trade_ratio > 0.02:
                reward += 1.0 * min(trade_ratio, 0.3)  # cap to avoid over-trading bonus

        # Sprint 16: reward clipping — prevent extreme gradients
        reward = float(np.clip(reward, -10.0, 10.0))

        observation = self._feature_tensor[self._t].copy()
        # Sprint 16: inject dynamic portfolio state into observation
        self._inject_portfolio_state(observation)
        info = self._build_info(pnl, drawdown, reward)
        self._history.append(info)

        if USE_GYMNASIUM:
            return observation, reward, terminated, truncated, info

        done = terminated or truncated
        return observation, reward, done, info

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _inject_portfolio_state(self, observation: np.ndarray) -> None:
        """Sprint 16: write live portfolio state into the observation vector.

        During training the portfolio_state features (cash_ratio,
        position_ratio, open_risk, kelly_fraction) were previously
        static placeholders (1,0,0,0).  Now we overwrite those indices
        with the agent's real-time portfolio metrics so the policy
        can learn to condition on its own state.
        """
        feature_cols = self.config.feature_columns
        _ps_cols = {
            "cash_ratio": max(0.0, 1.0 - abs(self._position)),
            "position_ratio": abs(self._position),
            "open_risk": 1.0 - (self._equity / self._max_equity),
            "kelly_fraction": self._position,  # signed position as kelly proxy
        }
        for col_name, value in _ps_cols.items():
            if col_name in feature_cols:
                idx = feature_cols.index(col_name)
                if idx < len(observation):
                    observation[idx] = float(value)

    def _clamp_action(self, action) -> float:
        value = float(action[0] if isinstance(action, list | tuple | np.ndarray) else action)
        max_abs = float(self._limits.max_absolute_position)
        if not self._limits.allow_shorting:
            value = max(0.0, value)
        value = float(np.clip(value, -max_abs, max_abs))
        risk_cap = float(self._limits.risk_appetite) / 10.0
        return np.clip(value, -risk_cap, risk_cap)

    def _regime_alignment(self, position: float) -> float:
        if not self._regimes:
            return 0.0
        regime = self._regimes[self._t]
        if regime == "trend":
            return float(abs(position))
        if regime == "range":
            return float(1.0 - abs(position))
        if regime == "volatility":
            return float(-abs(position))
        return 0.0

    def _build_info(self, pnl: float, drawdown: float, reward: float) -> dict[str, float | str]:
        timestamp = None
        if self._timestamps is not None and self._t < len(self._timestamps):
            ts = self._timestamps[self._t]
            timestamp = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
        feature_snapshot = self._feature_tensor[self._t].tolist()
        regime = None
        if self._regimes and self._t < len(self._regimes):
            regime = self._regimes[self._t]
        info: dict[str, float | str] = {
            "t": float(self._t),
            "pnl": float(pnl),
            "reward": float(reward),
            "drawdown": float(drawdown),
            "position": float(self._position),
            "equity": float(self._equity),
            "features": feature_snapshot,
        }
        if timestamp:
            info["timestamp"] = timestamp
        if regime is not None:
            info["regime"] = regime
        return info

    def get_history(self) -> list[dict[str, float | str]]:
        """Return a copy of the per-step diagnostic history."""

        return list(self._history)


__all__ = ["MarketEnv", "EpisodeData", "PortfolioSnapshot"]
