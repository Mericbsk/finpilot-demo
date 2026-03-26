"""Specialist Agent Definitions for FinPilot DRL.

Sprint 19 — Multi-Specialist Architecture:
Moves beyond 3 regime-only agents to 7 domain-specialist agents, each
trained with a tailored reward profile, data filter, and feature emphasis.

Architecture:
    ┌──────────────────────────────────────────────────────────┐
    │                  SPECIALIST AGENTS                       │
    ├────────────┬─────────────┬────────────┬──────────────────┤
    │  REGIME    │  STRATEGY   │  TIMEFRAME │  RISK STYLE      │
    │            │             │            │                  │
    │ • trend    │ • momentum  │ • scalper  │ • conservative   │
    │ • range    │ • meanrev   │ • swing    │ • aggressive     │
    │ • volatile │ • breakout  │            │                  │
    └────────────┴─────────────┴────────────┴──────────────────┘
                            │
                            ▼
                  HierarchicalEnsemble
                  (learnable meta-weights)

Each specialist has:
  1. RewardProfile  — custom reward weights emphasising its strength
  2. DataFilter     — how to select/weight training data
  3. FeatureBoost   — which feature groups matter most
  4. EnvOverrides   — PilotShield/cost overrides (e.g. scalper = lower costs)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import pandas as pd

from .config import (
    MarketEnvConfig,
    PilotShieldLimits,
    RewardWeights,
    TransactionCostModel,
)

# ---------------------------------------------------------------------------
# Specialist taxonomy
# ---------------------------------------------------------------------------


class SpecialistDomain(StrEnum):
    """High-level domain grouping."""

    REGIME = "regime"
    STRATEGY = "strategy"
    TIMEFRAME = "timeframe"
    RISK = "risk"


class SpecialistTag(StrEnum):
    """Unique identifier for each specialist agent."""

    # Regime (existing)
    TREND = "trend"
    RANGE = "range"
    VOLATILE = "volatile"
    # Strategy (new)
    MOMENTUM = "momentum"
    MEAN_REVERSION = "meanrev"
    BREAKOUT = "breakout"
    # Timeframe (new)
    SCALPER = "scalper"
    SWING = "swing"
    # Risk style (new)
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"


# ---------------------------------------------------------------------------
# Configuration dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RewardProfile:
    """Custom reward weights for a specialist.

    Extends the base RewardWeights with specialist-specific tuning.
    ``from_base()`` creates a RewardWeights instance compatible with MarketEnv.
    """

    pnl: float = 10.0
    drawdown: float = 0.3
    cost: float = 0.1
    sharpe_bonus: float = 0.0
    turnover_penalty: float = 0.0
    inactivity_penalty: float = 0.0
    regime_bonus: float = 0.0
    leverage: float = 0.0
    position_bonus: float = 0.0
    action_smoothing: float = 0.0  # Sprint 25: penalise abrupt action jumps
    terminal_dd_penalty: float = 0.0  # Sprint 26: quadratic terminal DD penalty
    dd_quadratic: bool = False  # Sprint 26: per-step DD²

    def to_reward_weights(self) -> RewardWeights:
        return RewardWeights(
            pnl=self.pnl,
            drawdown=self.drawdown,
            cost=self.cost,
            sharpe_bonus=self.sharpe_bonus,
            turnover_penalty=self.turnover_penalty,
            inactivity_penalty=self.inactivity_penalty,
            regime_bonus=self.regime_bonus,
            leverage=self.leverage,
            position_bonus=self.position_bonus,
            action_smoothing=self.action_smoothing,
            terminal_dd_penalty=self.terminal_dd_penalty,
            dd_quadratic=self.dd_quadratic,
        )


@dataclass(frozen=True)
class DataFilter:
    """Describes how training data should be selected and weighted.

    Attributes
    ----------
    regime_focus : str | None
        If set, oversample rows matching this regime label.
    min_atr_pct : float | None
        Minimum ATR% to include (filters calm periods for volatile expert).
    max_atr_pct : float | None
        Maximum ATR% to include (filters chaotic periods for calm expert).
    min_volume_ratio : float | None
        Minimum volume_ratio to include (liquidity filter).
    lookback_window : int | None
        Override episode length (shorter for scalper, longer for swing).
    rsi_range : tuple[float, float] | None
        (low, high) RSI band. Mean-rev agent focuses on extremes.
    trend_strength_min : float | None
        Minimum abs(close_ema20_ratio) to select trending periods.
    symbols_filter : list[str] | None
        Restrict to these symbols (e.g. high-vol tickers for aggressive).
    """

    regime_focus: str | None = None
    min_atr_pct: float | None = None
    max_atr_pct: float | None = None
    min_volume_ratio: float | None = None
    lookback_window: int | None = None
    rsi_range: tuple[float, float] | None = None
    trend_strength_min: float | None = None
    symbols_filter: list[str] | None = None


@dataclass(frozen=True)
class FeatureBoost:
    """Multipliers applied to feature groups to emphasise relevant signals.

    Values > 1.0 boost, < 1.0 suppress. Applied at pipeline level.
    """

    technicals: float = 1.0
    regime: float = 1.0
    sentiment: float = 1.0
    onchain: float = 0.0
    portfolio_state: float = 1.5


@dataclass(frozen=True)
class EnvOverrides:
    """PilotShield & transaction cost overrides for a specialist."""

    max_absolute_position: float | None = None
    allow_shorting: bool | None = None
    commission_bps: float | None = None
    slippage_bps: float | None = None
    risk_appetite: int | None = None


# ---------------------------------------------------------------------------
# Specialist definition
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AgentSpecialty:
    """Complete specification for a specialist agent."""

    tag: SpecialistTag
    domain: SpecialistDomain
    name: str
    description: str

    reward: RewardProfile = RewardProfile()
    data_filter: DataFilter = DataFilter()
    feature_boost: FeatureBoost = FeatureBoost()
    env_overrides: EnvOverrides = EnvOverrides()

    # Training hyperparameters overrides
    preferred_algorithm: str = "PPO"
    recommended_timesteps: int = 3_000_000
    n_stack: int = 4

    @property
    def model_name(self) -> str:
        algo = "rppo" if self.preferred_algorithm.upper() in ("RPPO", "RECURRENTPPO") else "ppo"
        return f"{algo}_{self.tag.value}"

    def build_config(self, base_config: MarketEnvConfig | None = None) -> MarketEnvConfig:
        """Create a MarketEnvConfig with this specialist's overrides applied."""
        from .config import DEFAULT_CONFIG

        base = base_config or DEFAULT_CONFIG

        # Apply reward profile
        reward = self.reward.to_reward_weights()

        # Apply env overrides to PilotShield
        shield_kwargs: dict[str, Any] = {}
        if self.env_overrides.max_absolute_position is not None:
            shield_kwargs["max_absolute_position"] = self.env_overrides.max_absolute_position
        if self.env_overrides.allow_shorting is not None:
            shield_kwargs["allow_shorting"] = self.env_overrides.allow_shorting
        if self.env_overrides.risk_appetite is not None:
            shield_kwargs["risk_appetite"] = self.env_overrides.risk_appetite
        pilotshield = PilotShieldLimits(
            max_absolute_position=shield_kwargs.get(
                "max_absolute_position", base.pilotshield.max_absolute_position
            ),
            max_leverage=base.pilotshield.max_leverage,
            risk_appetite=shield_kwargs.get("risk_appetite", base.pilotshield.risk_appetite),
            confidence_threshold=base.pilotshield.confidence_threshold,
            allow_shorting=shield_kwargs.get("allow_shorting", base.pilotshield.allow_shorting),
        )

        # Apply cost overrides
        cost_kwargs: dict[str, Any] = {}
        if self.env_overrides.commission_bps is not None:
            cost_kwargs["commission_bps"] = self.env_overrides.commission_bps
        if self.env_overrides.slippage_bps is not None:
            cost_kwargs["slippage_bps"] = self.env_overrides.slippage_bps
        costs = TransactionCostModel(
            commission_bps=cost_kwargs.get("commission_bps", base.transaction_costs.commission_bps),
            slippage_bps=cost_kwargs.get("slippage_bps", base.transaction_costs.slippage_bps),
            holding_penalty_bps=base.transaction_costs.holding_penalty_bps,
            stochastic_slippage=base.transaction_costs.stochastic_slippage,
            slippage_vol_scale=base.transaction_costs.slippage_vol_scale,
        )

        # Apply feature boosts (modify spec weights)
        boosted_specs = []
        boost_map = {
            "technicals": self.feature_boost.technicals,
            "regime": self.feature_boost.regime,
            "sentiment": self.feature_boost.sentiment,
            "onchain": self.feature_boost.onchain,
            "portfolio_state": self.feature_boost.portfolio_state,
        }
        from .config import FeatureSpec

        for spec in base.feature_specs:
            mult = boost_map.get(spec.name, 1.0)
            boosted_specs.append(
                FeatureSpec(
                    name=spec.name,
                    columns=spec.columns,
                    scaler=spec.scaler,
                    required=spec.required,
                    weight=spec.weight * mult,
                )
            )

        return MarketEnvConfig(
            feature_specs=boosted_specs,
            reward=reward,
            transaction_costs=costs,
            pilotshield=pilotshield,
            schema_version=base.schema_version,
            target_dtype=base.target_dtype,
        )


