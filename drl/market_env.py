"""OpenAI Gym compatible environment for FinPilot reinforcement learning.

The environment consumes feature tensors produced by :mod:`drl.feature_pipeline`
and applies reward shaping based on the configuration objects in
:mod:`drl.config`.  It is intentionally lightweight so that the same
implementation can be reused in offline training, paper trading, and real-time
monitoring agents.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional, Sequence, Tuple, Union

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

    observation_space: Optional[object] = None
    action_space: Optional[object] = None

    def reset(self, *, seed: Optional[int] = None, options: Optional[dict] = None):  # type: ignore[override]
        raise NotImplementedError

    def step(self, action):  # type: ignore[override]
        raise NotImplementedError


@dataclass
class EpisodeData:
    """Container passed to :class:`MarketEnv` during initialisation."""

    features: FeatureFrame
    prices: pd.Series
    regimes: Optional[pd.Series] = None
    timestamps: Optional[pd.Index] = None

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
        self._history: List[Dict[str, Union[float, str]]] = []

        # Spaces (if gym available)
        feature_dim = self._feature_tensor.shape[1]
        max_abs_pos = float(self._limits.max_absolute_position)
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
    def reset(self, *, seed: Optional[int] = None, options: Optional[dict] = None):  # type: ignore[override]
        self._t = 0
        self._position = 0.0
        self._equity = 1.0
        self._cash = 1.0
        self._max_equity = 1.0
        self._history.clear()
        observation = self._feature_tensor[self._t]
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
        commission_rate = (
            self._cost_model.commission_bps + self._cost_model.slippage_bps
        ) / 10000.0
        transaction_cost = abs(position_change) * commission_rate
        holding_cost = abs(target_position) * (self._cost_model.holding_penalty_bps / 10000.0)

        pnl = portfolio_return - transaction_cost - holding_cost

        # Update portfolio equity and drawdown
        self._position = target_position
        self._equity *= 1.0 + pnl
        self._equity = max(self._equity, 1e-6)
        self._max_equity = max(self._max_equity, self._equity)
        drawdown = 1.0 - (self._equity / self._max_equity)

        # Reward shaping
        reward = self._reward_weights.pnl * pnl
        reward -= self._reward_weights.cost * transaction_cost
        reward -= self._reward_weights.drawdown * drawdown
        leverage_penalty = max(0.0, abs(target_position) - self._limits.max_leverage)
        reward -= self._reward_weights.leverage * leverage_penalty
        reward += self._reward_weights.regime_bonus * self._regime_alignment(target_position)

        self._t = next_index
        terminated = next_index >= (self._episode_len - 1)
        truncated = False
        observation = self._feature_tensor[self._t]
        info = self._build_info(pnl, drawdown, reward)
        self._history.append(info)

        if USE_GYMNASIUM:
            return observation, reward, terminated, truncated, info

        done = terminated or truncated
        return observation, reward, done, info

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _clamp_action(self, action) -> float:
        value = float(action[0] if isinstance(action, (list, tuple, np.ndarray)) else action)
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

    def _build_info(
        self, pnl: float, drawdown: float, reward: float
    ) -> Dict[str, Union[float, str]]:
        timestamp = None
        if self._timestamps is not None and self._t < len(self._timestamps):
            ts = self._timestamps[self._t]
            timestamp = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
        feature_snapshot = self._feature_tensor[self._t].tolist()
        regime = None
        if self._regimes and self._t < len(self._regimes):
            regime = self._regimes[self._t]
        info: Dict[str, Union[float, str]] = {
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

    def get_history(self) -> List[Dict[str, Union[float, str]]]:
        """Return a copy of the per-step diagnostic history."""

        return list(self._history)


__all__ = ["MarketEnv", "EpisodeData", "PortfolioSnapshot"]
