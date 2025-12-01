"""Configuration objects for the FinPilot DRL stack.

These dataclasses define how features are constructed, which penalties are
applied inside the reward function, and how PilotShield risk controls clamp the
agent's actions.  A single ``MarketEnvConfig`` instance should be shared by the
feature pipeline, environment, and training utilities to guarantee consistent
behaviour across batch, paper-trading, and live deployments.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Optional, Sequence


@dataclass(frozen=True)
class FeatureSpec:
    """Represents a coherent group of features and their scaling strategy.

    Attributes
    ----------
    name:
        Human-readable identifier, e.g. ``"technicals"`` or ``"sentiment"``.
    columns:
        Ordered list of column names expected in the raw feature frame.
    scaler:
        Scaling strategy identifier. ``"zscore"`` for mean/std normalisation,
        ``"robust"`` for median/IQR scaling, ``"minmax"`` for (0, 1) scaling.
    required:
        Whether the columns must exist at runtime. If ``False`` the pipeline
        will skip missing columns instead of raising.
    weight:
        Optional multiplier applied to the feature group during scaling; useful
        for boosting the impact of certain inputs.
    """

    name: str
    columns: Sequence[str]
    scaler: str = "zscore"
    required: bool = True
    weight: float = 1.0


@dataclass(frozen=True)
class RewardWeights:
    """Hyper-parameters for reward shaping."""

    pnl: float = 1.0
    drawdown: float = 1.0
    cost: float = 0.1
    leverage: float = 0.2
    regime_bonus: float = 0.05


@dataclass(frozen=True)
class TransactionCostModel:
    """Settings that approximate execution frictions."""

    commission_bps: float = 10.0
    slippage_bps: float = 15.0
    holding_penalty_bps: float = 0.0


@dataclass(frozen=True)
class PilotShieldLimits:
    """Global risk guardrails that clamp the agent's behaviour."""

    max_absolute_position: float = 0.75
    max_leverage: float = 1.5
    risk_appetite: int = 5  # 1-10 slider exported from the UX layer
    confidence_threshold: float = 0.65
    allow_shorting: bool = True


@dataclass(frozen=True)
class MarketEnvConfig:
    """Container for all environment-wide parameters."""

    feature_specs: Sequence[FeatureSpec]
    reward: RewardWeights = RewardWeights()
    transaction_costs: TransactionCostModel = TransactionCostModel()
    pilotshield: PilotShieldLimits = PilotShieldLimits()
    schema_version: str = "1.0.0"
    target_dtype: str = "float32"

    @property
    def feature_columns(self) -> List[str]:
        cols: List[str] = []
        for spec in self.feature_specs:
            cols.extend(spec.columns)
        return cols


DEFAULT_FEATURE_SPECS: List[FeatureSpec] = [
    FeatureSpec(
        name="technicals",
        columns=[
            "close",
            "ema_20",
            "ema_50",
            "ema_200",
            "rsi",
            "macd",
            "macd_signal",
            "macd_hist",
            "atr",
            "bb_upper",
            "bb_lower",
            "volume",
            "volume_avg_20",
        ],
        scaler="zscore",
    ),
    FeatureSpec(
        name="regime",
        columns=["regime_trend", "regime_range", "regime_volatility"],
        scaler="none",
    ),
    FeatureSpec(
        name="sentiment",
        columns=["sentiment_score", "news_sentiment"],
        scaler="robust",
        required=False,
    ),
    FeatureSpec(
        name="onchain",
        columns=["onchain_active_addresses", "onchain_tx_volume"],
        scaler="robust",
        required=False,
    ),
    FeatureSpec(
        name="portfolio_state",
        columns=["cash_ratio", "position_ratio", "open_risk", "kelly_fraction"],
        scaler="minmax",
    ),
]


DEFAULT_CONFIG = MarketEnvConfig(feature_specs=DEFAULT_FEATURE_SPECS)
"""Default configuration used by the CLI utilities and demo harnesses."""