# ---------------------------------------------------------------------------
# Data filtering
# ---------------------------------------------------------------------------


def apply_data_filter(
    df: pd.DataFrame,
    filt: DataFilter,
    symbol: str | None = None,
) -> pd.DataFrame:
    """Apply a DataFilter to a feature DataFrame, returning filtered rows.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain columns from ``calculate_technical_features()``.
    filt : DataFilter
        Filtering specification.
    symbol : str | None
        Current symbol (used for symbol-level filtering).

    Returns
    -------
    pd.DataFrame
        Filtered (possibly shorter) DataFrame.
    """
    mask = pd.Series(True, index=df.index)

    if filt.regime_focus and "regime" in df.columns:
        mask &= df["regime"] == filt.regime_focus

    if filt.min_atr_pct is not None and "atr_pct" in df.columns:
        mask &= df["atr_pct"] >= filt.min_atr_pct

    if filt.max_atr_pct is not None and "atr_pct" in df.columns:
        mask &= df["atr_pct"] <= filt.max_atr_pct

    if filt.min_volume_ratio is not None and "volume_ratio" in df.columns:
        mask &= df["volume_ratio"] >= filt.min_volume_ratio

    if filt.rsi_range is not None and "rsi" in df.columns:
        low, high = filt.rsi_range
        mask &= (df["rsi"] <= low) | (df["rsi"] >= high)

    if filt.trend_strength_min is not None and "close_ema20_ratio" in df.columns:
        mask &= df["close_ema20_ratio"].abs() >= filt.trend_strength_min

    if filt.symbols_filter is not None and symbol is not None:
        if symbol not in filt.symbols_filter:
            return df.iloc[:0]  # empty

    result = df.loc[mask]

    # Apply lookback window (keep last N rows if specified)
    if filt.lookback_window is not None and len(result) > filt.lookback_window:
        result = result.iloc[-filt.lookback_window :]

    return result


