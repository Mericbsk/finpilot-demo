"""Configuration objects for the FinPilot DRL stack.

These dataclasses define how features are constructed, which penalties are
applied inside the reward function, and how PilotShield risk controls clamp the
agent's actions.  A single ``MarketEnvConfig`` instance should be shared by the
feature pipeline, environment, and training utilities to guarantee consistent
behaviour across batch, paper-trading, and live deployments.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


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
    """Hyper-parameters for reward shaping.

    Sprint 18 — Reward simplification:
    Previous 9-term reward caused conflicting gradients (inactivity vs drawdown),
    preventing convergence.  Reduced to 3 core terms so the agent learns a clear
    PnL signal first.  Secondary terms preserved at weight=0 for future re-activation.
    """

    pnl: float = 10.0  # PRIMARY: scaled PnL — the core learning signal
    drawdown: float = 0.3  # PRIMARY: penalise drawdown (reduced from 0.5)
    cost: float = 0.1  # PRIMARY: transaction cost awareness
    leverage: float = 0.0  # DISABLED Sprint 18: folded into PilotShield clamp
    regime_bonus: float = 0.0  # DISABLED Sprint 18: noisy — re-enable after convergence
    turnover_penalty: float = 0.0  # DISABLED Sprint 18: conflicts with exploration
    sharpe_bonus: float = 0.0  # DISABLED Sprint 18: re-enable in Faz 2 after base PnL learned
    inactivity_penalty: float = 0.0  # DISABLED Sprint 18: conflicts with drawdown penalty
    position_bonus: float = 0.0  # DISABLED Sprint 18: conflicts with turnover penalty
    action_smoothing: float = 0.0  # Sprint 25: penalise large action jumps to prevent bang-bang
    terminal_dd_penalty: float = 0.0  # Sprint 26: quadratic terminal DD ceza (α·MaxDD²)
    dd_quadratic: bool = False  # Sprint 26: per-step DD² instead of linear DD


@dataclass(frozen=True)
class TransactionCostModel:
    """Settings that approximate execution frictions."""

    commission_bps: float = 10.0
    slippage_bps: float = 15.0
    holding_penalty_bps: float = 0.0  # Sprint 14: zeroed — was penalising desired behaviour
    stochastic_slippage: bool = True  # Sprint 13: volume-dependent noise
    slippage_vol_scale: float = 0.5  # multiplier for low-volume impact


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
    def feature_columns(self) -> list[str]:
        cols: list[str] = []
        for spec in self.feature_specs:
            cols.extend(spec.columns)
        return cols


DEFAULT_FEATURE_SPECS: list[FeatureSpec] = [
    FeatureSpec(
        name="technicals",
        columns=[
            # Sprint 18 Phase 3.2 — Symbol-agnostic relative features.
            # All ratios/percentages; no absolute price or volume values.
            "close_ema20_ratio",  # price vs short-term trend
            "ema20_ema50_ratio",  # short vs medium trend alignment
            "ema50_ema200_ratio",  # medium vs long trend alignment
            "rsi",  # already 0-100, symbol-agnostic
            "macd_norm",  # MACD / ATR (scale-free momentum)
            "macd_signal_norm",  # MACD signal / ATR
            "macd_hist_norm",  # MACD histogram / ATR
            "atr_pct",  # ATR / close  (volatility %)
            "bb_width",  # Bollinger width / close
            "bb_position",  # position inside Bollinger (0-1)
            "volume_ratio",  # volume / 20d avg volume
        ],
        scaler="robust",  # robust scaling — resilient to outliers in ratios
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
        weight=0.0,  # Sprint 16: zeroed — placeholder data provides no signal
    ),
    FeatureSpec(
        name="portfolio_state",
        columns=["cash_ratio", "position_ratio", "open_risk", "kelly_fraction"],
        scaler="minmax",
        weight=1.5,  # Sprint 16: boosted — these are now dynamically simulated
    ),
    # INT-6: Qlib Alpha158-inspired feature group
    # 25 new features: ROC series (5), STD series (4), multi-period RSI (4),
    # price-volume correlation (3), candlestick features (5), extended EMA ratios (4).
    # required=False: training continues without these if data_loader
    # doesn't call calculate_alpha158_features().
    FeatureSpec(
        name="alpha158",
        columns=[
            # Rate of Change series
            "roc_5",
            "roc_10",
            "roc_20",
            "roc_30",
            "roc_60",
            # Rolling volatility series
            "std_5",
            "std_10",
            "std_20",
            "std_30",
            # Multi-period RSI
            "rsi_5",
            "rsi_10",
            "rsi_20",
            "rsi_30",
            # Price-volume correlation
            "corr_pv_5",
            "corr_pv_10",
            "corr_pv_20",
            # Candlestick features
            "kmid",
            "klen",
            "kmid2",
            "kup",
            "kdn",
            # Extended EMA ratios
            "close_ema5_ratio",
            "close_ema10_ratio",
            "close_ema30_ratio",
            "close_ema60_ratio",
        ],
        scaler="robust",
        required=False,  # gracefully skipped if not computed
        weight=0.8,  # slightly downweighted until validated in backtest
    ),
]


DEFAULT_CONFIG = MarketEnvConfig(feature_specs=DEFAULT_FEATURE_SPECS)
"""Default configuration used by the CLI utilities and demo harnesses."""
