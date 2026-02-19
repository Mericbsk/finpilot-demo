"""Multi-asset trading environment for FinPilot.

Extends :class:`~drl.market_env.MarketEnv` to handle portfolio allocation
across multiple assets simultaneously.  The agent outputs a weight vector
that is normalised via softmax to produce valid portfolio allocations.

Key design decisions:

* Each asset shares the **same** :class:`FeaturePipeline` configuration so that
  feature dimensions are consistent.
* The observation vector concatenates per-asset features with portfolio-level
  state (cash ratio, total equity, current weights).
* Transaction costs are applied per-asset based on weight changes.

Example::

    from drl.multi_asset_env import MultiAssetMarketEnv, MultiAssetEpisode

    episodes = {
        "AAPL": episode_aapl,
        "MSFT": episode_msft,
        "GOOGL": episode_googl,
    }
    env = MultiAssetMarketEnv(episodes, pipeline, config)
    obs, info = env.reset()
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .config import MarketEnvConfig
from .feature_pipeline import FeaturePipeline
from .market_env import USE_GYMNASIUM, BaseEnv, EpisodeData

try:
    import gymnasium as gym  # type: ignore
    from gymnasium import spaces  # type: ignore
except Exception:
    try:
        import gym  # type: ignore
        from gym import spaces  # type: ignore
    except Exception:
        gym = None  # type: ignore
        spaces = None  # type: ignore


@dataclass
class MultiAssetEpisode:
    """Container for multi-asset episode data."""

    assets: dict[str, EpisodeData]  # symbol -> EpisodeData
    common_index: pd.DatetimeIndex | None = None

    @property
    def symbols(self) -> list[str]:
        return list(self.assets.keys())

    @property
    def n_assets(self) -> int:
        return len(self.assets)

    def __post_init__(self) -> None:
        if not self.assets:
            raise ValueError("At least one asset is required")
        # Validate all assets have the same length
        lengths = {s: len(e.prices) for s, e in self.assets.items()}
        unique_lengths = set(lengths.values())
        if len(unique_lengths) > 1:
            raise ValueError(f"All assets must have the same length. Got: {lengths}")


@dataclass
class PortfolioState:
    """Current state of the multi-asset portfolio."""

    weights: np.ndarray  # current weight per asset
    cash_weight: float  # fraction held as cash
    equity: float  # total portfolio value
    max_equity: float  # peak equity for drawdown
    asset_returns: np.ndarray  # latest per-asset returns
    drawdown: float  # current drawdown from peak


def softmax(x: np.ndarray) -> np.ndarray:
    """Numerically stable softmax."""
    e_x = np.exp(x - np.max(x))
    return e_x / (e_x.sum() + 1e-8)


class MultiAssetMarketEnv(BaseEnv):
    """Portfolio management environment across multiple assets.

    The action space is ``Box(-1, 1, shape=(n_assets,))`` where each element
    represents a raw preference for that asset.  The preferences are converted
    to portfolio weights via softmax, guaranteeing non-negative weights that
    sum to 1.

    The observation is a flat vector:
    ``[asset_1_features | asset_2_features | ... | portfolio_state]``

    Portfolio state includes: ``[cash_ratio, total_equity_norm, weight_1, ..., weight_n]``
    """

    metadata = {"render.modes": []}

    def __init__(
        self,
        episode: MultiAssetEpisode,
        pipeline: FeaturePipeline,
        config: MarketEnvConfig,
        initial_capital: float = 1.0,
        max_weight_per_asset: float = 0.4,
        rebalance_cost_bps: float = 5.0,
    ) -> None:
        self.config = config
        self.pipeline = pipeline
        self._episode = episode
        self._n_assets = episode.n_assets
        self._symbols = episode.symbols
        self._initial_capital = initial_capital
        self._max_weight = max_weight_per_asset
        self._rebalance_cost_bps = rebalance_cost_bps

        # Process features for each asset
        self._feature_tensors: dict[str, np.ndarray] = {}
        self._prices: dict[str, np.ndarray] = {}

        for symbol, ep_data in episode.assets.items():
            if not pipeline._stats:
                pipeline.fit(ep_data.features)
            self._feature_tensors[symbol] = pipeline.transform(ep_data.features)
            self._prices[symbol] = ep_data.prices.astype(float).to_numpy()

        # Validate lengths
        first_symbol = self._symbols[0]
        self._episode_len = len(self._prices[first_symbol])
        for symbol in self._symbols:
            if len(self._prices[symbol]) != self._episode_len:
                raise ValueError(f"Price length mismatch for {symbol}")
            if len(self._feature_tensors[symbol]) != self._episode_len:
                raise ValueError(f"Feature length mismatch for {symbol}")

        if self._episode_len < 2:
            raise ValueError("Episode must contain at least two timesteps")

        # Determine observation dimensions
        self._per_asset_features = self._feature_tensors[first_symbol].shape[1]
        # portfolio_state: cash_ratio + equity_norm + n_assets weights
        self._portfolio_state_dim = 2 + self._n_assets
        self._obs_dim = (self._per_asset_features * self._n_assets) + self._portfolio_state_dim

        # Risk / reward config
        self._limits = config.pilotshield
        self._reward_weights = config.reward
        self._cost_model = config.transaction_costs

        # Internal state
        self._t = 0
        self._weights = np.zeros(self._n_assets)
        self._cash = initial_capital
        self._equity = initial_capital
        self._max_equity = initial_capital
        self._history: list[dict[str, Any]] = []

        # Spaces
        if spaces is not None:
            self.observation_space = spaces.Box(
                low=-np.inf,
                high=np.inf,
                shape=(self._obs_dim,),
                dtype=np.float32,
            )
            self.action_space = spaces.Box(
                low=-1.0,
                high=1.0,
                shape=(self._n_assets,),
                dtype=np.float32,
            )
        else:
            self.observation_space = None
            self.action_space = None

    # ------------------------------------------------------------------
    # Environment API
    # ------------------------------------------------------------------

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        self._t = 0
        self._weights = np.zeros(self._n_assets)
        self._cash = self._initial_capital
        self._equity = self._initial_capital
        self._max_equity = self._initial_capital
        self._history.clear()

        obs = self._build_observation()
        info = self._build_info(np.zeros(self._n_assets), 0.0, 0.0, 0.0)
        return obs, info

    def step(self, action):
        # Convert raw action to portfolio weights via softmax
        target_weights = self._action_to_weights(action)

        # Calculate per-asset returns
        asset_returns = np.zeros(self._n_assets)
        for i, symbol in enumerate(self._symbols):
            prev_price = self._prices[symbol][self._t]
            next_price = self._prices[symbol][self._t + 1]
            asset_returns[i] = (next_price - prev_price) / prev_price

        # Portfolio return (weighted sum)
        portfolio_return = np.sum(target_weights * asset_returns)

        # Transaction costs from rebalancing
        weight_changes = np.abs(target_weights - self._weights)
        total_turnover = np.sum(weight_changes)
        commission_rate = (
            self._cost_model.commission_bps + self._cost_model.slippage_bps
        ) / 10000.0
        rebalance_rate = self._rebalance_cost_bps / 10000.0
        transaction_cost = total_turnover * (commission_rate + rebalance_rate)

        # Net PnL
        pnl = portfolio_return - transaction_cost

        # Update portfolio state
        self._weights = target_weights
        self._equity *= 1.0 + pnl
        self._equity = max(self._equity, 1e-8)
        self._max_equity = max(self._max_equity, self._equity)
        drawdown = 1.0 - (self._equity / self._max_equity)

        # Reward shaping
        reward = self._compute_reward(pnl, drawdown, transaction_cost, target_weights)

        # Advance time
        self._t += 1
        terminated = self._t >= (self._episode_len - 1)
        truncated = False

        obs = self._build_observation()
        info = self._build_info(asset_returns, pnl, drawdown, reward)
        self._history.append(info)

        if USE_GYMNASIUM:
            return obs, reward, terminated, truncated, info

        done = terminated or truncated
        return obs, reward, done, info

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _action_to_weights(self, action) -> np.ndarray:
        """Convert raw action [-1, 1]^n to valid portfolio weights."""
        if isinstance(action, (list, tuple)):
            action = np.array(action, dtype=np.float32)
        action = np.asarray(action, dtype=np.float32).flatten()

        # Ensure correct shape
        if len(action) != self._n_assets:
            action = np.resize(action, self._n_assets)

        # Softmax for valid probability distribution
        weights = softmax(action)

        # Apply per-asset weight cap
        weights = np.minimum(weights, self._max_weight)
        total = weights.sum()
        if total > 0:
            weights = weights / total
        else:
            weights = np.ones(self._n_assets) / self._n_assets

        # If shorting is not allowed, weights are already non-negative via softmax
        if not self._limits.allow_shorting:
            weights = np.maximum(weights, 0.0)
            total = weights.sum()
            if total > 0:
                weights = weights / total

        return weights

    def _compute_reward(
        self,
        pnl: float,
        drawdown: float,
        transaction_cost: float,
        weights: np.ndarray,
    ) -> float:
        """Compute shaped reward for multi-asset portfolio."""
        reward = self._reward_weights.pnl * pnl
        reward -= self._reward_weights.cost * transaction_cost
        reward -= self._reward_weights.drawdown * drawdown

        # Concentration penalty: penalise putting too much in one asset
        herfindahl = float(np.sum(weights**2))
        # Perfect diversification: 1/n, worst: 1.0
        concentration_penalty = max(0.0, herfindahl - (1.0 / self._n_assets))
        reward -= self._reward_weights.leverage * concentration_penalty

        return float(reward)

    def _build_observation(self) -> np.ndarray:
        """Concatenate per-asset features with portfolio state."""
        parts = []

        # Per-asset features
        for symbol in self._symbols:
            features = self._feature_tensors[symbol][self._t]
            parts.append(features)

        # Portfolio state
        cash_ratio = float(self._cash / max(self._equity, 1e-8))
        equity_norm = float(self._equity / self._initial_capital)
        portfolio_state = np.array(
            [cash_ratio, equity_norm] + list(self._weights),
            dtype=np.float32,
        )
        parts.append(portfolio_state)

        obs = np.concatenate(parts).astype(np.float32)
        obs = np.nan_to_num(obs, nan=0.0, posinf=1e6, neginf=-1e6)
        return obs

    def _build_info(
        self,
        asset_returns: np.ndarray,
        pnl: float,
        drawdown: float,
        reward: float,
    ) -> dict[str, Any]:
        """Build info dictionary for the current step."""
        info: dict[str, Any] = {
            "t": self._t,
            "pnl": float(pnl),
            "reward": float(reward),
            "drawdown": float(drawdown),
            "equity": float(self._equity),
            "weights": {s: float(w) for s, w in zip(self._symbols, self._weights)},
            "asset_returns": {s: float(r) for s, r in zip(self._symbols, asset_returns)},
        }
        return info

    def get_history(self) -> list[dict[str, Any]]:
        """Return a copy of the per-step diagnostic history."""
        return list(self._history)

    def get_portfolio_state(self) -> PortfolioState:
        """Return current portfolio snapshot."""
        prev_returns = np.zeros(self._n_assets)
        if self._t > 0:
            for i, symbol in enumerate(self._symbols):
                prev_price = self._prices[symbol][self._t - 1]
                curr_price = self._prices[symbol][self._t]
                prev_returns[i] = (curr_price - prev_price) / prev_price

        return PortfolioState(
            weights=self._weights.copy(),
            cash_weight=float(self._cash / max(self._equity, 1e-8)),
            equity=float(self._equity),
            max_equity=float(self._max_equity),
            asset_returns=prev_returns,
            drawdown=1.0 - (self._equity / self._max_equity),
        )


__all__ = [
    "MultiAssetMarketEnv",
    "MultiAssetEpisode",
    "PortfolioState",
    "softmax",
]