def _normalize_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize a single symbol's close prices to start at 1.0.

    This prevents catastrophic price jumps when concatenating data from
    multiple symbols (e.g. AAPL $180 → MSFT $430 = fake +139% return).
    All price-derived columns are scaled by the same factor so PnL
    calculations remain valid within each symbol segment.
    """
    result = df.copy()
    if "close" in result.columns:
        first_close = result["close"].iloc[0]
        if first_close > 0:
            scale = 1.0 / first_close
            for col in ["close", "open", "high", "low"]:
                if col in result.columns:
                    result[col] = result[col] * scale
    return result


def filter_multi_symbol(
    data: dict[str, pd.DataFrame],
    filt: DataFilter,
) -> pd.DataFrame:
    """Apply DataFilter across multiple symbols and concatenate.

    Each symbol's prices are normalized to start at 1.0 before
    concatenation to prevent cross-symbol price jumps that would
    create artificial PnL spikes in MarketEnv.

    Returns
    -------
    pd.DataFrame
        Concatenated filtered data from all qualifying symbols.
    """
    frames = []
    for symbol, df in data.items():
        filtered = apply_data_filter(df, filt, symbol=symbol)
        if len(filtered) >= 50:  # need minimum data
            frames.append(_normalize_prices(filtered))

    if not frames:
        # Fallback: return all data unfiltered
        frames = [_normalize_prices(df) for df in data.values() if len(df) >= 50]

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# Specialist catalog — the complete library of agents
# ---------------------------------------------------------------------------

SPECIALIST_CATALOG: dict[SpecialistTag, AgentSpecialty] = {
    # ==================================================================
    # REGIME SPECIALISTS (existing, now with refined reward profiles)
    # ==================================================================
    SpecialistTag.TREND: AgentSpecialty(
        tag=SpecialistTag.TREND,
        domain=SpecialistDomain.REGIME,
        name="Trend Follower",
        description="Rides sustained directional moves. High position sizing in trending markets.",
        reward=RewardProfile(
            pnl=10.0,  # Sprint 24: reduced from 12
            drawdown=1.0,  # Sprint 26: 0.8→1.0 + quadratic = aggressive DD control
            cost=0.08,  # Sprint 24: cost awareness
            regime_bonus=0.3,  # Sprint 24: make regime signal matter
            turnover_penalty=0.15,  # Sprint 24: penalise excessive trading
            action_smoothing=0.12,  # Sprint 25: penalise bang-bang action jumps
            sharpe_bonus=0.15,  # Sprint 25: reward risk-adjusted returns
            terminal_dd_penalty=3.0,  # Sprint 26: NEW — α·MaxDD² at episode end
            dd_quadratic=True,  # Sprint 26: NEW — per-step DD² instead of linear
        ),
        data_filter=DataFilter(
            regime_focus="trend",
            trend_strength_min=0.005,
        ),
        feature_boost=FeatureBoost(
            technicals=1.2,  # EMA ratios very important
            regime=1.5,  # regime signal crucial
        ),
        preferred_algorithm="PPO",
        recommended_timesteps=2_000_000,
        n_stack=4,
    ),
    SpecialistTag.RANGE: AgentSpecialty(
        tag=SpecialistTag.RANGE,
        domain=SpecialistDomain.REGIME,
        name="Range Trader",
        description="Mean-reversion in sideways markets. Quick in/out near support/resistance.",
        reward=RewardProfile(
            pnl=10.0,
            drawdown=0.4,  # tighter DD — range trading should have low DD
            cost=0.15,  # higher cost awareness — more frequent trades
            sharpe_bonus=0.1,  # Sharpe matters for frequent small wins
        ),
        data_filter=DataFilter(
            regime_focus="range",
            max_atr_pct=0.03,  # exclude high-vol periods
        ),
        feature_boost=FeatureBoost(
            technicals=1.3,  # BB position & RSI critical
            regime=1.5,
        ),
    ),
    SpecialistTag.VOLATILE: AgentSpecialty(
        tag=SpecialistTag.VOLATILE,
        domain=SpecialistDomain.REGIME,
        name="Volatility Specialist",
        description="Profits from high-volatility events. Defensive positioning, quick exits.",
        reward=RewardProfile(
            pnl=8.0,  # lower PnL weight — survival > profit in vol
            drawdown=0.6,  # strict DD penalty — vol regime is dangerous
            cost=0.1,
            turnover_penalty=0.05,  # avoid overtrading in choppy markets
        ),
        data_filter=DataFilter(
            regime_focus="volatility",
            min_atr_pct=0.02,  # only high-vol data
        ),
        env_overrides=EnvOverrides(
            max_absolute_position=0.5,  # reduced position limits
        ),
        feature_boost=FeatureBoost(
            technicals=1.0,
            regime=2.0,  # regime signal crucial
            sentiment=1.5,  # news often drives vol
        ),
    ),
    # ==================================================================
    # STRATEGY SPECIALISTS (new)
    # ==================================================================
    SpecialistTag.MOMENTUM: AgentSpecialty(
        tag=SpecialistTag.MOMENTUM,
        domain=SpecialistDomain.STRATEGY,
        name="Momentum Hunter",
        description="Identifies and rides strong momentum signals. MACD/volume breakouts.",
        reward=RewardProfile(
            pnl=20.0,  # Sprint 20 Optuna: 14→20 (↑ aggressive PnL)
            drawdown=0.50,  # Sprint 20 Optuna: 0.40→0.50 (↑ DD control)
            cost=0.065,  # Sprint 20 Optuna: 0.08→0.065 (↓ slightly relaxed)
            position_bonus=0.05,  # reward for being in the market
            sharpe_bonus=0.08,  # Sprint 20 Optuna: 0.10→0.08
        ),
        data_filter=DataFilter(
            min_volume_ratio=1.2,  # momentum needs volume confirmation
            trend_strength_min=0.003,  # some directional bias
        ),
        feature_boost=FeatureBoost(
            technicals=1.5,  # MACD, volume ratio very important
            regime=0.8,  # less regime-dependent
            sentiment=1.2,  # sentiment can fuel momentum
        ),
        env_overrides=EnvOverrides(
            commission_bps=3.0,  # NEW: realistic txn costs
            slippage_bps=5.0,
        ),
        preferred_algorithm="PPO",
    ),
    SpecialistTag.MEAN_REVERSION: AgentSpecialty(
        tag=SpecialistTag.MEAN_REVERSION,
        domain=SpecialistDomain.STRATEGY,
        name="Mean Reversion Expert",
        description="Buys oversold, sells overbought. RSI extremes + Bollinger band edges.",
        reward=RewardProfile(
            pnl=10.0,
            drawdown=0.5,  # tight DD — mean-rev fails catastrophically if wrong
            cost=0.15,  # cost-aware — frequent small trades
            sharpe_bonus=0.15,  # Sharpe ratio is key for this strategy
        ),
        data_filter=DataFilter(
            rsi_range=(30, 70),  # focus on RSI extreme zones
            max_atr_pct=0.04,  # don't mean-revert in crashes
        ),
        feature_boost=FeatureBoost(
            technicals=1.5,  # RSI, BB position critical
            regime=1.0,
        ),
        preferred_algorithm="PPO",
    ),
    SpecialistTag.BREAKOUT: AgentSpecialty(
        tag=SpecialistTag.BREAKOUT,
        domain=SpecialistDomain.STRATEGY,
        name="Breakout Detector",
        description="Detects range breakouts via BB width compression then expansion + volume surge.",
        reward=RewardProfile(
            pnl=11.0,
            drawdown=0.3,
            cost=0.08,
            turnover_penalty=0.1,  # avoid false breakout whipsaws
        ),
        data_filter=DataFilter(
            min_volume_ratio=1.5,  # breakouts need volume
        ),
        feature_boost=FeatureBoost(
            technicals=1.5,  # BB width, volume_ratio critical
            regime=1.2,
        ),
        preferred_algorithm="PPO",
    ),
    # ==================================================================
    # TIMEFRAME SPECIALISTS (new)
    # ==================================================================
    SpecialistTag.SCALPER: AgentSpecialty(
        tag=SpecialistTag.SCALPER,
        domain=SpecialistDomain.TIMEFRAME,
        name="Scalper",
        description="Ultra-short-term. Many small trades. Optimised for speed and tight risk.",
        reward=RewardProfile(
            pnl=8.0,
            drawdown=0.6,  # very strict on DD
            cost=0.2,  # highest cost awareness
            sharpe_bonus=0.2,  # Sharpe is everything for scalping
            turnover_penalty=0.0,  # turnover is the point
        ),
        data_filter=DataFilter(
            lookback_window=100,  # short episodes
            min_volume_ratio=0.8,  # need liquid markets
        ),
        env_overrides=EnvOverrides(
            max_absolute_position=0.4,  # small positions
            commission_bps=5.0,  # institutional-grade costs
            slippage_bps=8.0,
        ),
        feature_boost=FeatureBoost(
            technicals=1.3,
            regime=0.5,  # regime less relevant at micro scale
            portfolio_state=2.0,  # own state very important for scalping
        ),
        preferred_algorithm="PPO",
        recommended_timesteps=5_000_000,  # needs more steps for high-frequency policy
        n_stack=8,  # more temporal context
    ),
    SpecialistTag.SWING: AgentSpecialty(
        tag=SpecialistTag.SWING,
        domain=SpecialistDomain.TIMEFRAME,
        name="Swing Trader",
        description="Multi-day holds. Patient entry, rides medium-term waves.",
        reward=RewardProfile(
            pnl=17.0,  # Sprint 20 Optuna: 12→17 (↑↑ stronger PnL)
            drawdown=0.29,  # Sprint 20 Optuna: 0.35→0.29 (↓ slightly relaxed)
            cost=0.03,  # Sprint 20 Optuna: 0.05→0.03 (↓ less cost penalty)
            sharpe_bonus=0.12,  # Sprint 20 Optuna: 0.10→0.12 (↑ Sharpe focus)
            position_bonus=0.03,  # encourage being in market
        ),
        data_filter=DataFilter(
            lookback_window=500,  # longer episodes
        ),
        feature_boost=FeatureBoost(
            technicals=1.2,
            regime=1.3,  # regime important for multi-day holds
            sentiment=1.5,  # news matters at swing scale
        ),
        preferred_algorithm="RPPO",  # LSTM good for longer sequences
        recommended_timesteps=3_000_000,
        n_stack=2,  # less stacking needed with LSTM
    ),
    # ==================================================================
    # RISK STYLE SPECIALISTS (new)
    # ==================================================================
    SpecialistTag.CONSERVATIVE: AgentSpecialty(
        tag=SpecialistTag.CONSERVATIVE,
        domain=SpecialistDomain.RISK,
        name="Conservative Investor",
        description="Capital preservation first. Low drawdown, steady returns. Ideal for risk_appetite ≤ 3.",
        reward=RewardProfile(
            pnl=13.0,  # Sprint 20 Optuna: 8→13 (↑↑ more return-seeking)
            drawdown=0.53,  # Sprint 20 Optuna: 0.8→0.53 (↓ relaxed DD for better returns)
            cost=0.11,  # Sprint 20 Optuna: 0.12→0.11 (↓ slightly relaxed)
            sharpe_bonus=0.43,  # Sprint 20 Optuna: 0.4→0.43 (↑ slightly)
            leverage=0.2,  # penalise leverage
        ),
        data_filter=DataFilter(
            max_atr_pct=0.03,  # skip extremely volatile periods
        ),
        env_overrides=EnvOverrides(
            max_absolute_position=0.3,  # small positions only
            allow_shorting=False,  # long-only
            risk_appetite=3,
            commission_bps=3.0,  # NEW: realistic txn costs
            slippage_bps=5.0,
        ),
        feature_boost=FeatureBoost(
            technicals=1.0,
            regime=1.5,  # regime awareness crucial — avoid vol
            portfolio_state=2.0,  # risk metrics very important
        ),
    ),
    SpecialistTag.AGGRESSIVE: AgentSpecialty(
        tag=SpecialistTag.AGGRESSIVE,
        domain=SpecialistDomain.RISK,
        name="Aggressive Trader",
        description="Maximum return seeking. Higher positions, shorter stops. For risk_appetite ≥ 7.",
        reward=RewardProfile(
            pnl=15.0,  # maximum PnL weight
            drawdown=0.15,  # relaxed DD — accepts larger swings
            cost=0.05,
            position_bonus=0.1,  # encourage being fully invested
        ),
        data_filter=DataFilter(
            min_atr_pct=0.01,  # needs some volatility to profit
            min_volume_ratio=1.0,
        ),
        env_overrides=EnvOverrides(
            max_absolute_position=0.75,
            risk_appetite=8,
        ),
        feature_boost=FeatureBoost(
            technicals=1.3,
            regime=0.8,
            sentiment=1.3,
        ),
    ),
}


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------


def get_specialist(tag: str | SpecialistTag) -> AgentSpecialty:
    """Look up a specialist by tag string or enum."""
    if isinstance(tag, str):
        tag = SpecialistTag(tag)
    return SPECIALIST_CATALOG[tag]


def get_specialists_by_domain(domain: str | SpecialistDomain) -> list[AgentSpecialty]:
    """Return all specialists in a given domain."""
    if isinstance(domain, str):
        domain = SpecialistDomain(domain)
    return [s for s in SPECIALIST_CATALOG.values() if s.domain == domain]


def list_all_tags() -> list[str]:
    """Return all available specialist tag strings."""
    return [t.value for t in SPECIALIST_CATALOG]


def get_default_ensemble_tags() -> list[str]:
    """Return the recommended set of specialists for ensemble prediction.

    Sprint 19 analysis selected the top-3 by implied Sharpe (Return/DD):
      - momentum  (strategy)  — highest Sharpe 0.05, +22% return
      - swing     (timeframe) — best Return/DD 1.02, +22.6% return, LSTM
      - conservative (risk)   — lowest DD 12.5%, capital preservation

    This trio maximises domain diversity (strategy + timeframe + risk)
    and balances aggression (momentum/swing) with defence (conservative).
    """
    return ["momentum", "swing", "conservative"]


__all__ = [
    "SpecialistDomain",
    "SpecialistTag",
    "AgentSpecialty",
    "RewardProfile",
    "DataFilter",
    "FeatureBoost",
    "EnvOverrides",
    "SPECIALIST_CATALOG",
    "get_specialist",
    "get_specialists_by_domain",
    "list_all_tags",
    "get_default_ensemble_tags",
    "apply_data_filter",
    "filter_multi_symbol",
    "_normalize_prices",
]
